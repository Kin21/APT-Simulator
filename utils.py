import simulator_config
import logging
import random
import string
import os
import base64
import subprocess
from datetime import datetime
import json
import ipaddress

exec_logger = logging.getLogger(simulator_config.execution_logger_name)
sim_logger = logging.getLogger(simulator_config.simulation_logger_name)


def get_file_paths(directory):
    file_paths = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            full_path = os.path.join(root, file)
            file_paths.append(full_path)
    return file_paths


def read_strings_from_file(file_name) -> list:
    try:
        with open(file_name, 'r', encoding='UTF-8') as f:
            return f.readlines()
    except FileNotFoundError:
        exec_logger.warning(f'Error while reading file {file_name} - FILE NOT FOUND!')
        exit(-1)


def write_to_temp_file(str_to_write) -> str:
    tmp_file_name = 'temp_file_' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    with open(tmp_file_name, 'w', encoding='UTF-8') as f:
        f.write(str_to_write)
    return tmp_file_name


def delete_file(file_name):
    os.remove(file_name)


def powershell_execute_wrapper(ps_command):

    command_bytes = ps_command.encode('utf-16le')
    encoded_command = base64.b64encode(command_bytes).decode('ascii')
    exec_logger.debug(f'Utils - command to run locally received: {ps_command}; Encoded: {encoded_command}')
    output = subprocess.run(['powershell.exe', '-EncodedCommand', encoded_command], stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True)
    return output


def get_current_date_time_as_str():
    current_datetime = datetime.now()
    return current_datetime.strftime('%Y-%m-%d %H:%M:%S')


def get_json_data(script_file_path: str):
    try:
        with open(script_file_path) as f:
            return json.load(f)
    except FileNotFoundError:
        exec_logger.error(f'Json file {script_file_path} not found !')
        exit(-1)


def get_random_valid_host_ip(subnet):
    ip_network = ipaddress.ip_network(subnet)
    hosts = list(ip_network.hosts())
    selected_ip = random.choice(hosts)
    return str(selected_ip)


def get_script_from_script_file(filename):
    data = get_json_data(filename)
    if data['read_script_from_file']:
        return '\n'.join(read_strings_from_file(data['path_to_file_with_script']))
    else:
        return data['script_text']


def generate_random_string():
    characters = string.ascii_letters + string.digits + '_'
    length = random.randint(4, 10)
    random_string = ''.join(random.choice(characters) for _ in range(length))
    return random_string


def propagate_random_arguments() -> dict:
    return {'random_str': generate_random_string()}
