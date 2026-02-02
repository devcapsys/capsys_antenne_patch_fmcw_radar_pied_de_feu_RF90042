# -*- coding: utf-8 -*-

import sys, os, time
if __name__ == "__main__":
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    if BASE_DIR not in sys.path:
        sys.path.insert(0, BASE_DIR)
import configuration  # Custom
from modules.capsys_serial_instrument_manager.kts1.cible_kts1 import Kts1Manager # Custom

def get_info():
    return "Cette étape teste le fonctionnement de TX."


def run_step(log, config: configuration.AppConfig, update_percentage=lambda x: None):
    step_name = os.path.splitext(os.path.basename(__file__))[0]
    return_msg = {"step_name": step_name, "infos": []}
    # Ensure db is initialized
    if not hasattr(config, "db") or config.db is None:
        return_msg["infos"].append(f"config.db n'est pas initialisé.")
        return 1, return_msg
    # We always save the name of the step in the db
    step_name_id = config.db.create(
        "step_name", {
            "device_under_test_id": config.device_under_test_id,
            "step_name": os.path.splitext(os.path.basename(__file__))[0],
        }
    )
    if config.multimeter_current is None:
        return_msg["infos"].append(f"config.multimeter_current n'est pas initialisé.")
        return 1, return_msg
    if config.target is None:
        return_msg["infos"].append(f"config.target n'est pas initialisé.")
        return 1, return_msg

    config.target.send_command_and_clean_answer("a0", "a0")
    config.target.send_command_and_clean_answer("t0", "t0")
    config.target.send_command_and_clean_answer("c0", "c0")
    log(f"Commande de nettoyage envoyée à la cible.", "blue")
    time.sleep(0.5)

    current_min = config.configItems.tx_current.minimum
    current_max = config.configItems.tx_current.maximum
    current_unit = "A"

    for attempt in range(1, config.max_retries + 1):
        current = round(float(config.multimeter_current.meas()), 3)
        log(f"Courant mesuré : {current}{current_unit} ; min={current_min}{current_unit} ; max={current_max}{current_unit}", "blue")
        id = config.save_value(step_name_id, "TX_CURRENT_A", current, current_unit, current_min, current_max)
        if current > current_max or current < current_min:
            if attempt < config.max_retries:
                log(f"Réessaie de mesurer le courant... (tentative {attempt + 1}/{config.max_retries})", "yellow")
                time.sleep(1)
                continue
            else:
                return_msg["infos"].append(f"Problème de courant.")
                return 1, return_msg
        config.db.update_by_id("skvp_float", id, {"valid": 1})

        freq_min = config.configItems.frequency_tx.minimum
        freq_max = config.configItems.frequency_tx.maximum
        freq_unit = "Hz"
        power_min = config.configItems.frequency_tx.power_min
        power_max = config.configItems.frequency_tx.power_max
        offset_power = config.configItems.frequency_tx.offset_power
        cmd = "m"
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
                    return_msg["infos"].append(f"Impossible de se connecter à la cible KTS1.")
                    return 1, return_msg
            except Exception as e:
                log(f"Error: {e}", "red")
                return_msg["infos"].append(f"Erreur lors de l'initialisation de la cible : {e}")
                return 1, return_msg
            # At this point, kts1 is good so we put it in the global config
            config.target = target
            response = config.target.send_command_and_clean_answer(cmd)
        log(f"commande \"{cmd}\" envoyée à la cible : \"{response}\"", "blue")
        response = response.split(" ")
        freq = float(response[12].split("\n")[1].replace("GHz", "")) * 1e9  # Convert GHz to Hz
        power = round(float(response[14].replace("dBm", "")) + offset_power, 1)
        log(f"Fréquence mesurée : {freq}{freq_unit} ; min={freq_min}{freq_unit} ; max={freq_max}{freq_unit}", "blue")
        id_freq = config.save_value(step_name_id, "TX_FREQ_Hz", freq, freq_unit, min_value=freq_min, max_value=freq_max)
        log(f"Puissance mesurée : {power}dBm ; min={power_min}dBm ; max={power_max}dBm", "blue")
        id_power = config.save_value(step_name_id, "TX_EIRP_dBm", power, "dBm", min_value=power_min, max_value=power_max)
        if freq < freq_min or freq > freq_max:
            if attempt < config.max_retries:
                log(f"Réessaie de mesurer la fréquence... (tentative {attempt + 1}/{config.max_retries})", "yellow")
                time.sleep(1)
                continue
            else:
                return_msg["infos"].append(f"Problème de fréquence.")
                return 1, return_msg
        config.db.update_by_id("skvp_float", id_freq, {"valid": 1})

        if power < power_min or power > power_max:
            if attempt < config.max_retries:
                log(f"Réessaie de mesurer la puissance... (tentative {attempt + 1}/{config.max_retries})", "yellow")
                time.sleep(1)
                continue
            else:
                return_msg["infos"].append(f"Problème de puissance.")
                return 1, return_msg
        config.db.update_by_id("skvp_float", id_power, {"valid": 1})
        log(f"Ajout de l'offset de puissance : {offset_power}dBm ; Puissance mesurée : {power}dBm", "blue")

        return_msg["infos"].append(f"OK")
        return 0, return_msg

    return_msg["infos"].append(f"NOK")
    return 1, return_msg


if __name__ == "__main__":
    """Allow to run this script directly for testing purposes."""
    from modules.capsys_mysql_command.capsys_mysql_command import (GenericDatabaseManager, DatabaseConfig) # Custom

    def log_message(message, color):
        print(f"{color}: {message}")

    # Initialize config
    config = configuration.AppConfig()
    config.arg.show_all_logs = False
    config.arg.product_list_id = configuration.PRODUCT_LIST_ID_DEFAULT

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