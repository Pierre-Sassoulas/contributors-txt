from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from contributors_txt.aliases import save_merged_aliases
from contributors_txt.create_content import (
    get_teams,
    line_for_person,
    person_should_be_shown,
)
from contributors_txt.document import Document, Entry, Section, parse
from contributors_txt.git import persons_from_shortlog

if TYPE_CHECKING:
    from pathlib import Path

    from contributors_txt.model import Alias, Person

LOGGER = logging.getLogger(__name__)


def update_content(
    output: Path | str,
    aliases: list[Alias],
    shortlog_output: str,
    configuration_file: str,
    no_bots: bool = False,
) -> str:
    header: str = f"""\
# This file is autocompleted by 'contributors-txt',
# using the configuration in '{configuration_file}'.
# Do not add new persons manually and only add information without
# using '-' as the line first character.
# Please verify that your change are stable if you modify manually.

"""
    persons, merged = persons_from_shortlog(aliases, shortlog_output, no_bots=no_bots)
    if merged:
        save_merged_aliases(aliases, merged, configuration_file)
    with open(output, encoding="utf8") as f:
        current_output = f.read()
    return update_teams(
        current_output if header in current_output else header + current_output,
        persons,
        configuration_file,
    )


def update_teams(
    current_result: str,
    persons: dict[str, Person],
    configuration_file: str = "the aliases file",
) -> str:
    teams = get_teams(persons, exclude_standard=False)
    if not teams:
        return current_result
    document = parse(current_result)
    _drop_duplicate_entries(document, persons)
    for team_name, members in teams.items():
        _update_section(document, team_name, members, configuration_file)
    _warn_about_entries_without_email(document)
    for team_name, members in teams.items():
        section = document.section(team_name)
        if section is not None:
            _reorder_entries_by_commits(section, members)
    result = document.render()
    if not result.endswith("\n"):
        result += "\n"
    return result


def _drop_duplicate_entries(document: Document, persons: dict[str, Person]) -> None:
    """Remove entries whose email is already listed on another entry."""
    for person in persons.values():
        if not person.mail:
            continue
        matching = [e for e in document.entries() if e.mail == person.mail]
        if len(matching) < 2:
            continue
        keep = next(
            (e for e in matching if e.matches_name(person.name)), matching[0]
        )
        for entry in matching:
            if entry is keep:
                continue
            LOGGER.warning(
                "Removing '%s', a duplicate of '%s'.", entry.lines[0], keep.lines[0]
            )
            for section in document.sections:
                if entry in section.items:
                    section.items.remove(entry)


def _update_section(
    document: Document,
    team_name: str,
    members: list[Person],
    configuration_file: str,
) -> None:
    section = document.section(team_name)
    if section is None:
        LOGGER.warning(
            "Section '%s' does not exist in the file, creating it.", team_name
        )
        section = document.add_section(team_name)
    LOGGER.debug("Updating team %s", team_name)
    for member in members:
        if person_should_be_shown(member):
            _update_member(document, section, member, members, configuration_file)


def _update_member(
    document: Document,
    section: Section,
    member: Person,
    members: list[Person],
    configuration_file: str,
) -> None:
    if member.mail and any(e.mail == member.mail for e in section.entries):
        return
    named = next((e for e in section.entries if e.matches_name(member.name)), None)
    if named is not None:
        if member.mail:
            LOGGER.debug("For %s in %s: Adding email", member, section.title)
            named.add_mail_after_name(member.name, member.mail)
        return
    if member.mail:
        wrong_section = _section_of_mail(document, member.mail)
        if wrong_section is not None:
            msg = (
                f"'{member}' is listed in the '{wrong_section.title}' section "
                f"but their team is '{section.title}'. Move the entry manually, "
                f"or fix the alias in '{configuration_file}'."
            )
            raise RuntimeError(msg)
        _insert_entry_by_commits(section, member, members)
        return
    LOGGER.warning("'%s' was not treated as there's no email.", member)


def _section_of_mail(document: Document, mail: str) -> Section | None:
    for section in document.sections:
        if any(e.mail == mail for e in section.entries):
            return section
    return None


def _insert_entry_by_commits(
    section: Section, new_person: Person, team_members: list[Person]
) -> None:
    new_entry = Entry([line_for_person(new_person).rstrip("\n")])
    commits_by_mail = {m.mail: m.number_of_commits for m in team_members if m.mail}
    positions = [
        (index, commits_by_mail[item.mail])
        for index, item in enumerate(section.items)
        if isinstance(item, Entry) and item.mail in commits_by_mail
    ]
    if not positions:
        section.items.insert(_fallback_insert_position(section), new_entry)
        return
    insert_after = None
    for index, commits in positions:
        if commits >= new_person.number_of_commits:
            insert_after = index
    if insert_after is None:
        # More commits than all matched entries, insert before the first one
        section.items.insert(positions[0][0], new_entry)
    else:
        section.items.insert(insert_after + 1, new_entry)


def _fallback_insert_position(section: Section) -> int:
    """Insert position when no entry of the section matches a team member."""
    last_entry_index = None
    for index, item in enumerate(section.items):
        if isinstance(item, Entry):
            last_entry_index = index
    if last_entry_index is not None:
        return last_entry_index + 1
    # No entries at all, append before the trailing blank lines
    position = len(section.items)
    while position > 0 and not str(section.items[position - 1]).strip():
        position -= 1
    return position


def _warn_about_entries_without_email(document: Document) -> None:
    for entry in document.entries():
        if entry.mail is None:
            LOGGER.warning("There's no email in %s", entry.lines[0])


def _reorder_entries_by_commits(section: Section, members: list[Person]) -> None:
    """Reorder the entries matching team members by commit count, in place."""
    commits_by_mail = {m.mail: m.number_of_commits for m in members if m.mail}
    slots = [
        index
        for index, item in enumerate(section.items)
        if isinstance(item, Entry) and item.mail in commits_by_mail
    ]
    if len(slots) < 2:
        return
    ordered = sorted(
        (section.items[index] for index in slots),
        key=lambda entry: -commits_by_mail[entry.mail],  # type: ignore[union-attr,index]
    )
    for slot, entry in zip(slots, ordered):
        section.items[slot] = entry
