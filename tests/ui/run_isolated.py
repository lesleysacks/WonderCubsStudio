"""Run every UI test in its own Python process.

Each UI test creates a Tk application, i.e. a new Tcl interpreter. On Windows,
creating many interpreters in one process eventually fails inside Tcl
('tcl_findLibrary' / 'Can't find a usable init.tcl'), independent of the
application. One process per test avoids that and isolates the tests.

Usage (from the repository root):  python tests/ui/run_isolated.py
"""
from __future__ import annotations

import subprocess
import sys


def main() -> int:
    collected = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider", "tests/ui"],
        capture_output=True, text=True,
    )
    test_ids = [line.strip() for line in collected.stdout.splitlines() if "::" in line]
    if collected.returncode != 0 or not test_ids:
        print(collected.stdout, collected.stderr, sep="\n")
        print("No UI tests were collected.", file=sys.stderr)
        return 1
    failed = []
    for test_id in test_ids:
        result = subprocess.run([sys.executable, "-m", "pytest", "-q", "-rs", "-p", "no:cacheprovider", test_id])
        if result.returncode != 0:
            failed.append(test_id)
    print(f"\nUI tests: {len(test_ids) - len(failed)} passed, {len(failed)} failed (one process each)")
    for test_id in failed:
        print(f"FAILED {test_id}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
