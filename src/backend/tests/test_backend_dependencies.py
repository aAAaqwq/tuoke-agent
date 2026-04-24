import tomllib
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PYPROJECT_PATH = PROJECT_ROOT / "pyproject.toml"


def test_upload_routes_require_python_multipart_runtime_dependency() -> None:
    with PYPROJECT_PATH.open("rb") as file:
        pyproject = tomllib.load(file)

    dependencies = pyproject["project"]["dependencies"]

    assert any(dependency.startswith("python-multipart") for dependency in dependencies)


def test_pytest_default_config_enforces_backend_coverage_gate() -> None:
    with PYPROJECT_PATH.open("rb") as file:
        pyproject = tomllib.load(file)

    pytest_options = pyproject["tool"]["pytest"]["ini_options"]
    addopts = pytest_options["addopts"]

    assert "--cov=app" in addopts
    assert "--cov-report=term-missing:skip-covered" in addopts
    assert "--cov-fail-under=80" in addopts
