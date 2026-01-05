import sys, os
import traceback
from pathlib import Path
from datetime import datetime, timezone

print(f"{datetime.now(timezone.utc).isoformat()}: Running: {Path(__file__)}")
if os.getenv("print_stack"):
    print(50 * "-", "\nCall stack:")
    traceback.print_stack(file=sys.stdout);
    print(50 * "-")
