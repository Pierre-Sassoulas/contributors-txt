from __future__ import annotations

import json
from pathlib import Path

import pytest
from contributors_txt.create_content import create_content
from pytest_remaster import CaseData, GoldenMaster, discover_test_cases

CASES_DIR = Path(__file__).parent / "create_content_cases"


@pytest.mark.parametrize("case", discover_test_cases(CASES_DIR))  # type: ignore[untyped-decorator]
def test_create_content(case: CaseData, golden_master: GoldenMaster) -> None:
    shortlog = (case.input / "shortlog").read_text(encoding="utf8")
    flags_path = case.input / "flags.json"
    flags = json.loads(flags_path.read_text()) if flags_path.exists() else {}
    result = create_content(
        aliases=[],
        shortlog_output=shortlog,
        configuration_file="foo.conf",
        no_bots=flags.get("no_bots", False),
    )
    golden_master.check(result, case.input / "expected.txt")
