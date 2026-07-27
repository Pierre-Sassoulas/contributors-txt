from __future__ import annotations

import pytest
from contributors_txt.create_content import line_for_person
from contributors_txt.model import Person


def test_line_for_person_without_mail_raises() -> None:
    person = Person(1, "Alice", None, "Contributors", "")
    with pytest.raises(ValueError, match="does not have an email"):
        line_for_person(person)
