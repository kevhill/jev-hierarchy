"""Compact 20 Newsgroups topic tree for the demo walk."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field


def node_id(label: str, description: str) -> str:
    payload = json.dumps(
        {"label": label, "description": description},
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Node:
    label: str
    description: str
    children: tuple["Node", ...] = ()
    id: str = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", node_id(self.label, self.description))

    @property
    def is_leaf(self) -> bool:
        return not self.children


def child_criteria(node: Node) -> dict[str, str]:
    return {c.id: f"{c.label}: {c.description}" for c in node.children}


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
