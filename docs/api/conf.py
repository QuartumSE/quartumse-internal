from __future__ import annotations

import sys
import inspect
from datetime import datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from sphinx.application import Sphinx
from sphinx.util import logging

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_PATH = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_PATH))

project = "QuartumSE"
author = "QuartumSE Team"
current_year = datetime.now().year
copyright = f"{current_year}, {author}"

try:
    release = version("quartumse")
except PackageNotFoundError:
    release = "0.1.0"

# Extract version from release (e.g., "0.1.0" from "0.1.0")
version = release.split("+")[0]  # Strip any +dev suffix if present

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autodoc.typehints",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "myst_parser",
    "sphinx_autodoc_typehints",
]

autosummary_generate = True
napoleon_google_docstring = True
napoleon_use_param = True
napoleon_use_rtype = False

autodoc_typehints = "description"
autodoc_typehints_format = "short"
autodoc_default_options = {
    "members": True,
    "undoc-members": False,
    "show-inheritance": True,
}

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "alabaster"
html_static_path = ["_static"]

# Suppress warnings for classes re-exported from multiple modules
# These warnings occur because classes are intentionally exposed from both their
# source module (e.g., quartumse.shadows.config) and parent package (e.g., quartumse.shadows)
suppress_warnings = [
    "ref.python",  # Ambiguous Python cross-references
    "autodoc",     # Duplicate object descriptions and other autodoc warnings
    "toc",         # TOC/toctree warnings (nonexistent documents, etc.)
]

# Modules that primarily re-export symbols from their submodules. Documenting the
# same class in both the parent package and the implementation module causes
# ``autodoc`` to emit duplicate-description warnings when Sphinx runs in
# nitpicky/``-W`` mode. We skip these re-exported members when documenting the
# parent package to avoid the duplicates while still keeping the canonical
# documentation attached to the implementation module.
REEXPORT_PACKAGES = {
    "quartumse",
    "quartumse.estimator",
    "quartumse.reporting",
    "quartumse.shadows",
}

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "sphinx": ("https://www.sphinx-doc.org/en/master", None),
    "numpy": ("https://numpy.org/doc/stable", None),
    "pandas": ("https://pandas.pydata.org/pandas-docs/stable", None),
    "scipy": ("https://docs.scipy.org/doc/scipy", None),
    "qiskit": ("https://quantum.cloud.ibm.com/docs/api/qiskit", None),
    "qiskit_ibm_runtime": ("https://quantum.cloud.ibm.com/docs/api/qiskit-ibm-runtime", None),
    "pydantic": ("https://docs.pydantic.dev/latest", None),
}

# Provide canonical targets for commonly re-exported types so that autodoc
# generates unambiguous cross references even when the symbols are available
# from multiple modules (e.g., ``quartumse`` and ``quartumse.shadows``).
autodoc_type_aliases = {
    "ShadowConfig": "quartumse.shadows.config.ShadowConfig",
    "MeasurementErrorMitigation": "quartumse.mitigation.mem.MeasurementErrorMitigation",
    "BackendSnapshot": "quartumse.reporting.manifest.BackendSnapshot",
    "CircuitFingerprint": "quartumse.reporting.manifest.CircuitFingerprint",
    "MitigationConfig": "quartumse.reporting.manifest.MitigationConfig",
    "ResourceUsage": "quartumse.reporting.manifest.ResourceUsage",
    "ShadowsConfig": "quartumse.reporting.manifest.ShadowsConfig",
    "ManifestSchema": "quartumse.reporting.manifest.ManifestSchema",
    "Backend": "qiskit.providers.backend.Backend",
    "SamplerV2": "qiskit_ibm_runtime.SamplerV2",
    "QiskitRuntimeService": "qiskit_ibm_runtime.QiskitRuntimeService",
    "ValidationInfo": "pydantic_core.core_schema.ValidationInfo",
    "Path": "pathlib.Path",
}

# ``numpy.random.Generator`` is exposed from an internal module in the NumPy
# documentation inventory, so Sphinx cannot resolve it automatically when we
# run in ``-n`` (nitpicky) mode. Silence the warning by explicitly ignoring the
# private target name that appears in the type hints.
nitpick_ignore = [
    ("py:class", "numpy.random._generator.Generator"),
    ("py:class", "pydantic.main.BaseModel"),
    ("py:attr", "confusion_matrix"),
    # External Qiskit classes that intersphinx can't always resolve
    ("py:class", "Backend"),
    ("py:class", "QiskitRuntimeService"),
    ("py:class", "Path"),
    # Pydantic classes (for missing reference warnings)
    ("py:class", "BackendSnapshot"),
    ("py:class", "MitigationConfig"),
]

apidoc_output_path = Path(__file__).parent / "reference"
apidoc_module_path = SRC_PATH / "quartumse"
apidoc_excluded = [str(SRC_PATH / "quartumse" / "tests")]
logger = logging.getLogger(__name__)

def run_apidoc(app: Sphinx) -> None:
    from sphinx.ext import apidoc

    if not apidoc_module_path.exists():
        logger.warning("API source path not found: %s", apidoc_module_path)
        return

    apidoc_output_path.mkdir(parents=True, exist_ok=True)
    argv = [
        "-f",
        "-M",
        "-e",
        "-o",
        str(apidoc_output_path),
        str(apidoc_module_path),
        *apidoc_excluded,
    ]
    apidoc.main(argv)


def setup(app: Sphinx) -> None:
    app.connect("builder-inited", run_apidoc)
    app.connect("autodoc-skip-member", skip_reexported_members)


def skip_reexported_members(app: Sphinx, what: str, name: str, obj: object, skip: bool, options: dict) -> bool | None:
    """Omit members that are re-exported from submodules.

    Returning ``True`` tells autodoc to skip the member. ``None`` defers to the
    default behaviour, so we only return ``True`` for classes that originate from
    a submodule of one of the re-export-heavy packages listed above. Attributes
    such as ``__version__`` (which come from ``builtins``) continue to be
    documented normally.
    """

    if skip or what != "module":
        return None

    module_name = options.get("module")
    if module_name is None and hasattr(app, "env"):
        module_name = getattr(app.env, "temp_data", {}).get("autodoc:module")

    if module_name not in REEXPORT_PACKAGES:
        return None

    if not inspect.isclass(obj):
        return None

    obj_module = getattr(obj, "__module__", "")
    if obj_module.startswith(f"{module_name}."):
        return True

    return None
