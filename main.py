import logging
import time

import simulator_logger
import simulator_config
import environment_manager
import gui
import simulator
import utils

exec_logger = logging.getLogger(simulator_config.execution_logger_name)
sim_logger = logging.getLogger(simulator_config.simulation_logger_name)


gui.start_gui()
e = environment_manager.VMWareWorkstationProEnviromentManager()
win = e.hosts[1]
kali = e.hosts[0]
deb = e.hosts[2]
exec_logger.info('SIMULATION STARTED')
e.start_environment()
# e.set_up_network()
#
# a1 = simulator.Action('T1566.001',
#                       'Give remote shell under non-privileged account(run .ps1 => reverse shell)',
#                       environment_manager.HostTypes.TargetFirstWindows)
# a2 = simulator.Action('T1204.002',
#                       'Run MSFVenom generated payload to get meterpreter session',
#                       environment_manager.HostTypes.TargetFirstWindows)
# p = simulator.Plan()
# p.load_plan('Test')
conf = simulator.SimulationConfiguration(utils.get_json_data(simulator_config.sim_config_location))
s = simulator.Simulator(e, ['APT3', ], conf)
# s.prepare_environment_for_action(a1)
# time.sleep(2)
# s.execute_action(a1)
s.execute_plans()
# time.sleep(10)
# e.shut_down_environment()

