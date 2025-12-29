# from src.handlers import HANDLER_REGISTRY
# from src.handlers.base import ActionType, ActionHandler, ActionHandlerFactory
from ...handlers.base import HANDLER_REGISTRY, ActionType, ActionHandler, ActionHandlerFactory
from pathlib import Path
from datetime import datetime, timezone

# class ActionHandlerFactory:
#     @staticmethod
#     def get_handler(action_type: ActionType) -> ActionHandler:
#         handler = HANDLER_REGISTRY.get(action_type)
#         if not handler:
#             raise ValueError(f"No handler registered for {action_type}")
#         return handler

print(f"{datetime.now(timezone.utc).isoformat()}: Running: {Path(__file__)}")
print(f"__name__ : {__name__}")

# --- Execution ---
if __name__ == "__main__":

    # Get the SMS handler from the factory
    sms_sender = ActionHandlerFactory.get_handler(ActionType.SMS)
    # sms_sender.set_message_client("default_sms_client")
    sms_sender.execute("Hello 1 via SMS!")

    # Get the Email handler from the factory
    email_sender = ActionHandlerFactory.get_handler(ActionType.EMAIL)
    email_sender.set_message_client("smtp_client")
    email_sender.execute("Hello 2 via Email!")

    wapp_sender = ActionHandlerFactory.get_handler(ActionType.WHATSAPP)
    wapp_sender.set_message_client("wapp_client")
    wapp_sender.execute("Hello 3 via WhatsApp!")

    # Show the internal registry created by __init__.py
    print(f"\nDiscovered Handlers: {list(HANDLER_REGISTRY.keys())}")