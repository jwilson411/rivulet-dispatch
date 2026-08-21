import importlib.resources
import tomllib
from pathlib import Path


def test_py_typed_marker_present():
    marker = importlib.resources.files("rivulet_dispatch").joinpath("py.typed")
    assert marker.is_file(), "PEP 561 marker py.typed is missing from rivulet_dispatch"


def test_package_data_includes_py_typed():
    pyproject = Path(__file__).resolve().parent.parent / "pyproject.toml"
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    package_data = data["tool"]["setuptools"]["package-data"]
    assert "py.typed" in package_data["rivulet_dispatch"]
