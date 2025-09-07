import os
import sys
import setuptools_scm

PROJECT_ROOT = "../"
PYTHON_ROOT = "../py"
DEFAULT_VERSION = "0.0.0"

project = "AI-6"
author = "Sayfan-AI"
try:
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), PROJECT_ROOT))
    release = setuptools_scm.get_version(root=repo_root, relative_to=__file__)
except Exception:
    release = DEFAULT_VERSION

# Add project root and /py to path
sys.path.insert(0, os.path.abspath(PROJECT_ROOT))
sys.path.insert(0, os.path.abspath(PYTHON_ROOT))


autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
}

autosummary_generate = True

exclude_patterns = [
    "README.md"  # Skip the docs README
]

extensions = [
    "myst_parser",  # Markdown support
    "sphinx.ext.autodoc",  # Auto API docs
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",  # Google/NumPy style docstrings
    "sphinx_autodoc_typehints",  # Show type hints
]

html_theme = "furo"
html_static_path = ["_static"]
html_js_files = [
    "custom_sidebar.js",
]

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

templates_path = ["_templates"]
