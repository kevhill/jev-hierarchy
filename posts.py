"""Sample newsgroup-style posts for the live demo."""

from __future__ import annotations

from dataclasses import dataclass


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
