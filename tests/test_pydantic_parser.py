from pathlib import Path

import pytest

from poet.model import Problem

ROOT = Path(__file__).resolve().parents[1]


def test_loads_all_test_cases(subtests: pytest.Subtests) -> None:
    test_cases_dir = ROOT / "examples"
    test_files = sorted(test_cases_dir.glob("*.yaml"))
    assert test_files, "No YAML input examples found."
    for path in test_files:
        with subtests.test(msg="YAML parser", path=path):
            assert Problem.from_yaml_file(path) is not None
