# CLAUDE.md

## Project overview

`contributors-txt` generates and updates CONTRIBUTORS files from git shortlog data, with
alias support for mapping multiple emails to one person.

## Commands

Activate the venv first: `source venv/bin/activate`

- **Tests**: `python -m pytest tests/ -v` (strict; uses stored expected files)
- **Regenerate expected files**: `python -m pytest tests/ --remaster` (after intentional
  output changes — review the diff before committing)
- **Lint**: `pre-commit run --all-files` (ruff, pylint, mypy, prettier, pyproject-fmt)
- **Single test**: `python -m pytest tests/test_create_content.py -v`
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
- `contributors_txt/const.py` — Constants (git command, excluded names/emails, bot
  deny-list substrings activated by `--no-bots`)

Key types: `Alias` (email mappings) and `Person` (contributor with commit count, name,
email, team, comment) — both `NamedTuple`s in `create_content.py`.

## Tests

Tests use [pytest-remaster](https://pypi.org/project/pytest-remaster/) (golden master)
with one directory per case:

```
tests/
  create_content_cases/<case>/    shortlog, optional flags.json, expected.txt
  extract_cases/<case>/           contributors.txt, aliases.json, expected.json
  get_aliases_cases/<case>/       aliases.json, optional flags.json, expected.json
  normalize_cases/<case>/         input.json, expected.json
```

Add a new case by creating a subdirectory with the input files, then run
`pytest --remaster` to generate `expected.*`. Strict comparison is the default
(`remaster-by-default = false` in `pyproject.toml`); `--remaster` is opt-in.

`flags.json` carries case-specific options:

- `{"no_bots": true}` — pass `no_bots=True` to `create_content`
- `{"expect_warning": "<substring>"}` — assert a warning matching the substring

Expected files are machine-formatted to match the runtime serializer byte-for-byte and
are listed in `.prettierignore` so prettier won't reformat them.

## Style

- Python 3.9+ (uses `from __future__ import annotations`)
- Ruff for formatting/linting, mypy strict mode, pylint
- No docstrings required (pylint `missing-docstring` disabled)
- Line length: 88

## Release

Versioning is handled by `setuptools-scm` from git tags — do not edit a `version` field.
Create a GitHub release with a `vX.Y.Z` tag; CI fetches full history, `setuptools-scm`
resolves the version from the tag, and `release.yml` publishes to PyPI. Untagged dev
builds get a `X.Y.Z.devN+g<sha>` version automatically.
