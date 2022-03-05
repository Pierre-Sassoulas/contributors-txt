from pathlib import Path

HERE = Path(__file__).parent
ALIASES_FILE = HERE / ".copyrigth_aliases.json"
DEFAULT_CONTRIBUTOR_PATH = HERE.parent / "CONTRIBUTORS.txt"
GIT_SHORTLOG = ["git", "shortlog", "--summary", "--numbered", "--email"]
NO_SHOW_MAIL = ["bot@noreply.github.com"]
NO_SHOW_NAME = ["root"]
