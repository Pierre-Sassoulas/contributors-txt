from __future__ import annotations

from pathlib import Path

from contributors_txt.aliases import get_aliases
from contributors_txt.cli import set_logging
from contributors_txt.create_content import create_content
from contributors_txt.git import get_shortlog_output
from contributors_txt.update_content import update_content


def create_contributors_txt(
    aliases_file: Path | str | None,
    output: Path | str,
    verbose: bool = False,
    no_bots: bool = False,
) -> None:
    set_logging(verbose)
    aliases = get_aliases(aliases_file)
    shortlog_output = get_shortlog_output()
    if Path(output).is_file():
        content = update_content(
            output, aliases, shortlog_output, str(aliases_file), no_bots=no_bots
        )
    else:
        content = create_content(
            aliases, shortlog_output, str(aliases_file), no_bots=no_bots
        )
    with open(output, "w", encoding="utf8") as f:
        f.write(content)
