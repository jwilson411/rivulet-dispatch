from rivulet_dispatch.engine import DispatchMethod, DispatchResult
from rivulet_dispatch.orchestration import apply_orchestrator_lock


def test_lock_routes_human_turns_to_orchestrator_only() -> None:
    result = apply_orchestrator_lock(
        DispatchResult(agent_ids=["coder", "assistant"], method=DispatchMethod.DETERMINISTIC),
        from_agent_id=None,
        orchestrator_id="assistant",
    )
    assert result.agent_ids == ["assistant"]
    assert result.method is DispatchMethod.DEFAULT


def test_lock_drops_unsolicited_agent_rematch() -> None:
    result = apply_orchestrator_lock(
        DispatchResult(agent_ids=["coder"], method=DispatchMethod.DETERMINISTIC),
        from_agent_id="assistant",
        orchestrator_id="assistant",
    )
    assert result.agent_ids == []
    assert result.method is DispatchMethod.NONE


def test_lock_sends_specialist_reply_back_to_assistant() -> None:
    result = apply_orchestrator_lock(
        DispatchResult(agent_ids=["writer"], method=DispatchMethod.DETERMINISTIC),
        from_agent_id="coder",
        orchestrator_id="assistant",
    )
    assert result.agent_ids == ["assistant"]
    assert result.method is DispatchMethod.DEFAULT


def test_lock_preserves_mentions() -> None:
    result = apply_orchestrator_lock(
        DispatchResult(agent_ids=["coder"], method=DispatchMethod.MENTION),
        from_agent_id=None,
        orchestrator_id="assistant",
    )
    assert result.agent_ids == ["coder"]
    assert result.method is DispatchMethod.MENTION


def test_lock_is_noop_without_orchestrator() -> None:
    original = DispatchResult(agent_ids=["coder"], method=DispatchMethod.DETERMINISTIC)
    assert (
        apply_orchestrator_lock(original, from_agent_id=None, orchestrator_id=None) is original
    )
