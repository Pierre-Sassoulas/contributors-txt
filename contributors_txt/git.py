from __future__ import annotations

import logging
import subprocess
from typing import NamedTuple

from contributors_txt.const import (
    DEFAULT_TEAM_ROLE,
    KNOWN_BOT_MAIL_SUBSTRINGS,
    KNOWN_BOT_NAME_SUBSTRINGS,
)
from contributors_txt.model import Alias, Person

LOGGER = logging.getLogger(__name__)


class ShortlogResult(NamedTuple):
    """Persons keyed by email (name when there is none), plus the groups of
    persons that shared an email under several names and got merged."""

    persons: dict[str, Person]
    merged: list[tuple[Person, list[Person]]]

# The explicit HEAD matters: without a revision and with a non-interactive
# stdin (CI, cron), git shortlog reads the log from stdin and returns nothing.
GIT_SHORTLOG = ["git", "shortlog", "--summary", "--numbered", "--email", "HEAD"]


def get_shortlog_output() -> str:
    git_shortlog = subprocess.run(GIT_SHORTLOG, capture_output=True, check=False)
    command = " ".join(GIT_SHORTLOG)
    if git_shortlog.returncode != 0:
        msg = (
            f"'{command}' failed with code {git_shortlog.returncode}: "
            f"{git_shortlog.stderr.decode('utf8').strip()}"
        )
        raise RuntimeError(
            msg
        )
    output = git_shortlog.stdout.decode("utf8")
    if not output.strip():
        msg = (
            f"'{command}' returned no contributors, is this a git repository "
            "with at least one commit?"
        )
        raise RuntimeError(
            msg
        )
    return output


def is_bot(name: str, mail: str | None) -> bool:
    if any(substring in name for substring in KNOWN_BOT_NAME_SUBSTRINGS):
        return True
    if not mail:
        return False
    return any(substring in mail for substring in KNOWN_BOT_MAIL_SUBSTRINGS)


def persons_from_shortlog(
    aliases: list[Alias], shortlog_output: str, no_bots: bool = False
) -> ShortlogResult:
    groups: dict[str, list[Person]] = {}
    for unparsed_person in shortlog_output.split("\n"):
        if not unparsed_person:
            # Empty line in git output
            continue
        # logging.debug("Handling %s", unparsed_person)
        new_person = _parse_person(unparsed_person, aliases)
        if no_bots and is_bot(new_person.name, new_person.mail):
            continue
        groups.setdefault(new_person.mail or new_person.name, []).append(new_person)
    persons: dict[str, Person] = {}
    merged: list[tuple[Person, list[Person]]] = []
    for key, group in groups.items():
        person = _merge_group(group)
        if len({p.name for p in group}) > 1:
            merged.append((person, group))
        persons[key] = person
    _warn_about_same_name_with_several_mails(persons)
    return ShortlogResult(persons, merged)


def _merge_group(group: list[Person]) -> Person:
    canonical = max(group, key=lambda p: p.number_of_commits)
    if len(group) == 1:
        return canonical
    return Person(
        sum(p.number_of_commits for p in group),
        canonical.name,
        canonical.mail,
        canonical.team,
        canonical.comment,
    )


def _warn_about_same_name_with_several_mails(persons: dict[str, Person]) -> None:
    by_name: dict[str, list[Person]] = {}
    for person in persons.values():
        by_name.setdefault(person.name, []).append(person)
    for name, group in by_name.items():
        if len(group) > 1:
            LOGGER.warning(
                "'%s' appears with several emails (%s); if this is a single "
                "person, add an alias to merge them.",
                name,
                ", ".join(f"<{p.mail}>" for p in group if p.mail),
            )


def _parse_person(unparsed_person: str, aliases: list[Alias]) -> Person:
    splitted_person = unparsed_person.split()
    number_of_commit, *names = splitted_person[:-1]
    name = " ".join(names)
    mail: str | None = splitted_person[-1][1:-1]
    team = DEFAULT_TEAM_ROLE
    comment: str | None = ""
    if mail == "none@none":
        mail = None
    for alias in aliases:
        if mail and mail in alias.mails:
            # logging.debug("Found an alias: %s", mail)
            mail = alias.authoritative_mail
            name = alias.name
            team = alias.team
            comment = alias.comment
            break
    # logging.debug("Person is aliased to %s %s %s", number_of_commit, name, mail)
    return Person(int(number_of_commit), name, mail, team, comment)
