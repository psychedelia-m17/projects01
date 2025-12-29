from abc import ABC, abstractmethod
from typing import Dict
from enum import StrEnum, auto
from pathlib import Path
from datetime import datetime, timezone

print(f"{datetime.now(timezone.utc).isoformat()}: Running: {Path(__file__)}")

class ActionType(StrEnum):
    EMAIL = auto()
    SMS = auto()
    WHATSAPP = auto()

class ActionHandler(ABC):
    def __init__(self) -> None:
        print(f"Initializing {self.__class__.__name__}")
        self.message_client: str = "default_client"

    @abstractmethod
    def get_action_type(self) -> ActionType:
        pass

    @abstractmethod
    def execute(self, data: str):
        pass

    def set_message_client(self, message_client: str):
        self.message_client = message_client

    def send_response(self, message: str):
        print(f"Executing send_response for class {self.__class__.__name__}, client: {self.message_client}  message: {message}")

class ActionHandlerFactory:
    @staticmethod
    def get_handler(action_type: ActionType) -> ActionHandler:
        handler = HANDLER_REGISTRY.get(action_type)
        if not handler:
            raise ValueError(f"No handler registered for {action_type}")
        return handler

# --- Execution ---
# 1. Initialize the registry
# Key: ActionType Enum, Value: Instance of the subclass
HANDLER_REGISTRY: Dict[ActionType, ActionHandler] = {}