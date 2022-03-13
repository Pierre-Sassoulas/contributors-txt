import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union

from contributors_txt.__main__ import parse_args, set_logging
from contributors_txt.const import DEFAULT_TEAM_ROLE
from contributors_txt.create_content import Alias, get_aliases


def main(args: Optional[List[str]] = None) -> None:
    parsed_args = parse_args(args)
    if parsed_args.output is None:
        parsed_args.output = parsed_args.aliases
    logging.debug("Launching normalization with %s", args)
    normalize_configuration(
        parsed_args.aliases, parsed_args.output, parsed_args.verbose
    )


def normalize_configuration(
    aliases_file: Union[Path, str], output: Union[Path, str], verbose: bool = False
) -> None:
    aliases = get_aliases(aliases_file, normalize=True)
    set_logging(verbose)
    content = get_new_aliases(aliases)
    with open(output, "w", encoding="utf8") as f:
        json.dump(content, f, indent=4, sort_keys=True, ensure_ascii=False)


def get_new_aliases(aliases: List[Alias]) -> Dict:
    result = {}
    for alias in aliases:
        updated_alias = {
            "mails": alias.mails,
            "name": alias.name,
        }
        if alias.team != DEFAULT_TEAM_ROLE:
            updated_alias["team"] = alias.team
        result[alias.authoritative_mail] = updated_alias
    return result
