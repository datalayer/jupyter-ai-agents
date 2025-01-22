<!--
  ~ Copyright (c) 2023-2024 Datalayer, Inc.
  ~
  ~ BSD 3-Clause License
-->

# Making a new release of jupyter_ai_agents

The extension can be published to `PyPI` manually or using the [Jupyter Releaser](https://github.com/jupyter-server/jupyter_releaser).

## Manual release

### Python package

This repository can be distributed as Python
package. All of the Python
packaging instructions in the `pyproject.toml` file to wrap your extension in a
Python package. Before generating a package, we first need to install `build`.

```bash
pip install build twine
```

To create a Python source package (`.tar.gz`) and the binary package (`.whl`) in the `dist/` directory, do:

```bash
python -m build
```

Then to upload the package to PyPI, do:

```bash
twine upload dist/*
```

## Automated releases with the Jupyter Releaser

> [!NOTE]
> The extension repository is compatible with the Jupyter Releaser. But
> the GitHub repository and PyPI may need to be properly set up. Please
> follow the instructions of the Jupyter Releaser [checklist](https://jupyter-releaser.readthedocs.io/en/latest/how_to_guides/convert_repo_from_repo.html).

Here is a summary of the steps to cut a new release:

- Go to the Actions panel
- Run the "Step 1: Prep Release" workflow
- Check the draft changelog
- Run the "Step 2: Publish Release" workflow

> [!NOTE]
> Check out the [workflow documentation](https://jupyter-releaser.readthedocs.io/en/latest/get_started/making_release_from_repo.html)
> for more information.

## Publishing to `conda-forge`

If the package is not on conda forge yet, check the documentation to learn how to add it: https://conda-forge.org/docs/maintainer/adding_pkgs.html

Otherwise a bot should pick up the new version publish to PyPI, and open a new PR on the feedstock repository automatically.
