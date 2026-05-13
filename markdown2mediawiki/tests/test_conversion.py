import sys
from pathlib import Path

import pytest
from click.testing import CliRunner

sys.path.insert(0, str(Path(__file__).parent.parent))
from markdown2mediawiki import main  # noqa: E402

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def fixture_cases():
    cases = []
    for md_file in sorted(FIXTURES_DIR.glob("*.md")):
        args_file = md_file.with_suffix(".args")
        extra_args = args_file.read_text().split() if args_file.exists() else []
        cases.append(pytest.param(md_file, extra_args, id=md_file.stem))
    return cases


@pytest.mark.parametrize("input_file,extra_args", fixture_cases())
def test_fixture(input_file, extra_args):
    expected = input_file.with_suffix(".mediawiki").read_text()
    runner = CliRunner()
    result = runner.invoke(main, [str(input_file)] + extra_args)
    assert result.exit_code == 0, result.output
    assert result.output == expected
