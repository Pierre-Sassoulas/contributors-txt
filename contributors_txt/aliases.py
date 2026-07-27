from __future__ import annotations

import json
import logging
import warnings
from pathlib import Path
from typing import TYPE_CHECKING

from contributors_txt.const import DEFAULT_TEAM_ROLE
from contributors_txt.model import Alias

if TYPE_CHECKING:
    from collections.abc import Sequence

    from contributors_txt.model import Person

LOGGER = logging.getLogger(__name__)


def get_aliases(
    aliases_file: Path | str | None, normalize: bool = False
) -> list[Alias]:
    aliases: list[Alias] = []
    if aliases_file is None:
        return aliases
    with open(aliases_file, encoding="utf8") as f:
        parsed_aliases = json.load(f)
        for alias in parsed_aliases:
            # logging.debug("Alias: %s", alias)
            if isinstance(alias, str):
                entry = parsed_aliases[alias]
                if "team" not in entry:
                    entry["team"] = DEFAULT_TEAM_ROLE
                if "name" in entry:
                    python_alias = Alias(authoritative_mail=alias, **entry)
                elif "authoritative_mail" in entry:
                    python_alias = Alias(name=alias, **entry)
                else:
                    msg = (
                        f"Malformed alias entry '{alias}' in '{aliases_file}': "
                        "it must contain a 'name' or an 'authoritative_mail' key."
                    )
                    raise ValueError(msg)
            else:
                if not normalize:
                    warnings.warn(
                        "Using old copyrite format, you should use the configuration "
                        "normalization with 'contributors-txt-normalize-configuration'",
                        stacklevel=2,
                    )
                if "authoritative_mail" not in alias:
                    alias["authoritative_mail"] = None
                if "team" not in alias:
                    alias["team"] = DEFAULT_TEAM_ROLE
                python_alias = Alias(**alias)
            aliases.append(python_alias)
    return aliases


def save_merged_aliases(
    aliases: list[Alias],
    merged: list[tuple[Person, list[Person]]],
    configuration_file: str,
) -> None:
    """Persist the aliases of persons merged from several names, so the
    chosen name stays stable across runs."""
    for person, group in merged:
        assert person.mail
        aliases.append(
            Alias(
                mails=[person.mail],
                authoritative_mail=person.mail,
                name=person.name,
                team=person.team,
                comment=person.comment or None,
            )
        )
        LOGGER.warning(
            "<%s> committed under several names (%s): merged into '%s', "
            "the name with the most commits.",
            person.mail,
            ", ".join(f"'{p.name}'" for p in group),
            person.name,
        )
    if Path(configuration_file).is_file():
        dump_normalized_aliases(aliases, configuration_file)
        LOGGER.warning(
            "Added the merged names to '%s' as aliases.", configuration_file
        )
    else:
        LOGGER.warning(
            "Could not save the aliases for the merged names because '%s' "
            "is not a file, the merge will happen again on the next run.",
            configuration_file,
        )


def dump_normalized_aliases(aliases: list[Alias], output: Path | str) -> None:
    content = get_new_aliases(aliases)
    with open(output, "w", encoding="utf8") as f:
        json.dump(content, f, indent=4, sort_keys=True, ensure_ascii=False)


def get_new_aliases(
    aliases: list[Alias],
) -> dict[str | None, dict[str, Sequence[str] | str]]:
    result = {}
    for alias in aliases:
        updated_alias = {
            "mails": sorted(alias.mails),
            "name": alias.name,
        }
        if alias.team != DEFAULT_TEAM_ROLE:
            updated_alias["team"] = alias.team
        if alias.comment:
            updated_alias["comment"] = alias.comment
        result[alias.authoritative_mail] = updated_alias
    return result
