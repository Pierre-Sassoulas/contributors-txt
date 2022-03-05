from unittest.mock import patch

import pytest

from contributors_txt.create_content import create_content


@pytest.mark.parametrize(
    "git_output,expected",
    [
        [
            "1 name <email@net.com>",
            "(email@net.com)",
        ],
        [
            "1 another_name <email@net.com>",
            "- another_name",
        ],
        [
            "\n1 name <aemail@net.com>\n2 another_name <email@net.com>",
            """- another_name (email@net.com)
- name (aemail@net.com)
""",
        ],
    ],
)
def test_basic(git_output: str, expected: str):
    class Mock:
        stdout = git_output.encode()

    with patch("subprocess.run") as subprocess:
        subprocess.return_value = Mock
        result = create_content(aliases=[])
    assert expected in result
