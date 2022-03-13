import logging
from pathlib import Path
from typing import Dict, List, Tuple, Union

from contributors_txt.create_content import (
    Alias,
    Person,
    get_teams,
    line_for_person,
    person_should_be_shown,
    persons_from_shortlog,
)


def update_content(
    output: Union[Path, str],
    aliases: List[Alias],
    shortlog_output: str,
    configuration_file: str,
) -> str:
    result: str = ""
    header: str = f"""\
# This file is autocompleted by 'contributors-txt',
# using the configuration in '{configuration_file}'.
# Do not modify titles or lines with name / email
# Please verify that your change are stable if you
# modify manually.

"""
    persons = persons_from_shortlog(aliases, shortlog_output)
    with open(output, encoding="utf8") as f:
        current_output = f.read()
    result = update_teams(
        current_output if header in current_output else header + current_output, persons
    )
    return result


# def update_contributors(persons):
#     result = get_team_header(DEFAULT_TEAM_ROLE)
#     for person in sorted(persons.values(), reverse=True):
#         if person.team != DEFAULT_TEAM_ROLE:
#             continue
#         if person.mail in NO_SHOW_MAIL or person.name in NO_SHOW_NAME:
#             continue
#         result += f"- {person}\n"
#     return result


def update_teams(current_result: str, persons: Dict[str, Person]):
    teams = get_teams(persons, exclude_standard=False)
    if not teams:
        return current_result
    current_result = add_email_if_missing(current_result, teams)
    current_result = order_by_commit(current_result, teams)
    return current_result + "\n"


def order_by_commit(current_result, teams) -> str:
    new_teams: List[str] = []
    team_boundary = get_team_boundary(current_result, list(teams.keys()))
    for team_name, team_members in teams.items():
        new_teams.append(
            order_by_commit_in_team(
                current_result, team_boundary, team_members, team_name
            )
        )
    return "".join(new_teams)


def order_by_commit_in_team(
    current_result, team_boundary, team_members, team_name
) -> str:
    logging.debug("Updating team %s", team_name)
    begin, end = team_boundary[team_name]
    new_team = []
    existing_persons = current_result[begin:end].split("\n-")
    logging.debug(existing_persons[0])
    consumed = []
    for team_member in team_members:
        if not person_should_be_shown(team_member):
            continue
        # logging.debug(f"Finding the content for {team_member}")
        person_found = False
        for i, existing_person in enumerate(existing_persons):
            if team_member.mail and team_member.mail in existing_person:
                # logging.debug(f"Placing {team_member.name}: {existing_person}")
                new_team.append(existing_person)
                person_found = True
                consumed.append(i)
                break
            # if team_member.mail is None and team_member.name in existing_person:
            #     logging.debug(f"Placing {team_member.name} by name: {existing_person}")
            #     new_team.append(existing_person)
            #     break
        if not person_found:
            logging.debug("Could not find %s in %s !", team_member, team_name)
            new_team.append(f" {team_member}")
    for i, person_not_found in enumerate(existing_persons):
        if i not in consumed:
            new_team.insert(i, person_not_found)
    return "\n-".join(new_team)


def add_email_if_missing(current_result, teams):
    new_teams: List[str] = []
    team_boundary = get_team_boundary(current_result, list(teams.keys()))
    bound = team_boundary["Header"]
    new_teams.append(current_result[bound[0] : bound[1]])
    for team_name, team_members in teams.items():
        logging.debug("Updating team %s", team_name)
        begin, end = team_boundary[team_name]
        new_team = str(current_result[begin:end])
        for team_member in team_members:
            if not person_should_be_shown(team_member):
                continue
            if team_member.name in current_result[begin:end]:
                if team_member.mail and team_member.mail in current_result[begin:end]:
                    continue
                if team_member.mail:
                    if team_member.name.find(" ") != -1:
                        logging.debug(
                            "For %s in %s: Adding email", team_member, team_name
                        )
                        new_team = new_team.replace(
                            team_member.name, f"{team_member.name} {team_member.mail}"
                        )
                    else:
                        logging.debug(
                            "There's only one word in %s not replacing anything.",
                            team_member.name,
                        )
                    continue
            if team_member.mail is not None and team_member.mail in current_result:
                raise RuntimeError(
                    f"{team_member} already exists in the file but is not in the "
                    f"proper section, it should be {team_name}, please fix "
                    f"manually."
                )
            new_team += line_for_person(team_member)
        new_teams.append(new_team)
    return "".join(new_teams)


def get_team_boundary(
    current_result: str, teams: List[str]
) -> Dict[str, Tuple[int, int]]:
    teams_boundary: Dict[str, Tuple[int, int]] = {}
    last_boundary = 0
    end = len(current_result)
    for i, team in enumerate(teams):
        # logging.debug("Handling %s", (i, team))
        team_name = teams[i - 1] if i > 0 else "Header"
        if team not in current_result:
            teams_boundary[team_name] = (0, end)
        else:
            next_boundary = current_result.find(team)
            teams_boundary[team_name] = (last_boundary, next_boundary)
            last_boundary = next_boundary
    teams_boundary[teams[-1]] = (last_boundary, end)
    return teams_boundary
