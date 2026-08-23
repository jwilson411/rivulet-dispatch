import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "examples" / "loop.py"


def test_loop_example_prints_cycle_detected() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=ROOT,
        capture_output=True,
    )
    assert result.returncode == 0
    assert b"cycle_detected" in result.stdout
