from __future__ import annotations

import pytest
from contributors_txt.create_content import line_for_person
from contributors_txt.model import Person


def test_add_with_different_mails_raises() -> None:
    person = Person(1, "Alice", "alice@example.com", "Contributors", "")
    other = Person(2, "Alice", "alice@corp.example.com", "Contributors", "")
    with pytest.raises(RuntimeError, match="Mails are not the same"):
        person + other  # pylint: disable=pointless-statement


def test_add_with_different_teams_raises() -> None:
    person = Person(1, "Alice", "alice@example.com", "Maintainers", "")
    other = Person(2, "Alice", "alice@example.com", "Contributors", "")
    with pytest.raises(RuntimeError, match="two teams at once"):
        person + other  # pylint: disable=pointless-statement


def test_line_for_person_without_mail_raises() -> None:
    person = Person(1, "Alice", None, "Contributors", "")
    with pytest.raises(ValueError, match="does not have an email"):
        line_for_person(person)
