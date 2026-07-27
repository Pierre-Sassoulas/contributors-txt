from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from contributors_txt.aliases import get_aliases
from contributors_txt.update_content import update_content
from pytest_remaster import CaseData, GoldenMaster, discover_test_cases

CASES_DIR = Path(__file__).parent / "update_cases"


@pytest.mark.parametrize("case", discover_test_cases(CASES_DIR))
def test_update_content(
    case: CaseData,
    golden_master: GoldenMaster,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    flags_path = case.input / "flags.json"
    flags = json.loads(flags_path.read_text()) if flags_path.exists() else {}
    configuration_file = flags.get("configuration_file", "aliases.json")
    contributors_path = tmp_path / "CONTRIBUTORS.txt"
    shutil.copy(case.input / "contributors.txt", contributors_path)
    # The aliases file is copied to the tmp dir (and the test runs from there)
    # because update_content saves auto-merged aliases back into it.
    aliases_path = tmp_path / configuration_file
    aliases_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(case.input / "aliases.json", aliases_path)
    monkeypatch.chdir(tmp_path)
    aliases = get_aliases(aliases_path)
    shortlog = (case.input / "shortlog").read_text(encoding="utf8")
    kwargs = {
        "output": contributors_path,
        "aliases": aliases,
        "shortlog_output": shortlog,
        "configuration_file": configuration_file,
        "no_bots": flags.get("no_bots", False),
    }
    if flags.get("expect_error"):
        with pytest.raises(RuntimeError) as exc_info:
            update_content(**kwargs)
        golden_master.check(str(exc_info.value), case.input / "expected.txt")
        return
    result = update_content(**kwargs)
    golden_master.check(
        _annotate_with_commit_counts(result, shortlog), case.input / "expected.txt"
    )
    if flags.get("check_aliases"):
        golden_master.check(
            aliases_path.read_text(encoding="utf8"),
            case.input / "expected_aliases.json",
        )


def _annotate_with_commit_counts(result: str, shortlog: str) -> str:
    """Append ``# N commits`` to each contributor line, for debug readability."""
    counts: dict[str, int] = {}
    for line in shortlog.splitlines():
        parts = line.split()
        if len(parts) < 2 or not parts[-1].startswith("<"):
            continue
        mail = parts[-1][1:-1]
        counts[mail] = counts.get(mail, 0) + int(parts[0])
    return "".join(
        _annotate_line(line, counts) for line in result.splitlines(keepends=True)
    )


def _annotate_line(line: str, counts: dict[str, int]) -> str:
    if not line.startswith("- "):
        return line
    for mail, count in counts.items():
        if f"<{mail}>" in line:
            return f"{line.rstrip(chr(10))}  # {count} commits\n"
    return line
