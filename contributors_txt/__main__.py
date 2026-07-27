"""Create a file listing the contributors of a git repository.
"""

from __future__ import annotations

from contributors_txt.api import create_contributors_txt
from contributors_txt.cli import parse_args


def main(args: list[str] | None = None) -> None:
    parsed_args = parse_args(args)
    create_contributors_txt(
        parsed_args.aliases,
        parsed_args.output,
        parsed_args.verbose,
        no_bots=parsed_args.no_bots,
    )


if __name__ == "__main__":
    main()
