from __future__ import annotations

import subprocess

from contributors_txt.const import (
    DEFAULT_TEAM_ROLE,
    KNOWN_BOT_MAIL_SUBSTRINGS,
    KNOWN_BOT_NAME_SUBSTRINGS,
)
from contributors_txt.model import Alias, Person

GIT_SHORTLOG = ["git", "shortlog", "--summary", "--numbered", "--email"]


def get_shortlog_output() -> str:
    git_shortlog = subprocess.run(GIT_SHORTLOG, capture_output=True, check=False)
    return git_shortlog.stdout.decode("utf8")


def is_bot(name: str, mail: str | None) -> bool:
    if any(substring in name for substring in KNOWN_BOT_NAME_SUBSTRINGS):
        return True
    if not mail:
        return False
    return any(substring in mail for substring in KNOWN_BOT_MAIL_SUBSTRINGS)


def persons_from_shortlog(
    aliases: list[Alias], shortlog_output: str, no_bots: bool = False
) -> dict[str, Person]:
    persons: dict[str, Person] = {}
    for unparsed_person in shortlog_output.split("\n"):
        if not unparsed_person:
            # Empty line in git output
            continue
        # logging.debug("Handling %s", unparsed_person)
        new_person = _parse_person(unparsed_person, aliases)
        if no_bots and is_bot(new_person.name, new_person.mail):
            continue
        if new_person.name in persons:
            new_person = persons[new_person.name] + new_person
        persons[new_person.name] = new_person
    return persons


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
    return Person(
        int(number_of_commit), name, f"<{mail}>" if mail else None, team, comment
    )
