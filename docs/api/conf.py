from __future__ import annotations

import sys
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

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "sphinx": ("https://www.sphinx-doc.org/en/master", None),
    "numpy": ("https://numpy.org/doc/stable", None),
    "pandas": ("https://pandas.pydata.org/pandas-docs/stable", None),
    "scipy": ("https://docs.scipy.org/doc/scipy", None),
    "qiskit": ("https://docs.quantum.ibm.com/api/qiskit", None),
}

# Provide canonical targets for commonly re-exported types so that autodoc
# generates unambiguous cross references even when the symbols are available
# from multiple modules (e.g., ``quartumse`` and ``quartumse.shadows``).
autodoc_type_aliases = {
    "ShadowConfig": "quartumse.shadows.config.ShadowConfig",
    "MeasurementErrorMitigation": "quartumse.mitigation.mem.MeasurementErrorMitigation",
}

# ``numpy.random.Generator`` is exposed from an internal module in the NumPy
# documentation inventory, so Sphinx cannot resolve it automatically when we
# run in ``-n`` (nitpicky) mode. Silence the warning by explicitly ignoring the
# private target name that appears in the type hints.
nitpick_ignore = [
    ("py:class", "numpy.random._generator.Generator"),
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
