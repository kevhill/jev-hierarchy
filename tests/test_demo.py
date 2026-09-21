from __future__ import annotations

import os

from demo import main


def test_cli_exits_1_when_api_key_missing(monkeypatch, capsys):
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    assert main([]) == 1
    err = capsys.readouterr().err
    assert "TYPESAFE_API_KEY" in err
    assert "console.typesafe.ai/keys" in err


def test_cli_does_not_read_key_from_cwd_files(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("TYPESAFE_API_KEY=should-not-load\n")
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    assert main([]) == 1
    assert os.environ.get("TYPESAFE_API_KEY") is None
