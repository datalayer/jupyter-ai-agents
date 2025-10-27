#!/usr/bin/env bash
pip install -e ".[lint, typing]"
mypy --install-types --non-interactive .
ruff check .
mdformat --check *.md
pipx run 'validate-pyproject[all]' pyproject.toml
