"""Demo: route an unmatched message through an injected fake-LLM fallback.

Run: python examples/llm_fallback.py

The fallback is a plain async callable. No network, no vendor SDK; the
engine only sees the `LlmFallbackResult` it returns.
"""

import sys

from rivulet_dispatch import (
    AgentDispatchInfo,
    LlmFallbackResult,
    Rule,
    RuleType,
    dispatch_sync,
)


class FakeLlm:
    """Stands in for an LLM router and records whether it actually ran."""

    def __init__(self) -> None:
        self.calls = 0

    async def __call__(
        self, message: str, agents: list[AgentDispatchInfo]
    ) -> LlmFallbackResult:
        self.calls += 1
        return LlmFallbackResult(agent_ids=["ds-1"], invoked=True)


def build_team() -> list[AgentDispatchInfo]:
    return [
        AgentDispatchInfo(
            agent_id="dba-1",
            name="DBA",
            rules=[Rule(rule_type=RuleType.KEYWORD, pattern=["postgresql"])],
        ),
        AgentDispatchInfo(agent_id="ds-1", name="DataScientist"),
    ]


def main() -> None:
    team = build_team()
    fake_llm = FakeLlm()

    result = dispatch_sync("I need a postgresql schema", team, llm_fallback=fake_llm)
    ran = fake_llm.calls > 0
    print(f"{result.method} llm_invoked={result.llm_invoked} ran={ran}")
    assert result.method == "deterministic"
    assert result.llm_invoked is False
    assert ran is False

    fake_llm.calls = 0
    result = dispatch_sync("why does my model keep overfitting", team, llm_fallback=fake_llm)
    ran = fake_llm.calls > 0
    print(f"{result.method} llm_invoked={result.llm_invoked} ran={ran}")
    assert result.method == "llm"
    assert result.agent_ids == ["ds-1"]
    assert result.llm_invoked is True
    assert ran is True

    sys.exit(0)


if __name__ == "__main__":
    main()
