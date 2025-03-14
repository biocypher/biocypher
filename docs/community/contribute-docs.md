!!! warning

    This page is redundant with the unified docs in `biocypher/documentation`.
    Community docs will be maintained there.

# Contributing to the documentation

Contributing to the documentation benefits everyone who uses BioCypher. We
encourage you to help us improve the documentation, and you don't have to be an
expert on BioCypher to do so! In fact, there are sections of the docs that are
worse off after being written by experts. If something in the docs doesn't make
sense to you, updating the relevant section after you figure it out is a great
way to ensure it will help the next person.


## How to contribute to the documentation

The documentation is written in **Markdown**, which is almost like writing in
plain English, and built using [Material for
MkDocs](https://squidfunk.github.io/mkdocs-material/). The simplest way to
contribute to the docs is to click on the `Edit` button (pen and paper) at the
top right of any page. This will take you to the source file on GitHub, where
you can make your changes and create a pull request using GitHub's web
interface (the `Commit changes...` button).

Some other important things to know about the docs:

- The BioCypher documentation consists of two parts: the docstrings in the code
  itself and the docs in the `docs/` folder. The docstrings provide a clear
  explanation of the usage of the individual functions, while the documentation
  website you are looking at is built from the `docs/` folder.

- The docstrings follow a BioCypher convention, based on the [Google Docstring
  Standard](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings).

- Our API documentation files in `docs/reference/source` contain the
  instructions for the auto-generated documentation from the docstrings. For
  classes, there are a few subtleties around controlling which methods and
  attributes have pages auto-generated.
