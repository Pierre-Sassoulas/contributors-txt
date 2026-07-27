"""Create a file listing the contributors of a git repository.
"""

from __future__ import annotations

import argparse
import logging

from contributors_txt.const import DEFAULT_CONTRIBUTOR_PATH


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    add_default_arguments(parser)
    parser.add_argument(
        "-o",
        "--output",
        default=str(DEFAULT_CONTRIBUTOR_PATH),
        help="Where to output the contributor list",
    )
    parser.add_argument(
        "--no-bots",
        action="store_true",
        default=False,
        help=(
            "Exclude known bots (GitHub Apps with the '[bot]' suffix, e.g. "
            "dependabot, pre-commit-ci, github-actions) from the contributor list."
        ),
    )
    parsed_args: argparse.Namespace = parser.parse_args(args)
    return parsed_args


def add_default_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "-a",
        "--aliases",
        default=None,
        help="The path to the aliases file.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        default=False,
        help="Display logging messages",
    )


def set_logging(verbose: bool) -> None:
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
