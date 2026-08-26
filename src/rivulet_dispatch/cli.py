"""Print a dispatch decision as JSON."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from rivulet_dispatch import __version__
from rivulet_dispatch.engine import (
    AgentDispatchInfo,
    DispatchResult,
    dispatch_sync,
)
from rivulet_dispatch.orchestration import apply_orchestrator_lock
from rivulet_dispatch.rules import Rule, RuleType


def _validate_team(raw: object) -> None:
    # Required-key walk over the parsed JSON. The full shape is documented
    # in examples/team.schema.json; this only checks what the loader below
    # would otherwise KeyError on.
    if not isinstance(raw, list):
        raise ValueError("team file must be a JSON array of agents")
    for i, item in enumerate(raw):
        if not isinstance(item, dict):
            raise ValueError(f"agent {i} must be a JSON object")
        for key in ("id", "name"):
            value = item.get(key)
            if not isinstance(value, str) or not value:
                raise ValueError(f"agent {i} must have a non-empty string {key!r}")
        rules = item.get("rules", [])
        if not isinstance(rules, list):
            raise ValueError(f"agent {i} 'rules' must be an array")
        for j, rule in enumerate(rules):
            if not isinstance(rule, dict) or "rule_type" not in rule:
                raise ValueError(f"agent {i} rule {j} must be an object with 'rule_type'")


def _load_team(path: Path) -> list[AgentDispatchInfo]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    _validate_team(raw)
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


def _result_to_json(result: DispatchResult, indent: int | None = None) -> str:
    return json.dumps(
        {
            "agent_ids": result.agent_ids,
            "method": result.method.value,
            "llm_invoked": result.llm_invoked,
        },
        indent=indent,
    )


def _run(args: argparse.Namespace) -> int:
    try:
        agents = _load_team(Path(args.team))
    except FileNotFoundError:
        print(f"error: team file not found: {args.team}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"error: invalid JSON in team file {args.team}: {exc}", file=sys.stderr)
        return 2
    except ValueError as exc:
        print(f"error: invalid team file {args.team}: {exc}", file=sys.stderr)
        return 2
    result = dispatch_sync(args.message, agents, speaker_id=args.speaker_id)
    if args.orchestrator:
        orch = next((a for a in agents if a.name.lower() == args.orchestrator.lower()), None)
        result = apply_orchestrator_lock(
            result,
            from_agent_id=args.speaker_id,
            orchestrator_id=None if orch is None else orch.agent_id,
        )
    print(_result_to_json(result, indent=2 if args.pretty else None))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Route a message against a team JSON file.")
    # action="version" exits before the required-argument check, so
    # --version works without --message/--team.
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    parser.add_argument("--message", required=True, help="Incoming chat message")
    parser.add_argument("--team", required=True, help="Path to team JSON")
    parser.add_argument("--speaker-id", default=None, help="Previous speaker agent id, if any")
    parser.add_argument(
        "--orchestrator",
        default=None,
        help="Apply the one-specialist lock using this agent name (usually Assistant)",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Print indented JSON instead of a single compact line",
    )
    args = parser.parse_args(argv)
    return _run(args)


if __name__ == "__main__":
    sys.exit(main())
