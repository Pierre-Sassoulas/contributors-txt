from pathlib import Path
from typing import List, Union

from contributors_txt.create_content import (
    Alias,
    add_contributors,
    add_teams,
    persons_from_shortlog,
)


def update_content(
    output: Union[Path, str],
    aliases: List[Alias],
    shortlog_output: str,
    configuration_file: str,
) -> str:
    result: str = f"""\
# This file is autocompleted by 'contributors-txt',
# using the configuration in '{configuration_file}'
# please verify that your change are stable if you
# modify manually

"""
    persons = persons_from_shortlog(aliases, shortlog_output)
    with open(output, encoding="utf8") as f:
        current_output = f.read()
    result += add_teams(persons)
    result += add_contributors(persons)
    return result
