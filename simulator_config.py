# Logger configuration
execution_logger_name = 'EXECUTION'
simulation_logger_name = 'SIMULATION'
simulator_execution_log_file_path = 'logs\\simulator_execution.log'
simulator_simulation_log_file_path = 'logs\\apt_simulation.log'
simulator_log_exec_log_to_console = True
simulator_log_sim_log_to_console = True
exec_log_format = '%(asctime)s - %(name)s - %(levelname)s: %(message)s'
sim_log_format = '%(asctime)s - %(name)s - %(levelname)s: %(message)s'
console_log_format = '%(asctime)s - %(name)s - %(levelname)s: %(message)s'

# MITRE Database Configuration
mitre_github_attack_stix_data_url = 'https://raw.githubusercontent.com/mitre-attack/attack-stix-data/master/enterprise-attack/enterprise-attack.json'
knowledgebase_location = 'mitre_knowledgebase/'
knowledgebase_db_location = knowledgebase_location + 'enterprise-attack.json'

# VMWareWorkstation Pro config
# Exposed locally in test set-up so leaving password here ^_^
vmware_api_username = 'admin'
vmware_api_password = 'y*U@9jiCw*'
vmware_api_url = 'http://127.0.0.1:8697/api'
vmware_config_path = 'configs/vmware.json'
vmware_vmrest_binary_path = r'C:\Program Files (x86)\VMware\VMware Workstation\vmrest.exe'
vmware_vmrun_binary_path = r'C:\Program Files (x86)\VMware\VMware Workstation\vmrun.exe'
vmware_root_login = 'root'
vmware_root_password = 'rer23f324f34kf43l@1112@'

# Environment Config
simulation_base_snapshot_name = 'simulator_base'
enviroment_scripts_folder = 'enviroment_scripts/'
wait_for_os_boot_timer = 2
network_config_path = 'configs/network.json'
plans_folder = 'plans/'
actions_folder = 'actions/'
payloads_folder = 'payloads/'
sim_config_location = 'configs/sim_config.json'
common_execution_delay = 2.5
