# contributors-txt

[![PyPI version](https://badge.fury.io/py/contributors-txt.svg)](https://badge.fury.io/py/contributors-txt)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/contributors-txt)](https://pypi.org/project/contributors-txt/)
[![PyPI - License](https://img.shields.io/pypi/l/contributors-txt)](https://pypi.org/project/contributors-txt/)

Generate a list of contributors automatically from git data.

## Install

```bash
pip install contributors-txt
```

## Usage

Run inside a git repository. Without an alias file, contributors are listed straight
from `git shortlog`:

```bash
contributors-txt -o CONTRIBUTORS.txt
```

Pass an alias file to merge multiple emails under one name and assign teams:

```bash
contributors-txt -a aliases.json -o CONTRIBUTORS.txt
```

Add `--no-bots` to filter out GitHub Apps (`dependabot[bot]`, `pre-commit-ci[bot]`,
`github-actions[bot]`, Copilot, Claude, …):

```bash
contributors-txt --no-bots -a aliases.json -o CONTRIBUTORS.txt
```

If the output file already exists it is updated in place: missing emails are added and
new contributors are inserted in commit-count order, preserving any manual edits.

## Alias file

```json
{
  "pierre.sassoulas@gmail.com": {
    "mails": ["pierre.sassoulas@gmail.com", "pierre.sassoulas@elum-energy.com"],
    "name": "Pierre Sassoulas",
    "team": "Maintainers"
  }
}
```

Two helpers ship alongside the main command:

- `contributors-txt-normalize-configuration -a aliases.json` rewrites an alias file in
  the canonical sorted form.
- `contributors-txt-extract-comment <CONTRIBUTORS.txt> -a aliases.json` pulls free-text
  comments from an existing CONTRIBUTORS file back into the alias file.
