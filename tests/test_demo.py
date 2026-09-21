from __future__ import annotations

import os
import re

from demo import HIERARCHY, Post, _bar, main, render_tree
from jev_hierarchy import WalkResult, outside_choice_id


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


def test_bar_is_empty_only_at_zero():
    assert _bar(0.0).count("█") == 0
    assert _bar(0.01).count("█") >= 1
    assert _bar(0.02).count("█") >= 1


def test_bar_is_full_only_at_one():
    width = 18
    assert _bar(1.0, width).count("█") == width
    assert _bar(0.96, width).count("█") < width
    assert _bar(0.99, width).count("█") < width


def _node(label: str, root=HIERARCHY):
    if root.label == label:
        return root
    for child in root.children:
        found = _node(label, child)
        if found is not None:
            return found
    return None


def test_outside_choice_render_shows_root_absorbed_and_share_of_covered():
    news = HIERARCHY
    rec = _node("Recreation")
    talk = _node("Talk")
    guns = _node("Guns")
    autos = _node("Autos")
    baseball = _node("Baseball")
    result = WalkResult(
        queried=[news.id, rec.id, talk.id],
        node_mass={
            news.id: 1.0,
            rec.id: 0.02,
            talk.id: 0.96,
            guns.id: 0.96,
            autos.id: 0.0,
            baseball.id: 0.0,
            outside_choice_id(news.id): 0.02,
            outside_choice_id(rec.id): 0.02,
            outside_choice_id(talk.id): 0.0,
        },
        absorbed_mass={
            news.id: 0.96,
            rec.id: 0.0,
            talk.id: 0.96,
            guns.id: 0.96,
            autos.id: 0.0,
            baseball.id: 0.0,
        },
    )
    post = Post(id="p4", gold_label="Guns", text="x")
    out = render_tree(post, result, show_coverage=True)
    assert "coverage=96.0%" in out
    news_line = next(line for line in out.splitlines() if line.startswith("News"))
    assert "100.0%" in news_line
    assert "abs= 96.0%" in news_line
    guns_line = next(line for line in out.splitlines() if "└─ Guns" in line)
    assert re.search(r"96\.0%.*100\.0%", guns_line)
    talk_line = next(line for line in out.splitlines() if "└─ Talk" in line)
    assert re.search(r"96\.0%.*100\.0%", talk_line)
    rec_line = next(line for line in out.splitlines() if "└─ Recreation" in line)
    assert re.search(r"2\.0%.*0\.0%", rec_line)
    none_lines = [line for line in out.splitlines() if "none" in line]
    assert none_lines
    assert all("abs=" not in line for line in none_lines)
    assert "abs=" not in rec_line
    assert "abs=" not in guns_line


def _bar_col(line: str) -> int:
    for i, ch in enumerate(line):
        if ch in "█░":
            return i
    raise AssertionError(f"no bar in {line!r}")


def test_none_rows_align_bars_with_named_siblings():
    news = HIERARCHY
    rec = _node("Recreation")
    talk = _node("Talk")
    guns = _node("Guns")
    result = WalkResult(
        queried=[news.id, rec.id, talk.id],
        node_mass={
            news.id: 1.0,
            rec.id: 0.02,
            talk.id: 0.96,
            guns.id: 0.96,
            outside_choice_id(news.id): 0.02,
            outside_choice_id(rec.id): 0.02,
            outside_choice_id(talk.id): 0.0,
        },
        absorbed_mass={
            news.id: 0.96,
            rec.id: 0.0,
            talk.id: 0.96,
            guns.id: 0.96,
        },
    )
    out = render_tree(Post(id="p4", gold_label="Guns", text="x"), result)
    talk_line = next(line for line in out.splitlines() if "└─ Talk" in line)
    guns_line = next(line for line in out.splitlines() if "└─ Guns" in line)
    none_lines = [line for line in out.splitlines() if "└─ none" in line]
    assert _bar_col(talk_line) == _bar_col(none_lines[-1])
    assert _bar_col(guns_line) == _bar_col(none_lines[1])


def test_render_shows_coverage_when_cutoff_skips_a_branch():
    news = HIERARCHY
    computer = _node("Computer")
    graphics = _node("Graphics")
    science = _node("Science")
    result = WalkResult(
        queried=[news.id, computer.id],
        node_mass={
            news.id: 1.0,
            computer.id: 0.99,
            graphics.id: 0.99,
            science.id: 0.01,
        },
        absorbed_mass={
            news.id: 0.99,
            computer.id: 0.99,
            graphics.id: 0.99,
            science.id: 0.0,
        },
    )
    out = render_tree(Post(id="p3", gold_label="Graphics", text="x"), result, show_coverage=True)
    assert "coverage=99.0%" in out
    news_line = next(line for line in out.splitlines() if line.startswith("News"))
    assert "abs= 99.0%" in news_line
    science_line = next(line for line in out.splitlines() if "└─ Science" in line)
    assert re.search(r"1\.0%.*0\.0%", science_line)
    graphics_line = next(line for line in out.splitlines() if "└─ Graphics" in line)
    assert re.search(r"99\.0%.*100\.0%", graphics_line)
    assert "none" not in out


def test_render_hides_coverage_on_full_walk_without_outside_choice():
    news = HIERARCHY
    result = WalkResult(
        queried=[news.id],
        node_mass={news.id: 1.0},
        absorbed_mass={news.id: 1.0},
    )
    out = render_tree(
        Post(id="p4", gold_label="Guns", text="x"), result, show_coverage=False
    )
    assert "coverage=" not in out
    news_line = next(line for line in out.splitlines() if line.startswith("News"))
    assert "abs=" not in news_line
