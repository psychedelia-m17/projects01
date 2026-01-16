# Define Enums

from enum import StrEnum, auto

class MessageType(StrEnum):
    order_create = auto()
    order_update = auto()
    order_delete = auto()
    # quote_create = auto()
    # quote_update = auto()
    # quote_delete = auto()

class OpStatus(StrEnum):
    create_ok = auto()
    create_failed = auto()
    update_ok = auto()
    update_failed = auto()
    delete_ok = auto()
    delete_failed = auto()
    list_ok = auto()
    list_failed = auto()
