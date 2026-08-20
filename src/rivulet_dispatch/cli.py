"""Print a dispatch decision as JSON."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from rivulet_dispatch.engine import (
    AgentDispatchInfo,
    DispatchResult,
    dispatch_sync,
)
from rivulet_dispatch.orchestration import apply_orchestrator_lock
from rivulet_dispatch.rules import Rule, RuleType


def _load_team(path: Path) -> list[AgentDispatchInfo]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    agents: list[AgentDispatchInfo] = []
    for item in raw:
        rules = [
            Rule(
                rule_type=RuleType(rule["rule_type"]),
                pattern=rule.get("pattern", ""),
                priority=int(rule.get("priority", 0)),
            )
            for rule in item.get("rules", [])
        ]
        agents.append(
            AgentDispatchInfo(
                agent_id=item["id"],
                name=item["name"],
                rules=rules,
                description=item.get("description", ""),
            )
        )
    return agents


def _result_to_json(result: DispatchResult) -> str:
    return json.dumps(
        {
            "agent_ids": result.agent_ids,
            "method": result.method.value,
            "llm_invoked": result.llm_invoked,
        }
    )


def _run(args: argparse.Namespace) -> int:
    agents = _load_team(Path(args.team))
    result = dispatch_sync(args.message, agents, speaker_id=args.speaker_id)
    if args.orchestrator:
        orch = next((a for a in agents if a.name.lower() == args.orchestrator.lower()), None)
        result = apply_orchestrator_lock(
            result,
            from_agent_id=args.speaker_id,
            orchestrator_id=None if orch is None else orch.agent_id,
        )
    print(_result_to_json(result))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Route a message against a team JSON file.")
    parser.add_argument("--message", required=True, help="Incoming chat message")
    parser.add_argument("--team", required=True, help="Path to team JSON")
    parser.add_argument("--speaker-id", default=None, help="Previous speaker agent id, if any")
    parser.add_argument(
        "--orchestrator",
        default=None,
        help="Apply the one-specialist lock using this agent name (usually Assistant)",
    )
    args = parser.parse_args(argv)
    return _run(args)


if __name__ == "__main__":
    sys.exit(main())
