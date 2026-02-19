from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="Replay an ANSI-colored log to stdout.")
    ap.add_argument(
        "path",
        nargs="?",
        default="consumer_tests.txt",
        help="Path to ANSI log file (default: consumer_tests.txt)",
    )
    args = ap.parse_args()

    path = Path(args.path)
    if not path.exists():
        print(f"[replay] log file not found: {path}", file=sys.stderr)
        return 2

    # Stream it out exactly as-is so ANSI escapes remain intact
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), ""):
            if not chunk:
                break
            sys.stdout.write(chunk)

    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
