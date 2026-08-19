"""Two-stage channel dispatcher.

Stage 1: deterministic rule matching over the team. Cheap, in-process.
Stage 2: only when no agent's rules matched, an injected LLM fallback
callable decides. The callable is injected so this module has zero
dependency on a specific LLM provider.

@mentions bypass both stages entirely.

On an agent-originated re-dispatch, pass `speaker_id` so the agent that
just spoke cannot be selected again by rules or the LLM fallback.
Mentions still can. `always` is a human-turn rule, not a license to
bounce on every teammate reply.
"""

from __future__ import annotations

import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from enum import StrEnum

from rivulet_dispatch.rules import Rule, RuleType, rule_matches

_UNSOLICITED_RULE_TYPES = frozenset({RuleType.KEYWORD, RuleType.REGEX, RuleType.SEMANTIC})
_MENTION_RE = re.compile(r"@([A-Za-z0-9_-]+)")


@dataclass(frozen=True, slots=True)
class LlmFallbackResult:
    """What the injected LLM fallback callable actually did.

    `invoked` tells the caller whether a real LLM call was attempted, as
    distinct from a "no match" outcome reached without ever calling a
    provider. Both look identical from `agent_ids` alone. Only one of
    them costs money.
    """

    agent_ids: list[str]
    invoked: bool


@dataclass(frozen=True, slots=True)
class AgentDispatchInfo:
    agent_id: str
    name: str
    rules: list[Rule] = field(default_factory=list)
    description: str = ""


class DispatchMethod(StrEnum):
    MENTION = "mention"
    DETERMINISTIC = "deterministic"
    LLM = "llm"
    DEFAULT = "default"
    NONE = "none"


@dataclass(frozen=True, slots=True)
class DispatchResult:
    agent_ids: list[str]
    method: DispatchMethod
    llm_invoked: bool = False


LlmFallback = Callable[[str, list[AgentDispatchInfo]], Awaitable[LlmFallbackResult]]


def _is_mention_only(agent: AgentDispatchInfo) -> bool:
    return bool(agent.rules) and all(
        rule.rule_type is RuleType.MENTION_ONLY for rule in agent.rules
    )


def _unsolicited_for_agent_reply(agent: AgentDispatchInfo) -> AgentDispatchInfo | None:
    """What this teammate may match against another agent's message.

    Always-only / mention-only / no-rule agents sit the bounce out.
    Keyword/regex/semantic specialists can still join.
    """
    kept = [rule for rule in agent.rules if rule.rule_type in _UNSOLICITED_RULE_TYPES]
    if not kept:
        return None
    return AgentDispatchInfo(
        agent_id=agent.agent_id,
        name=agent.name,
        rules=kept,
        description=agent.description,
    )


class DispatchEngine:
    def __init__(self, llm_fallback: LlmFallback | None = None) -> None:
        self._llm_fallback = llm_fallback

    def match_mentions(self, message: str, agents: list[AgentDispatchInfo]) -> list[str]:
        mentioned_names = {m.group(1).lower() for m in _MENTION_RE.finditer(message)}
        if not mentioned_names:
            return []
        return [a.agent_id for a in agents if a.name.lower() in mentioned_names]

    def pick_default_teammate(self, agents: list[AgentDispatchInfo]) -> str | None:
        """Who should answer a human message that missed every mention,
        rule, and LLM-fallback pick. Mention-only agents opted out.
        Prefer a teammate named Assistant; otherwise the first remaining.
        """
        eligible = [a for a in agents if not _is_mention_only(a)]
        if not eligible:
            return None
        for agent in eligible:
            if agent.name.lower() == "assistant":
                return agent.agent_id
        return eligible[0].agent_id

    def match_deterministic(self, message: str, agents: list[AgentDispatchInfo]) -> list[str]:
        matched: list[str] = []
        for agent in agents:
            rules_by_priority = sorted(agent.rules, key=lambda r: -r.priority)
            for rule in rules_by_priority:
                if rule.rule_type is RuleType.MENTION_ONLY:
                    continue
                if rule_matches(rule, message):
                    matched.append(agent.agent_id)
                    break
        return matched

    async def dispatch(
        self,
        message: str,
        agents: list[AgentDispatchInfo],
        *,
        speaker_id: str | None = None,
    ) -> DispatchResult:
        if mentioned := self.match_mentions(message, agents):
            return DispatchResult(agent_ids=mentioned, method=DispatchMethod.MENTION)

        if speaker_id is not None:
            candidates: list[AgentDispatchInfo] = []
            for agent in agents:
                if agent.agent_id == speaker_id:
                    continue
                info = _unsolicited_for_agent_reply(agent)
                if info is not None:
                    candidates.append(info)
            if not candidates:
                return DispatchResult(agent_ids=[], method=DispatchMethod.NONE)
            agents = candidates

        if matched := self.match_deterministic(message, agents):
            return DispatchResult(agent_ids=matched, method=DispatchMethod.DETERMINISTIC)

        if self._llm_fallback is None:
            return DispatchResult(agent_ids=[], method=DispatchMethod.NONE)

        fallback_result = await self._llm_fallback(message, agents)
        method = DispatchMethod.LLM if fallback_result.agent_ids else DispatchMethod.NONE
        return DispatchResult(
            agent_ids=fallback_result.agent_ids,
            method=method,
            llm_invoked=fallback_result.invoked,
        )
