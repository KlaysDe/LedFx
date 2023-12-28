#
# Configuration file for the Sphinx documentation builder.
#
# This file does only contain a selection of the most common options. For a
# full list see the documentation:
# http://www.sphinx-doc.org/en/master/config

# -- Path setup --------------------------------------------------------------

import os

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
import sys

import sphinx_rtd_theme

sys.path.insert(0, os.path.abspath(".."))

import ledfx.consts as const
from ledfx.consts import PROJECT_AUTHOR, PROJECT_NAME, PROJECT_VERSION

# -- Project information -----------------------------------------------------

PROJECT_PACKAGE_NAME = PROJECT_NAME
PROJECT_AUTHOR = PROJECT_AUTHOR
PROJECT_COPYRIGHT = f" 2018-2023, {PROJECT_AUTHOR}"
PROJECT_SHORT_DESCRIPTION = "LedFx is an open-source effect controller"
PROJECT_LONG_DESCRIPTION = (
    "LedFx is an open-source effect controller "
    "designed to synchronize reactive effects across "
    "various networked devices."
)
PROJECT_GITHUB_USERNAME = "LedFx"
PROJECT_GITHUB_REPOSITORY = "LedFx"
PROJECT_GITHUB_BRANCH = "main"
PROJECT_GITHUB_PATH = f"{PROJECT_GITHUB_USERNAME}/{PROJECT_GITHUB_REPOSITORY}"
PROJECT_GITHUB_URL = f"https://github.com/{PROJECT_GITHUB_PATH}"

project = f"{PROJECT_NAME}"
author = f"{PROJECT_AUTHOR}"
copyright = f"{PROJECT_COPYRIGHT}" + " & contributors"
release = PROJECT_VERSION
version = PROJECT_VERSION

# -- General configuration ---------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
#
# needs_sphinx = '1.0'

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.githubpages",
    "sphinxcontrib.httpdomain",
    "sphinx_rtd_theme",
    "sphinx_toolbox.collapse",
]

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
#
# source_suffix = ['.rst', '.md']
source_suffix = ".rst"

# The master toctree document.
master_doc = "index"

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path .
exclude_patterns = []

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "sphinx"

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#
# This is also used if you do content translation via gettext catalogs.
# Usually you set "language" from the command line for these cases.
language = "en"

gettext_compact = False

linkcheck_timeout = 2

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_rtd_theme"
html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]


def setup(app):
    """Sphinx setup function."""
    app.add_css_file("css/custom.css")


# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
#
html_theme_options = {"logo_only": True}

html_context = {
    "display_github": True,
    "github_user": PROJECT_GITHUB_USERNAME,
    "github_repo": PROJECT_GITHUB_REPOSITORY,
    "github_version": f"{PROJECT_GITHUB_BRANCH}/docs/",
    "conf_py_path": "docs",
    "source_suffix": ".rst",
}
# TODO: Use os.path.join for these instead of hardcoding
html_logo = "_static/small_white_alpha.png"
html_favicon = "../ledfx_assets/favicon.ico"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

# Custom sidebar templates, must be a dictionary that maps document names
# to template names.
#
# The default sidebars (for documents that don't match any pattern) are
# defined by theme itself.  Builtin themes are using these templates by
# default: ``['localtoc.html', 'relations.html', 'sourcelink.html',
# 'searchbox.html']``.
#
html_sidebars = {
    "**": [
        "about.html",
        "navigation.html",
        "relations.html",
        "searchbox.html",
        "donate.html",
    ]
}

html_show_sourcelink = False

# html_style = '_static/custom.css'
# html_css_files = 'css/custom.css'

# -- Options for HTMLHelp output ---------------------------------------------

# Output file base name for HTML help builder.
htmlhelp_basename = f"{PROJECT_PACKAGE_NAME}doc"


# -- Options for LaTeX output ------------------------------------------------

latex_elements = {
    # The paper size ('letterpaper' or 'a4paper').
    #
    # 'papersize': 'letterpaper',
    # The font size ('10pt', '11pt' or '12pt').
    #
    # 'pointsize': '10pt',
    # Additional stuff for the LaTeX preamble.
    #
    # 'preamble': '',
    # Latex figure (float) alignment
    #
    # 'figure_align': 'htbp',
}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title,
#  author, LaTeX theme [manual, howto]).
latex_documents = [
    (
        master_doc,
        f"{PROJECT_PACKAGE_NAME}.tex",
        f"{PROJECT_NAME} Documentation",
        PROJECT_AUTHOR,
        "manual",
    ),
]


# -- Options for manual page output ------------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [
    (
        master_doc,
        PROJECT_PACKAGE_NAME.lower(),
        f"{PROJECT_NAME} Documentation",
        [PROJECT_AUTHOR],
        1,
    )
]


# -- Options for Texinfo output ----------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
    (
        master_doc,
        PROJECT_PACKAGE_NAME,
        f"{PROJECT_NAME} Documentation",
        PROJECT_AUTHOR,
        PROJECT_NAME,
        PROJECT_SHORT_DESCRIPTION,
        "Miscellaneous",
    ),
]


# -- Extension configuration -------------------------------------------------
