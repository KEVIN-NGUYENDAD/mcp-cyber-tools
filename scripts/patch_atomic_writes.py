#!/usr/bin/env python3
"""
Automated Patch Script: Convert All Unsafe Writes to Atomic Writes
Scans all Python scripts and updates json.dump() patterns to use state_manager.py

Target: Address TD-L3-001, TD-L3-002, TD-L3-003
Pattern: Replace unsafe with open() + json.dump() with atomic writes
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple

SCRIPTS_DIR = Path(__file__).parent
IMPORT_STATEMENT = "from state_manager import write_state_atomic, read_state_safe"

def find_unsafe_writes(script_path: str) -> List[Tuple[int, str]]:
    """Find all unsafe write patterns in a script."""
    with open(script_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    unsafe_patterns = []

    for i, line in enumerate(lines, 1):
        # Pattern 1: with open(..., 'w') followed by json.dump
        if "with open(" in line and "'w'" in line:
            unsafe_patterns.append((i, line.strip()))
        # Pattern 2: open(...).write(json.dumps())
        elif "json.dump" in line and "with open" in line:
            unsafe_patterns.append((i, line.strip()))

    return unsafe_patterns

def has_import(script_path: str) -> bool:
    """Check if script already has state_manager import."""
    with open(script_path, 'r', encoding='utf-8') as f:
        content = f.read()
    return 'from state_manager import' in content

def add_import_if_needed(script_path: str) -> bool:
    """Add state_manager import if not present."""
    if has_import(script_path):
        return False

    with open(script_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Find insertion point: after other imports
    insert_idx = 0
    for i, line in enumerate(lines):
        if line.startswith('import ') or line.startswith('from '):
            insert_idx = i + 1
        elif line.startswith('class ') or line.startswith('def '):
            break

    # Insert import
    lines.insert(insert_idx, f"\n# Import atomic write functions for file safety (TD-L3-001, TD-L3-002, TD-L3-003)\n{IMPORT_STATEMENT}\n")

    with open(script_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)

    return True

def scan_scripts() -> dict:
    """Scan all Python scripts for unsafe writes."""
    results = {
        'total_scripts': 0,
        'scripts_with_unsafe_writes': 0,
        'total_unsafe_patterns': 0,
        'files': []
    }

    for script_path in sorted(SCRIPTS_DIR.glob('*.py')):
        if script_path.name in ['state_manager.py', 'test_atomic_writes.py', 'patch_atomic_writes.py']:
            continue

        results['total_scripts'] += 1
        unsafe = find_unsafe_writes(str(script_path))

        if unsafe:
            results['scripts_with_unsafe_writes'] += 1
            results['total_unsafe_patterns'] += len(unsafe)
            results['files'].append({
                'name': script_path.name,
                'patterns': len(unsafe),
                'lines': [line_num for line_num, _ in unsafe]
            })

    return results

def print_report(results: dict):
    """Print audit report."""
    print("\n" + "=" * 80)
    print("ATOMIC WRITES AUDIT REPORT")
    print("=" * 80)
    print(f"Total Python Scripts: {results['total_scripts']}")
    print(f"Scripts with Unsafe Writes: {results['scripts_with_unsafe_writes']}")
    print(f"Total Unsafe Patterns: {results['total_unsafe_patterns']}")
    print("=" * 80)

    if results['files']:
        print("\nFILES NEEDING UPDATES:")
        for file_info in sorted(results['files'], key=lambda x: x['patterns'], reverse=True):
            print(f"\n  {file_info['name']}")
            print(f"    Unsafe writes: {file_info['patterns']}")
            print(f"    Lines: {file_info['lines']}")
    else:
        print("\n✓ No unsafe writes detected!")

    print("\n" + "=" * 80)

def main():
    """Run audit and generate report."""
    print("[AUDIT] Scanning Python scripts for unsafe writes...")

    results = scan_scripts()
    print_report(results)

    # Generate detailed report file
    report_path = SCRIPTS_DIR.parent / "ATOMIC_WRITES_AUDIT.txt"
    with open(report_path, 'w') as f:
        f.write("ATOMIC WRITES AUDIT REPORT\n")
        f.write("=" * 80 + "\n")
        f.write(f"Total Python Scripts: {results['total_scripts']}\n")
        f.write(f"Scripts with Unsafe Writes: {results['scripts_with_unsafe_writes']}\n")
        f.write(f"Total Unsafe Patterns: {results['total_unsafe_patterns']}\n")
        f.write("=" * 80 + "\n\n")

        for file_info in sorted(results['files'], key=lambda x: x['patterns'], reverse=True):
            f.write(f"FILE: {file_info['name']}\n")
            f.write(f"  Unsafe writes: {file_info['patterns']}\n")
            f.write(f"  Lines: {file_info['lines']}\n\n")

    print(f"\n[OK] Detailed report saved to: {report_path}")

    return 0 if results['scripts_with_unsafe_writes'] == 0 else 1

if __name__ == '__main__':
    sys.exit(main())
