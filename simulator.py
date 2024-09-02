import json
import logging
import simulator_logger
import simulator_config
import environment_manager
import stix2
import attack_flow_model as attack_model
import os
import utils
from functools import cmp_to_key
import time
import datetime
import time


exec_logger = logging.getLogger(simulator_config.execution_logger_name)
sim_logger = logging.getLogger(simulator_config.simulation_logger_name)


class CommonAssets:
    assets = {
        environment_manager.HostTypes.TargetFirstWindows: attack_model.AttackAsset(
            name='asset',
            description=environment_manager.HostTypes.TargetFirstWindows.name,
            extensions={
                 "extension-definition--fb9c968a-745b-4ade-9b25-c324172197f4": {
                 "extension_type": "new-sdo"}}),
        environment_manager.HostTypes.Attacker: attack_model.AttackAsset(
            name='asset',
            description=environment_manager.HostTypes.Attacker.name,
            extensions={
                 "extension-definition--fb9c968a-745b-4ade-9b25-c324172197f4": {
                 "extension_type": "new-sdo"}}),
        environment_manager.HostTypes.TargetLaterMovement: attack_model.AttackAsset(
            name='asset',
            description=environment_manager.HostTypes.TargetLaterMovement.name,
            extensions={
                 "extension-definition--fb9c968a-745b-4ade-9b25-c324172197f4": {
                 "extension_type": "new-sdo"}})
    }


class Action:
    def __init__(self, technique_id, name, target: environment_manager.HostTypes):
        self.technique_id = technique_id
        self.target = target
        self.name = name
        self.raw_action = Action.get_action_by_name(self.technique_id, self.name)
        self.flow_action = None
        self.flow_targets = None
        self.flow_command = None
        self.flow_next = None
        self.linked_actions = None

    def __repr__(self):
        return f'{self.technique_id}:{self.name}'

    def create_flow_data(self, next_action):
        additional_effects = []
        for linked_actions in self.raw_action['actions_included']:
            if linked_actions:
                additional_effects.append(attack_model.AttackAction(name=linked_actions,
                                                                    technique_id=linked_actions,
                                                                    description='Inherited or executed simultaneously',
                                                                     extensions={
                                                                         "extension-definition--fb9c968a-745b-4ade-9b25-c324172197f4": {
                                                                         "extension_type": "new-sdo"}}))
        self.flow_targets = CommonAssets.assets[self.target]
        self.flow_command = stix2.Process(command_line=Action.get_commands(self.technique_id, self.name))
        if not next_action:
            self.flow_action = attack_model.AttackAction(name=self.technique_id,
                                                         technique_id=self.technique_id,
                                                         description=self.raw_action['name'],
                                                         asset_refs=self.flow_targets,
                                                         command_ref=self.flow_command,
                                                         effect_refs=additional_effects,
                                                         extensions={
                                                             "extension-definition--fb9c968a-745b-4ade-9b25-c324172197f4": {
                                                             "extension_type": "new-sdo"}})
        else:
            set_up_config = Action.get_set_up_config(next_action.technique_id, next_action.name)
            next_obj = None
            if set_up_config['target']['required']:
                script_file_name = simulator_config.enviroment_scripts_folder + set_up_config['target']['script_file']
                description = f'{set_up_config['target']['script_file'].split('.')[0]} => '
                description += utils.get_script_from_script_file(script_file_name)
                in_args = {}
                for arg in next_action.raw_action['input_args']:
                    in_args.update({arg['name']: arg['value']})
                in_args.update(**utils.propagate_random_arguments())
                if 'ip_target' not in in_args:
                    in_args.update({'ip_target': 'ip_target_random'})
                if 'ip_attacker' not in in_args:
                    in_args.update({'ip_attacker': 'ip_attacker_random'})
                try:
                    description = description.format(**in_args)
                except KeyError as e:
                    exec_logger.error(f'Arguments for {str(next_action)} can not be resolved in {script_file_name} {e}')
                next_obj = attack_model.AttackCondition(description=description,
                                                        on_true_refs=next_action.flow_action,
                                                        extensions={
                                                             "extension-definition--fb9c968a-745b-4ade-9b25-c324172197f4": {
                                                             "extension_type": "new-sdo"}})
            if not next_obj:
                next_obj = next_action.flow_action
            self.flow_next = next_obj
            self.linked_actions = additional_effects
            self.flow_action = attack_model.AttackAction(name=self.technique_id,
                                                         technique_id=self.technique_id,
                                                         description=self.raw_action['name'],
                                                         asset_refs=self.flow_targets,
                                                         effect_refs=[next_obj,] + additional_effects,
                                                         command_ref=self.flow_command,
                                                         extensions={
                                                             "extension-definition--fb9c968a-745b-4ade-9b25-c324172197f4": {
                                                             "extension_type": "new-sdo"}}
                                                         )

    @staticmethod
    def get_commands(technique_id, action_name, dynamic_args: dict = None):
        action = Action.get_action_by_name(technique_id, action_name)
        file_with_commands = simulator_config.actions_folder + action['commands_file']
        raw_commands = ';'.join(utils.read_strings_from_file(file_with_commands))
        in_args = {}
        for arg in action['input_args']:
            in_args.update({arg['name']: arg['value']})
        if dynamic_args:
            in_args.update(dynamic_args)
        in_args.update(**utils.propagate_random_arguments())
        try:
            return raw_commands.format(**in_args)
        except KeyError as e:
            exec_logger.error(f'Argument {e} for {str(action)} in {file_with_commands} not defined!')
            exit(-1)

    @staticmethod
    def get_set_up_config(technique_id, action_name):
        action = Action.get_action_by_name(technique_id, action_name)
        return action['set_up']

    @staticmethod
    def get_action_by_name(technique_id, action_name):
        data = Action.load_raw_action_from_file(technique_id)
        for a in data['actions']:
            if a['name'] == action_name:
                return a
        exec_logger.error(f'Action {action_name} for {technique_id} not found within defined file.')

    @staticmethod
    def add_action_to_db(action_data):
        action_file = simulator_config.actions_folder + action_data['technique_id'] + '.json'
        if os.path.exists(action_file):
            exec_logger.error(f'File for actions already exists {action_file}')
            return
        action_data.update({'actions': []})
        with open(action_file, 'w') as f:
            json.dump(action_data, f)

    @staticmethod
    def update_input_argument(technique, action, original_name, new_data):
        data = Action.load_raw_action_from_file(technique)
        for a in data['actions']:
            if a['name'] == action:
                for i, i_obj in enumerate(a['input_args']):
                    if i_obj['name'] == original_name:
                        del a['input_args'][i]
                        break
                if new_data:
                    a['input_args'].append(new_data)
        Action.update_action_file(technique, data)

    @staticmethod
    def update_action_file(technique_id, data):
        with open(simulator_config.actions_folder + technique_id + '.json', 'w') as f:
            json.dump(data, f, indent=4)

    @staticmethod
    def add_action_to_action(technique_id, action_data):
        data = Action.load_raw_action_from_file(technique_id)
        data['actions'].append(action_data)
        Action.update_action_file(technique_id, data)

    @staticmethod
    def load_raw_action_from_file(technique_id):
        return utils.get_json_data(simulator_config.actions_folder + technique_id + '.json')

    @staticmethod
    def update_action(technique_id, action, new_data):
        data = Action.load_raw_action_from_file(technique_id)
        for i,a in enumerate(data['actions']):
            if a['name'] == action:
                if new_data:
                    data['actions'][i].update(new_data)
                else:
                    del data['actions'][i]
                break
        Action.update_action_file(technique_id, data)

    @staticmethod
    def update_set_up(technique_id, action, side, new_data):
        data = Action.load_raw_action_from_file(technique_id)
        for a in data['actions']:
            if a['name'] == action:
                a['set_up'][side].update(new_data)
                break
        Action.update_action_file(technique_id, data)

    @staticmethod
    def update_technique(technique_id, new_data):
        data = Action.load_raw_action_from_file(technique_id)
        data.update(new_data)
        Action.update_action_file(technique_id, data)


class Plan:
    def __init__(self):
        self.actions = []
        self.name = None
        self.description = None

    def __repr__(self):
        return f'{self.name}: {self.actions}'

    def load_plan(self, plan_name):
        plan_data = utils.get_json_data(simulator_config.plans_folder + plan_name + '.json')
        self.name = plan_data['name']
        self.description = plan_data['description']
        for a in plan_data['actions']:
            for i in environment_manager.HostTypes:
                if i.name == a['target']:
                    real_target = i
                    break
            action = Action(technique_id=a['technique_id'],
                                       name=a['name'],
                                       target=real_target)
            self.actions.append(action)
        for i in range(len(self.actions) - 1, -1, -1):
            if i == (len(self.actions) - 1):
                self.actions[i].create_flow_data(None)
            else:
                self.actions[i].create_flow_data(self.actions[i+1])

    def create_flow(self, result_folder):
        a = attack_model.AttackFlow(name=self.name,
                                    start_refs=[self.actions[0].flow_action],
                                    scope='other',
                                    description=self.description,
                                    extensions={
                                        "extension-definition--fb9c968a-745b-4ade-9b25-c324172197f4": {
                                            "extension_type": "new-sdo"}})
        with open(r'configs/attack_flow_ext.json') as f:
            att_ex = json.load(f)
        att_ex = stix2.ExtensionDefinition(**att_ex)
        list_for_bundle = [a, att_ex]
        for i in self.actions:
            list_for_bundle.append(i.flow_action)
            list_for_bundle.append(i.flow_targets)
            list_for_bundle.append(i.flow_command)
            if i.flow_next:
                if isinstance(i.flow_next, attack_model.AttackCondition):
                    list_for_bundle.append(i.flow_next)
            if i.linked_actions:
                list_for_bundle += i.linked_actions
        b = stix2.Bundle(*list_for_bundle)
        with open(result_folder + self.name + '_flow.json', 'w') as f:
            f.write(b.serialize(pretty=True))


class SimulationConfiguration:
    def __init__(self, configuration):
        self.configuration = configuration
        self.initial_configuration = self.configuration['on_start']
        self.post_scripts = self.configuration['on_end']


class Simulator:
    def __init__(self, env_manager: environment_manager.EnviromentManager,
                 plans: list[str],
                 simulation_config: SimulationConfiguration):
        self.env_mng = env_manager
        self.plans = plans
        self.simulation_config = simulation_config

    def _check_success_or_delay(self, delay=simulator_config.common_execution_delay,
                                check_by=None, target=None,
                                recursive=False):
        if not check_by or not target:
            exec_logger.debug(f'Execution after operation is simply delayed by {delay} seconds.')
            time.sleep(delay)
            return True
        check_mode_log_str = 'recursive' if recursive else 'once'
        exec_logger.debug(f'Operation success will by checked by {check_by} on {target} in "{check_mode_log_str}" mode.')
        if check_by.get('file_created', False):
            res = self.env_mng.run_script_file(script_file_path=simulator_config.enviroment_scripts_folder + 'check_file.json',
                                               target=target, custom_args=check_by['args'])
            if recursive and not res:
                return self._check_success_or_delay(delay, check_by, target, recursive)
            return res
        if check_by.get('process_created', False):
            res = self.env_mng.run_script_file(script_file_path=simulator_config.enviroment_scripts_folder + 'check_process.json',
                                               target=target, custom_args=check_by['args'])
            if recursive and not res:
                return self._check_success_or_delay(delay, check_by, target, recursive)
            return res

    def _resolve_arguments_for_config(self, runtime_args):
        dynamic_args = {}
        dynamic_args.update(utils.propagate_random_arguments())
        for host in self.env_mng.hosts:
            dynamic_args.update(host.dynamic_parameters)
        dynamic_args.update(runtime_args)
        for item in self.simulation_config.initial_configuration:
            for key, val in item['args'].items():
                if isinstance(val, str):
                    item['args'][key] = val.format(**dynamic_args)

        for item in self.simulation_config.post_scripts:
            for key, val in item['args'].items():
                if isinstance(val, str):
                    item['args'][key] = val.format(**dynamic_args)

    def _resolve_dynamic_arguments(self, action: Action):
        in_args = {}
        for arg in action.raw_action['input_args']:
            in_args.update({arg['name']: arg['value']})
        in_args.update(utils.propagate_random_arguments())
        for h in self.env_mng.hosts:
            in_args.update(h.dynamic_parameters)
        exec_logger.debug(f'Arguments for set up resolved {in_args}')
        return in_args

    def prepare_environment_for_action(self, action: Action):
        set_up = action.raw_action['set_up']
        things_to_set_up = []
        if set_up['target']['required']:
            set_up['target'].update({'target': True})
            things_to_set_up.append(set_up['target'])
        if set_up['attacker']['required']:
            set_up['attacker'].update({'attacker': True})
            things_to_set_up.append(set_up['attacker'])
        things_to_set_up.sort(key=cmp_to_key(lambda i1, i2: int(i1['priority']) - int(i2['priority'])))
        exec_logger.debug(f'Defining things to set up for {str(action)}. Set up list: {things_to_set_up}')

        in_args = self._resolve_dynamic_arguments(action)

        for set_item in things_to_set_up:
            if 'attacker' in set_item:
                target = environment_manager.HostTypes.Attacker
            else:
                target = action.target
            file_with_script = simulator_config.enviroment_scripts_folder + set_item['script_file']
            exec_logger.debug(f'Running set up script {file_with_script} on {target} for {str(action)}')
            self.env_mng.run_script_file(file_with_script, target, in_args)
            self._check_success_or_delay()

    def execute_action(self, action: Action):
        commands_file = simulator_config.actions_folder + action.raw_action['commands_file']
        in_args = self._resolve_dynamic_arguments(action)
        commands = '\n'.join(utils.read_strings_from_file(commands_file))
        commands = commands.format(**in_args)
        exec_logger.debug(f'Commands for {str(action)} execution is prepared: {commands.replace('\n', ';')}')
        handler_script = simulator_config.enviroment_scripts_folder + 'write_commands_to_attacker_remote_handler.json'
        if action.target == environment_manager.HostTypes.Attacker:
            commands = commands.replace('\n', ';')
            in_args.update({'command': commands})
            self.env_mng.run_script_file('enviroment_scripts/run_program_linux.json',
                                         environment_manager.HostTypes.Attacker,
                                         custom_args=in_args)
            self._check_success_or_delay(delay=simulator_config.common_execution_delay*2)
            return
        for c in commands.split('\n'):
            in_args.update({'commands': c})
            self.env_mng.run_script_file(handler_script,
                                         environment_manager.HostTypes.Attacker,
                                         custom_args=in_args)
            self._check_success_or_delay(simulator_config.common_execution_delay/4)
        self._check_success_or_delay(simulator_config.common_execution_delay*4)

    def run_pre_simulation_scripts(self):
        for scr in self.simulation_config.initial_configuration:
            exec_logger.debug(f'Pre-simulation script: {scr['script']} with {scr['args']}')
            self.env_mng.run_script_file(scr['script'], environment_manager.HostTypes[scr['target']],
                                         custom_args=scr['args'])
            self._check_success_or_delay(simulator_config.common_execution_delay)

    def run_post_simulation_scripts(self):
        self._check_success_or_delay(simulator_config.common_execution_delay*10)
        for scr in self.simulation_config.post_scripts:
            exec_logger.debug(f'Post-simulation script: {scr['script']} with {scr['args']}')
            self.env_mng.run_script_file(scr['script'], environment_manager.HostTypes[scr['target']],
                                         custom_args=scr['args'])
            self._check_success_or_delay(simulator_config.common_execution_delay * 9)

    def execute_plans(self):
        current_datetime = datetime.datetime.now()
        simulation_result_folder = f'simulation_results_{current_datetime.strftime("%Y_%m_%d_%H_%M")}/'
        os.makedirs(simulation_result_folder)
        exec_logger.info(f'Simulation results will be saved to {simulation_result_folder}')

        for p in self.plans:
            plan_result_folder = f'{simulation_result_folder}/plan_{p.replace(' ', '_')}_results/'
            self._resolve_arguments_for_config(runtime_args={'results_folder': plan_result_folder})
            exec_logger.info(f'Start plan {str(p)} execution, result will be save to {plan_result_folder}')
            os.makedirs(plan_result_folder)

            self.env_mng.start_environment()
            current_plan = Plan()
            current_plan.load_plan(p)
            current_plan.create_flow(plan_result_folder)

            exec_logger.info(f'Running pre-simulation scripts')
            self.run_pre_simulation_scripts()

            exec_logger.info(f'Building environment for {str(p)}')
            for a in current_plan.actions:
                self.prepare_environment_for_action(a)
                exec_logger.info(f'Environment prepared for {str(a)}')

            exec_logger.info(f'Actions execution started for {str(p)}')
            for a in current_plan.actions:
                self.execute_action(a)
                exec_logger.info(f'Action executed {str(a)}')

            exec_logger.info(f'Running post-simulation scripts')
            self.run_post_simulation_scripts()

            self.env_mng.shut_down_environment()
            exec_logger.info(f'Simulation for {str(p)} finished. Results in {plan_result_folder}')
        exec_logger.info('SIMULATION EXIT')







