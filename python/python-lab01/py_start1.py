# py_start1.py
from pathlib import Path
from datetime import datetime, timezone
import traceback
import sys

print(f"{datetime.now(timezone.utc).isoformat()}: Running: {Path(__file__)}")
MESSAGE_TEMPLATE_1 = "A simple string template with arguments: {arguments}."

def get_stack() -> list[str]:
    return traceback.format_stack()

def print_stack() -> None:
    print(50 * "-", "\nCall stack:"); traceback.print_stack(file=sys.stdout);print(50 * "-")

def main():
    print("Hello World")
    msg_args={"arguments": "value2"}
    print(MESSAGE_TEMPLATE_1.format(**{"arguments": "value3"}))
    print(MESSAGE_TEMPLATE_1.format(arguments="value4"))


if __name__ == '__main__':
    main()
    print_stack()

