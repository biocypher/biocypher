!!! warning

    This page is redundant with the unified docs in `biocypher/documentation`.
    Community docs will be maintained there.

# Developer Guide

Thank you for considering to contribute to the project! This guide will help you
to get started with the development of the project. If you have any questions,
please feel free to ask them in the issue tracker or on Zulip.

## Small Contributions

If you want to contribute a small change (e.g., a bugfix), you can probably
immediately go ahead and create a [pull request](#submitting-a-pull-request).
For more substantial changes or additions, please read on.

## Larger Contributions

If you want to contribute a larger change, please create an
[issue](./contribute.md#categories) first. This will allow us to discuss the
change and make sure that it fits into the project.  It can happen that
development for a feature is already in progress, so it is important to check
first to avoid duplicate work. If you have any questions, feel free to approach
us in any way you like.

## Dependency management

We use [uv](https://docs.astral.sh/uv/) for dependency management. Please
make sure that you have installed uv and set up the environment correctly
before starting development.

### Setting up the environment

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

- Add new dependencies via `uv add`:
`uv add <dependency> --group <group>`. This will update the `pyproject.toml`
and lock file automatically.

- Add new dependencies via `pyproject.toml`: Add the dependency to the
`pyproject.toml` file in the correct group, including version. Then update the
lock file: `uv lock` and install the dependencies: `uv sync --all-extras`.

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

- **NEW** [Ruff](https://docs.astral.sh/ruff/) An extremely fast Python linter
and code formatter, written in Rust

We recommend configuring your IDE to execute Ruff on save/type, which will
automatically keep your code clean and fix some linting errors as you type. This
is made possible by the fast execution of Ruff and removes the need to run a
dedicated pre-commit step. For instance, in VSCode or Cursor, you can add this
to your `.vscode/settings.json`:

```json
{
    "editor.formatOnType": true,
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.fixAll.ruff": "explicit",
        "source.organizeImports.ruff": "explicit"
    },
    "editor.defaultFormatter": "charliermarsh.ruff"
}
```

Alternatively, pre-commit hooks can be used to automatically or manually run
these tools before each commit. They are defined in `.pre-commit-config.yaml`.
To install the hooks run `uv run pre-commit install`. The hooks are then
executed before each commit. For running the hook for all project files (not
only the changed ones) run `uv run pre-commit run --all-files`. Our CI runs
the pre-commit hooks, so running them locally is a good way to check if your
code conforms to the formatting rules.

<!--
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
-->

## Testing

The project uses [pytest](https://docs.pytest.org/en/stable/) for testing. To
run the tests, please run `pytest` in the root directory of the project. We are
developing BioCypher using test-driven development. Please make sure that you
add tests for your code before submitting a pull request.

The existing tests can also help you to understand how the code works. If you
have any questions, please feel free to ask them in the issue tracker or on
Zulip.

**Before submitting a pull request, please make sure that all tests pass and
that the documentation builds correctly.**

## Versioning

We use [semantic versioning](https://semver.org/) for the project. This means
that the version number is incremented according to the following scheme:

- Increment the major version number if you make incompatible API changes.

- Increment the minor version number if you add functionality in a backwards-
  compatible manner. Since we are still in the 0.x.y version range, most of the
  significant changes will increase the minor version number.

- Increment the patch version number if you make backwards-compatible bug fixes.

We use the `bumpversion` tool to update the version number in the
`pyproject.toml` file. This will create a new git tag automatically. Usually,
versioning is done by the maintainers, so please do not increment versions in
pull requests by default.

## Finding an issue to contribute to

If you are brand new to BioCypher or open-source development, we recommend
searching the GitHub "Issues" tab to find issues that interest you. Unassigned
issues labeled `Docs` and [good first
issue](https://github.com/biocypher/biocypher/labels/good%20first%20issue) are
typically good for newer contributors.

Once you've found an interesting issue, it's a good idea to assign the issue to
yourself, so nobody else duplicates the work on it.

If for whatever reason you are not able to continue working with the issue,
please unassign it, so other people know it's available again. If you want to
work on an issue that is currently assigned but you're unsure whether work is
actually being done, feel free to kindly ask the current assignee if you can
take over (please allow at least a week of inactivity before getting in touch).


## Submitting a Pull Request

### Tips for a successful pull request

To improve the chances of your pull request being reviewed, you should:

- **Reference an open issue** for non-trivial changes to clarify the PR's purpose.
- **Ensure you have appropriate tests**. Tests should be the focus of any PR (apart from documentation changes).
- **Keep your pull requests as simple as possible**. Larger PRs take longer to review.
- **Ensure that CI is in a green state**. Reviewers may tell you to fix the CI before looking at anything else.

### Version control, Git, and GitHub

BioCypher is hosted on GitHub, and to contribute, you will need to sign up for a
[free GitHub account](https://github.com/signup/free). We use
[Git](https://git-scm.com/) for version control to allow many people to work
together on the project.

If you are new to Git, you can reference some of these resources for learning
Git. Feel free to reach out to the contributor community for help if needed:

- [Git documentation](https://git-scm.com/doc).


The project follows a forking workflow further described on this page whereby
contributors fork the repository, make changes and then create a Pull Request.
So please be sure to read and follow all the instructions in this guide.

If you are new to contributing to projects through forking on GitHub, take a
look at the [GitHub documentation for contributing to
projects](https://docs.github.com/en/get-started/quickstart/contributing-to-projects).
GitHub provides a quick tutorial using a test repository that may help you
become more familiar with forking a repository, cloning a fork, creating a
feature branch, pushing changes and making Pull Requests.

Below are some useful resources for learning more about forking and Pull
Requests on GitHub:

- the [GitHub documentation for forking a repo](https://docs.github.com/en/get-started/quickstart/fork-a-repo).

- the [GitHub documentation for collaborating with Pull Requests](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests).

- the [GitHub documentation for working with forks](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks).

There are also many unwritten rules and conventions that are helpful in
interacting with other open-source contributors. These
[lessons](https://www.pyopensci.org/lessons/) from PyOpenSci are a good resource
for learning more about how to interact with other open-source contributors in
scientific computing.

### Getting started with Git

[GitHub has
instructions](https://docs.github.com/en/get-started/quickstart/set-up-git) for
installing git, setting up your SSH key, and configuring git. All these steps
need to be completed before you can work seamlessly between your local
repository and GitHub.

### Create a fork of BioCypher

You will need your own fork of BioCypher in order to eventually open a Pull
Request. Go to the BioCypher project page and hit the Fork button. Please
uncheck the box to copy only the main branch before selecting Create Fork. You
will then want to clone your fork to your machine.

```bash
git clone https://github.com/your-user-name/biocypher.git
cd biocypher
git remote add upstream https://github.com/biocypher/biocypher.git
git fetch upstream
```

This creates the directory `biocypher` and connects your repository to the
upstream (main project) *biocypher* repository. They have the same name, but
your local repository and fork are separate from the upstream repository.

### Creating a feature branch

Your local `main` branch should always reflect the current state of BioCypher
repository. First ensure it's up-to-date with the main BioCypher repository.

```bash
git checkout main
git pull upstream main --ff-only
```

Then, create a feature branch for making your changes. For example, we are going
to create a branch called `my-new-feature-for-biocypher`

```bash
git checkout -b my-new-feature-for-biocypher
```

This changes your working branch from `main` to the
`my-new-feature-for-biocypher` branch. Keep any changes in this branch specific
to one bug or feature so it is clear what the branch brings to *BioCypher*. You
can have many feature branches and switch between them using the `git
checkout` command.

### Making code changes

Before modifying any code, ensure you follow the contributing environment
guidelines to set up an appropriate development environment.

When making changes, follow these BioCypher-specific guidelines:

1. Keep changes of that branch/PR focused on a single feature or bug fix.

2. Follow roughly the [conventional commit message conventions](https://www.conventionalcommits.org/en/v1.0.0/).

### Pushing your changes

When you want your [committed](https://git-scm.com/docs/git-commit) changes to
appear publicly on your GitHub page, you can
[push](https://git-scm.com/docs/git-push) your forked feature branch's commits
to your forked repository on GitHub.

Now your code is on GitHub, but it is not yet a part of the BioCypher project.
For that to happen, a Pull Request (PR) needs to be submitted.

### Opening a Pull Request (PR)

If everything looks good according to the general guidelines, you are ready to
make a Pull Request. A Pull Request is how code from your fork becomes available
to the project maintainers to review and merge into the project to appear in the
next release. To submit a Pull Request:

1. Navigate to your repository on GitHub.

1. Click on the Compare & Pull Request button.

1. You can then click on Commits and Files Changed to make sure everything looks okay one last time.

1. Write a descriptive title that includes prefixes. BioCypher uses a convention for title prefixes, most commonly, `feat:` for features, `fix:` for bug fixes, and `refactor:` for refactoring.

1. Write a description of your changes in the `Preview Discussion` tab. This description will inform the reviewers about the changes you made, so please include all relevant information, including the motivation, implementation details, and references to any issues that you are addressing.

1. Make sure to `Allow edits from maintainers`; this allows the maintainers to make changes to your PR directly, which is useful if you are not sure how to fix the PR.

1. Click `Send Pull Request`.

1. Optionally, you can assign reviewers to your PR, if you know who should review it.

This request then goes to the repository maintainers, and they will review the code.

### Updating your Pull Request

Based on the review you get on your pull request, you will probably need to make
some changes to the code. You can follow the steps above again to address any
feedback and update your pull request.

### Parallel changes in the upstream `main` branch

In case of simultaneous changes to the upstream code, it is important that
these changes are reflected in your pull request. To update your feature
branch with changes in the biocypher `main` branch, run:

```shell

    git checkout my-new-feature-for-biocypher
    git fetch upstream
    git merge upstream/main
```

If there are no conflicts (or they could be fixed automatically), a file with a
default commit message will open, and you can simply save and quit this file.

If there are merge conflicts, you need to resolve those conflicts. See
[here](https://help.github.com/articles/resolving-a-merge-conflict-using-the-command-line/)
for an explanation on how to do this.

Once the conflicts are resolved, run:

1. `git add -u` to stage any files you've updated;
2. `git commit` to finish the merge.

After the feature branch has been updated locally, you can now update your pull
request by pushing to the branch on GitHub:

```shell
    git push origin my-new-feature-for-biocypher
```

Any `git push` will automatically update your pull request with your branch's changes
and restart the `Continuous Integration` checks.
