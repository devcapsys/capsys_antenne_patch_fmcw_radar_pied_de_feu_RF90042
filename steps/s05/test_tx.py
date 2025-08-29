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
from modules.capsys_serial_instrument_manager.kts1.cible_kts1 import Kts1Manager

def get_info():
    return "Cette étape teste le fonctionnement de TX."


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
    if config.multimeter_current is None:
        return 1, f"{step_name} : config.multimeter_current n'est pas initialisé."
    if config.target is None:
        return 1, f"{step_name} : config.target n'est pas initialisé."

    # Paramètres spécifiques tx 4
    tx_min = config.configItems.tx.min_map
    tx_max = config.configItems.tx.max_map
    tx_cmd = config.configItems.tx.cmd # Example : "--> ok - Freq : 241596720 "
    tx_expected_prefix = config.configItems.tx.expected_prefix
    tx_replace_map = config.configItems.tx.replace_map
    tx_save_prefix = config.configItems.tx.save_prefix_map
    tx_timeout = config.configItems.tx.timeout

    # Retry logic for the command
    for attempt in range(1, config.max_retries + 1):
        log(f"Exécution de l'étape test TX (tentative {attempt}/{config.max_retries})", "yellow")

        status, msg = config.run_meas_on_patch(
            log, step_name_id, tx_min, tx_max, tx_cmd, tx_expected_prefix, "", {}, tx_timeout, tx_replace_map
        )
        if status != 0:
            if attempt < config.max_retries:
                log(f"Réessaie de \"{tx_cmd}\"... (tentative {attempt + 1}/{config.max_retries})", "yellow")
                time.sleep(1)
                continue
            else:
                return status, f"{step_name} : {msg}"

        current_min = config.configItems.current_tx.minimum
        current_max = config.configItems.current_tx.maximum
        current = round(float(config.multimeter_current.meas()), 3)
        log(f"Courant mesuré : {current}A ; min={current_min}A ; max={current_max}A", "blue")
        config.save_value(step_name_id, config.configItems.current_tx.key, str(current), config.configItems.current_tx.unit)
        if current > current_max or current < current_min:
            if attempt < config.max_retries:
                log(f"Réessaie de mesurer le courant... (tentative {attempt + 1}/{config.max_retries})", "yellow")
                time.sleep(1)
                continue
            else:
                return 1, f"{step_name} : Problème de courant."

        freq_min = config.configItems.frequency_tx.minimum
        freq_max = config.configItems.frequency_tx.maximum
        power_min = config.configItems.frequency_tx.power_min
        power_max = config.configItems.frequency_tx.power_max
        offset_power = config.configItems.frequency_tx.offset_power
        cmd = config.configItems.frequency_tx.cmd
        try:
            response = config.target.send_command_and_clean_answer(cmd) # Example : "m\nf (Rx)     P (Rx)    P (AUX)\n24.161GHz  -41.0dBm  -74.9dBm"
        except:
            # Try to reconnect target
            config.target = None
            target = Kts1Manager(debug=config.arg.show_all_logs)
            port = config.configItems.target.port
            try:
                if target.open_with_usb_name_and_sn(usb_name="USB Serial Port", sn="21260003", start_with_port=port):
                    log(f"{target.identification()}", "blue")
                else:
                    return 1, f"{step_name} : Impossible de se connecter à la cible KTS1."
            except Exception as e:
                log(f"Error: {e}", "red")
                return 1, f"{step_name} : Erreur lors de l'initialisation de la cible : {e}"
            # At this point, kts1 is good so we put it in the global config
            config.target = target
            response = config.target.send_command_and_clean_answer(cmd)
        log(f"commande \"{cmd}\" envoyée à la cible : \"{response}\"", "blue")
        response = response.split(" ")
        freq = float(response[12].split("\n")[1].replace("GHz", "")) * 1e9  # Convert GHz to Hz
        power = round(float(response[14].replace("dBm", "")) + offset_power, 1)
        log(f"Fréquence mesurée : {freq}Hz ; min={freq_min}Hz ; max={freq_max}Hz", "blue")
        config.save_value(step_name_id, config.configItems.frequency_tx.key, str(freq), config.configItems.frequency_tx.unit)
        log(f"Puissance mesurée : {power}dBm ; min={power_min}dBm ; max={power_max}dBm", "blue")
        config.save_value(step_name_id, "TX_PUISSANCE_dBm", str(power), "dBm")
        if freq < freq_min or freq > freq_max:
            if attempt < config.max_retries:
                log(f"Réessaie de mesurer la fréquence... (tentative {attempt + 1}/{config.max_retries})", "yellow")
                time.sleep(1)
                continue
            else:
                return 1, f"{step_name} : Problème de fréquence."

        if power < power_min or power > power_max:
            if attempt < config.max_retries:
                log(f"Réessaie de mesurer la puissance... (tentative {attempt + 1}/{config.max_retries})", "yellow")
                time.sleep(1)
                continue
            else:
                return 1, f"{step_name} : Problème de puissance."

        log(f"Ajout de l'offset de puissance : {offset_power}dBm ; Puissance mesurée : {power}dBm", "blue")

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