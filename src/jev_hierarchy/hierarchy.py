"""Frozen category nodes for a Jev walk."""

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

