import pkgutil
import importlib
import sys
import traceback
from typing import Dict
from .base import ActionHandler, ActionType, HANDLER_REGISTRY
from pathlib import Path
from datetime import datetime, timezone

print(50 * "-", "\n", f"{datetime.now(timezone.utc).isoformat()}: Running: {Path(__file__)}", "\nCall stack:")
traceback.print_stack(file=sys.stdout);
print(50 * "-")

# # 1. Initialize the registry
# # Key: ActionType Enum, Value: Instance of the subclass
# HANDLER_REGISTRY: Dict[ActionType, ActionHandler] = {}

# 2. Automatically discover and import all modules in this package
# __path__ provides the directory of the current package
for loader, module_name, is_pkg in pkgutil.iter_modules(__path__):
    # Import the module dynamically (e.g., 'handlers.email_handler')
    full_module_name = f"{__name__}.{module_name}"
    importlib.import_module(full_module_name)

# 3. Use __subclasses__() to find all loaded implementations
# This only works after the modules are imported above
for cls in ActionHandler.__subclasses__():
    try:
        instance = cls()  # Create an instance
        action_type = instance.get_action_type()
        HANDLER_REGISTRY[action_type] = instance
    except TypeError:
        # Handles cases where a subclass might be another ABC
        continue
