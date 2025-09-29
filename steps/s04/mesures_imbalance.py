# -*- coding: utf-8 -*-

import time
import sys
import os
if __name__ == "__main__":
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    if BASE_DIR not in sys.path:
        sys.path.insert(0, BASE_DIR)
import configuration  # Custom
from modules.capsys_mysql_command.capsys_mysql_command import (GenericDatabaseManager, DatabaseConfig) # Custom

def get_info():
    return "Cette étape teste TODO."

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
    if config.serial_patch_fmcw is None:
        return 1, f"{step_name} : config.serial_patch n'est pas initialisé."
    if config.target is None:
        return 1, f"{step_name} : config.target n'est pas initialisé."

    # Paramètres spécifiques imbalance
    min_map_1 = config.configItems.imbalance_freq_1.min_map
    max_map_1 = config.configItems.imbalance_freq_1.max_map
    save_prefix_map_1 = ["IMB_IDX_F1", "IMB_PUISS_F1", "IMB_F1_dB"]
    cmd_1 = "test imb 1\r"

    min_map_2 = config.configItems.imbalance_freq_2.min_map
    max_map_2 = config.configItems.imbalance_freq_2.max_map
    save_prefix_map_2 = ["IMB_IDX_F2", "IMB_PUISS_F2", "IMB_F2_dB"]
    cmd_2 = "test imb 2\r"

    min_map_3 = config.configItems.imbalance_freq_3.min_map
    max_map_3 = config.configItems.imbalance_freq_3.max_map
    save_prefix_map_3 = ["IMB_IDX_F3", "IMB_PUISS_F3", "IMB_F3_dB"]
    cmd_3 = "test imb 3\r"

    min_map_groups = [min_map_1, min_map_2, min_map_3]
    max_map_groups = [max_map_1, max_map_2, max_map_3]
    save_prefix_map_groups = [save_prefix_map_1, save_prefix_map_2, save_prefix_map_3]
    cmd_map_target_capsys = [cmd_1, cmd_2, cmd_3]
    replace_map = [("--> ok : ", ""), ("- ", "")]
    expected_prefix = "--> ok : "
    timeout = 2

    # Retry logic for the command
    for attempt in range(1, config.max_retries + 1):
        all_ok = 1
        log(f"Exécution de l'étape {step_name} (tentative {attempt}/{config.max_retries})", "yellow")

        config.target.send_command_and_clean_answer("g9999", expected_response="g9999")
        config.target.send_command_and_clean_answer("t1", expected_response="t1")
        for i in range(3):
            status, msg = config.run_meas_on_patch(
                log, step_name_id, min_map_groups[i], max_map_groups[i], cmd_map_target_capsys[i], expected_prefix, save_prefix_map_groups[i], timeout=timeout, replace_map=replace_map
            )
            if status != 0:
                if attempt < config.max_retries:
                    log(f"Réessaie de \"{cmd_map_target_capsys[i]}\"... (tentative {attempt + 1}/{config.max_retries})", "yellow")
                    time.sleep(1)
                    break
                else:
                    return status, f"{step_name} : {msg}"
            else:
                # return 0, f"{step_name} : OK"
                all_ok = 0
        if all_ok == 0:
            return 0, f"{step_name} : OK"
    
    return 1, f"{step_name} : NOK"


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