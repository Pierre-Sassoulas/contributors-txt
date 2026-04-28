from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from contributors_txt.create_content import get_aliases
from contributors_txt.update_content import update_content
from pytest_remaster import CaseData, GoldenMaster, discover_test_cases

CASES_DIR = Path(__file__).parent / "update_cases"


@pytest.mark.parametrize("case", discover_test_cases(CASES_DIR))
def test_update_content(
    case: CaseData, golden_master: GoldenMaster, tmp_path: Path
) -> None:
    flags_path = case.input / "flags.json"
    flags = json.loads(flags_path.read_text()) if flags_path.exists() else {}
    contributors_path = tmp_path / "CONTRIBUTORS.txt"
    shutil.copy(case.input / "contributors.txt", contributors_path)
    aliases = get_aliases(case.input / "aliases.json")
    shortlog = (case.input / "shortlog").read_text(encoding="utf8")
    result = update_content(
        output=contributors_path,
        aliases=aliases,
        shortlog_output=shortlog,
        configuration_file=flags.get("configuration_file", "aliases.json"),
        no_bots=flags.get("no_bots", False),
    )
    golden_master.check(result, case.input / "expected.txt")
