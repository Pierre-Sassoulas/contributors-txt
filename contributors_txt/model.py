from __future__ import annotations

from typing import NamedTuple


class Alias(NamedTuple):
    mails: list[str]
    authoritative_mail: str | None
    name: str
    team: str
    comment: str | None = None


class Person(NamedTuple):
    number_of_commits: int
    name: str
    mail: str | None
    team: str
    comment: str | None

    def __gt__(self, other: Person) -> bool:  # type: ignore[override]
        """Permit sorting contributors by number of commits."""
        return self.number_of_commits.__gt__(other.number_of_commits)

    def get_template(self, template: str, other: Person | None = None) -> str:
        template += f'"{self.mail}": '
        template += "{"
        mail = self.mail if self.mail is not None else ""
        if other:
            other_mail = other.mail if other.mail is not None else ""
            return f"""{template}
            "mails": ["{mail}","{other_mail}"],
            "name": "{self.name}"
"""
        return f"""{template}
            "mails": ["{mail}"],
            "name": "{self.name}"
"""

    def __repr__(self) -> str:
        # return f"{self.name=} {self.mail=} {self.number_of_commits=} {self.team=}"
        return (
            f"name={self.name} mail={self.mail} "
            f"number_of_commits={self.number_of_commits} team={self.team}"
        )

    def __str__(self) -> str:
        result = f"{self.name}"
        if self.mail:
            result += f" <{self.mail}>"
        if self.comment:
            result += f"{self.comment}"
        return result
