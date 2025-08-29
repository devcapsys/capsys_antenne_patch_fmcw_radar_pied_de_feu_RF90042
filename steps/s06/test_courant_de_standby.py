# -*- coding: utf-8 -*-

import sys
import os
if __name__ == "__main__":
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    if BASE_DIR not in sys.path:
        sys.path.insert(0, BASE_DIR)
import time
import configuration  # Custom
from modules.capsys_mysql_command.capsys_mysql_command import (GenericDatabaseManager, DatabaseConfig) # Custom

def get_info():
    return "Cette étape vérifie le courant."


def run_step(log, config: configuration.AppConfig):
    step_name = os.path.splitext(os.path.basename(__file__))[0]
    # Ensure db is initialized
    if not hasattr(config, "db") or config.db is None:
        return 1, f"{step_name} : config.db n'est pas initialisé."
    # We always save the name of the step in the db
    step_name_id = config.db.create(
        "step_name", {
            "device_under_test_id": config.device_under_test_id,
            "step_name": os.path.splitext(os.path.basename(__file__))[0],
        }
    )
    if config.serial_patch is None:
        return 1, f"{step_name} : config.serial_patch n'est pas initialisé."
    if config.multimeter_current is None:
        return 1, f"{step_name} : config.multimeter_current n'est pas initialisé."

    command_to_send = config.configItems.current_standby.cmd  # Example: "--> ok"
    expected_response = config.configItems.current_standby.expected_prefix
    config.serial_patch.send_command(command_to_send, expected_response, timeout=1)

    # Verify current limits
    current_min = config.configItems.current_standby.minimum
    current_max = config.configItems.current_standby.maximum
    name = config.configItems.current_standby.key
    unit = config.configItems.current_standby.unit
    config.multimeter_current.send_command("RANGE:ACI 1\n")
    config.multimeter_current.send_command("RATE F\n")
    current = float(config.multimeter_current.meas())
    config.multimeter_current.send_command("RANGE:ACI 4\n")
    log(f"Courant mesuré : {current}{unit}, min={current_min}{unit}, max={current_max}{unit}", "blue")
    config.save_value(step_name_id, name, str(current), unit)
    if current > float(current_max) or current < float(current_min):
        return 1, f"{step_name} : Courant mesuré {current}{unit} hors des limites ({current_min}{unit} - {current_max}{unit})."

    return 0, f"{step_name} : OK"


if __name__ == "__main__":
    """Allow to run this script directly for testing purposes."""

    def log_message(message, color):
        print(f"{color}: {message}")

    # Initialize config
    config = configuration.AppConfig()
    config.arg.show_all_logs = False

    # Initialize Database
    config.db_config = DatabaseConfig(password="root")
    config.db = GenericDatabaseManager(config.db_config, debug=False)
    config.db.connect()
    
    # Launch the initialisation step
    from steps.s01.initialisation import run_step as run_step_init
    success_end, message_end = run_step_init(log_message, config)
    print(message_end)
    
    # Launch this step
    success, message = run_step(log_message, config)
    print(message)

    # Clear ressources
    from steps.zz.fin_du_test import run_step as run_step_fin_du_test
    success_end, message_end = run_step_fin_du_test(log_message, config)
    print(message_end)