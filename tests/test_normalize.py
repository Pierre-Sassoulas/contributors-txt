from __future__ import annotations

import logging
from pathlib import Path

import pytest
from contributors_txt.normalize import main
from pytest_remaster import CaseData, GoldenMaster, discover_test_cases

CASES_DIR = Path(__file__).parent / "normalize_cases"


@pytest.mark.parametrize("case", discover_test_cases(CASES_DIR))  # type: ignore[untyped-decorator]
def test_normalize(
    case: CaseData,
    tmp_path: Path,
    golden_master: GoldenMaster,
    caplog: pytest.LogCaptureFixture,
    recwarn: pytest.WarningsRecorder,
) -> None:
    caplog.set_level(logging.DEBUG)
    output = tmp_path / "out.json"
    main(["-v", "-a", str(case.input / "input.json"), "-o", str(output)])
    golden_master.check(output.read_text(encoding="utf8"), case.input / "expected.json")
    assert not recwarn


@pytest.mark.parametrize("case", discover_test_cases(CASES_DIR))  # type: ignore[untyped-decorator]
def test_normalize_is_idempotent(
    case: CaseData,
    tmp_path: Path,
    golden_master: GoldenMaster,
    caplog: pytest.LogCaptureFixture,
    recwarn: pytest.WarningsRecorder,
) -> None:
    caplog.set_level(logging.DEBUG)
    output = tmp_path / "out.json"
    main(["-v", "-a", str(case.input / "expected.json"), "-o", str(output)])
    golden_master.check(output.read_text(encoding="utf8"), case.input / "expected.json")
    assert not recwarn
