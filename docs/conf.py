from __future__ import annotations

import os
import sys
from datetime import datetime

# Add project src to path so autodoc can import modules
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)


project = "Robot Library (Python)"
author = "PeraSwarm"
copyright = f"{datetime.now().year}, {author}"

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx_autodoc_typehints",
]

autosummary_generate = True
autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
}

napoleon_google_docstring = True
napoleon_numpy_docstring = False

# If you cannot or do not want to install heavy deps, you can mock them here
# autodoc_mock_imports = ["paho", "paho.mqtt", "paho.mqtt.client"]

templates_path = ["_templates"]
html_static_path = ["_static"]

# html_theme = "furo"
html_theme = "sphinx_rtd_theme"
html_theme_options = {
    "collapse_navigation": False,
    "navigation_depth": 3,
    "titles_only": False,
    "prev_next_buttons_location": "bottom",
    "sticky_navigation": False,
    "style_nav_header_background": "#3468af",
}


source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", ".venv", ".github"]
