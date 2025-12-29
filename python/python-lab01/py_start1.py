# py_start1.py
from pathlib import Path
from datetime import datetime, timezone

print(f"{datetime.now(timezone.utc).isoformat()}: Running: {Path(__file__)}")

def main():
    print("Hello World")

if __name__ == '__main__':
    main()
