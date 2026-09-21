# Recursive forced-choice hierarchy walk (Jev)

Date: 2026-09-20

## Goal

Walk a small 20 Newsgroups topic tree by asking TypeSafe Jev a **Choice** at each internal node (forced pick among children). Recurse into every child whose sibling probability is `>= cutoff`. Cutoff `0` is a full tree walk.

## Inputs

`walk_hierarchy(state, hierarchy, cutoff, *, client)`:

- `state` — source content (string or JSON-able object) Jev judges
- `hierarchy` — root `Node`
- `cutoff` — float in `[0, 1]`; compare against `p(child | parent)` from that node’s Choice
- `client` — injected `JevClient` (not part of the data flow; tests use a scripted fake)

## Behavior

- Leaves are never queried.
- At an internal node, criteria are the children (`id → "label: description"`).
- Record the sibling simplex and `P(node) = P(parent) * p(child|parent)` for each child.
- Recurse iff `p(child|parent) >= cutoff`. Unvisited subtrees keep mass at that child.
- Invalid cutoff (`< 0` or `> 1`) raises `ValueError` before any call.

## Key

Put the TypeSafe key in `TYPESAFE_API_KEY`. Create one at https://console.typesafe.ai/keys.

- `export TYPESAFE_API_KEY=...`
- or `uv run --env-file .env pytest` / `uv run --env-file .env python demo.py` with a gitignored `.env` containing `TYPESAFE_API_KEY=...`

Live tests skip when the var is unset. Unit tests never need it.

## Tests

Scripted client: cutoff `0` queries every internal node; high cutoff skips low-mass subtrees; path mass is the product along the path; CLI without a key exits 1.
