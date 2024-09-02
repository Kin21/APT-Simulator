import json
import pprint
import time
from enum import Enum, auto
import requests
import simulator_config
import logging
import subprocess
import base64
import utils
import os


exec_logger = logging.getLogger(simulator_config.execution_logger_name)
sim_logger = logging.getLogger(simulator_config.simulation_logger_name)


class HostTypes(Enum):
    TargetFirstWindows = auto()
    TargetFirstLinux = auto()
    TargetLaterMovement = auto()
    Attacker = auto()
    TransparentRouter = auto()


class HostStates(Enum):
    Stopped = auto()
    Running = auto()
    Ready = auto()


class HostPlatform(Enum):
    LinuxGeneric = auto()
    WindowsGeneric = auto()
    WindowsAD = auto()


WindowsBasedHosts = [HostPlatform.WindowsGeneric, HostPlatform.WindowsAD, ]
LinuxBasedHosts = [HostPlatform.LinuxGeneric, ]


class VMWarePowerStates:
    ON = 'poweredOn'
    OFF = 'poweredOff'
    SHUTDOWN = 'shutdown'
    SUSPEND = 'suspended'
    PAUSE = 'paused'


class Host:
    def __init__(self, host_type: HostTypes, host_platform: HostPlatform):
        self.host_type = host_type
        self.state = None
        self.platform = host_platform
        self.dynamic_parameters = {}

    def start(self):
        pass

    def stop(self):
        pass

    def revert(self):
        """
        Revert host to state that was before simulation started.
        """
        pass

    def get_state(self):
        """
        Return either host in stop or running state and if simulation can be started.
        """
        pass

    def execute_command(self, command: str = None, interpreter_on_guest: str = None, local_file_with_commands: str = None):
        """
        Interface to execute command inside host.
        """
        pass

    def start_program(self, command: str = None, arguments: str = None):
        """
        Interface to start program inside host with arguments
        """
        pass

    def sent_file(self, local_file_path, host_file_path):
        pass

    def get_file(self, host_file_path, local_file_path):
        pass

    def wait_for_ready_state(self):
        pass


class VMWareWorkstationProHost(Host):
    vmware_api_session = requests.session()
    vmware_api_session.auth = (simulator_config.vmware_api_username, simulator_config.vmware_api_password)
    vmware_api_session.headers.update({'Accept': 'application/vnd.vmware.vmw.rest-v1+json',
                                       'Content-Type': 'application/vnd.vmware.vmw.rest-v1+json'})

    def __init__(self, host_type: HostTypes, host_platform: HostPlatform,
                 vm_path, vm_id=None):
        super().__init__(host_type, host_platform)
        self.vm_path = vm_path
        self.vm_id = vm_id
        self._get_my_id()
        exec_logger.debug(f'VMWareWorkstationPro host - [{str(self)}] - initialized.')

    def __str__(self):
        return f'[{str(self.host_type)}:{str(self.vm_path).split('\\')[-1]}]'

    def _get_my_id(self):
        r = self.vmware_api_session.get(f'{simulator_config.vmware_api_url}/vms')
        for i in r.json():
            if i['path'] == self.vm_path:
                self.vm_id = i['id']
                exec_logger.debug(f'VMWare API request for ID for {str(self)}.')
                return
        exec_logger.error(f'VMWare API ID for {str(self)} NOT FOUND !')
        exit(-1)

    def _get_my_snapshots(self):
        ps_command = f'& "{simulator_config.vmware_vmrun_binary_path}" listSnapshots "{self.vm_path}"'
        output = utils.powershell_execute_wrapper(ps_command)
        exec_logger.debug(f'VMWare vmrun retrieving snapshots for {str(self)}. Raw results: Errors: {output.stderr.replace('\n', ' ')} Output: {output.stdout.replace('\n', ' ')}')
        snapshots_out_list = output.stdout.split('\n')
        total_snapshots = int(snapshots_out_list[0].split(':')[-1])
        snapshots_out_list = snapshots_out_list[1:-1]
        exec_logger.debug(f'VMWare vmrun retrieving snapshots for {str(self)}. Results: Total:{total_snapshots}, Snapshots: {','.join(snapshots_out_list)}')
        return total_snapshots, snapshots_out_list

    def get_state(self):
        r = self.vmware_api_session.get(f'{simulator_config.vmware_api_url}/vms/{self.vm_id}/power')
        exec_logger.debug(f'Getting PowerState for VM: {self.vm_path}:{self.vm_id} - Result: {r.status_code} {r.text}'.replace('\n', ' '))
        if r.status_code != 200:
            exec_logger.warning(f'Bad HTTP response code while getting VM Power State')
            exit(-1)
        if r.json()['power_state'] == VMWarePowerStates.ON:
            return self.state if self.state else HostStates.Running
        elif r.json()['power_state'] == VMWarePowerStates.OFF:
            return HostStates.Stopped

    def wait_for_os_boot(self):
        exec_logger.info(f'Wait for OS boot for {str(self)}')
        commands, output = self.execute_command(local_file_with_commands=simulator_config.enviroment_scripts_folder+'create_test_file_on_os_start.txt')
        while output.stderr or output.stdout:
            time.sleep(simulator_config.wait_for_os_boot_timer)
            commands, output = self.execute_command(local_file_with_commands=simulator_config.enviroment_scripts_folder+'create_test_file_on_os_start.txt')
        exec_logger.info(f'OS booted, host {str(self)} -> Ready. Raw results: Errors: {output.stderr.replace('\n', ' ')} Output: {output.stdout.replace('\n', ' ')}')
        self.state = HostStates.Ready

    def wait_for_ready_state(self):
        self.wait_for_os_boot()

    def start(self):
        r = self.vmware_api_session.put(f'{simulator_config.vmware_api_url}/vms/{self.vm_id}/power',
                                        data='on')
        exec_logger.debug(
            f'VMWare API request to power on VM: {str(self)} - Result: {r.status_code} {r.text}'.replace('\n', ' '))
        return r.status_code == 200

    def stop(self):
        r = self.vmware_api_session.put(f'{simulator_config.vmware_api_url}/vms/{self.vm_id}/power',
                                        data='off')
        exec_logger.debug(f'VMWare API request to shutdown VM: {str(self)} - Result: {r.status_code} {r.text}'.replace('\n', ' '))
        return r.status_code == 200

    def revert(self):
        total_snaps, snaps = self._get_my_snapshots()
        if simulator_config.simulation_base_snapshot_name not in snaps:
            exec_logger.error(f'Base snapshot not found for {str(self)}, impossible to revert environment.')
            return
        ps_command = f'& "{simulator_config.vmware_vmrun_binary_path}" revertToSnapshot "{self.vm_path}" {simulator_config.simulation_base_snapshot_name}'
        output = utils.powershell_execute_wrapper(ps_command)
        exec_logger.debug(f'VMWare vmrun reverting to base snapshot {simulator_config.simulation_base_snapshot_name} for {str(self)}. Raw results: Errors: {output.stderr.replace('\n', ' ')} Output: {output.stdout.replace('\n', ' ')}')

    def execute_commands_from_file(self, local_file_with_commands, interpreter_on_guest):
        if self.platform in WindowsBasedHosts:
            commands_in_guest = ''.join(utils.read_strings_from_file(local_file_with_commands))
            exec_logger.debug(f'VMWare command to execute on {str(self)} received: {commands_in_guest.replace('\n', ';')}')
            commands_in_guest_bytes = commands_in_guest.encode('utf-16le')
            encoded_commands_in_guest = base64.b64encode(commands_in_guest_bytes).decode('ascii')
            ps_command = f'& "{simulator_config.vmware_vmrun_binary_path}" -T ws -gu "{simulator_config.vmware_root_login}" -gp {simulator_config.vmware_root_password} runProgramInGuest "{self.vm_path}" -noWait -interactive "{interpreter_on_guest}" "Start-Process powershell.exe -ArgumentList \'-EncodedCommand {encoded_commands_in_guest}\' -Verb RunAs"'
            exec_logger.debug(f'VMWare raw command to run vmrun: {ps_command}')
            command_bytes = ps_command.encode('utf-16le')
            encoded_command = base64.b64encode(command_bytes).decode('ascii')
            output = subprocess.run(['powershell.exe', '-EncodedCommand', encoded_command], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            exec_logger.debug(f'VMWare vmrun output: Errors: {output.stderr} Output: {output.stdout}')
            return encoded_commands_in_guest, output
        else:
            commands_in_guest = ''.join(utils.read_strings_from_file(local_file_with_commands))
            exec_logger.debug(f'VMWare command to execute on {str(self)} received: {commands_in_guest.replace('\n', ';')}')
            commands_in_guest_bytes = commands_in_guest.encode()
            encoded_commands_in_guest = base64.b64encode(commands_in_guest_bytes).decode('ascii')
            ps_command = f'& "{simulator_config.vmware_vmrun_binary_path}" -T ws -gu "{simulator_config.vmware_root_login}" -gp {simulator_config.vmware_root_password} runScriptInGuest "{self.vm_path}" "{interpreter_on_guest}" "echo {encoded_commands_in_guest} | base64 -d | {interpreter_on_guest}"'
            exec_logger.debug(f'VMWare raw command to run vmrun: {ps_command}')
            command_bytes = ps_command.encode('utf-16le')
            encoded_command = base64.b64encode(command_bytes).decode('ascii')
            output = subprocess.run(['powershell.exe', '-EncodedCommand', encoded_command], stdout=subprocess.PIPE,stderr=subprocess.PIPE, text=True)
            exec_logger.debug(f'VMWare vmrun output: Errors: {'None' if not output.stderr else output.stderr} Output: {output.stdout}')
            return encoded_commands_in_guest, output

    def execute_command(self, command: str=None, interpreter_on_guest: str=None, local_file_with_commands: str=None):
        if not interpreter_on_guest:
            interpreter_on_guest = r'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe' if self.platform in WindowsBasedHosts else r'/bin/bash'
            exec_logger.debug(f'Default interpreter {interpreter_on_guest} used for {str(self)}')
        if not interpreter_on_guest:
            exec_logger.warning(f'VMWare execute_command interpreter_on_guest is not provided for {str(self)}')
            exit(-1)
        if local_file_with_commands:
            file_content = ''.join(utils.read_strings_from_file(local_file_with_commands)).replace('\n', ';')
            exec_logger.debug(f'VMWare executing command from file: {local_file_with_commands}, on: {str(self)}, script text: |{file_content}|')
            return self.execute_commands_from_file(local_file_with_commands, interpreter_on_guest)
        elif command:
            tmp_file = utils.write_to_temp_file(command)
            encoded_commands_in_guest, output = self.execute_commands_from_file(tmp_file, interpreter_on_guest)
            utils.delete_file(tmp_file)
            return encoded_commands_in_guest, output

    def _check_if_file_exists_in_guest(self, file_path_on_guest):
        ps_command = f'& "{simulator_config.vmware_vmrun_binary_path}" -T ws -gu "{simulator_config.vmware_root_login}" -gp {simulator_config.vmware_root_password} fileExistsInGuest "{self.vm_path}" "{file_path_on_guest}"'
        output = utils.powershell_execute_wrapper(ps_command)
        exec_logger.debug(f'VMWare vmrun fileExistsInGuest for {str(self)}. Raw results: Errors: {output.stderr.replace('\n', ' ')} Output: {output.stdout.replace('\n', ' ')}')

    def sent_file(self, local_file_path, host_file_path):
        ps_command = f'& "{simulator_config.vmware_vmrun_binary_path}" -T ws -gu "{simulator_config.vmware_root_login}" -gp {simulator_config.vmware_root_password} copyFileFromHostToGuest "{self.vm_path}" "{local_file_path}" "{host_file_path}"'
        output = utils.powershell_execute_wrapper(ps_command)
        exec_logger.debug(f'VMWare vmrun copyFileFromHostToGuest {local_file_path} -> {host_file_path} for {str(self)}. Raw results: Errors: {output.stderr.replace('\n', ' ')} Output: {output.stdout.replace('\n', ' ')}')

    def get_file(self, host_file_path, local_file_path):
        ps_command = f'& "{simulator_config.vmware_vmrun_binary_path}" -T ws -gu "{simulator_config.vmware_root_login}" -gp {simulator_config.vmware_root_password} copyFileFromGuestToHost "{self.vm_path}" "{host_file_path}" "{local_file_path}"'
        output = utils.powershell_execute_wrapper(ps_command)
        exec_logger.debug(f'VMWare vmrun copyFileFromGuestToHost {host_file_path} -> {local_file_path} for {str(self)}. Raw results: Errors: {output.stderr.replace('\n', ' ')} Output: {output.stdout.replace('\n', ' ')}')


class EnviromentManager:
    def __init__(self):
        self.hosts: list[Host] = []

    def _find_target_host(self, target: HostTypes) -> Host:
        h = None
        for i in self.hosts:
            if target == i.host_type:
                h = i
        if not h:
            exec_logger.error(f'Host for specified target {target} is not found in defined host {self.hosts}')
        return h

    def run_script_file(self, script_file_path: str, target: HostTypes, custom_args=None):
        target_host: Host = self._find_target_host(target)
        if not target_host:
            exec_logger.error(f'Target host for script not found: target {target}')
        else:
            exec_logger.debug(f'Executing script file {script_file_path} for {str(target_host)}')

        script_data = utils.get_json_data(script_file_path)
        if 'mode' in script_data:
            if script_data['mode'] == 'sent_file' or script_data['mode'] == 'sent_file_simple':
                exec_logger.debug(f'Environment script for file transfer {custom_args['local_path']} -> {str(target_host)}:{custom_args['remote_path']}')
                target_host.sent_file(custom_args['local_path'], custom_args['remote_path'])
                if script_data['mode'] == 'sent_file_simple':
                    return
            if script_data['mode'] == 'get_file':
                exec_logger.debug(f'Environment script for file transfer {str(target_host)}:{custom_args['remote_path']} -> {custom_args['local_path']}')
                target_host.get_file(custom_args['remote_path'], custom_args['local_path'])
                return
            if script_data['mode'] == 'recursive_arguments':
                if custom_args:
                    for k, val in custom_args.items():
                        custom_args[k] = custom_args[k].format(**custom_args)
        input_log_text = ','.join(script_data['input_arguments']) if isinstance(script_data['input_arguments'], list) else ''
        output_log_text = ','.join(script_data['output']) if isinstance(script_data['output'], list) else ''
        script_store_method = f'Reading script from file {script_data['path_to_file_with_script']}' if script_data['read_script_from_file'] else 'Using script text'
        exec_logger.debug(f'Running script file for {str(target_host)}, {script_store_method} with input: {input_log_text}, output: {output_log_text}')
        exec_logger.debug(f'Current host parameters: {target_host.dynamic_parameters}')
        script_text = None
        if script_data['read_script_from_file']:
            script_text = ''.join(utils.read_strings_from_file(script_data['path_to_file_with_script']))
        elif script_data['script_text']:
            script_text = script_data['script_text']
        if script_text:
            if custom_args:
                script_text = script_text.format(**custom_args)
            else:
                script_text = script_text.format(**target_host.dynamic_parameters)
            exec_logger.debug(f'Final script text: {script_text.replace('\n',';')}')
            target_host.execute_command(command=script_text, interpreter_on_guest=script_data['interpreter'])
        if script_data['output']:
            target_host.dynamic_parameters.update(script_data['output'])
            exec_logger.debug(f'Host parameters {str(target_host)} updated after script: {target_host.dynamic_parameters}')

    def set_up_network(self):
        exec_logger.info('Setting network.')
        attack_side_ips_in_use = []
        target_side_ips_in_use = []
        network_conf = utils.get_json_data(simulator_config.network_config_path)
        random_ip_str = 'random'

        router_ip_attack = network_conf['router_ip_attack_side']
        if router_ip_attack == random_ip_str:
            router_ip_attack = utils.get_random_valid_host_ip(network_conf['attacker_subnet'])
            while router_ip_attack in attack_side_ips_in_use:
                router_ip_attack = utils.get_random_valid_host_ip(network_conf['attacker_subnet'])
        attack_side_ips_in_use.append(router_ip_attack)

        router_ip_target = network_conf['router_ip_target_side']
        if router_ip_target == random_ip_str:
            router_ip_target = utils.get_random_valid_host_ip(network_conf['target_subnet'])
            while router_ip_target in target_side_ips_in_use:
                router_ip_target = utils.get_random_valid_host_ip(network_conf['target_subnet'])
        target_side_ips_in_use.append(router_ip_target)
        self.run_script_file(simulator_config.enviroment_scripts_folder+'set_ip_linux.json',
                             HostTypes.TransparentRouter,
                             custom_args={'ip_address': router_ip_attack,
                                          'interface_name': network_conf['router_interface_name_attack_side']})
        self.run_script_file(simulator_config.enviroment_scripts_folder + 'set_ip_linux.json',
                             HostTypes.TransparentRouter,
                             custom_args={'ip_address': router_ip_target,
                                          'interface_name': network_conf['router_interface_name_target_side']})
        exec_logger.info(f'Router IPs set: {network_conf['router_interface_name_target_side']}:{router_ip_target},{network_conf['router_interface_name_attack_side']}:{router_ip_attack}')

        win_target_first_ip = network_conf['target_first_windows_ip']
        if win_target_first_ip == random_ip_str:
            win_target_first_ip = utils.get_random_valid_host_ip(network_conf['target_subnet'])
            while win_target_first_ip in target_side_ips_in_use:
                win_target_first_ip = utils.get_random_valid_host_ip(network_conf['target_subnet'])
        target_side_ips_in_use.append(win_target_first_ip)
        self.run_script_file(simulator_config.enviroment_scripts_folder + 'set_ip_and_gateway_windows.json',
                             HostTypes.TargetFirstWindows,
                             custom_args={'ip_address': win_target_first_ip,
                                          'interface_name': network_conf['target_first_windows_interface_name'],
                                          'gateway': router_ip_target})
        exec_logger.info(f'Target Windows IP set {network_conf['target_first_windows_interface_name']}:{win_target_first_ip}, default gateway: {router_ip_target}')
        self._find_target_host(HostTypes.TargetFirstWindows).dynamic_parameters.update({'ip_target': win_target_first_ip})
        self._find_target_host(HostTypes.TargetFirstWindows).dynamic_parameters.update(
            {'ip_interface_target': network_conf['target_first_windows_interface_name']})
        attack_host_ip = network_conf['attack_host_ip']
        if attack_host_ip == random_ip_str:
            attack_host_ip = utils.get_random_valid_host_ip(network_conf['attacker_subnet'])
            while attack_host_ip in attack_side_ips_in_use:
                attack_host_ip = utils.get_random_valid_host_ip(network_conf['attacker_subnet'])
        attack_side_ips_in_use.append(attack_host_ip)
        self.run_script_file(simulator_config.enviroment_scripts_folder + 'set_ip_linux.json',
                             HostTypes.Attacker,
                             custom_args={'ip_address': attack_host_ip,
                                          'interface_name': network_conf['attack_interface_name']})
        self.run_script_file(simulator_config.enviroment_scripts_folder + 'set_default_gateway_linux.json',
                             HostTypes.Attacker,
                             custom_args={'ip_address': router_ip_attack})
        exec_logger.info(f'Attack host IP set {network_conf['attack_interface_name']}:{attack_host_ip}, default gateway: {router_ip_attack}')
        self._find_target_host(HostTypes.Attacker).dynamic_parameters.update(
            {'ip_attacker': attack_host_ip})
        self._find_target_host(HostTypes.Attacker).dynamic_parameters.update(
            {'ip_interface_attacker': network_conf['attack_interface_name']})

    def start_environment(self):
        exec_logger.info('Starting Environment.')
        for h in self.hosts:
            h.start()
        for h in self.hosts:
            h.wait_for_ready_state()
        exec_logger.debug(f'Waiting for OS boot check delay.')
        time.sleep(simulator_config.wait_for_os_boot_timer * 5)
        self.set_up_network()

    def shut_down_environment(self):
        exec_logger.info('Shutting environment.')
        for h in self.hosts:
            h.stop()
        for h in self.hosts:
            while h.get_state() != HostStates.Stopped:
                time.sleep(simulator_config.wait_for_os_boot_timer)
        for h in self.hosts:
            h.revert()


class VMWareWorkstationProEnviromentManager(EnviromentManager):
    @staticmethod
    def get_default_empty_config():
        return {'Hosts': [{'type': '', 'vm_path': '', 'platform': ''}]}

    @staticmethod
    def load_config():
        exec_logger.debug('VMWareWorkstationProEnviromentManager loading configuration')
        try:
            with open(simulator_config.vmware_config_path) as f:
                return json.load(f)

        except FileNotFoundError:
            exec_logger.debug('VMWareWorkstationProEnviromentManager config file not found, default configuration is used')
            return VMWareWorkstationProEnviromentManager.get_default_empty_config()

    @staticmethod
    def save_config(config: dict):
        exec_logger.debug(f'VMWareWorkstationProEnviromentManager saving configuration - {config}'.replace('\n', ' '))
        with open(simulator_config.vmware_config_path, 'w') as f:
            json.dump(config, f)

    @staticmethod
    def add_host_to_config(host_type, vm_path, platform):
        exec_logger.debug(f'VMWareWorkstationProEnviromentManager adding host to configuration - host_type: {host_type} vm_path: {vm_path} platform: {platform}')
        config = VMWareWorkstationProEnviromentManager.load_config()
        if config != VMWareWorkstationProEnviromentManager.get_default_empty_config():
            config['Hosts'].append({'type': host_type, 'vm_path': vm_path, 'platform': platform})
        else:
            config['Hosts'] = [{'type': host_type, 'vm_path': vm_path, 'platform': platform}, ]
        VMWareWorkstationProEnviromentManager.save_config(config)

    @staticmethod
    def delete_host_from_config(host_type, vm_path, platform):
        exec_logger.debug(
            f'VMWareWorkstationProEnviromentManager deleting host from configuration - host_type: {host_type} vm_path: {vm_path} platform: {platform}')
        tmp_host_data = {'type': host_type, 'vm_path': vm_path, 'platform': platform}
        config = VMWareWorkstationProEnviromentManager.load_config()
        config['Hosts'] = [i for i in config['Hosts'] if i != tmp_host_data]
        VMWareWorkstationProEnviromentManager.save_config(config)

    @staticmethod
    def start_vmware_api_server():
        exec_logger.info('VMWareWorkstationProEnviromentManager - Starting VMWare API Server')
        with open(os.devnull, 'w') as fp:
            subprocess.Popen(simulator_config.vmware_vmrest_binary_path, stdout=fp)

    def __init__(self):
        super().__init__()
        VMWareWorkstationProEnviromentManager.start_vmware_api_server()
        exec_logger.info('VMWareWorkstationProEnviromentManager is used for environment building.')
        config = self.load_config()
        for h in config['Hosts']:
            host_type = [t for t in HostTypes if t.name == h['type']][0]
            host_platform = [p for p in HostPlatform if p.name == h['platform']][0]
            self.hosts.append(VMWareWorkstationProHost(host_type,
                                                       host_platform,
                                                       h['vm_path']))
        exec_logger.debug('VMWareWorkstationProEnviromentManager initialization completed.')


