"""Recursive forced-choice walk: state, hierarchy, cutoff."""

from __future__ import annotations

from dataclasses import dataclass, field

from .hierarchy import Node, child_criteria
from .jev import ChoiceResult, JevClient


@dataclass
class WalkResult:
    queried: list[str] = field(default_factory=list)
    distributions: dict[str, dict[str, float]] = field(default_factory=dict)
    confidences: dict[str, float] = field(default_factory=dict)
    node_mass: dict[str, float] = field(default_factory=dict)
    choices: dict[str, str] = field(default_factory=dict)


def walk_hierarchy(
    state: object,
    hierarchy: Node,
    cutoff: float,
    *,
    client: JevClient,
) -> WalkResult:
    if cutoff < 0.0 or cutoff > 1.0:
        raise ValueError(f"cutoff must be in [0, 1], got {cutoff}")

    result = WalkResult()
    result.node_mass[hierarchy.id] = 1.0
    _visit(state, hierarchy, cutoff, client, result)
    return result


def _visit(
    state: object,
    node: Node,
    cutoff: float,
    client: JevClient,
    result: WalkResult,
) -> None:
    if node.is_leaf:
        return

    answer: ChoiceResult = client.choose(
        state,
        node_id=node.id,
        instructions=(
            f"Which child of '{node.label}' best describes this input? "
            "Pick the one option that fits."
        ),
        criteria=child_criteria(node),
    )
    result.queried.append(node.id)
    result.distributions[node.id] = dict(answer.probabilities)
    result.confidences[node.id] = answer.confidence
    result.choices[node.id] = answer.choice

    parent_mass = result.node_mass[node.id]
    for child in node.children:
        p = float(answer.probabilities.get(child.id, 0.0))
        result.node_mass[child.id] = parent_mass * p
        if p >= cutoff:
            _visit(state, child, cutoff, client, result)
