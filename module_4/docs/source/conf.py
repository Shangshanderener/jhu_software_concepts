# Configuration file for the Sphinx documentation builder.

import os
import sys
# Insert project root into path so src can be imported
sys.path.insert(0, os.path.abspath('../..'))  # Points to module_4 root

project = 'Module 4 - Testing and Documentation Experiment Assignment'
copyright = '2026'
author = 'Zicheng Han'
release = '1.0'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
    'sphinx_rtd_theme',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

autodoc_mock_imports = ['psycopg', 'llama_cpp', 'huggingface_hub']
