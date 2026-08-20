import json
from pathlib import Path

from rivulet_dispatch.cli import main

ROOT = Path(__file__).resolve().parents[1]
TEAM = ROOT / "examples" / "team.json"
TEAM_NO_ASSISTANT = ROOT / "examples" / "team-no-assistant.json"
TEAM_MENTION_ONLY = ROOT / "examples" / "team-mention-only.json"


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


def test_cli_no_assistant_keyword(capsys) -> None:
    rc = main(
        ["--message", "need a postgresql schema", "--team", str(TEAM_NO_ASSISTANT)]
    )
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["method"] == "deterministic"
    assert payload["agent_ids"] == ["dba-1"]


def test_cli_no_assistant_unmatched(capsys) -> None:
    rc = main(["--message", "hello there", "--team", str(TEAM_NO_ASSISTANT)])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["method"] == "none"
    assert payload["agent_ids"] == []


def test_cli_mention_only_roster_mention(capsys) -> None:
    rc = main(["--message", "hey @Archivist", "--team", str(TEAM_MENTION_ONLY)])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["method"] == "mention"
    assert payload["agent_ids"] == ["arch-1"]


def test_cli_mention_only_roster_unmatched(capsys) -> None:
    rc = main(
        ["--message", "need a postgresql schema", "--team", str(TEAM_MENTION_ONLY)]
    )
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["method"] == "none"
    assert payload["agent_ids"] == []
