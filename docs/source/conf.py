# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Kubejobs'
copyright = '2023, Antreas Antoniou'
author = 'Antreas Antoniou'
release = '0.1.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
extensions = ["sphinx.ext.autodoc", "sphinx_rtd_theme"]
extensions.append("sphinx.ext.autosummary")
extensions.append("sphinx.ext.viewcode")
extensions.append("sphinx.ext.intersphinx")
extensions.append("sphinx.ext.napoleon")
extensions.append("sphinx.ext.coverage")
extensions.append("sphinx.ext.todo")

templates_path = ['_templates']
exclude_patterns = []
