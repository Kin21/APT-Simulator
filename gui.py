import json

import dearpygui.dearpygui as dpg
import mitre_knowledge_base
import environment_manager
import utils
import simulator_config
import simulator


def gui_delete_current_window(sender, app_data, user_data):
    dpg.set_primary_window(sender, False)
    dpg.delete_item(sender)


def add_technique(sender, app_data, user_data):
    user_data = {key: dpg.get_value(val) for key, val in user_data.items()}
    simulator.Action.add_action_to_db(user_data)
    gui_view_simulation_objects(None, None, None)


def update_args(sender, app_data, user_data):
    user_data['new_data'] = {key: dpg.get_value(val) for key, val in user_data['new_data'].items()}
    simulator.Action.update_input_argument(**user_data)
    gui_view_simulation_objects(None, None, None)


def update_set_up(sender, app_data, user_data):
    user_data['new_data'] = {key: dpg.get_value(val) for key, val in user_data['new_data'].items()}
    simulator.Action.update_set_up(**user_data)
    gui_view_simulation_objects(None, None, None)


def update_technique(sender, app_data, user_data):
    user_data['new_data'] = {key: dpg.get_value(val) for key, val in user_data['new_data'].items()}
    simulator.Action.update_technique(**user_data)
    gui_view_simulation_objects(None, None, None)


def update_action(sender, app_data, user_data):
    user_data['new_data'] = {key: dpg.get_value(val) for key, val in user_data['new_data'].items()}
    user_data['new_data']['actions_included'] = user_data['new_data']['actions_included'].split(',')
    simulator.Action.update_action(**user_data)
    gui_view_simulation_objects(None, None, None)


def add_action_to_action(sender, app_data, user_data):
    user_data['action_data'] = {key: dpg.get_value(val) for key, val in user_data['action_data'].items()}
    user_data['action_data']['actions_included'] = user_data['action_data']['actions_included'].split(',')
    user_data['action_data'].update({"set_up": {
                                                "target": {
                                                    "required": False,
                                                    "priority": "1",
                                                    "script_file": ""
                                                },
                                                "attacker": {
                                                    "required": False,
                                                    "priority": "0",
                                                    "script_file": ""
                                                }
                                            },
                                        "input_args": []})
    simulator.Action.add_action_to_action(**user_data)
    gui_view_simulation_objects(None, None, None)


def gui_view_simulation_objects(sender, app_data, user_data):
    dpg.delete_item("actions_window_tag")
    el_width = 700
    el_intend = 20
    w, h = dpg.get_viewport_width() - 10, dpg.get_viewport_height() - 100
    with dpg.window(no_title_bar=False, no_move=False, width=w, height=h, pos=(0, 0),
                    on_close=gui_delete_current_window, modal=False, label='Actions Editor',
                    tag='actions_window_tag') as curr_window:
        action_files = utils.get_file_paths(simulator_config.actions_folder)
        action_files = [f for f in action_files if '.json' in f]
        for f in action_files:
            name = '.'.join(f.split('/')[-1].split('.')[0:-1])
            with dpg.collapsing_header(label=name, default_open=False):
                action_data = simulator.Action.load_raw_action_from_file(name)
                with dpg.group(horizontal=True):
                    dpg.add_text(default_value='Name:')
                    name_id = dpg.add_input_text(default_value=action_data['name'], width=el_width)
                with dpg.group(horizontal=True):
                    dpg.add_text(default_value='Description:')
                    description_id = dpg.add_input_text(default_value=action_data['description'], width=el_width,
                                                    multiline=True)
                with dpg.group(horizontal=True):
                    dpg.add_text(default_value='Technique ID:')
                    technique_id = dpg.add_input_text(default_value=action_data['technique_id'], width=el_width)
                dpg.add_button(label='Update', callback=update_technique, user_data={'technique_id': action_data['technique_id'],
                                                                                     'new_data':{
                                                                                         'name': name_id,
                                                                                         'description': description_id,
                                                                                         'technique_id': technique_id
                                                                                     }})
                for a in action_data['actions']:
                    with dpg.collapsing_header(label=a['name'], default_open=True, indent=el_intend):
                        with dpg.group(horizontal=True):
                            dpg.add_text(default_value='Name:')
                            action_name_id = dpg.add_input_text(default_value=a['name'], width=el_width)
                        with dpg.group(horizontal=True):
                            dpg.add_text(default_value='Includes actions:')
                            actions_included_id = dpg.add_input_text(default_value=','.join(a['actions_included']),
                                                                     width=el_width)
                        with dpg.group(horizontal=True):
                            dpg.add_text(default_value='Interpreter:')
                            interpreter_id = dpg.add_input_text(default_value=a['interpreter'], width=el_width)
                        with dpg.group(horizontal=True):
                            dpg.add_text(default_value='Platform:')
                            platform_id = dpg.add_input_text(default_value=a['platform'], width=el_width)
                        with dpg.group(horizontal=True):
                            dpg.add_text(default_value='Commands file:')
                            commands_file_id = dpg.add_input_text(default_value=a['commands_file'], width=el_width)

                        with dpg.collapsing_header(label='Input Arguments', default_open=True, indent=el_intend*2):
                            for i_arg in a['input_args']:
                                arg_name_id = dpg.add_input_text(default_value=i_arg['name'], width=el_width)
                                arg_val_id = dpg.add_input_text(default_value=i_arg['value'], width=el_width)
                                with dpg.group(horizontal=True):
                                    dpg.add_button(label='Update', callback=update_args, user_data={'technique': action_data['technique_id'],
                                                                                                    'action': a['name'],
                                                                                                    'original_name': i_arg['name'],
                                                                                                    'new_data': {
                                                                                                    'name': arg_name_id,
                                                                                                    'value': arg_val_id}})
                                    dpg.add_button(label='Delete', callback=update_args,
                                                   user_data={'technique': action_data['technique_id'],
                                                              'action': a['name'],
                                                              'original_name': i_arg['name'],
                                                              'new_data': {}})
                            with dpg.collapsing_header(label='Add Args'):
                                with dpg.group(horizontal=True):
                                    dpg.add_text('name:')
                                    arg_name_id = dpg.add_input_text(width=el_width)
                                with dpg.group(horizontal=True):
                                    dpg.add_text('value:')
                                    value_name_id = dpg.add_input_text(width=el_width)
                                dpg.add_button(label='Add', callback=update_args,
                                               user_data={'technique': action_data['technique_id'],
                                                          'action': a['name'],
                                                          'original_name': '',
                                                          'new_data': {
                                                                    'name': arg_name_id,
                                                                    'value': value_name_id
                                                          }})
                        with dpg.collapsing_header(label='Environment Set Up', default_open=False, indent=el_intend):
                            with dpg.collapsing_header(label='target', default_open=True, indent=el_intend*2):
                                target_required_id = dpg.add_checkbox(label='required', default_value=a['set_up']['target']['required'])
                                priority_id = dpg.add_input_text(label='priority', default_value=a['set_up']['target']['priority'])
                                script_file_id = dpg.add_input_text(label='script_file', default_value=a['set_up']['target']['script_file'])
                                dpg.add_button(label='Update', callback=update_set_up,
                                               user_data={'technique_id': action_data['technique_id'],
                                                          'action': a['name'],
                                                          'side': 'target',
                                                          'new_data': {
                                                              'required': target_required_id,
                                                              'priority': priority_id,
                                                              'script_file': script_file_id}})
                            with dpg.collapsing_header(label='attacker', default_open=True, indent=el_intend*2):
                                target_required_id = dpg.add_checkbox(label='required', default_value=a['set_up']['attacker']['required'])
                                priority_id = dpg.add_input_text(label='priority', default_value=a['set_up']['attacker']['priority'])
                                script_file_id = dpg.add_input_text(label='script_file', default_value=a['set_up']['attacker']['script_file'])
                                dpg.add_button(label='Update', callback=update_set_up,
                                               user_data={'technique_id': action_data['technique_id'],
                                                          'action': a['name'],
                                                          'side': 'attacker',
                                                          'new_data': {
                                                              'required': target_required_id,
                                                              'priority': priority_id,
                                                              'script_file': script_file_id}})
                        with dpg.group(horizontal=True):
                            dpg.add_button(label='Update', callback=update_action, user_data={
                                'technique_id': action_data['technique_id'],
                                'action': a['name'],
                                'new_data':
                                {
                                    'name': action_name_id,
                                    'interpreter': interpreter_id,
                                    'commands_file': commands_file_id,
                                    'actions_included': actions_included_id,
                                    'platform': platform_id
                                }
                            })
                with dpg.collapsing_header(label='Add Action', default_open=True, indent=el_intend):
                    with dpg.group(horizontal=True):
                        dpg.add_text(default_value='Name:')
                        action_name_id = dpg.add_input_text(width=el_width)
                    with dpg.group(horizontal=True):
                        dpg.add_text(default_value='Includes actions:')
                        actions_included_id = dpg.add_input_text(width=el_width)
                    with dpg.group(horizontal=True):
                        dpg.add_text(default_value='Interpreter:')
                        interpreter_id = dpg.add_input_text(width=el_width)
                    with dpg.group(horizontal=True):
                        dpg.add_text(default_value='Platform:')
                        platform_id = dpg.add_input_text(width=el_width)
                    with dpg.group(horizontal=True):
                        dpg.add_text(default_value='Commands file:')
                        commands_file_id = dpg.add_input_text(width=el_width)
                    dpg.add_button(label='Add', callback=add_action_to_action, user_data={
                        'technique_id': action_data['technique_id'],
                        'action_data':
                            {
                                'name': action_name_id,
                                'interpreter': interpreter_id,
                                'commands_file': commands_file_id,
                                'actions_included': actions_included_id,
                                'platform': platform_id
                            }
                    })

        with dpg.collapsing_header(label='Create', default_open=True):
            with dpg.group(horizontal=True):
                dpg.add_text(default_value='Name')
                name_id = dpg.add_input_text(width=el_width)
            with dpg.group(horizontal=True):
                dpg.add_text(default_value='Description:')
                description_id = dpg.add_input_text(width=el_width)
            with dpg.group(horizontal=True):
                dpg.add_text(default_value='Technique ID:')
                technique_id = dpg.add_input_text(width=el_width)
            dpg.add_button(label='Create', callback=add_technique, user_data={'name': name_id,
                                                                              'description': description_id,
                                                                              'technique_id': technique_id})

def filter_mitre_data(sender, filter_string, user_data):
    dpg.set_value("mitre_id_filter", filter_string)


def gui_mitre_database_window_1():
    dpg.delete_item('MITRE DB Window 1')
    stix_data = mitre_knowledge_base.stix_data
    tactics = mitre_knowledge_base.get_all_tactics(stix_data)
    techniques = mitre_knowledge_base.get_techniques_or_subtechniques(stix_data)
    tactics += techniques

    w, h = dpg.get_viewport_width() - 10, dpg.get_viewport_height() - 100
    with dpg.window(no_title_bar=False, no_move=False, width=w, height=h, pos=(0, 0),
                    on_close=gui_delete_current_window, modal=False, label='MITRE DB Viewer', tag='MITRE DB Window 1'):

        dpg.add_input_text(label="Filter (inc, -exc)", callback=filter_mitre_data,
                           hint='Display tactic or techniques containing TAxxx or TTyyy with TAxxx,TTyyy')

        with dpg.filter_set(id="mitre_id_filter"):
            for t in tactics:
                tactic_mitre_id = t['external_references'][0]['external_id']
                tactic_fields_to_show = ['name', 'description', 'id', 'type', 'created', 'modified']
                with dpg.collapsing_header(label=tactic_mitre_id, filter_key=tactic_mitre_id):
                    with dpg.collapsing_header(label='MITRE ID', default_open=True, leaf=True):
                        dpg.add_input_text(default_value=tactic_mitre_id, readonly=True, multiline=True, width=w,
                                           height=30, indent=8)
                    for field in tactic_fields_to_show:
                        with dpg.collapsing_header(label=field, default_open=True, leaf=True):
                            text = str(t[field]).replace('. ', '.\n')
                            dynamic_height = 30 if field != 'description' else 200
                            dpg.add_input_text(default_value=text, readonly=True, multiline=True, width=w,
                                               height=dynamic_height, indent=8)


def update_gui_vmware_host_path(sender, app_data, user_data):
    dpg.set_value(user_data['path_el_id'], list(app_data['selections'].values())[0])


def gui_delete_vmware_host_from_config(sender, app_data, user_data):
    environment_manager.VMWareWorkstationProEnviromentManager.delete_host_from_config(user_data['type'],
                                                                                      user_data['vm_path'],
                                                                                      user_data['platform'])
    vmware_workstation_pro_config_window(None, None, None)


def gui_add_vmware_host_to_config(sender, app_data, user_data):
    host_type = dpg.get_value(user_data['type_el_id'])
    vm_path = dpg.get_value(user_data['path_el_id'])
    platform = dpg.get_value(user_data['platform_el_id'])
    environment_manager.VMWareWorkstationProEnviromentManager.add_host_to_config(host_type, vm_path, platform)
    vmware_workstation_pro_config_window(None, None,None)


def vmware_workstation_pro_config_window(sender, app_data, user_data):
    dpg.delete_item('VMWareWorkstationProConfigWindow')
    w, h = dpg.get_viewport_width() - 10, dpg.get_viewport_height() - 100
    with dpg.window(no_title_bar=False, no_move=False, width=w, height=h, pos=(0, 0),
                    on_close=gui_delete_current_window, modal=False, label='VMWareWorkstationPro Config',
                    tag='VMWareWorkstationProConfigWindow'):
        with dpg.collapsing_header(label='Hosts Config', default_open=True):
            config = environment_manager.VMWareWorkstationProEnviromentManager.load_config()
            hosts = []
            if config != environment_manager.VMWareWorkstationProEnviromentManager.get_default_empty_config():
                hosts = config['Hosts']
            for h in hosts:
                with dpg.group(horizontal=True):
                    dpg.add_listbox(default_value=h['type'],
                                    items=list(i.name for i in environment_manager.HostTypes), width=200)
                    dpg.add_input_text(label='vm_path', hint='path/to/vm', width=600,
                                       default_value=h['vm_path'])
                    dpg.add_listbox(default_value=h['platform'],
                                    items=list(i.name for i in environment_manager.HostPlatform), width=200)
                    dpg.add_button(label='Delete', callback=gui_delete_vmware_host_from_config, user_data=h)
            with dpg.collapsing_header(default_open=True, leaf=True, label='New Host'):
                with dpg.group(horizontal=True, label='Add new Host'):
                    type_el_id = dpg.add_listbox(items=list(i.name for i in environment_manager.HostTypes), width=200)
                    path_el_id = dpg.add_input_text(hint='path/to/vm', width=600)
                    platform_el_id = dpg.add_listbox(items=list(i.name for i in environment_manager.HostPlatform), width=200)
                    with dpg.file_dialog(directory_selector=False, show=False,
                                         callback=update_gui_vmware_host_path,
                                         user_data={'path_el_id': path_el_id,
                                                    'type_el_id': type_el_id,
                                                    'platform_el_id': platform_el_id}) as file_selector_id:
                        dpg.add_file_extension(".vmx", color=(0, 255, 0, 255))
                        f_id = file_selector_id
                    dpg.add_button(label="VM Path Selector", callback=lambda: dpg.show_item(f_id))
                    dpg.add_button(label='Add Host', callback=gui_add_vmware_host_to_config,
                                   user_data={'type_el_id': type_el_id,
                                              'path_el_id': path_el_id,
                                              'platform_el_id': platform_el_id})


def update_plan_data(sender, app_data, user_data):
    if user_data.get('new_action'):
        if not user_data['data'].get('actions'):
            user_data['data'].update({'actions': [dpg.get_value(user_data['new_action']) + '->' + dpg.get_value(user_data['with_target'])]})
        else:
            user_data['data']['actions'].append(dpg.get_value(user_data['new_action']) + '->'+ dpg.get_value(user_data['with_target']))
    if user_data.get('del_action'):
        user_data['data']['actions'] = [a for a in user_data['data']['actions'] if a != dpg.get_value(user_data.get('del_action'))]
    user_data['data']['name'] = dpg.get_value(user_data['new_name'])
    user_data['data']['description'] = dpg.get_value(user_data['new_description'])
    create_plan(None, None, user_data)


def save_plan(sender, app_data, user_data):
    plan_name = user_data['data']['name']
    parsed_data = []
    for a in user_data['data']['actions']:
        technique_id = a.split(':')[0]
        name = a.split(':')[1].split('->')[0]
        target = a.split(':')[1].split('->')[1]
        parsed_data.append({'technique_id': technique_id,
                            'name': name,
                            'target': target})
    plan_data = {'name': plan_name,
                 'description': user_data['data']['description'],
                 'actions': parsed_data}
    with open(simulator_config.plans_folder + plan_name + '.json', 'w') as f:
        json.dump(plan_data, f, indent=4)
    create_plan(None, None, None)


def create_plan(sender, app_data, user_data):
    if not user_data:
        user_data = {'data': {}}
    dpg.delete_item('PlanConfigWindow')
    w, h = dpg.get_viewport_width() - 10, dpg.get_viewport_height() - 100
    el_width = 1600
    with dpg.window(no_title_bar=False, no_move=False, width=w, height=h, pos=(0, 0),
                    on_close=gui_delete_current_window, modal=False, label='Simulation Plan Editor',
                    tag='PlanConfigWindow'):
        with dpg.group(horizontal=True):
            dpg.add_text(default_value='Name:')
            name_id = dpg.add_input_text(width=el_width, default_value=user_data['data'].get('name', ''))
        with dpg.group(horizontal=True):
            dpg.add_text(default_value='Description:')
            description_id = dpg.add_input_text(width=el_width, multiline=True,
                                                default_value=user_data['data'].get('description', ''))

        dpg.add_text(default_value='Choose Target:')
        target_id = dpg.add_listbox(items=list(i.name for i in environment_manager.HostTypes), width=int(el_width/2),
                                    indent=50)
        with dpg.group(horizontal=True):
            action_files = utils.get_file_paths(simulator_config.actions_folder)
            action_files = [f for f in action_files if '.json' in f]
            techniques = ['.'.join(f.split('/')[-1].split('.')[0:-1]) for f in action_files]
            all_actions = [f'{t}:{action['name']}' for t in techniques for action in simulator.Action.load_raw_action_from_file(t)['actions']]
            techniques_id = dpg.add_listbox(all_actions, width=int(el_width/2), num_items=10)
            current_actions = user_data['data'].get('actions', [])
            current_list = dpg.add_listbox(current_actions, width=int(el_width/2), num_items=10)
        with dpg.group(horizontal=True):
            dpg.add_button(label='->', callback=update_plan_data, user_data={'data': user_data.get('data', {}),
                                                                             'new_action': techniques_id,
                                                                             'with_target': target_id,
                                                                             'new_name': name_id,
                                                                             'new_description': description_id},
                           width=int(el_width/2))
            dpg.add_button(label='<-', callback=update_plan_data, user_data={'data': user_data.get('data', {}),
                                                                             'del_action': current_list,
                                                                             'new_name': name_id,
                                                                             'new_description': description_id},
                           width=int(el_width/2))

        dpg.add_button(label='Save Plan', callback=save_plan, user_data={'data': user_data['data']})


def sim_config_window(sender, app_data, user_data):
    dpg.delete_item('SimConfigWindow')
    w, h = dpg.get_viewport_width() - 10, dpg.get_viewport_height() - 100
    el_width = 1600
    with dpg.window(no_title_bar=False, no_move=False, width=w, height=h, pos=(0, 0),
                    on_close=gui_delete_current_window, modal=False, label='Simulation Configuration',
                    tag='SimConfigWindow'):
        conf_data = utils.get_json_data(simulator_config.sim_config_location)
        with dpg.collapsing_header(label='Pre-Simulation Scripts'):
            for scr in conf_data['on_start']:
                dpg.add_input_text(default_value=scr['script'], label='Script file')
                dpg.add_listbox(items=[e.name for e in environment_manager.HostTypes], default_value=scr['target'],
                                label='Target')
                with dpg.collapsing_header(label='Custom Arguments', indent=50, default_open=True):
                    for name, val in scr['args'].items():
                        dpg.add_input_text(default_value=name, label='Name')
                        dpg.add_input_text(default_value=val, label='Value', multiline=True)
        with dpg.collapsing_header(label='Post-Simulation Scripts'):
            for scr in conf_data['on_end']:
                dpg.add_input_text(default_value=scr['script'], label='Script file')
                dpg.add_listbox(items=[e.name for e in environment_manager.HostTypes], default_value=scr['target'],
                                label='Target')
                with dpg.collapsing_header(label='Custom Arguments', indent=50):
                    for name, val in scr['args'].items():
                        dpg.add_input_text(default_value=name, label='Name')
                        dpg.add_input_text(default_value=val, label='Value', multiline=True)
        with dpg.group(horizontal=True):
            dpg.add_button(label='Create')
            dpg.add_button(label='Update')
            dpg.add_button(label='Delete')


def start_gui():
    dpg.create_context()
    dpg.create_viewport(title='APT Simulator', width=1920, height=1080, x_pos=0, y_pos=0)

    with dpg.viewport_menu_bar(tag='main_menu_bar'):
        with dpg.menu(label='Base Simulation Objects', tag='Base Simulation Objects'):
            dpg.add_menu_item(label='Actions Editor', callback=gui_view_simulation_objects)
            dpg.add_menu_item(label='Create Plan', callback=create_plan)
            dpg.add_menu_item(label='Simulator config', callback=sim_config_window)

        with dpg.menu(label='Knowledgebase'):
            dpg.add_menu_item(label='MITRE ATT&CK Database: Tactics & Techniques', callback=gui_mitre_database_window_1)

        with dpg.menu(label='Simulation Config'):
            with dpg.menu(label='Environment'):
                dpg.add_menu_item(label='VMWareWorkstationPro', callback=vmware_workstation_pro_config_window)
        with dpg.menu(label="Simulator"):
            dpg.add_menu_item(label="Run", callback=lambda: dpg.stop_dearpygui())
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()

if __name__ == '__main__':
    start_gui()