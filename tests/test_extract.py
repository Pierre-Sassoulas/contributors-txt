from __future__ import annotations

import logging
from pathlib import Path

import pytest
from contributors_txt.extract_comment import main
from pytest_remaster import CaseData, GoldenMaster, discover_test_cases

CASES_DIR = Path(__file__).parent / "extract_cases"


@pytest.mark.parametrize("case", discover_test_cases(CASES_DIR))
def test_extract(
    case: CaseData,
    tmp_path: Path,
    golden_master: GoldenMaster,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG)
    output = tmp_path / "out.json"
    main(
        [
            str(case.input / "contributors.txt"),
            "-a",
            str(case.input / "aliases.json"),
            "-o",
            str(output),
        ]
    )
    golden_master.check(output.read_text(encoding="utf8"), case.input / "expected.json")
