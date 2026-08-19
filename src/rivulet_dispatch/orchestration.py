"""Assistant-as-orchestrator: always present, specialists speak on request.

A conversation is routed through the workspace Assistant. Specialists
stay quiet unless someone @mentions them or Assistant hands off.
Keyword rematch must not let Coder's reply wake Writer, who wakes Coder.

If there is no orchestrator id, dispatch is unchanged.
"""

from __future__ import annotations

from rivulet_dispatch.engine import DispatchMethod, DispatchResult

ORCHESTRATOR_NAME = "Assistant"


def is_orchestrator_name(name: str) -> bool:
    return name.lower() == ORCHESTRATOR_NAME.lower()


def apply_orchestrator_lock(
    result: DispatchResult,
    *,
    from_agent_id: str | None,
    orchestrator_id: str | None,
    team_engaged: bool = False,
) -> DispatchResult:
    """Keep specialists off the rematch path. Mentions still win.

    Human turns go to Assistant, who hands off. A specialist's reply
    bounces back to Assistant so they can pick the next step. Assistant's
    own reply does not rematch. They already had a turn; they use handoff
    to call someone. `team_engaged` is kept for callers that still pass
    it. It no longer opens the roster.
    """
    if orchestrator_id is None:
        return result
    if result.method is DispatchMethod.MENTION:
        return result
    _ = team_engaged
    if from_agent_id is None:
        return DispatchResult(
            agent_ids=[orchestrator_id],
            method=DispatchMethod.DEFAULT,
            llm_invoked=result.llm_invoked,
        )
    if from_agent_id == orchestrator_id:
        return DispatchResult(
            agent_ids=[],
            method=DispatchMethod.NONE,
            llm_invoked=result.llm_invoked,
        )
    return DispatchResult(
        agent_ids=[orchestrator_id],
        method=DispatchMethod.DEFAULT,
        llm_invoked=result.llm_invoked,
    )
