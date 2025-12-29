from .base import ActionHandler, ActionType
from pathlib import Path
from datetime import datetime, timezone

print(f"{datetime.now(timezone.utc).isoformat()}: Running: {Path(__file__)}")

class SMSHandler(ActionHandler):
    def get_action_type(self):
        return ActionType.SMS

    def execute(self, data: str):
        print(f"Sending {self.get_action_type()}: {data}")
        self.send_response(f"send_response called from SMSHandler, data: {data}")

