# Contributing

Welcome! As a [Jupyter](https://jupyter.org) project, you can follow the [Jupyter contributor guide](https://jupyter.readthedocs.io/en/latest/contributor/content-contributor.html).

Make sure to also follow [Project Jupyter's Code of Conduct](https://github.com/jupyter/governance/blob/master/conduct/code_of_conduct.md) for a friendly and welcoming collaborative environment.

## Setting up for local development

This package requires Python >= 3.5.

As a Python package, you can set up a development environment by cloning this repo and running:

    python3 -m pip install --editable .

from the repo directory.

You can also install the tools we use for testing and development with:

    python3 -m pip install -r dev-requirements.txt


### Auto-format with black

We are trying out the [black](https://github.com/ambv/black) auto-formatting
tool on this repo.

You can run `black` manually on the repo with:

    black .

in the root of the repo. You can also enable this automatically on each commit
by installing a pre-commit hook:

    ./git-hooks/install

After doing this, every time you make a commit,
the `black` autoformatter will run,
ensuring consistent style without you having to worry too much about style.

## Running the tests

After doing a development install, you can run the tests with:

    pytest -v

in the repo directory.
