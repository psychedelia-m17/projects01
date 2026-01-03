import sys
import traceback
from pathlib import Path
from datetime import datetime, timezone

print(50 * "-", "\n", f"{datetime.now(timezone.utc).isoformat()}: Running: {Path(__file__)}", "\nCall stack:")
traceback.print_stack(file=sys.stdout);
print(50 * "-")
