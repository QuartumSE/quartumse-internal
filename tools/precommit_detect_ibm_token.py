#!/usr/bin/env python3
"""Fail commits that include IBM Quantum API tokens."""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Iterable, List, Tuple

TOKEN_PATTERNS = [
    re.compile(r"QISKIT_IBM_TOKEN\s*=\s*['\"]?([A-Za-z0-9]{32,64})['\"]?"),
    re.compile(r"QISKIT_RUNTIME_API_TOKEN\s*=\s*['\"]?([A-Za-z0-9]{32,64})['\"]?"),
]

PLACEHOLDER_MARKERS = {"<YOUR_TOKEN>", "<YOUR_RUNTIME_TOKEN>", "<YOUR_QISKIT_TOKEN>"}


def find_hits(path: Path) -> List[Tuple[int, str]]:
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, FileNotFoundError):
        return []

    hits: List[Tuple[int, str]] = []
    for idx, line in enumerate(text.splitlines(), start=1):
        if any(marker in line for marker in PLACEHOLDER_MARKERS):
            continue
        for pattern in TOKEN_PATTERNS:
            if pattern.search(line):
                hits.append((idx, line.rstrip()))
                break
    return hits


def main(argv: Iterable[str]) -> int:
    files = [Path(arg) for arg in argv]
    problems: List[Tuple[Path, int, str]] = []
    for file_path in files:
        for lineno, line in find_hits(file_path):
            problems.append((file_path, lineno, line))

    if problems:
        print("Potential IBM Quantum credentials detected:")
        for path, lineno, line in problems:
            print(f"  {path}:{lineno}: {line}")
        print("Replace real tokens with placeholders such as <YOUR_TOKEN> before committing.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
