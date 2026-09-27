import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_requirements_txt_matches_pyproject():
    """Vercel installs from pyproject.toml, local setup from requirements.txt;
    they must pin the same versions."""
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    requirements = [
        line.strip()
        for line in (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]

    assert sorted(requirements) == sorted(pyproject["project"]["dependencies"])
