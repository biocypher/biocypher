---
status: under-dev
---

# Contributing to the documentation

Contributing to the documentation benefits everyone who uses biocypher.
We encourage you to help us improve the documentation, and
you don't have to be an expert on biocypher to do so! In fact,
there are sections of the docs that are worse off after being written by
experts. If something in the docs doesn't make sense to you, updating the
relevant section after you figure it out is a great way to ensure it will help
the next person. Please visit the [issues page](https://github.com/biocypher/biocypher/issues)
for a full list of issues that are currently open regarding the
biocypher documentation.


## About the Biocypher documentation
--------------------------------

The documentation is written in **Markdown**, which is almost like writing
in plain English, and built using [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/).
Some other important things to know about the docs:

- The biocypher documentation consists of two parts: the docstrings in the code
  itself and the docs in this folder `docs/`.

  The docstrings provide a clear explanation of the usage of the individual
  functions, while the documentation in this folder consists of tutorial-like
  overviews per topic together with some other information (what's new,
  installation, etc).

- The docstrings follow a biocypher convention, based on the **Google Docstring
  Standard**. Follow the [biocypher docstring guide](./biocypher-docstring-guide.md) for detailed
  instructions on how to write a correct docstring.

- Our API documentation files in `docs/reference/source` house the auto-generated
  documentation from the docstrings. For classes, there are a few subtleties
  around controlling which methods and attributes have pages auto-generated.
