from __future__ import annotations

import json
from pathlib import Path

import pytest
from contributors_txt.create_content import get_aliases
from pytest_remaster import CaseData, GoldenMaster, discover_test_cases

CASES_DIR = Path(__file__).parent / "get_aliases_cases"


@pytest.mark.parametrize("case", discover_test_cases(CASES_DIR))  # type: ignore[untyped-decorator]
def test_get_aliases(
    case: CaseData,
    golden_master: GoldenMaster,
    recwarn: pytest.WarningsRecorder,
) -> None:
    flags_path = case.input / "flags.json"
    flags = json.loads(flags_path.read_text()) if flags_path.exists() else {}
    aliases = get_aliases(case.input / "aliases.json")
    serialized = json.dumps(
        [a._asdict() for a in aliases], indent=2, ensure_ascii=False
    )
    golden_master.check(serialized, case.input / "expected.json")
    expected_warning = flags.get("expect_warning")
    if expected_warning:
        assert len(recwarn) == 1
        assert expected_warning in str(recwarn.pop())
    else:
        assert not recwarn
