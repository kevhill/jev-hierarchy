#!/usr/bin/env python3
"""Walk a 20 Newsgroups tree with recursive Jev Choices.

Requires TYPESAFE_API_KEY. Create one at https://console.typesafe.ai/keys
"""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Sequence

from hierarchy import HIERARCHY, Node
from jev import TypeSafeJevClient
from posts import POSTS, Post
from walk import WalkResult, walk_hierarchy

KEY_HELP = (
    "Set TYPESAFE_API_KEY (https://console.typesafe.ai/keys) and retry. "
    "Example: export TYPESAFE_API_KEY=... "
    "or uv run --env-file .env python demo.py"
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--model",
        default=os.environ.get("TYPESAFE_DEFAULT_MODEL", "jev-latest"),
        help="Jev alias or versioned id (default: jev-latest)",
    )
    parser.add_argument(
        "--cutoff",
        type=float,
        default=0.0,
        help="Descend into children with p >= cutoff (default: 0 = full walk)",
    )
    parser.add_argument(
        "--post",
        action="append",
        dest="post_ids",
        help="Run a subset by id (repeatable). Default: all sample posts.",
    )
    return parser.parse_args(argv)


def _bar(p: float, width: int = 18) -> str:
    filled = round(max(0.0, min(1.0, p)) * width)
    return "█" * filled + "░" * (width - filled)


def _label_index(root: Node) -> dict[str, str]:
    index: dict[str, str] = {}

    def rec(node: Node) -> None:
        index[node.id] = node.label
        for child in node.children:
            rec(child)

    rec(root)
    return index


def render_tree(post: Post, result: WalkResult) -> str:
    labels = _label_index(HIERARCHY)
    queried = [labels.get(node_id, node_id) for node_id in result.queried]
    lines = [
        f"{post.id}  gold={post.gold_label}  queried={queried}",
        "",
    ]

    def rec(node: Node, depth: int) -> None:
        if node.id not in result.node_mass:
            return
        indent = "  " * depth
        branch = "└─ " if depth else ""
        mass = result.node_mass[node.id]
        mark = " ← gold" if node.is_leaf and node.label == post.gold_label else ""
        lines.append(f"{indent}{branch}{node.label:<18} {_bar(mass)} {mass:6.1%}{mark}")
        for child in node.children:
            rec(child, depth + 1)

    rec(HIERARCHY, 0)
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if not os.environ.get("TYPESAFE_API_KEY"):
        print(KEY_HELP, file=sys.stderr)
        return 1

    selected = POSTS
    if args.post_ids:
        wanted = set(args.post_ids)
        selected = tuple(p for p in POSTS if p.id in wanted)
        missing = wanted - {p.id for p in selected}
        if missing:
            print(f"unknown post ids: {sorted(missing)}", file=sys.stderr)
            return 1

    client = TypeSafeJevClient(model=args.model)
    print(
        f"model={args.model}  cutoff={args.cutoff}  "
        "recursive Choice over children\n"
    )
    for post in selected:
        result = walk_hierarchy(post.text, HIERARCHY, args.cutoff, client=client)
        print(render_tree(post, result))
        print("-" * 72)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
