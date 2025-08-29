import os
from typing import Optional
import atexit
from modules.capsys_mysql_command.capsys_mysql_command import (GenericDatabaseManager, DatabaseConfig) # Custom
# from modules.capsys_serial_instrument_manager.ka3005p import alimentation_ka3005p  # Custom

# Initialize global variables
NAME = "Test antenne patch FMCW radar pied de feu RF90042"
AUTHOR = "Thomas GERARDIN"
CURRENTH_PATH = os.path.dirname(__file__)
VERSION = "DEBUG"  # Will be replaced by the Git hash when compiled with command .\build.bat
VERSION_USER = "V0.0.1 ; Commit : " + VERSION

def get_project_path(*paths):
    """Return the absolute path from the project root, regardless of current working directory."""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), *paths))

class ConfigItems:
    """Container for all configuration items used in the test sequence."""
    key_map = {
        "MULTIMETRE": "multimeter", # Example
        # Add other keys and their corresponding ConfigItem attributes as needed
    }

    def init_config_items(self, configJson):
        """Initialize configItems attributes from the config JSON mapping pins and keys."""
        key_map = ConfigItems.key_map
        # For each element of config.json, create a corresponding ConfigItem
        for json_key, attr_name in key_map.items():
            item = configJson.get(json_key, {}) # Retrieves the JSON object or {} if absent
            # Create the ConfigItem with all the parameters from the JSON
            setattr(
                self,
                attr_name,
                ConfigItems.ConfigItem(                
                    key=item.get("key"),
                    # Add other parameters as needed
                )
            )

    class ConfigItem:
        """Represents a single configuration item loaded from config.json or database."""
        def __init__(
            self,
            key = "",
            # Add other parameters as needed
        ):
            """Initialize a ConfigItem with optional parameters for test configuration."""
            self.key = key
            # Add other parameters as needed
    
    def __init__(self):
        """Initialize all ConfigItem attributes for different test parameters."""
        self.multimeter = self.ConfigItem() # Example
        # Add other ConfigItems as needed

class Arg:
    name = NAME
    show_all_logs = False
    operator = AUTHOR
    commande = ""
    of = ""
    article = ""
    indice = ""
    product_list_id = "1"
    user = "root"
    password = "root"
    host = "127.0.0.1"
    port = "3306"
    database = "mysqltest"
    product_list: Optional[list[str]] = None
    parameters_group: list[str] = []
    external_devices: Optional[list[str]] = None
    script: Optional[str] = None

class AppConfig:
    def __init__(self):
        self.arg = Arg()
        self.VERSION = VERSION_USER
        self.db_config: Optional[DatabaseConfig] = None
        self.db: Optional[GenericDatabaseManager] = None
        self.device_under_test_id: Optional[int] = None
        self.configItems = ConfigItems()
        atexit.register(self.cleanup) # Register cleanup function to be called on exit

    def save_value(self, step_name_id: int, key: str, value: str, unit: str = ""):
        """Save a key-value pair in the database."""
        if not self.db or not self.device_under_test_id:
            raise ValueError("Database or device under test ID is not initialized.")
        self.db.create("step_key_val_pairs",
                       {"step_name_id": step_name_id, "key": key, "val_char": value, "unit": unit})
        
    def cleanup(self):
        if self.db:
            self.db.disconnect()
            self.db = None
        self.device_under_test_id = None