# CLAUDE.md

## Project overview

`contributors-txt` generates and updates CONTRIBUTORS files from git shortlog data, with
alias support for mapping multiple emails to one person.

## Commands

Activate the venv first: `source venv/bin/activate`

- **Tests**: `python -m pytest tests/ -v`
- **Lint**: `pre-commit run --all-files` (ruff, pylint, mypy, prettier, pyproject-fmt)
- **Single test**: `python -m pytest tests/test_create_content.py::test_basic -v`
- **Install dev deps**: `pip install -e ".[test]"`

## Architecture

- `contributors_txt/__main__.py` — CLI entry point, creates or updates CONTRIBUTORS
  files
- `contributors_txt/create_content.py` — Parses git shortlog, builds content from
  scratch (sorted by commits descending)
- `contributors_txt/update_content.py` — Updates existing files: adds missing emails,
  inserts new contributors in commit-count order
- `contributors_txt/extract_comment.py` — Extracts comments from existing CONTRIBUTORS
  files back into aliases
- `contributors_txt/normalize.py` — Normalizes alias JSON files
- `contributors_txt/const.py` — Constants (git command, excluded names/emails)

Key types: `Alias` (email mappings) and `Person` (contributor with commit count, name,
email, team, comment) — both `NamedTuple`s in `create_content.py`.

## Style

- Python 3.9+ (uses `from __future__ import annotations`)
- Ruff for formatting/linting, mypy strict mode, pylint
- No docstrings required (pylint `missing-docstring` disabled)
- Line length: 88

## Release

Bump version in `pyproject.toml`, create a GitHub release with tag — CI auto-publishes
to PyPI.
