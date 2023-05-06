# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import os
import sys

sys.path.insert(0, os.path.abspath(".."))

project = "Kubejobs"
copyright = "2023, Antreas Antoniou"
author = "Antreas Antoniou"
release = "0.3.0"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

html_theme = "sphinx_material"
html_static_path = ["_static"]
extensions = ["sphinx.ext.autodoc", "sphinx_rtd_theme"]
extensions.append("sphinx.ext.autosummary")
extensions.append("sphinx.ext.viewcode")
extensions.append("sphinx.ext.intersphinx")
extensions.append("sphinx.ext.napoleon")
extensions.append("sphinx.ext.coverage")
extensions.append("sphinx.ext.todo")

templates_path = ["_templates"]
exclude_patterns = []

html_theme_options = {
    # Set the name of the project to appear in the navigation.
    "nav_title": project,
    # Set you GA account ID to enable tracking
    # "google_analytics_account": "UA-XXXXX",
    # Specify a base_url used to generate sitemap.xml. If not
    # specified, then no sitemap will be built.
    "base_url": "https://antreas.io/kubejobs",
    # Set the color and the accent color
    "color_primary": "blue",
    "color_accent": "light-blue",
    # Set the repo location to get a badge with stats
    "repo_url": "https://github.com/AntreasAntoniou/Kubejobs",
    "repo_name": "kubejobs",
    # Visible levels of the global TOC; -1 means unlimited
    "globaltoc_depth": 3,
    # If False, expand all TOC entries
    "globaltoc_collapse": False,
    # If True, show hidden TOC entries
    "globaltoc_includehidden": False,
}

# # Get the current Git commit hash
# commit_hash = os.popen("git rev-parse --short HEAD").read().strip()

# source_suffix = {
#     ".rst": "restructuredtext",
#     ".md": "markdown",
# }


# html_context = {
#     "display_github": True,  # Enable "View page source" link to point to GitHub
#     "github_user": "AntreasAntoniou",
#     "github_repo": "kubejobs",
#     "github_version": "main",  # Replace with the default branch name, if different
#     "conf_py_path": "/docs/source/",  # Path to the conf.py file in your repository
#     "source_suffix": source_suffix,
#     "commit_hash": commit_hash,
# }


# # Custom function to build the GitHub URL for the source code
# def _get_github_url(app, pagename, templatename, context, doctree):
#     if context["display_github"]:
#         github_user = context["github_user"]
#         github_repo = context["github_repo"]
#         github_version = context["github_version"]
#         conf_py_path = context["conf_py_path"]
#         source_suffix = context["source_suffix"]
#         commit_hash = context["commit_hash"]

#         path = pagename.replace("source/", "")
#         if path.endswith(".txt"):
#             path = path[:-4] + source_suffix

#         return f"https://github.com/{github_user}/{github_repo}/blob/{commit_hash}{conf_py_path}{path}.rst"
#     else:
#         return None


# # Connect the custom function to the html-page-context event
# def setup(app):
#     app.connect("html-page-context", _get_github_url)
