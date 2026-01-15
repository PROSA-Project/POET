from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

from poet.model import Problem


def test_loads_all_test_cases(subtests) -> None:
    test_cases_dir = ROOT / "examples"
    test_files = sorted(test_cases_dir.glob("*.yaml"))
    assert test_files, "No YAML input examples found."
    for path in test_files:
        with subtests.test(msg="YAML parser", path=path):
            assert Problem.from_yaml_file(path) is not None
