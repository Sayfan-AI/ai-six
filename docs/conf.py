import os
import sys

# Add project root and /py to path
sys.path.insert(0, os.path.abspath("../"))
sys.path.insert(0, os.path.abspath("../py"))

project = "AI-6"
author = "Sayfan-AI"
release = "0.1.0"

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
html_static_path = ['_static']
html_js_files = [
    'custom_sidebar.js',
]

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

templates_path = ["_templates"]


