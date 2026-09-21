"""Live Jev call. Skipped until TYPESAFE_API_KEY is set."""

from __future__ import annotations

import os

import pytest

from hierarchy import HIERARCHY
from jev import TypeSafeJevClient
from walk import walk_hierarchy

pytestmark = pytest.mark.skipif(
    not os.environ.get("TYPESAFE_API_KEY"),
    reason="TYPESAFE_API_KEY not set",
)


def test_live_walk_queries_root():
    client = TypeSafeJevClient(model=os.environ.get("TYPESAFE_DEFAULT_MODEL", "jev-latest"))
    result = walk_hierarchy(
        "NASA launched a probe toward Jupiter last night.",
        HIERARCHY,
        0.3,
        client=client,
    )
    assert result.queried[0] == HIERARCHY.id
    assert result.node_mass[HIERARCHY.id] == pytest.approx(1.0)
