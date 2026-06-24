# Contributing Guidelines

Contributions are welcome from the community. Questions can be asked on the
[issues page][1]. Before creating a new issue, please take a moment to search
and make sure a similar issue does not already exist. If one does exist, you
can comment (most simply even with just a `+1`) to show your support for that
issue.

If you have direct contributions you would like considered for incorporation
into the project you can [fork this repository][2] and
[submit a pull request][3] for review.

Please see the Guidelines for Contributors section of the 
ShakeMap manual for information on contribution to ShakeMap:

https://code.usgs.gov/ghsc/esi/shakemap/-/blob/main/CONTRIBUTING.md?ref_type=heads

For additional information, please see the [USGS software development best
practices guide][4] and the [USGS Code of Scientific Conduct][5]. 

The big picture guidelines are: 

- Submit changes via a pull request from a feature branch section on Merge Requests for more details.
- We generally try to follow [pep8](https://www.python.org/dev/peps/pep-0008/) as much as possible.
- Include doc strings for all public methods. We use the [Google][6] doc string style.
- Please use [black][7] to format python code.
- Use Python's [built-in][8] exceptions as much as possible.


## Merge Request Guidelines

1. Use concise, yet informative commit messages.
2. Rebase (if you know how) to provide an easy-to-follow history of changes in your branch.
3. Update the changelog (`CHANGELOG.md`) for significant changes into the "main" section.
4. Update docs if relevant.
5. Add unit tests for any new features.
6. Run the unit tests (we use ``pytest``) prior to sending in your changes.

### Commit Messages

Commit messages should begin with a one line concise yet informative summary.
A blank line should separate the one line summary from any additional information.
We strongly recommend using the following templates, in which the first starts with
a commit type (in all caps) that indicates the type of changes in the commit.

For example, a commit related to documentation would look like:

```
DOCS: [one line description]

[Optional additional information]
```

We use the set of commit types from the [angular][9] project:
* **BUILD**: Changes that affect the build system or external dependencies (e.g., pyproject.toml)
* **CI**: Changes to our CI configuration files and scripts (e.g., .gitlab-ci.yml)
* **DOCS**: Documentation only changes
* **FEAT**: A new feature
* **FIX**: A bug fix
* **PERF**: A code change that improves performance
* **REFACTOR**: A code change that neither fixes a bug nor adds a feature
* **STYLE**: Changes that do not affect the meaning of the code (white-space, formatting, missing semi-colons, etc)
* **TEST**: Adding missing tests or correcting existing tests


### Rebasing

:::{danger}
Rebasing can do permanent damage to your branch if you do not do it correctly.
Practice on a scratch repository until you are comfortable with how rebasing works.
:::

You can use rebasing to clean up the history of commits in a branch to make the changes easier to follow.
Common reasons to rebase include:

* squashing (combining) several closely related commits into a single commit,
* reordering commits, especially to allow squashing, and
* dropping (removing) commits related to debugging.


## Releases

### Step 1: Release Upstream Packages to PyPI

If any upstream packages have changed, release them in order to PyPI:

1. **`esi-utils-*`**
2. **`esi-shakelib`**
3. **`shakemap-modules`**

### Step 2: Update `pyproject.toml` Dependency Versions

In `pyproject.toml`, update the minimum version for any dependencies that were
bumped in Step 1. Commit this change before regenerating the lock file.

### Step 3: Update the Conda Lock File

The `install_shakemap.sh` script creates a `conda-lock` conda environment with the `conda-lock` tool.
If the `conda-lock` environment does not yet exist on your system, create it first:

```bash
conda create -n conda-lock -c conda-forge conda-lock
```

#### Option A: Update Specific Packages Only

Do this if only pip packages (`shakemap-modules`, `esi-shakelib`, etc.) are changed.

```bash
conda activate conda-lock
conda-lock lock \
    --lockfile conda-lock.yml \
    --update shakemap-modules \
    --update esi-shakelib
```

#### Option B: Create New Lock File

Major changes (a new Python version, or significant dependency changes) require generating a new
lock file from `environment.yml`.

**Important**: `environment.yml` should be a minimal file listing only direct runtime dependencies
with loose version constraints. Do **not** generate it with `conda env export`, which produces a
bloated file that pins all transitive dependencies and is not portable. Do **not** use
`pyproject.toml` directly as input to conda-lock, as it will attempt to resolve all optional
dependency groups (e.g., `dev`, `test`, `doc`) as conda packages, which will fail for
PyPI-only packages like `esi-releases`.

The `environment.yml` should look like this, mirroring only the `[project.dependencies]` section
of `pyproject.toml`:

```yaml
name: shakemap
channels:
  - conda-forge
dependencies:
  - python>=3.12,<3.13
  - pip
  - pip:
    - shakemap-modules[all]>=1.1.15
    - esi-utils-comcat>=0.0.2
    - python-daemon>=3.0
    - lockfile>=0.12.2
    - importlib_resources
    - scipy>=1.16.0,<1.17.0
```

Then generate the lock file with:

```bash
conda activate conda-lock
conda-lock lock \
    -f environment.yml \
    --lockfile conda-lock.yml \
    -p linux-64 \
    -p osx-arm64
```

After generating the lock file, test it by installing into a fresh environment before committing:

```bash
conda-lock install -n shakemap-test conda-lock.yml
conda activate shakemap-test
pip install -e .
pytest
```

### Step 4: Commit the Lock File

Commit the updated `conda-lock.yml` to the repo.

### Step 5: Prepare the Release Candidate Branch

1. Create a release candidate branch with a name related to the release version,
   e.g., `v1.2.1.rc0`.
2. Update the package version in `pyproject.toml`.
3. Update `code.json` using the `esi-releases` package. For example, to increment
   the minor version:
   ```
   releases minor
   ```
   Options are `major`, `minor`, and `patch`.
4. Update `CHANGELOG.md` to include the changes for this version. The goal is for
   the changelog to be kept up to date with each merge request, so this step should
   largely consist of creating a new section for this release and moving content
   into it from "main".
5. Rebuild docs if relevant (see instructions below for more details).
6. Run Integration Tests
   Before finalizing a release, run the integration tests to verify ShakeMap produces
   consistent output across all test events. The integration test script and reference
   JSON are located in `tests/integration/`.
  ```bash
  python tests/integration/integration_test.py us6000j985 us6000d58t ak01613v15nv \
      us6000kawn us2000h9e2 usb000j4iz us7000s0pc us7000fcye \
      official20110311054624120_30 usp0000ehr official20100227063411530_30 \
      usp0002jwe us6000sasz us6000m31m usp000gvtu us6000d3zh usp0009e46 \
      us6000qw60 usp000b73z ci38457511
  ```
  All events should pass.
7. Commit all changes to the release candidate branch and push to your origin:
   ```
   git push origin v1.2.1.rc0
   ```
8. Create a merge request into upstream main, merge it, and rebase locally.
9. Create an annotated tag from main and push it upstream:
   ```
   git tag -a v1.2.1 -m "Version 1.2.1"
   git push upstream v1.2.1
   ```
   Notes on tag naming:
   - Tag names cannot contain a hyphen.
   - If the tag name ends with `dev`, it will be uploaded to PyPI as a pre-release
     version, meaning it will not be installed unless the user specifies the exact
     version explicitly.
10. Create a release from the tag in GitLab. Give it a release title like `v1.2.1`.
11. Copy/paste the relevant part of the changelog into the "describe this release"
    section.


## Build Documentation

Some additional packages are required to build the documentation, which can be included
with the `doc` install option, e.g.,

```
pip install .[doc]
```

Then the docs are built with

```
cd doc_source/
./makedocs.sh
```

Note that the script includes the following arguments:
 - `rebuild` - Build documentation from a clean starting point.
 - `update` - Incremental build of the documentation. No cleaning.
 - `clean_data` - Remove all temporary data files generated when building the documentation.
 - `clean_all` - Remove all temporary data files and generated documentation.

The docs can then be previewed by opening `docs/index.html` in a browser.

Notes:
 - Never edit the contents of `docs`, only edit the files in `doc_source`.


[1]: https://code.usgs.gov/ghsc/esi/shakemap/issues
[2]: https://help.github.com/articles/fork-a-repo/
[3]: https://help.github.com/articles/about-pull-requests/
[4]: https://github.com/usgs/best-practices
[5]: https://www.usgs.gov/about/organization/science-support/science-quality-and-integrity/fundamental-science-practices
[6]: https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html
[7]: https://github.com/psf/black
[8]: https://docs.python.org/3.8/library/exceptions.html#built-in-exceptions
[9]: https://github.com/angular/angular/blob/22b96b9/CONTRIBUTING.md#type
