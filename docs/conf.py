# Configuration file for the Sphinx documentation builder.

import os
import sys
from pathlib import Path

# Add the parent directory to the path so Sphinx can find the modules
sys.path.insert(0, str(Path(__file__).parent.parent))

project = 'Paint Robot'
copyright = '2026, Simon'
author = 'Simon'
release = '0.1.0'
version = '0.1.0'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.doctest',
    'sphinx.ext.intersphinx',
    'sphinx.ext.todo',
    'sphinx.ext.coverage',
    'sphinx.ext.mathjax',
    'sphinx.ext.ifconfig',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
]

templates_path = ['_templates']
source_suffix = '.rst'
master_doc = 'index'

language = 'en'
exclude_patterns = ['_build']
pygments_style = 'sphinx'
todo_include_todos = False

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_theme_options = {
    'analytics_id': '',
    'logo_only': False,
    'display_version': True,
    'prev_next_buttons_location': 'bottom',
    'style_external_links': False,
    'vcs_pageview_mode': '',
    'style_nav_header_background': '#2980B9',
}

intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'numpy': ('https://numpy.org/doc/stable/', None),
    'matplotlib': ('https://matplotlib.org/', None),
}

napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_keyword = True
napoleon_use_rtype = True

autodoc_typehints = 'description'
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'undoc-members': True,
    'show-inheritance': True,
}
