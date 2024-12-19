# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "Longue Vie Aux Objets"
copyright = "2024, Fabien Le Frapper (@fabienheureux), Nicolas Oudard, Max Corbeau"
author = "Fabien Le Frapper, Nicolas Oudard, Max Corbeaux"

# Add MyST Parser extension
extensions = ["myst_parser"]

# Configure source suffix to recognize Markdown files
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

master_doc = "README"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

language = "fr"

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
