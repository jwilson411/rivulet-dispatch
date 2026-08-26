import json
from pathlib import Path

import pytest

from rivulet_dispatch.cli import main

ROOT = Path(__file__).resolve().parents[1]
TEAM = ROOT / "examples" / "team.json"
TEAM_NO_ASSISTANT = ROOT / "examples" / "team-no-assistant.json"
TEAM_MENTION_ONLY = ROOT / "examples" / "team-mention-only.json"


def test_cli_version_without_required_flags(capsys) -> None:
    with pytest.raises(SystemExit) as excinfo:
        main(["--version"])
    assert excinfo.value.code == 0
    assert "0.1.0" in capsys.readouterr().out


def test_cli_keyword_match(capsys) -> None:
    rc = main(["--message", "need a postgresql schema", "--team", str(TEAM)])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["method"] == "deterministic"
    # Assistant's always rule and DBA's keyword both fire. The lock is
    # what collapses this to one specialist.
    assert payload["agent_ids"] == ["asst-1", "dba-1"]


def test_cli_default_output_is_single_line(capsys) -> None:
    rc = main(["--message", "need a postgresql schema", "--team", str(TEAM)])
    assert rc == 0
    out = capsys.readouterr().out
    printed = out.rstrip("\n")
    assert "\n" not in printed
    payload = json.loads(printed)
    assert payload["method"] == "deterministic"
    assert payload["agent_ids"] == ["asst-1", "dba-1"]


def test_cli_pretty_output_is_indented(capsys) -> None:
    rc = main(
        ["--message", "need a postgresql schema", "--team", str(TEAM), "--pretty"]
    )
    assert rc == 0
    out = capsys.readouterr().out
    printed = out.rstrip("\n")
    assert "\n}" in printed
    payload = json.loads(printed)
    assert payload["method"] == "deterministic"
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


def test_cli_missing_team_file(capsys, tmp_path) -> None:
    rc = main(
        ["--message", "hello", "--team", str(tmp_path / "does-not-exist.json")]
    )
    assert rc == 2
    captured = capsys.readouterr()
    lines = [line for line in captured.err.splitlines() if line]
    assert len(lines) == 1
    assert "Traceback" not in captured.err
    assert "Traceback" not in captured.out


def test_cli_invalid_team_json(capsys, tmp_path) -> None:
    bad = tmp_path / "team.json"
    bad.write_text("{not valid json", encoding="utf-8")
    rc = main(["--message", "hello", "--team", str(bad)])
    assert rc == 2
    captured = capsys.readouterr()
    lines = [line for line in captured.err.splitlines() if line]
    assert len(lines) == 1
    assert "Traceback" not in captured.err
    assert "Traceback" not in captured.out


def test_cli_mention_only_roster_unmatched(capsys) -> None:
    rc = main(
        ["--message", "need a postgresql schema", "--team", str(TEAM_MENTION_ONLY)]
    )
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["method"] == "none"
    assert payload["agent_ids"] == []


def test_cli_agent_missing_id(capsys, tmp_path) -> None:
    team = tmp_path / "team.json"
    team.write_text(
        json.dumps([{"name": "Assistant", "rules": []}]), encoding="utf-8"
    )
    rc = main(["--message", "hello", "--team", str(team)])
    assert rc == 2
    captured = capsys.readouterr()
    lines = [line for line in captured.err.splitlines() if line]
    assert len(lines) == 1
    assert lines[0].startswith("error:")
    assert "Traceback" not in captured.err
    assert "Traceback" not in captured.out


def test_cli_agent_missing_name(capsys, tmp_path) -> None:
    team = tmp_path / "team.json"
    team.write_text(
        json.dumps([{"id": "asst-1", "rules": []}]), encoding="utf-8"
    )
    rc = main(["--message", "hello", "--team", str(team)])
    assert rc == 2
    captured = capsys.readouterr()
    lines = [line for line in captured.err.splitlines() if line]
    assert len(lines) == 1
    assert lines[0].startswith("error:")
    assert "Traceback" not in captured.err
    assert "Traceback" not in captured.out


def test_team_schema_file_exists() -> None:
    schema = json.loads(
        (ROOT / "examples" / "team.schema.json").read_text(encoding="utf-8")
    )
    assert isinstance(schema, dict)
    assert "$schema" in schema
    assert schema["type"] == "array"
