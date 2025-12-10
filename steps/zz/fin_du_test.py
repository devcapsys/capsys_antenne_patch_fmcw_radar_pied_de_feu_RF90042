# -*- coding: utf-8 -*-
import os
import sys
if __name__ == "__main__":
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    if BASE_DIR not in sys.path:
        sys.path.insert(0, BASE_DIR)
import configuration  # Custom
from modules.capsys_mysql_command.capsys_mysql_command import (GenericDatabaseManager, DatabaseConfig) # Custom
from configuration import get_project_path

def get_info():
    return "Cette étape effectue le nettoyage et la fermeture des ressources en fin de test."

def run_step(log, config: configuration.AppConfig):
    step_name = os.path.splitext(os.path.basename(__file__))[0]
    return_msg = {"step_name": step_name, "infos": []}
    # Ensure db is initialized
    if not hasattr(config, "db") or config.db is None:
        return_msg["infos"].append("Erreur : config.db n'est pas initialisé.")
        return 1, return_msg
    # We always save the name of the step in the db
    config.db.create("step_name", {"device_under_test_id": config.device_under_test_id, "step_name": step_name})

    success = 0
    
    # delete config.json file
    config_file_path = get_project_path("config.json")
    if os.path.exists(config_file_path):
        os.remove(config_file_path)
        log("Fichier config.json supprimé.", "blue")
    else:
        log("Problème lors de la suppression du fichier config.json.", "yellow")
        success = 2

    if config.serial_target_capsys and config.serial_target_capsys.ser and config.serial_target_capsys.ser.is_open:
        log(f"Envoie de la commande \"set cible off\" : {config.serial_target_capsys.send_command('set cible off\r', expected_response='ok', timeout=2)}", "blue")
        config.serial_target_capsys.close()
        config.serial_target_capsys = None
        log("Port série de la cible fermé.", "blue")

    if config.target and config.target.ser and config.target.ser.is_open:
        config.target.send_command_and_clean_answer("a0", "a0")
        config.target.send_command_and_clean_answer("t0", "t0")
        config.target.send_command_and_clean_answer("c0", "c0")
        log("Commande de nettoyage envoyée à la cible.", "blue")
    else:
        log("Aucune cible à déconnecter.", "yellow")
        success = 2

    if config.serial_patch_fmcw and config.serial_patch_fmcw.ser and config.serial_patch_fmcw.ser.is_open:
        log(f"Envoie de la commande \"test power off\" : {config.serial_patch_fmcw.send_command('test power off\r', expected_response='ok', timeout=2)}", "blue")
    else:
        log("Le port série du patch n'avait pas été initialisé.", "yellow")
        success = 2

    if success == 0:
        return_msg["infos"].append("Nettoyage effectué avec succès.")
        return success, return_msg
    elif success == 2:
        return_msg["infos"].append("Nettoyage effectué partiellement.")
        return success, return_msg
    else:
        return_msg["infos"].append("Erreur inconnue lors du nettoyage.")
        return 1, return_msg

if __name__ == "__main__":
    """Allow to run this script directly for testing purposes."""

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