import logging
import logging.handlers
import simulator_config


def configure_logging():
    # Logger for simulator program execution
    exec_logger = logging.getLogger(simulator_config.execution_logger_name)
    exec_logger.setLevel(logging.DEBUG)
    exec_file_handler = logging.FileHandler(simulator_config.simulator_execution_log_file_path)
    exec_file_handler.setLevel(logging.DEBUG)
    exec_file_handler.setFormatter(logging.Formatter(simulator_config.exec_log_format))
    exec_logger.addHandler(exec_file_handler)

    # Logger for simulation itself
    sim_logger = logging.getLogger(simulator_config.simulation_logger_name)
    sim_logger.setLevel(logging.DEBUG)
    sim_file_handler = logging.FileHandler(simulator_config.simulator_simulation_log_file_path)
    sim_file_handler.setLevel(logging.DEBUG)
    sim_file_handler.setFormatter(logging.Formatter(simulator_config.sim_log_format))
    sim_logger.addHandler(sim_file_handler)

    # Common console handler for both loggers
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(simulator_config.console_log_format))

    # Console handler to loggers
    if simulator_config.simulator_log_exec_log_to_console:
        exec_logger.addHandler(console_handler)
    if simulator_config.simulator_log_sim_log_to_console:
        sim_logger.addHandler(console_handler)


configure_logging()
