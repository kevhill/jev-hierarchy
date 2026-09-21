"""Recursive forced-choice walk: state, hierarchy, cutoff, optional outside choice."""

from __future__ import annotations

from dataclasses import dataclass, field

from .hierarchy import Node, child_criteria
from .jev import ChoiceResult, JevClient

OUTSIDE_LABEL = "none"
OUTSIDE_DESCRIPTION = "None of the other choices apply"


def outside_choice_id(parent_id: str) -> str:
    """Bookkeeping key for the opt-out Choice at ``parent_id``.

    Not a taxonomy ``Node.id``. Distinct per parent so masses do not collide.
    """
    return f"outside:{parent_id}"


def _choice_criteria(node: Node, outside_choice: bool) -> dict[str, str]:
    criteria = child_criteria(node)
    if outside_choice:
        criteria[outside_choice_id(node.id)] = (
            f"{OUTSIDE_LABEL}: {OUTSIDE_DESCRIPTION}"
        )
    return criteria


@dataclass
class WalkResult:
    """Record of one hierarchy walk.

    All dict keys are node ids except outside-choice keys
    (``outside_choice_id(parent_id)``) in ``distributions``, ``choices``,
    and ``node_mass``.

    Attributes:
        queried: Internal nodes sent to Jev, root-first, children in tree order.
        distributions: Sibling simplex at each queried node (sums to 1).
        confidences: Jev confidence at each queried node.
        node_mass: Path mass from the root. The root is 1.0; a child is
            parent mass times that child's sibling probability. Children
            below ``cutoff`` still get mass; their descendants are omitted.
        absorbed_mass: Path mass with outside choices omitted. A queried
            parent is the sum of its named children's absorbed mass. Leaves
            and unqueried internals equal ``node_mass``.
        choices: Jev argmax child id (or outside-choice key) at each queried
            node.

    ``share_of_covered(node_id, root_id)`` is absorbed mass as a fraction of
    the root's absorbed mass (how the covered pie is split). None if the
    root absorbed nothing.
    """

    queried: list[str] = field(default_factory=list)
    distributions: dict[str, dict[str, float]] = field(default_factory=dict)
    confidences: dict[str, float] = field(default_factory=dict)
    node_mass: dict[str, float] = field(default_factory=dict)
    absorbed_mass: dict[str, float] = field(default_factory=dict)
    choices: dict[str, str] = field(default_factory=dict)

    def share_of_covered(self, node_id: str, root_id: str) -> float | None:
        """``absorbed_mass[node] / absorbed_mass[root]``, or None if root absorbed is 0."""
        total = float(self.absorbed_mass.get(root_id, 0.0))
        if total <= 0.0:
            return None
        return float(self.absorbed_mass.get(node_id, 0.0)) / total


def walk_hierarchy(
    state: object,
    hierarchy: Node,
    cutoff: float,
    *,
    client: JevClient,
    outside_choice: bool = False,
) -> WalkResult:
    """Walk ``hierarchy`` with a Jev Choice at every expanded internal node.

    ``state`` is forwarded unchanged on every Choice. The walker does not
    interpret it. ``hierarchy`` is a rooted tree of frozen :class:`Node`s;
    a node is a category, not the document. Leaves are never sent to Jev.

    At an internal node the Choice instructions name the parent label
    (``Which child of '{label}' best describes this input?``). Option keys
    are child ids; option text is ``label: description``.

    If ``outside_choice`` is true, each Choice also gets an opt-out option
    ``none: None of the other choices apply``, keyed by
    :func:`outside_choice_id` for that parent — not a taxonomy node id.
    Cutoff still applies to named children only; the outside option is never
    recursed into.

    Descent is cutoff, not argmax. Recurse into every named child whose
    sibling probability is ``>= cutoff``. Cutoff ``0`` expands even
    probability-0 children. Path mass is the product of sibling
    probabilities from the root; it is recorded for a child even when that
    child is not expanded. ``absorbed_mass`` bubbles named-child mass up
    and does not absorb the outside option into the parent.

    This is a tree of forced Choices, not a nested-logit / GEV model: there
    is no inclusive value, no nest-correlation parameter, and no estimated
    random-utility likelihood. ``outside_choice`` is an opt-out Choice, not
    a GEV outside good.

    Args:
        state: Whatever Jev should judge (string, JSON object, or array).
        hierarchy: Root of the category tree.
        cutoff: In ``[0, 1]``. Compared to ``p(child | parent)``.
        client: How to ask Jev (``TypeSafeJevClient`` or a test double).
        outside_choice: If true, inject a ``none`` option at every queried
            internal node.

    Returns:
        :class:`WalkResult` with queried nodes, sibling simplexes, path
        mass, absorbed mass, argmax, and confidences.

    Raises:
        ValueError: If ``cutoff`` is outside ``[0, 1]``.
    """
    if cutoff < 0.0 or cutoff > 1.0:
        raise ValueError(f"cutoff must be in [0, 1], got {cutoff}")

    result = WalkResult()
    result.node_mass[hierarchy.id] = 1.0
    _visit(state, hierarchy, cutoff, client, outside_choice, result)
    _fill_absorbed_mass(hierarchy, result)
    return result


def _visit(
    state: object,
    node: Node,
    cutoff: float,
    client: JevClient,
    outside_choice: bool,
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
        criteria=_choice_criteria(node, outside_choice),
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
            _visit(state, child, cutoff, client, outside_choice, result)

    if outside_choice:
        none_id = outside_choice_id(node.id)
        p_none = float(answer.probabilities.get(none_id, 0.0))
        result.node_mass[none_id] = parent_mass * p_none


def _fill_absorbed_mass(node: Node, result: WalkResult) -> float:
    down = result.node_mass.get(node.id)
    if down is None:
        return 0.0
    if node.is_leaf or node.id not in result.queried:
        result.absorbed_mass[node.id] = down
        return down
    total = 0.0
    for child in node.children:
        total += _fill_absorbed_mass(child, result)
    result.absorbed_mass[node.id] = total
    return total
