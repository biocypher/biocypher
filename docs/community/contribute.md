# Contributing to BioCypher

## Bug reports and enhancement requests

Bug reports and enhancement requests are an important part of making BioCypher more stable and are curated though Github issues. When reporting and issue or request, please select the appropriate category and fill out the issue form fully to ensure others and the core development team can fully understand the scope of the issue.

The issue will then show up to the BioCypher community and be open to comments/ideas from others.


Categories

- Bug Report: Report incorrect behavior in the BioCypher library
- Documentation Improvement: Report wrong or missing documentation
- Feature Request: Suggest and idea for BioCypher
- Installation Issue: Report issues installing the BioCypher on the system

## Finding and issue to contribute to

If you are brand new to BioCypher or open-source development, we recommend searching the GitHub "issues" tab to find issues that interest you. Unassigned issues labeled `Docs` and `good first issue` are typically good for newer contributors.

Once you’ve found an interesting issue, it’s a good idea to assign the issue to yourself, so nobody else duplicates the work on it. On the Github issue, a comment with the exact text take to automatically assign you the issue (this will take seconds and may require refreshing the page to see it).

If for whatever reason you are not able to continue working with the issue, please unassign it, so other people know it’s available again. You can check the list of assigned issues, since people may not be working in them anymore. If you want to work on one that is assigned, feel free to kindly ask the current assignee if you can take it (please allow at least a week of inactivity before considering work in the issue discontinued).


### Submitting a Pull Request
#### Version control, Git, and GitHub
BioCypher is hosted on GitHub, and to contribute, you will need to sign up for a [free GitHub account](https://github.com/signup/free). We use [Git](https://git-scm.com/) for version control to allow many people to work together on the project.

If you are new to Git, you can reference some of these resources for learning Git. Feel free to reach out to the contributor community for help if needed:

- [Git documentation](https://git-scm.com/doc).


Also, the project follows a forking workflow further described on this page whereby contributors fork the repository, make changes and then create a Pull Request. So please be sure to read and follow all the instructions in this guide.

If you are new to contributing to projects through forking on GitHub, take a look at the [GitHub documentation for contributing to projects](https://docs.github.com/en/get-started/quickstart/contributing-to-projects). GitHub provides a quick tutorial using a test repository that may help you become more familiar with forking a repository, cloning a fork, creating a feature branch, pushing changes and making Pull Requests.

Below are some useful resources for learning more about forking and Pull Requests on GitHub:

- the [GitHub documentation for forking a repo](https://docs.github.com/en/get-started/quickstart/fork-a-repo).

- the [GitHub documentation for collaborating with Pull Requests](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests).

- the [GitHub documentation for working with forks](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks).

#### Getting started with Git
[GitHub has instructions](https://docs.github.com/en/get-started/quickstart/set-up-git) for installing git, setting up your SSH key, and configuring git. All these steps need to be completed before you can work seamlessly between your local repository and GitHub.

#### Create a fork of BioCypher
You will need your own copy of BioCypher (aka fork) to work on the code. Go to the BioCypher project page and hit the Fork button. Please uncheck the box to copy only the main branch before selecting Create Fork. You will want to clone your fork to your machine

```bash
git clone https://github.com/your-user-name/biocypher.git biocypher-yourname
cd biocypher-yourname
git remote add upstream https://github.com/biocypher/biocypher.git
git fetch upstream
```
This creates the directory `biocypher-yourname` and connects your repository to the upstream (main project) *biocypher* repository.

#### Creating a feature branch
Your local `main` branch should always reflect the current state of BioCypher repository. First ensure it’s up-to-date with the main BioCypher repository.

```bash
git checkout main
git pull upstream main --ff-only
```

Then, create a feature branch for making your changes. For example, we are going to create a branch called `my-new-feature-for-biocypher`

```bash
git checkout -b my-new-feature-for-biocypher
```

This changes your working branch from `main` to the `my-new-feature-for-biocypher` branch. Keep any changes in this branch specific to one bug or feature so it is clear what the branch brings to *Biocypher*. You can have many feature branches and switch in between them using the `git checkout` command.

When you want to update the feature branch with changes in main after you created the branch, check the section on updating a PR.

#### Making code changes
Before modifying any code, ensure you follow the contributing environment guidelines to set up an appropriate development environment.

Then once you have made code changes, you can see all the changes you¿ve currently made by running.

```bash
git status
```

For files you intended to modify or add, run

```bash
git add path/to/file-to-be-added-or-changed
```

Running `git status` again should display

```bash
On branch my-new-feature-for-BioCypher

    modified:   /relative/path/to/file-to-be-added-or-changed
```

Finally, commit your changes to your local repository with an explanatory commit message
```bash
git commit -m "your commit message goes here"
```
!!! tip "How to write good commit messages?"
    You can consult the following references to understand how to write better commit messages.
    - [Conventional Commits: A specification for adding human and machine readable meaning to commit messages](https://www.conventionalcommits.org/en/v1.0.0/)
    - [Git Commit Good Practice by OpenStack](https://wiki.openstack.org/wiki/GitCommitMessages)

#### Pushing your changes
When you want your changes to appear publicly on your GitHub page, push your forked feature branch’s commits

```bash
git push origin my-new-feature-for-biocypher
```

Here `origin` is the default name given to your remote repository on GitHub. You can see the remote repositories
```bash
git remote -v
```
If you added the upstream repository as described above you will see something like
```bash
origin  git@github.com:yourname/biocypher.git (fetch)
origin  git@github.com:yourname/biocypher.git (push)
upstream        git://github.com/biocypher/biocypher.git (fetch)
upstream        git://github.com/biocypher/biocypher.git (push)
```

Now your code is on GitHub, but it is not yet a part of the BioCypher project. For that to happen, a Pull Request (PR) needs to be submitted on GitHub.

#### Making a Pull Request (PR)
One you have finished your code changes, your code change will need to follow the BioCypher contribution guidelines to be successfully accepted.

If everything looks good, you are ready to make a Pull Request. A Pull Request is how code from your local repository becomes available to the GitHub community to review and merged into project to appear the in the next release. To submit a Pull Request:

1. Navigate to your repository on GitHub

2. Click on the Compare & Pull Request button

3. You can then click on Commits and Files Changed to make sure everything looks okay one last time

4. Write a descriptive title that includes prefixes. BioCypher uses a convention for title prefixes. Here are some common ones along with general guidelines for when to use them:

```markdown
- ENH: Enhancement, new functionality

- BUG: Bug fix

- DOCS: Additions/updates to documentation

- TEST: Additions/updates to tests

- BUILD: Updates to the build process/scripts

- PERF: Performance improvement

```

5. Write a description of your changes in the `Preview Discussion` tab
6. Click `Send Pull Request`

This request then goes to the repositorz maintainers, and they will review the code.

#### Updating your Pull Request

Based on the review you get on your pull request, you will probably need to make
some changes to the code. You can follow the :ref:`code committing steps <contributing.commit-code>`
again to address any feedback and update your pull request.

It is also important that updates in the biocypher ``main`` branch are reflected in your pull request.
To update your feature branch with changes in the biocypher ``main`` branch, run:

```shell

    git checkout my-new-feature-for-biocypher
    git fetch upstream
    git merge upstream/main
```

If there are no conflicts (or they could be fixed automatically), a file with a
default commit message will open, and you can simply save and quit this file.

If there are merge conflicts, you need to solve those conflicts. See for
example at https://help.github.com/articles/resolving-a-merge-conflict-using-the-command-line/
for an explanation on how to do this.

Once the conflicts are resolved, run:

1. `git add -u` to stage any files you've updated;
2. `git commit` to finish the merge.

!!! note "Note"
    If you have uncommitted changes at the moment you want to update the branch with
    `main`, you will need to `stash` them prior to updating (see the
    `stash docs <https://git-scm.com/book/en/v2/Git-Tools-Stashing-and-Cleaning>`__).
    This will effectively store your changes and they can be reapplied after updating.

After the feature branch has been update locally, you can now update your pull
request by pushing to the branch on GitHub:

```shell
    git push origin shiny-new-feature
```

Any `git push` will automatically update your pull request with your branch's changes
and restart the :ref:`Continuous Integration <contributing.ci>` checks.



#### Tips for a successful pull request

If you have made it to the `Making a pull request`_ phase, one of the core contributors may
take a look. Please note however that a handful of people are responsible for reviewing
all of the contributions, which can often lead to bottlenecks.

To improve the chances of your pull request being reviewed, you should:

- **Reference an open issue** for non-trivial changes to clarify the PR's purpose
- **Ensure you have appropriate tests**. These should be the first part of any PR
- **Keep your pull requests as simple as possible**. Larger PRs take longer to review
- **Ensure that CI is in a green state**. Reviewers may not even look otherwise
