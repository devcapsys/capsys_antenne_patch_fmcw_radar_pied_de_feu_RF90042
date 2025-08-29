import os
from typing import Optional
import atexit
from modules.capsys_serial_instrument_manager.capsys_serial_instrument_manager import SerialInstrumentManager  # Custom
from modules.capsys_serial_instrument_manager.mp730424.multimeter_mp730424 import Mp730424Manager  # Custom
from modules.capsys_mysql_command.capsys_mysql_command import (GenericDatabaseManager, DatabaseConfig) # Custom
from modules.capsys_serial_instrument_manager.rsd3305p import alimentation_rsd3305p  # Custom
from modules.capsys_serial_instrument_manager.kts1.cible_kts1 import Kts1Manager  # Custom

# Initialize global variables
NAME = "Test antenne patch FMCW radar pied de feu RF90042"
AUTHOR = "Thomas GERARDIN"
CURRENTH_PATH = os.path.dirname(__file__)
VERSION = "DEBUG"  # Will be replaced by the Git hash when compiled with command .\build.bat
VERSION_USER = "V0.0.1 ; Commit : " + VERSION

def get_project_path(*paths):
    """Return the absolute path from the project root, regardless of current working directory."""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), *paths))

class SerialPatch(SerialInstrumentManager):
    def __init__(self, port=None, baudrate=115200, timeout=0.3, debug=False):
        SerialInstrumentManager.__init__(self, port, baudrate, timeout, debug)
        self._debug_log("PatchManager initialized")

    def get_valid(self, sn=None) -> bool:
        idn = self.send_command("help\r", timeout=1) # Example : help = "Command disp : prod param stat all"
        if not idn:
            raise RuntimeError("Failed to get valid IDN response")
        if idn.startswith("Command disp :\r prod\r param\r stat\r all\r"):
            self._debug_log(f"Device IDN: {idn}")
            return True
        else:
            raise RuntimeError(f"Invalid device IDN: {idn}")
        
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
            port = ""
        ):
            """Initialize a ConfigItem with optional parameters for test configuration."""
            self.key = key
            self.port = port
    
    def __init__(self):
        """Initialize all ConfigItem attributes for different test parameters."""
        self.target = self.ConfigItem()
        self.multimeter_current = self.ConfigItem()
        self.alim = self.ConfigItem()
        self.serial_patch = self.ConfigItem()

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
        self.max_retries = 2
        self.multimeter_current: Optional[Mp730424Manager] = None
        self.alim: Optional[alimentation_rsd3305p.Rsd3305PManager] = None
        self.target: Optional[Kts1Manager] = None
        self.serial_patch: Optional[SerialPatch] = None
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