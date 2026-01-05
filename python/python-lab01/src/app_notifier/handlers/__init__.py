import pkgutil
import importlib
import os, sys
import traceback
from typing import Dict
from .base import ActionHandler, ActionType, HANDLER_REGISTRY
from pathlib import Path
from datetime import datetime, timezone

def list_all_modules(start_path: str, indent: int = 2) -> None:
    print(f"{(indent - 2) * '-'}Walking: {start_path}")
    for ldr, mod_name, is_pkg2 in pkgutil.walk_packages(start_path):
        full_mod_name = f"{__name__}.{mod_name}"
        print(f"{indent * '.'}module_name: {mod_name}, is_pkg: {is_pkg2}, full_module_name: {full_mod_name}, loader: {ldr}")
        if is_pkg2:
            mod = importlib.import_module(full_mod_name)
            # print(mod.__path__)
            list_all_modules(mod.__path__, indent + 2)


print(f"{datetime.now(timezone.utc).isoformat()}: Running: {Path(__file__)}")
if os.getenv("print_stack"):
    print(50 * "-", "\nCall stack:")
    traceback.print_stack(file=sys.stdout);
    print(50 * "-")

# # 1. Initialize the registry
# # Key: ActionType Enum, Value: Instance of the subclass
# HANDLER_REGISTRY: Dict[ActionType, ActionHandler] = {}

# 2. Automatically discover and import all modules in this package
# __path__ provides the directory of the current package
print(f"Loading modules in __path__: {__path__}")
for loader, module_name, is_pkg in pkgutil.iter_modules(__path__):
    # Import the module dynamically (e.g., 'handlers.email_handler')
    full_module_name = f"{__name__}.{module_name}"
    print(f"    loader: {loader}, module_name: {module_name}, is_pkg: {is_pkg}, full_module_name: {full_module_name}")
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

# Recursively list all modules and submodules using pkgutil.walk_packages()
print(50 * "=", "\nListing modules recursively")
list_all_modules(start_path=__path__, indent=2)
print(50 * "=")