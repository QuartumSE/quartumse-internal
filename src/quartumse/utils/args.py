"""Reusable argparse helpers for experiment scripts."""

from __future__ import annotations

import argparse
from pathlib import Path

__all__ = [
    "DEFAULT_DATA_DIR",
    "add_backend_option",
    "add_data_dir_option",
    "add_seed_option",
    "add_shadow_size_option",
    "namespace_overrides",
]

DEFAULT_DATA_DIR = Path("data")

_BACKEND_HELP = (
    "Backend descriptor. Use 'aer_simulator' for local runs or 'ibm:<device>' "
    "for IBM Quantum hardware."
)

_DATA_DIR_HELP = (
    "Directory for manifests, shot archives, and cached calibration data. "
    "Created automatically when missing."
)

_SEED_HELP = (
    "Random seed used when sampling classical shadows. Overrides any value "
    "loaded from configuration files."
)

_SHADOW_SIZE_HELP = (
    "Number of classical shadow measurements to perform per experiment. "
    "Higher values improve precision but cost more shots."
)


def add_backend_option(
    parser: argparse.ArgumentParser,
    *,
    default: str | None = None,
    required: bool = False,
) -> argparse.Action:
    """Attach a ``--backend`` option to *parser* and return the created action."""

    return parser.add_argument(
        "--backend",
        type=str,
        default=default,
        required=required,
        help=_BACKEND_HELP,
    )


def add_data_dir_option(
    parser: argparse.ArgumentParser,
    *,
    default: Path | str | None = None,
) -> argparse.Action:
    """Attach a ``--data-dir`` option that returns :class:`~pathlib.Path` values."""

    default_path: Path | None
    if default is None:
        default_path = None
        help_text = f"{_DATA_DIR_HELP} [default: {DEFAULT_DATA_DIR}]"
    else:
        default_path = Path(default)
        help_text = f"{_DATA_DIR_HELP} [default: {default_path}]"

    return parser.add_argument(
        "--data-dir",
        type=Path,
        default=default_path,
        help=help_text,
    )


def add_seed_option(
    parser: argparse.ArgumentParser,
    *,
    default: int | None = None,
) -> argparse.Action:
    """Attach a ``--seed`` option for reproducibility overrides."""

    return parser.add_argument(
        "--seed",
        type=int,
        default=default,
        help=_SEED_HELP,
    )


def add_shadow_size_option(
    parser: argparse.ArgumentParser,
    *,
    default: int | None = None,
) -> argparse.Action:
    """Attach a ``--shadow-size`` option for measurement counts."""

    return parser.add_argument(
        "--shadow-size",
        type=int,
        default=default,
        help=_SHADOW_SIZE_HELP,
    )


def namespace_overrides(namespace: argparse.Namespace) -> dict[str, object]:
    """Extract CLI overrides present in *namespace*.

    Only values that were explicitly provided are returned; ``None`` values are
    omitted so callers can fall back to configuration defaults.
    """

    overrides: dict[str, object] = {}
    for attr in ("backend", "data_dir", "seed", "shadow_size"):
        value = getattr(namespace, attr, None)
        if value is not None:
            overrides[attr] = value
    return overrides
