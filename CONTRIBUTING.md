# Contributing

Welcome! As a [Jupyter](https://jupyter.org) project, you can follow the [Jupyter contributor guide](https://jupyter.readthedocs.io/en/latest/contributor/content-contributor.html).

Make sure to also follow [Project Jupyter's Code of Conduct](https://github.com/jupyter/governance/blob/HEAD/conduct/code_of_conduct.md) for a friendly and welcoming collaborative environment.

## Setting up for local development

This package requires Python >= 3.6.

As a Python package, you can set up a development environment by cloning this repo and running:

    python3 -m pip install --editable ".[test]"

from the repo directory.

### Auto-format with pre-commit

We use the [pre-commit](https://pre-commit.com) tool for autoformatting.

You can install and enable it with:

    pip install pre-commit
    pre-commit install

After doing this, every time you make a commit,
`pre-commit` will run autoformatting.
If it makes any changes, it'll let you know and you can make the commit again with the autoformatting changes.

## Running the tests

After doing a development install, you can run the tests with:

    pytest

in the repo directory.
