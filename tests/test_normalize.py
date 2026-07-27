from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest
from contributors_txt.normalize import main
from pytest_remaster import CaseData, GoldenMaster, discover_test_cases

CASES_DIR = Path(__file__).parent / "normalize_cases"


@pytest.mark.parametrize("case", discover_test_cases(CASES_DIR))
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


def test_normalize_in_place_by_default(tmp_path: Path) -> None:
    """Without -o the aliases file itself is normalized, not CONTRIBUTORS.txt."""
    aliases_path = tmp_path / "aliases.json"
    source = CASES_DIR / "legacy_format" / "expected.json"
    aliases_path.write_text(source.read_text(encoding="utf8"), encoding="utf8")
    main(["-a", str(aliases_path)])
    assert json.loads(aliases_path.read_text(encoding="utf8")) == json.loads(
        source.read_text(encoding="utf8")
    )
    assert not (tmp_path / "CONTRIBUTORS.txt").exists()


def test_normalize_requires_aliases_file() -> None:
    with pytest.raises(SystemExit):
        main([])


@pytest.mark.parametrize("case", discover_test_cases(CASES_DIR))
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
