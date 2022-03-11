import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union

from contributors_txt.__main__ import parse_args, set_logging
from contributors_txt.create_content import Alias, get_aliases


def main(args: Optional[List[str]] = None) -> None:
    parsed_args = parse_args(args)
    if parsed_args.output is None:
        parsed_args.output = parsed_args.aliases
    logging.debug("Launching migration with %s", args)
    migrate_from_copyrite(parsed_args.aliases, parsed_args.output, parsed_args.verbose)


def migrate_from_copyrite(
    aliases_file: Union[Path, str], output: Union[Path, str], verbose: bool = False
) -> None:
    aliases = get_aliases(aliases_file)
    set_logging(verbose)
    content = get_new_aliases(aliases)
    # logging.debug(content)
    with open(output, "w", encoding="utf8") as f:
        json.dump(content, f, indent=4, sort_keys=True)


def get_new_aliases(aliases: List[Alias]) -> Dict:
    return {
        alias.name: {
            "mails": alias.mails,
            "authoritative_mail": alias.authoritative_mail,
        }
        for alias in aliases
    }
