"""Node identity. Failures name the production bug they catch."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from hierarchy import Node, node_id


def test_id_is_stable_hash_of_label_and_description():
    node = Node(label="Space", description="Astronomy or spacecraft")
    assert node.id == node_id("Space", "Astronomy or spacecraft")
    assert node.id == Node(label="Space", description="Astronomy or spacecraft").id


def test_different_description_changes_id():
    a = Node(label="Space", description="Astronomy")
    b = Node(label="Space", description="NASA gossip")
    assert a.id != b.id


def test_label_and_description_are_not_concatenated_ambiguously():
    a = Node(label="ab", description="c")
    b = Node(label="a", description="bc")
    assert a.id != b.id


def test_node_is_frozen():
    node = Node(label="Space", description="Astronomy")
    with pytest.raises(FrozenInstanceError):
        node.label = "Med"
    with pytest.raises(FrozenInstanceError):
        node.description = "other"
    with pytest.raises(FrozenInstanceError):
        node.id = "nope"


def test_id_is_not_an_init_argument():
    with pytest.raises(TypeError):
        Node(id="hand-written", label="Space", description="Astronomy")
