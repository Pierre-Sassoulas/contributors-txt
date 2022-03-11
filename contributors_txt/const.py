from pathlib import Path

HERE = Path(__file__).parent
DEFAULT_CONTRIBUTOR_PATH = "CONTRIBUTORS.txt"
GIT_SHORTLOG = ["git", "shortlog", "--summary", "--numbered", "--email"]
NO_SHOW_MAIL = ["bot@noreply.github.com"]
NO_SHOW_NAME = ["root", "bot"]
