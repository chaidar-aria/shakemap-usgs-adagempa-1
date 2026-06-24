import os
import sys
import importlib.metadata

sys.path.insert(0, os.path.abspath(".."))


project = "ShakeMap"
copyright = "Unlicense"
author = "U.S. Geological Survey"
release = importlib.metadata.version("shakemap").split(".dev")[0]
version = release.rsplit(".", 1)[0]

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.todo",
    "sphinx.ext.viewcode",
    "sphinx.ext.doctest",
    "sphinx.ext.intersphinx",
    "sphinx.ext.coverage",
    "sphinx.ext.mathjax",
    "sphinx.ext.ifconfig",
    "sphinxcontrib.programoutput",
    "sphinx_copybutton",
    "sphinx_inline_tabs",
    "myst_nb",
]

myst_enable_extensions = [
    "colon_fence",
    "deflist",
]


# Prevent duplicate label warnings from autosectionlabel across files
autosectionlabel_prefix_document = True

myst_enable_extensions = [
    "colon_fence",
    "deflist",
]

# myst_nb settings
nb_execution_mode = "off"

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


html_theme = "furo"

base_url = "https://code.usgs.gov/ghsc/esi/shakemap/-/raw/main/doc/"
# base_url = "/Users/cbworden/Unix/python/shakemap/doc_source/"

announcement_html = """
    <a href='https://www.usgs.gov/' style='text-decoration: none'>
        <img id="announcement_left_img" valign="middle" src="%s_static/usgs-logo.svg"/></a>
    ShakeMap
    <a href='https://code.usgs.gov/ghsc/esi/shakemap' style='text-decoration: none'>
        <img id="announcement_right_img" valign="middle"
            src="%s_static/GitLabLogo/gitlab-logo-500 cropped.png"/></a>
""" % (
    base_url,
    base_url,
)

# The name of an image file (within the static path) to use as favicon of the
# docs.  This file should be a Windows icon file (.ico) being 16x16 or 32x32
# pixels large.
html_favicon = "_static/shakemap_icon.ico"

html_logo = "_static/shakemap_icon_transparent_background.png"

html_static_path = ["_static"]

html_theme_options = {
    "announcement": announcement_html,
    "sidebar_hide_name": True,
}

# If true, links to the reST sources are added to the pages.
html_show_sourcelink = False

# If true, "Created using Sphinx" is shown in the HTML footer. Default is True.
html_show_sphinx = False


# If true, "(C) Copyright ..." is shown in the HTML footer. Default is True.
html_show_copyright = False


# Show TODOs in local builds; suppress in CI
todo_include_todos = not os.environ.get("CI", False)

autodoc_default_options = {
    "members": True,
    "undoc-members": False,
    "show-inheritance": True,
}


def setup(app):
    app.add_css_file("css/custom.css")  # may also be an URL
