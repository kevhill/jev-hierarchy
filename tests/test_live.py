"""Live Jev call. Skipped until TYPESAFE_API_KEY is set."""

from __future__ import annotations

import os

import pytest

from jev_hierarchy import Node, TypeSafeJevClient, walk_hierarchy

pytestmark = pytest.mark.skipif(
    not os.environ.get("TYPESAFE_API_KEY"),
    reason="TYPESAFE_API_KEY not set",
)


def test_live_walk_queries_root():
    tree = Node(
        label="News",
        description="A Usenet-style topical post",
        children=(
            Node(label="Space", description="Astronomy, spacecraft, NASA, or orbital mechanics"),
            Node(label="Medicine", description="Health, disease, treatment, or medical advice"),
        ),
    )
    client = TypeSafeJevClient(model=os.environ.get("TYPESAFE_DEFAULT_MODEL", "jev-latest"))
    result = walk_hierarchy(
        "NASA launched a probe toward Jupiter last night.",
        tree,
        0.3,
        client=client,
    )
    assert result.queried[0] == tree.id
    assert result.node_mass[tree.id] == pytest.approx(1.0)
