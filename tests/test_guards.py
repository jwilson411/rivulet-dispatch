from datetime import UTC, datetime, timedelta

from rivulet_dispatch.guards import LoopGuard


def test_turn_limit_pauses() -> None:
    guard = LoopGuard(turn_limit=3, cycle_threshold=99)
    assert guard.record_agent_message(from_agent_id=None, to_agent_id="a") is None
    assert guard.record_agent_message(from_agent_id="a", to_agent_id="b") is None
    pause = guard.record_agent_message(from_agent_id="b", to_agent_id="a")
    assert pause is not None
    assert pause.reason == "turn_limit"
    assert guard.paused is True


def test_cycle_detection_pauses_repeating_pair() -> None:
    guard = LoopGuard(turn_limit=99, cycle_window=8, cycle_threshold=3)
    assert guard.record_agent_message(from_agent_id="a", to_agent_id="b") is None
    assert guard.record_agent_message(from_agent_id="a", to_agent_id="b") is None
    pause = guard.record_agent_message(from_agent_id="a", to_agent_id="b")
    assert pause is not None
    assert pause.reason == "cycle_detected"
    assert "a" in pause.message and "b" in pause.message


def test_human_reset_clears_pause() -> None:
    guard = LoopGuard(turn_limit=1)
    assert guard.record_agent_message(from_agent_id=None, to_agent_id="a") is not None
    guard.reset()
    assert guard.paused is False
    assert guard.record_agent_message(from_agent_id=None, to_agent_id="a") is not None


def test_timeout_pauses() -> None:
    start = datetime(2026, 8, 19, 12, 0, tzinfo=UTC)
    guard = LoopGuard(turn_limit=99, cycle_threshold=99, timeout_minutes=30)
    assert guard.record_agent_message(from_agent_id=None, to_agent_id="a", now=start) is None
    later = start + timedelta(minutes=31)
    pause = guard.record_agent_message(from_agent_id="a", to_agent_id="b", now=later)
    assert pause is not None
    assert pause.reason == "timeout"


def test_already_paused_stays_paused() -> None:
    guard = LoopGuard(turn_limit=1)
    first = guard.record_agent_message(from_agent_id=None, to_agent_id="a")
    second = guard.record_agent_message(from_agent_id="a", to_agent_id="b")
    assert first is not None
    assert second is not None
    assert second.reason == "turn_limit"
