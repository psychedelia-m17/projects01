# Dynamic Subclass Loading

## Objective

Implementing a mechanism for dynamically instantiating all subclasses of a base class from the __init__.py of the package containing the base class. The subclasses are returned to the main application by a factory class. 

### Use Case

Demonstrate the dynamic instantiation of subclasses through a notification application that needs to send notification messages via different notification channels like email, sms, whatsapp, etc.  

The main application module is located at: `apps/notification/app_notifier.py`  
To start the application, `cd` to the `src` directory and type the command:  
Usage:  
```bash
python3 -m app_notifier.apps.notification.app_notifier
```

