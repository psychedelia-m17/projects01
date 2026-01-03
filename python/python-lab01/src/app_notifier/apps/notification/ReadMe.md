# Message Notification Application

## Structure

1. Iterative Import: When `from handlers import ...` is called, `handlers/__init__.py` runs.  
It uses `pkgutil` to find every .py file in the `handlers/` folder and imports them.

2. Subclass Tracking: Once imported, the class definitions exist in memory.  
Python's `ActionHandler.__subclasses__()` method finds all classes that inherited from it.

3. Singleton Mapping: We instantiate each class and map its returned `ActionType` to that instance in HANDLER_REGISTRY.

4. Factory Access: The factory doesn't need to know which modules exist;
it just checks the HANDLER_REGISTRY dictionary.


