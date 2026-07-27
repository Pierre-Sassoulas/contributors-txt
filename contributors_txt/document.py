"""Structural model of a CONTRIBUTORS file.

parse() is lossless: parse(text).render() == text. Sections and entries
are mutated as objects, then rendered back, so no operation can match or
replace text outside the entry it targets.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

MAIL_REGEX = re.compile(r"<([^<>]+)>")
UNDERLINE_REGEX = re.compile(r"^-{2,}$")


@dataclass
class Entry:
    """A '- Name <mail>' line plus its continuation lines."""

    lines: list[str]

    @property
    def mail(self) -> str | None:
        match = MAIL_REGEX.search(self.lines[0])
        return match.group(1) if match else None

    def matches_name(self, name: str) -> bool:
        prefix = f"- {name}"
        if not self.lines[0].startswith(prefix):
            return False
        rest = self.lines[0][len(prefix) :]
        return not rest or not rest[0].isalnum()

    def add_mail_after_name(self, name: str, mail: str) -> None:
        self.lines[0] = self.lines[0].replace(name, f"{name} <{mail}>", 1)


@dataclass
class Section:
    """A titled block of the file; the leading untitled block has title None."""

    title: str | None
    items: list[Entry | str] = field(default_factory=list)

    @property
    def entries(self) -> list[Entry]:
        return [item for item in self.items if isinstance(item, Entry)]


@dataclass
class Document:
    sections: list[Section]

    def entries(self) -> list[Entry]:
        return [entry for section in self.sections for entry in section.entries]

    def section(self, title: str) -> Section | None:
        for section in self.sections:
            if section.title == title:
                return section
        return None

    def add_section(self, title: str) -> Section:
        last_items = self.sections[-1].items if self.sections else []
        if last_items and (
            not isinstance(last_items[-1], str) or last_items[-1].strip()
        ):
            last_items.append("")
        section = Section(title, [title, "-" * len(title)])
        self.sections.append(section)
        return section

    def render(self) -> str:
        lines: list[str] = []
        for section in self.sections:
            for item in section.items:
                if isinstance(item, Entry):
                    lines.extend(item.lines)
                else:
                    lines.append(item)
        return "\n".join(lines)


def parse(text: str) -> Document:
    lines = text.split("\n")
    sections = [Section(None)]
    i = 0
    while i < len(lines):
        if _is_section_title(lines, i):
            sections.append(Section(lines[i], [lines[i], lines[i + 1]]))
            i += 2
            continue
        if lines[i].startswith("- "):
            j = i + 1
            while (
                j < len(lines)
                and lines[j]
                and not lines[j].startswith("- ")
                and not _is_section_title(lines, j)
            ):
                j += 1
            sections[-1].items.append(Entry(lines[i:j]))
            i = j
            continue
        sections[-1].items.append(lines[i])
        i += 1
    return Document(sections)


def _is_section_title(lines: list[str], i: int) -> bool:
    return (
        i + 1 < len(lines)
        and bool(UNDERLINE_REGEX.match(lines[i + 1]))
        and bool(lines[i].strip())
        and not lines[i].startswith("- ")
    )
