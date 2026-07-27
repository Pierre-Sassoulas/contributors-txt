from __future__ import annotations

import json
import logging
import re
from pathlib import Path

from contributors_txt.create_content import (
    Alias,
    Person,
    dump_normalized_aliases,
    get_teams,
    line_for_person,
    person_should_be_shown,
    persons_from_shortlog,
)

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
    persons = persons_from_shortlog(aliases, shortlog_output, no_bots=no_bots)
    merged = _merge_duplicate_names(persons)
    if merged:
        _save_merged_aliases(aliases, merged, configuration_file)
    with open(output, encoding="utf8") as f:
        current_output = f.read()
    return update_teams(
        current_output if header in current_output else header + current_output,
        persons,
        configuration_file,
    )


def _merge_duplicate_names(
    persons: dict[str, Person],
) -> list[tuple[Person, list[Person]]]:
    """Merge persons sharing an email, keeping the name with the most commits."""
    by_mail: dict[str, list[Person]] = {}
    for person in persons.values():
        if person.mail:
            by_mail.setdefault(person.mail, []).append(person)
    merged: list[tuple[Person, list[Person]]] = []
    for group in by_mail.values():
        if len(group) < 2:
            continue
        canonical = max(group, key=lambda p: p.number_of_commits)
        for person in group:
            del persons[person.name]
        new_person = Person(
            sum(p.number_of_commits for p in group),
            canonical.name,
            canonical.mail,
            canonical.team,
            canonical.comment,
        )
        persons[canonical.name] = new_person
        merged.append((new_person, group))
    return merged


def _save_merged_aliases(
    aliases: list[Alias],
    merged: list[tuple[Person, list[Person]]],
    configuration_file: str,
) -> None:
    for person, group in merged:
        assert person.mail
        bare_mail = person.mail[1:-1]
        aliases.append(
            Alias(
                mails=[bare_mail],
                authoritative_mail=bare_mail,
                name=person.name,
                team=person.team,
                comment=person.comment or None,
            )
        )
        LOGGER.warning(
            "%s committed under several names (%s): merged into '%s', "
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


def update_teams(
    current_result: str,
    persons: dict[str, Person],
    configuration_file: str = "the aliases file",
) -> str:
    teams = get_teams(persons, exclude_standard=False)
    if not teams:
        return current_result
    current_result = _drop_duplicate_person_lines(current_result, persons)
    current_result = add_email_if_missing(current_result, teams, configuration_file)
    check_no_email(current_result)
    current_result = reorder_existing_by_commits(current_result, teams)
    if current_result[-1] != "\n":
        current_result += "\n"
    return current_result


def _drop_duplicate_person_lines(
    current_result: str, persons: dict[str, Person]
) -> str:
    """Remove entries whose email is already listed under another entry."""
    lines = current_result.split("\n")
    blocks = _person_blocks(lines)
    to_drop: set[int] = set()
    for person in persons.values():
        if not person.mail:
            continue
        matching = [b for b in blocks if person.mail in lines[b[0]]]
        if len(matching) < 2:
            continue
        keep = next((b for b in matching if person.name in lines[b[0]]), matching[0])
        for block in matching:
            if block == keep:
                continue
            LOGGER.warning(
                "Removing '%s', a duplicate of '%s'.",
                lines[block[0]],
                lines[keep[0]],
            )
            to_drop.update(range(*block))
    if not to_drop:
        return current_result
    return "\n".join(line for i, line in enumerate(lines) if i not in to_drop)


def check_no_email(current_result: str) -> None:
    for part in current_result.split("\n-"):
        if all(c not in part for c in [">", "<", "@"]):
            LOGGER.warning("There's no email in %s", part)


def reorder_existing_by_commits(
    current_result: str, teams: dict[str, list[Person]]
) -> str:
    if not teams:
        return current_result
    team_boundary = get_team_boundary(current_result, list(teams.keys()))
    parts: list[str] = []
    for team_name in sorted(team_boundary, key=lambda t: team_boundary[t][0]):
        begin, end = team_boundary[team_name]
        section = current_result[begin:end]
        if team_name == "Header" or team_name not in teams:
            parts.append(section)
            continue
        parts.append(_reorder_section(section, teams[team_name]))
    return "".join(parts)


def _reorder_section(section: str, members: list[Person]) -> str:
    lines = section.split("\n")
    blocks = _person_blocks(lines)
    if len(blocks) < 2:
        return section
    matched = _match_blocks_to_members(lines, blocks, members)
    if len(matched) < 2:
        return section
    new_block_order = list(range(len(blocks)))
    matched_sorted = sorted(matched, key=lambda x: -x[1])
    for (slot, _), (orig_bi, _) in zip(matched, matched_sorted):
        new_block_order[slot] = orig_bi
    rebuilt: list[str] = list(lines[: blocks[0][0]])
    for bi in new_block_order:
        start, stop = blocks[bi]
        rebuilt.extend(lines[start:stop])
    rebuilt.extend(lines[blocks[-1][1] :])
    return "\n".join(rebuilt)


def _match_blocks_to_members(
    lines: list[str], blocks: list[tuple[int, int]], members: list[Person]
) -> list[tuple[int, int]]:
    """Return (block index, commit count) pairs for blocks matched by mail."""
    members_by_mail = {m.mail: m for m in members if m.mail}
    matched: list[tuple[int, int]] = []
    for bi, (start, stop) in enumerate(blocks):
        block_text = "\n".join(lines[start:stop])
        for mail, member in members_by_mail.items():
            if mail in block_text:
                matched.append((bi, member.number_of_commits))
                break
    return matched


def _person_blocks(lines: list[str]) -> list[tuple[int, int]]:
    blocks: list[tuple[int, int]] = []
    i = 0
    while i < len(lines):
        if lines[i].startswith("- "):
            j = i + 1
            while j < len(lines) and lines[j] and not lines[j].startswith("- "):
                j += 1
            blocks.append((i, j))
            i = j
        else:
            i += 1
    return blocks


def add_email_if_missing(
    current_result: str,
    teams: dict[str, list[Person]],
    configuration_file: str = "the aliases file",
) -> str:
    new_teams: list[str] = []
    team_boundary = get_team_boundary(current_result, list(teams.keys()))
    being_header, end_header = team_boundary["Header"]
    new_teams.append(current_result[being_header:end_header])
    for team_name in sorted(team_boundary, key=team_boundary.get):  # type: ignore[arg-type]
        if team_name == "Header":
            continue
        begin, end = team_boundary[team_name]
        new_team = str(current_result[begin:end])
        if team_name not in teams:
            # Section exists in file but has no committers (e.g. Co-Author),
            # pass through unchanged
            new_teams.append(new_team)
            continue
        team_members = teams[team_name]
        LOGGER.debug("Updating team %s", team_name)
        section_slice = current_result[begin:end]
        for team_member in team_members:
            if not person_should_be_shown(team_member):
                continue
            if team_member.name in section_slice:
                if team_member.mail and team_member.mail in section_slice:
                    check_for_duplication(
                        current_result, team_member, configuration_file
                    )
                else:
                    new_team = _add_email_to_existing(
                        new_team, team_member, team_name
                    )
            elif team_member.mail is not None and team_member.mail in current_result:
                base_message = (
                    f"'{team_member}' already exists in the file at "
                    f"{current_result.find(team_member.mail)} "
                    f"({team_boundary}) but is not in the proper section, "
                    f"it should be '{team_name}', please fix manually. Did "
                    "you consider uniformizing the name ? :\n"
                )
                raise RuntimeError(
                    team_member.get_template(base_message) + "}\n"
                )
            elif team_member.mail:
                new_team = _insert_person_by_commits(
                    new_team, team_member, team_members
                )
            else:
                LOGGER.warning(
                    "'%s' was not treated as there's no email.", team_member
                )
        new_teams.append(new_team)
    return "".join(new_teams)


def _add_email_to_existing(
    new_team: str, team_member: Person, team_name: str
) -> str:
    if not team_member.mail:
        return new_team
    if team_member.name.find(" ") != -1:
        LOGGER.debug("For %s in %s: Adding email", team_member, team_name)
        return new_team.replace(
            team_member.name, f"{team_member.name} {team_member.mail}"
        )
    LOGGER.debug(
        "For %s, there's only a one word name not replacing "
        "anything but it exists.",
        repr(team_member),
    )
    return new_team


def _insert_person_by_commits(
    section_text: str, new_person: Person, team_members: list[Person]
) -> str:
    """Insert a new person into a section, ordered by number of commits."""
    new_line = line_for_person(new_person)
    lines = section_text.split("\n")
    person_entries = _find_person_entries(lines, team_members)
    insert_pos = _find_insert_position(lines, person_entries, new_person)
    lines.insert(insert_pos, new_line.rstrip("\n"))
    return "\n".join(lines)


def _find_person_entries(
    lines: list[str], team_members: list[Person]
) -> list[tuple[int, int]]:
    """Return (line_index, commit_count) for person lines matched to team members."""
    entries: list[tuple[int, int]] = []
    for i, line in enumerate(lines):
        if not line.startswith("- "):
            continue
        for tm in team_members:
            if tm.mail and tm.mail in line:
                entries.append((i, tm.number_of_commits))
                break
    return entries


def _find_insert_position(
    lines: list[str],
    person_entries: list[tuple[int, int]],
    new_person: Person,
) -> int:
    """Find the line index where a new person should be inserted."""
    if not person_entries:
        return _fallback_insert_position(lines)

    # After the last matched person with >= commits
    insert_after_idx = None
    for line_idx, commits in person_entries:
        if commits >= new_person.number_of_commits:
            insert_after_idx = line_idx

    if insert_after_idx is None:
        # More commits than all matched entries, insert before first matched
        return person_entries[0][0]
    return _end_of_person_entry(lines, insert_after_idx)


def _fallback_insert_position(lines: list[str]) -> int:
    """Find insert position when no matched person entries exist."""
    last_person_idx = None
    for i, line in enumerate(lines):
        if line.startswith("- "):
            last_person_idx = i
    if last_person_idx is not None:
        return _end_of_person_entry(lines, last_person_idx)
    # No person entries at all, append before trailing whitespace
    pos = len(lines)
    while pos > 0 and lines[pos - 1].strip() == "":
        pos -= 1
    return pos


def _end_of_person_entry(lines: list[str], person_line_idx: int) -> int:
    """Return the line index after a person entry and its continuation lines."""
    pos = person_line_idx + 1
    while pos < len(lines) and lines[pos] and not lines[pos].startswith("- "):
        pos += 1
    return pos


def check_for_duplication(
    current_result: str,
    team_member: Person,
    configuration_file: str = "the aliases file",
) -> None:
    assert team_member.mail
    if current_result.count(team_member.mail) != 1:
        raise RuntimeError(
            _duplication_error(current_result, team_member, configuration_file)
        )
    name_count = current_result.count(team_member.name)
    name_in_email = team_member.name in team_member.mail
    if (name_count > 1 and not name_in_email) or (name_count > 2 and name_in_email):
        LOGGER.info(
            "It's possible that %s is duplicated, please check by yourself",
            team_member,
        )


def _duplication_error(
    current_result: str, team_member: Person, configuration_file: str
) -> str:
    assert team_member.mail
    occurrences = "\n".join(
        f"  line {lineno}: {line}"
        for lineno, line in enumerate(current_result.splitlines(), start=1)
        if team_member.mail in line
    )
    bare_mail = team_member.mail[1:-1]
    alias_example = json.dumps(
        {bare_mail: {"mails": [bare_mail], "name": team_member.name}},
        indent=2,
        ensure_ascii=False,
    )
    return (
        f"{team_member.mail} appears multiple times in the contributors file "
        "and could not be merged automatically:\n"
        f"{occurrences}\n"
        "To fix this:\n"
        "1. Merge these entries in the contributors file manually, keeping a "
        f"single line for {team_member.mail}.\n"
        "2. If the same person contributed under several names, add an entry "
        f"in '{configuration_file}' so a single name is always used for this "
        f"email, for example:\n{alias_example}\n"
        "Then run contributors-txt again."
    )


def get_team_boundary(
    current_result: str, teams: list[str]
) -> dict[str, tuple[int, int]]:
    teams_boundary: dict[str, tuple[int, int]] = {"Header": (0, 0)}
    for team in teams:
        teams_boundary[team] = current_result.find(team), 0
    # Also detect section headers in the file that aren't in the teams dict
    # (e.g. "Co-Author" sections with no committers in the shortlog)
    for match in re.finditer(r"^(.+)\n-{2,}$", current_result, re.MULTILINE):
        section_name = match.group(1)
        if section_name not in teams_boundary:
            teams_boundary[section_name] = match.start(), 0
    ordered_teams = sorted(teams_boundary, key=teams_boundary.get)  # type: ignore[arg-type]
    for i, team in enumerate(ordered_teams):
        begin = teams_boundary[team][0]
        if i == len(ordered_teams) - 1:
            end = len(current_result)
        else:
            end = teams_boundary[ordered_teams[i + 1]][0]
        teams_boundary[team] = (begin, end)
    return teams_boundary
