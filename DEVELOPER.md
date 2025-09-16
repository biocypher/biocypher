# 🔬 Developer Guide

Thank you for considering to contribute to the project! This guide will help you
to get started with the development of the project. If you have any questions,
please feel free to ask them in the issue tracker.

## Dependency management

We use [uv](https://docs.astral.sh/uv/) for dependency management. Please
make sure that you have installed uv and set up the environment correctly
before starting development.

### Setup the environment

- Install dependencies from the lock file: `uv sync --all-extras`

- Use the environment: Run commands directly with `uv run <command>`.

### Updating the environment

If you want to fix dependency issues, please do so in the uv
framework. If uv does not work for you for some reason, please let us know.

The uv dependencies are organized in three sections:
- **Main dependencies** (`[project.dependencies]`): Core dependencies needed for running BioCypher
- **Optional dependencies** (`[project.optional-dependencies]`): Optional features like `scirpy` for AIRR functionality
- **Development dependencies** (`[dependency-groups.dev]`): Dependencies needed for development, testing, and documentation

For adding new dependencies:

- Add new dependencies: `uv add <dependency> --group <group>`

- Update lock file (after adding new dependencies in pyproject.toml): `uv lock`

## Code quality and formal requirements

For ensuring code quality, the following tools are used:

- [isort](https://isort.readthedocs.io/en/latest/) for sorting imports

- [black](https://black.readthedocs.io/en/stable/) for automated code formatting

- [pre-commit-hooks](https://github.com/pre-commit/pre-commit-hooks) for
ensuring some general rules

- [pep585-upgrade](https://github.com/snok/pep585-upgrade) for automatically
upgrading type hints to the new native types defined in PEP 585

- [pygrep-hooks](https://github.com/pre-commit/pygrep-hooks) for ensuring some
general naming rules

Pre-commit hooks are used to automatically run these tools before each commit.
They are defined in [.pre-commit-config.yaml](./.pre-commit-config.yaml). To
install the hooks run `uv run pre-commit install`. The hooks are then
executed before each commit. For running the hook for all project files (not
only the changed ones) run `uv run pre-commit run --all-files`.

The project uses a [Sphinx](https://www.sphinx-doc.org/en/master/) autodoc
GitHub Actions workflow to generate the documentation. If you add new code,
please make sure that it is documented accordingly and in a consistent manner
with the existing code base. The docstrings should follow the [Google style
guide](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html).
To check if the docs build successfully, you can build them locally by running
`make html` in the `docs` directory.

When adding new code snippets to the documentation, make sure that they are
automatically tested with
[doctest](https://sphinx-tutorial.readthedocs.io/step-3/#testing-your-code);
this ensures that no outdated code snippets are part of the documentation.

## Testing

The project uses [pytest](https://docs.pytest.org/en/stable/) for testing. To
run the tests, please run `pytest` in the root directory of the project. We are
developing BioCypher using test-driven development. Please make sure that you
add tests for your code before submitting a pull request.

The existing tests can also help you to understand how the code works. If you
have any questions, please feel free to ask them in the issue tracker.

**Before submitting a pull request, please make sure that all tests pass and
that the documentation builds correctly.**

## Small Contributions

If you want to contribute a small change (e.g. a bugfix), you can probably
immediately go ahead and create a pull request. For more substantial changes or
additions, please read on.

## Larger Contributions

If you want to contribute a larger change, please create an issue first. This
will allow us to discuss the change and make sure that it fits into the project.
It can happen that development for a feature is already in progress, so it is
important to check first to avoid duplicate work. If you have any questions,
feel free to approach us in any way you like.

## Versioning

We use [semantic versioning](https://semver.org/) for the project. This means
that the version number is incremented according to the following scheme:

- Increment the major version number if you make incompatible API changes.

- Increment the minor version number if you add functionality in a backwards-
  compatible manner.

- Increment the patch version number if you make backwards-compatible bug fixes.

We use the `bumpversion` tool to update the version number in the
`pyproject.toml` file. This will create a new git tag automatically. Usually,
versioning is done by the maintainers, so please do not increment versions in
pull requests by default.
