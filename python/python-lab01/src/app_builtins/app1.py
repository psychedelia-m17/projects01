# Use built-ins
from constants import RESPONSE
from enums import MessageType, OpStatus

def print_message(msg_type: MessageType, op_status: OpStatus, **kwargs):
    text = RESPONSE.get(msg_type, {}).get(op_status, "Not defined").format(**kwargs)
    print(text)


if __name__ == "__main__":
    for mt in MessageType:
        for op in OpStatus:
            print(50 * "-")
            print(f"Printing message for: {mt.name}, {op.name}")
            print_message(mt, op, id="id1", name="name1")
