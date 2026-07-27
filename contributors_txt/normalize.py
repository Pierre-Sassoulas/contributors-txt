from __future__ import annotations

import argparse
import logging
from typing import TYPE_CHECKING

from contributors_txt.aliases import dump_normalized_aliases, get_aliases
from contributors_txt.cli import add_default_arguments, set_logging

if TYPE_CHECKING:
    from pathlib import Path

LOGGER = logging.getLogger(__name__)


def main(args: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Normalize an aliases file to the canonical format."
    )
    add_default_arguments(parser)
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Where to write the normalized aliases (defaults to the aliases file)",
    )
    parsed_args = parser.parse_args(args)
    if parsed_args.aliases is None:
        parser.error("an aliases file is required (use -a/--aliases)")
    if parsed_args.output is None:
        parsed_args.output = parsed_args.aliases
    LOGGER.debug("Launching normalization with %s", args)
    normalize_configuration(
        parsed_args.aliases, parsed_args.output, parsed_args.verbose
    )


def normalize_configuration(
    aliases_file: Path | str, output: Path | str, verbose: bool = False
) -> None:
    aliases = get_aliases(aliases_file, normalize=True)
    set_logging(verbose)
    dump_normalized_aliases(aliases, output)
