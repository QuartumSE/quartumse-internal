"""Utilities for collecting run provenance metadata."""

from __future__ import annotations

import platform
import subprocess
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path


def get_python_version() -> str:
    """Return the current Python version string."""
    return platform.python_version()


def get_git_commit_hash(repo_root: Path | None = None) -> str | None:
    """Return the current git commit hash, if available."""
    root = repo_root or _resolve_repo_root()
    if root is None:
        return None

    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(root),
            check=True,
            capture_output=True,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None

    commit_hash = result.stdout.strip()
    return commit_hash or None


def get_quartumse_version() -> str | None:
    """Return the QuartumSE version string."""
    try:
        return version("quartumse")
    except PackageNotFoundError:
        pass

    package_root = Path(__file__).resolve().parents[1]
    init_path = package_root / "__init__.py"
    if not init_path.exists():
        return None

    for line in init_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("__version__"):
            _, raw_value = line.split("=", 1)
            return raw_value.strip().strip("\"").strip("'")

    return None


def get_environment_lock(repo_root: Path | None = None) -> str | None:
    """Return environment lock contents from uv.lock or pip freeze output."""
    root = repo_root or _resolve_repo_root() or Path.cwd()
    uv_lock = _find_lock_file(root, "uv.lock")
    if uv_lock is not None:
        return uv_lock.read_text(encoding="utf-8")

    return _get_pip_freeze()


def _resolve_repo_root() -> Path | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None

    root = result.stdout.strip()
    return Path(root) if root else None


def _find_lock_file(start: Path, name: str) -> Path | None:
    current = start.resolve()
    for parent in (current, *current.parents):
        candidate = parent / name
        if candidate.exists():
            return candidate
    return None


def _get_pip_freeze() -> str | None:
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "freeze"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None

    output = result.stdout.strip()
    return output or None
