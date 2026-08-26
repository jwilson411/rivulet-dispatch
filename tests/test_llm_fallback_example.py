"""llm_invoked is true only when the injected fallback callable ran."""

import importlib.util
import subprocess
import sys
from pathlib import Path

from rivulet_dispatch import DispatchMethod, dispatch_sync

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "examples" / "llm_fallback.py"


def _load_example():
    spec = importlib.util.spec_from_file_location("llm_fallback_example", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_keyword_match_skips_fallback() -> None:
    example = _load_example()
    fake_llm = example.FakeLlm()
    result = dispatch_sync(
        "I need a postgresql schema", example.build_team(), llm_fallback=fake_llm
    )
    assert result.method is DispatchMethod.DETERMINISTIC
    assert result.agent_ids == ["dba-1"]
    assert result.llm_invoked is False
    assert fake_llm.calls == 0


def test_unmatched_message_runs_fallback() -> None:
    example = _load_example()
    fake_llm = example.FakeLlm()
    result = dispatch_sync(
        "why does my model keep overfitting", example.build_team(), llm_fallback=fake_llm
    )
    assert result.method is DispatchMethod.LLM
    assert result.agent_ids == ["ds-1"]
    assert result.llm_invoked is True
    assert fake_llm.calls == 1


def test_example_script_runs_and_prints_both_lines() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=ROOT,
        capture_output=True,
    )
    assert result.returncode == 0
    assert b"deterministic llm_invoked=False ran=False" in result.stdout
    assert b"llm llm_invoked=True ran=True" in result.stdout
