"""
Helpers that are copied into each handler folder must stay byte-identical.

Handlers import their own local copy, so a fix applied to one copy silently
leaves the others broken. See docs/ARCHITECTURE.md, "Traps".
"""
from pathlib import Path

import pytest

LAMBDA_DIR = Path(__file__).resolve().parent.parent

# response_utils.py and dynamodb_client.py are deliberately not listed: they
# have real per-handler differences.
COPIED_EVERYWHERE = ["auth_middleware.py", "decimal_utils.py"]


@pytest.mark.parametrize("filename", COPIED_EVERYWHERE)
def test_copies_are_identical(filename):
    copies = sorted(
        p for p in LAMBDA_DIR.rglob(filename) if ".venv" not in p.parts
    )
    assert len(copies) > 1, f"expected several copies of {filename}"

    by_content = {}
    for path in copies:
        by_content.setdefault(path.read_bytes(), []).append(
            str(path.relative_to(LAMBDA_DIR))
        )

    assert len(by_content) == 1, (
        f"{filename} has drifted. Groups of identical copies: "
        f"{list(by_content.values())}"
    )
