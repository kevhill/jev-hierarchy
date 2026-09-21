#!/usr/bin/env python3
"""Walk a 20 Newsgroups tree with recursive Jev Choices.

Requires TYPESAFE_API_KEY. Create one at https://console.typesafe.ai/keys
"""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Sequence
from dataclasses import dataclass

from jev_hierarchy import (
    Node,
    TypeSafeJevClient,
    WalkResult,
    outside_choice_id,
    walk_hierarchy,
)

KEY_HELP = (
    "Set TYPESAFE_API_KEY (https://console.typesafe.ai/keys) and retry. "
    "Example: export TYPESAFE_API_KEY=... "
    "or uv run --env-file .env python demo.py"
)

# Classic 20 Newsgroups coarse groups, trimmed to eight leaves.
HIERARCHY = Node(
    label="News",
    description="A Usenet-style topical post",
    children=(
        Node(
            label="Computer",
            description="Hardware, graphics, or operating systems",
            children=(
                Node(
                    label="Graphics",
                    description="Computer graphics, rendering, images, or visualization",
                ),
                Node(
                    label="Windows / X",
                    description="Microsoft Windows or X Window System software",
                ),
            ),
        ),
        Node(
            label="Recreation",
            description="Hobbies, vehicles, or sports",
            children=(
                Node(
                    label="Autos",
                    description="Cars, driving, repairs, or automotive products",
                ),
                Node(
                    label="Baseball",
                    description="Baseball games, teams, players, or stats",
                ),
            ),
        ),
        Node(
            label="Science",
            description="Scientific or technical discussion",
            children=(
                Node(
                    label="Space",
                    description="Astronomy, spacecraft, NASA, or orbital mechanics",
                ),
                Node(
                    label="Medicine",
                    description="Health, disease, treatment, or medical advice",
                ),
            ),
        ),
        Node(
            label="Talk",
            description="Debate, politics, or religion",
            children=(
                Node(
                    label="Guns",
                    description="Firearms policy, gun rights, or related politics",
                ),
                Node(
                    label="Religion",
                    description="Religious belief, practice, or theology",
                ),
            ),
        ),
    ),
)


@dataclass(frozen=True)
class Post:
    id: str
    gold_label: str
    text: str


POSTS: tuple[Post, ...] = (
    Post(
        id="p1",
        gold_label="Space",
        text=(
            "Subject: Mars sample return timeline\n"
            "Has NASA published a revised date for bringing Perseverance samples back? "
            "I keep seeing 2033 and 2035 in different articles."
        ),
    ),
    Post(
        id="p2",
        gold_label="Baseball",
        text=(
            "Subject: wild card race\n"
            "If the Sox win tonight and the Jays lose, do they clinch a wild card, "
            "or is it still down to the remaining series against Tampa?"
        ),
    ),
    Post(
        id="p3",
        gold_label="Graphics",
        text=(
            "Subject: ray marching vs rasterization\n"
            "I'm trying to render a signed-distance scene in real time. Should I stick "
            "with sphere tracing or bake a voxel grid and rasterize?"
        ),
    ),
    Post(
        id="p4",
        gold_label="Guns",
        text=(
            "Subject: magazine capacity limits\n"
            "The new bill caps magazines at ten rounds. Does that apply to pistols "
            "already owned, or only to sales after the effective date?"
        ),
    ),
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
    parser.add_argument(
        "--outside-choice",
        action="store_true",
        help=(
            "Inject a none option at each internal Choice "
            "(opt-out, not a GEV outside good)"
        ),
    )
    return parser.parse_args(argv)


def _bar(p: float, width: int = 18) -> str:
    p = max(0.0, min(1.0, p))
    if p <= 0.0:
        filled = 0
    elif p >= 1.0:
        filled = width
    else:
        filled = min(width - 1, max(1, round(p * width)))
    return "█" * filled + "░" * (width - filled)


def _label_index(root: Node) -> dict[str, str]:
    index: dict[str, str] = {}

    def rec(node: Node) -> None:
        index[node.id] = node.label
        for child in node.children:
            rec(child)

    rec(root)
    return index


def render_tree(
    post: Post, result: WalkResult, *, outside_choice: bool = False
) -> str:
    labels = _label_index(HIERARCHY)
    queried = [labels.get(node_id, node_id) for node_id in result.queried]
    header = f"{post.id}  gold={post.gold_label}  queried={queried}"
    if outside_choice:
        covered = result.absorbed_mass.get(HIERARCHY.id)
        if covered is not None:
            header += f"  coverage={covered:.1%}"
    lines = [header, ""]

    def rec(node: Node, depth: int) -> None:
        if node.id not in result.node_mass:
            return
        indent = "  " * depth
        branch = "└─ " if depth else ""
        mass = result.node_mass[node.id]
        mark = " ← gold" if node.is_leaf and node.label == post.gold_label else ""
        extra = ""
        if outside_choice:
            if depth == 0:
                absorbed = result.absorbed_mass.get(node.id)
                if absorbed is not None:
                    extra = f"  abs={absorbed:6.1%}"
            else:
                share = result.share_of_covered(node.id, HIERARCHY.id)
                extra = f"  {share:6.1%}" if share is not None else "       —"
        lines.append(
            f"{indent}{branch}{node.label:<18} {_bar(mass)} {mass:6.1%}{extra}{mark}"
        )
        for child in node.children:
            rec(child, depth + 1)
        none_id = outside_choice_id(node.id)
        if none_id in result.node_mass:
            p = result.node_mass[none_id]
            lines.append(
                f"{indent}  └─ {'none':<16} {_bar(p)} {p:6.1%}"
            )

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
        f"outside_choice={args.outside_choice}  "
        "recursive Choice over children\n"
    )
    for post in selected:
        result = walk_hierarchy(
            post.text,
            HIERARCHY,
            args.cutoff,
            client=client,
            outside_choice=args.outside_choice,
        )
        print(render_tree(post, result, outside_choice=args.outside_choice))
        print("-" * 72)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
