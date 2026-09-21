"""Recursive cutoff walk. Failures name the production bug they catch."""

from __future__ import annotations

import pytest

from hierarchy import Node
from jev import ChoiceResult, ScriptedJevClient
from walk import walk_hierarchy


def _tree() -> Node:
    return Node(
        label="Root",
        description="Top",
        children=(
            Node(
                label="A",
                description="Branch A",
                children=(
                    Node(label="A1", description="Leaf A1"),
                    Node(label="A2", description="Leaf A2"),
                ),
            ),
            Node(
                label="B",
                description="Branch B",
                children=(
                    Node(label="B1", description="Leaf B1"),
                    Node(label="B2", description="Leaf B2"),
                ),
            ),
        ),
    )


def _parts(tree: Node | None = None) -> tuple[Node, Node, Node, Node, Node, Node, Node]:
    root = tree or _tree()
    a, b = root.children
    a1, a2 = a.children
    b1, b2 = b.children
    return root, a, b, a1, a2, b1, b2


def _client(tree: Node | None = None) -> ScriptedJevClient:
    root, a, b, a1, a2, b1, b2 = _parts(tree)
    return ScriptedJevClient(
        {
            root.id: ChoiceResult(
                choice=a.id,
                confidence=0.8,
                probabilities={a.id: 0.8, b.id: 0.2},
            ),
            a.id: ChoiceResult(
                choice=a1.id,
                confidence=0.9,
                probabilities={a1.id: 0.9, a2.id: 0.1},
            ),
            b.id: ChoiceResult(
                choice=b1.id,
                confidence=0.6,
                probabilities={b1.id: 0.6, b2.id: 0.4},
            ),
        }
    )


def test_rejects_cutoff_below_zero():
    with pytest.raises(ValueError, match="cutoff"):
        walk_hierarchy("x", _tree(), -0.01, client=_client())


def test_rejects_cutoff_above_one():
    with pytest.raises(ValueError, match="cutoff"):
        walk_hierarchy("x", _tree(), 1.01, client=_client())


def test_leaf_root_makes_no_client_calls():
    leaf = Node(label="Only", description="A leaf")
    client = ScriptedJevClient({})
    result = walk_hierarchy("post", leaf, 0.0, client=client)
    assert client.calls == []
    assert result.node_mass == {leaf.id: 1.0}
    assert result.queried == []


def test_cutoff_zero_queries_every_internal_node():
    tree = _tree()
    root, a, b, *_ = _parts(tree)
    client = _client(tree)
    result = walk_hierarchy("a post about graphics", tree, 0.0, client=client)
    assert result.queried == [root.id, a.id, b.id]


def test_cutoff_zero_still_descends_into_zero_probability_children():
    tree = _tree()
    root, a, b, a1, a2, b1, b2 = _parts(tree)
    client = ScriptedJevClient(
        {
            root.id: ChoiceResult(
                choice=a.id,
                confidence=1.0,
                probabilities={a.id: 1.0, b.id: 0.0},
            ),
            a.id: ChoiceResult(
                choice=a1.id,
                confidence=1.0,
                probabilities={a1.id: 1.0, a2.id: 0.0},
            ),
            b.id: ChoiceResult(
                choice=b1.id,
                confidence=1.0,
                probabilities={b1.id: 1.0, b2.id: 0.0},
            ),
        }
    )
    result = walk_hierarchy("post", tree, 0.0, client=client)
    assert result.queried == [root.id, a.id, b.id]
    assert result.node_mass[b.id] == pytest.approx(0.0)
    assert result.node_mass[b1.id] == pytest.approx(0.0)


def test_cutoff_skips_children_below_threshold_and_does_not_query_them():
    tree = _tree()
    root, a, b, _a1, _a2, b1, _b2 = _parts(tree)
    client = _client(tree)
    result = walk_hierarchy("a post", tree, 0.3, client=client)
    assert result.queried == [root.id, a.id]
    assert b1.id not in result.node_mass
    assert result.node_mass[b.id] == pytest.approx(0.2)


def test_cutoff_one_only_descends_into_certainty():
    tree = _tree()
    root, a, b, a1, a2, b1, _b2 = _parts(tree)
    client = ScriptedJevClient(
        {
            root.id: ChoiceResult(
                choice=a.id,
                confidence=1.0,
                probabilities={a.id: 1.0, b.id: 0.0},
            ),
            a.id: ChoiceResult(
                choice=a1.id,
                confidence=1.0,
                probabilities={a1.id: 1.0, a2.id: 0.0},
            ),
        }
    )
    result = walk_hierarchy("post", tree, 1.0, client=client)
    assert result.queried == [root.id, a.id]
    assert result.node_mass[a1.id] == pytest.approx(1.0)
    assert b1.id not in result.node_mass


def test_path_mass_is_product_of_sibling_probabilities():
    tree = _tree()
    root, a, b, a1, a2, b1, b2 = _parts(tree)
    result = walk_hierarchy("post", tree, 0.0, client=_client(tree))
    assert result.node_mass[root.id] == pytest.approx(1.0)
    assert result.node_mass[a.id] == pytest.approx(0.8)
    assert result.node_mass[a1.id] == pytest.approx(0.72)
    assert result.node_mass[a2.id] == pytest.approx(0.08)
    assert result.node_mass[b.id] == pytest.approx(0.2)
    assert result.node_mass[b1.id] == pytest.approx(0.12)
    assert result.node_mass[b2.id] == pytest.approx(0.08)


def test_records_sibling_distribution_at_each_queried_node():
    tree = _tree()
    root, a, b, a1, a2, *_ = _parts(tree)
    result = walk_hierarchy("post", tree, 0.0, client=_client(tree))
    assert result.distributions[root.id] == {a.id: 0.8, b.id: 0.2}
    assert result.distributions[a.id] == {a1.id: 0.9, a2.id: 0.1}


def test_passes_state_and_child_criteria_into_each_choice():
    tree = _tree()
    root, a, b, *_ = _parts(tree)
    client = _client(tree)
    state = {"text": "NASA launched a probe"}
    walk_hierarchy(state, tree, 0.0, client=client)
    assert client.calls[0].state == state
    assert client.calls[0].node_id == root.id
    assert set(client.calls[0].criteria) == {a.id, b.id}
    assert "Branch A" in client.calls[0].criteria[a.id]


def test_scripted_client_raises_if_a_node_was_not_scripted():
    tree = _tree()
    client = ScriptedJevClient({})
    with pytest.raises(KeyError, match=tree.id):
        walk_hierarchy("post", tree, 0.0, client=client)
