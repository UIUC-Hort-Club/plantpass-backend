"""
The Lambda zips must be reproducible and complete.

Reproducible: the same code gives the same bytes, or every deploy re-uploads
every function and a pull request's plan can never say "No changes".
Complete: a handler folder that is not packaged deploys nothing.
"""
import importlib.util
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

spec = importlib.util.spec_from_file_location("package", ROOT / "scripts" / "package.py")
package = importlib.util.module_from_spec(spec)
spec.loader.exec_module(package)


def test_two_builds_are_byte_identical(tmp_path):
    package.build(tmp_path / "a")
    package.build(tmp_path / "b")
    first = {p.name: p.read_bytes() for p in (tmp_path / "a").iterdir()}
    second = {p.name: p.read_bytes() for p in (tmp_path / "b").iterdir()}
    assert first == second and len(first) == 10


def test_every_handler_folder_is_packaged_with_all_its_python_files(tmp_path):
    handler_folders = sorted(p.parent.name for p in (ROOT / "lambda").glob("*/lambda_handler.py"))
    assert sorted(package.ZIPS) == handler_folders

    package.build(tmp_path)
    for folder, name in package.ZIPS.items():
        with zipfile.ZipFile(tmp_path / name) as archive:
            assert sorted(archive.namelist()) == sorted(
                p.name for p in (ROOT / "lambda" / folder).glob("*.py")
            )
            source = (ROOT / "lambda" / folder / "lambda_handler.py").read_bytes()
            assert archive.read("lambda_handler.py") == source


def test_zip_names_are_the_ones_terraform_is_given():
    tfvars = (ROOT / "terraform" / "terraform.tfvars").read_text()
    expected = set(re.findall(r'_lambda_zip_path\s*=\s*"([^"]+)"', tfvars))
    assert set(package.ZIPS.values()) == expected
