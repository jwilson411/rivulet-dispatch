import json
from pathlib import Path

from rivulet_dispatch.cli import main

TEAM = Path(__file__).resolve().parents[1] / "examples" / "team.json"


def test_cli_keyword_match(capsys) -> None:
    rc = main(["--message", "need a postgresql schema", "--team", str(TEAM)])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["method"] == "deterministic"
    # Assistant's always rule and DBA's keyword both fire. The lock is
    # what collapses this to one specialist.
    assert payload["agent_ids"] == ["asst-1", "dba-1"]


def test_cli_orchestrator_lock_sends_human_to_assistant(capsys) -> None:
    rc = main(
        [
            "--message",
            "need a postgresql schema",
            "--team",
            str(TEAM),
            "--orchestrator",
            "Assistant",
        ]
    )
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["method"] == "default"
    assert payload["agent_ids"] == ["asst-1"]


def test_cli_mention_only(capsys) -> None:
    rc = main(["--message", "hey @Silent", "--team", str(TEAM)])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["method"] == "mention"
    assert payload["agent_ids"] == ["silent-1"]
