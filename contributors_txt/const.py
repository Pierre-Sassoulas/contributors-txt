from pathlib import Path

HERE = Path(__file__).parent
DEFAULT_CONTRIBUTOR_PATH = "CONTRIBUTORS.txt"
GIT_SHORTLOG = ["git", "shortlog", "--summary", "--numbered", "--email"]
NO_SHOW_MAIL = ["bot@noreply.github.com"]
NO_SHOW_NAME = ["root", "bot", "root@clnstor.am.local", "amdev@AMDEV-WS01.cisco.com"]
DEFAULT_TEAM_ROLE = "Contributors"

# Substrings that mark a contributor as an automation. Activated by --no-bots.
# The "[bot]" suffix is GitHub's convention for App accounts (dependabot[bot],
# pre-commit-ci[bot], github-actions[bot], etc.). Copilot and Claude commit
# under regular-looking accounts, so they're matched explicitly.
KNOWN_BOT_NAME_SUBSTRINGS = ["[bot]"]
KNOWN_BOT_MAIL_SUBSTRINGS = [
    "[bot]@",
    "+Copilot@users.noreply.github.com",
    "noreply@anthropic.com",
]
