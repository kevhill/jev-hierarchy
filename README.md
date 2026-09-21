# Recursive Jev classification over a topic tree

TypeSafe [Jev](https://docs.typesafe.ai/) is a System One model: you give it **state** (a post) and typed **questions**, and it returns a forced **Choice** — one winner, a probability on every option, and a confidence. It does not generate text.

This demo asks those Choices *down a tree* instead of over a flat label set.

## What you are classifying

The **state** is a short newsgroup-style post (`posts.py`). It is not part of the tree.

The **hierarchy** is a rooted tree of frozen `Node`s (`hierarchy.py`). A node is a category:

| Field | Role |
| --- | --- |
| `label` | Human name (`Science`, `Space`, …). Shown in the CLI. |
| `description` | What the category means. This is what Jev reads. |
| `children` | Ordered siblings. Empty ⇒ a **leaf**. |
| `id` | SHA-256 of `{"description", "label"}` (canonical JSON). Not passed in; derived so two nodes with the same name and meaning share an id, and a wording change gets a new id. |

There is no parent pointer. Parenthood is “who listed you in `children`”. Leaves are never sent to Jev. Internal nodes exist only so Jev can be forced to pick among their children.

The bundled tree is a compact **20 Newsgroups** cut: `News` → Computer / Recreation / Science / Talk → eight leaves.

## How the walk works

```text
walk_hierarchy(state, hierarchy, cutoff, *, client)
```

1. Start at the root. Path mass of the root is `1.0`.
2. If the node is a leaf, stop.
3. Otherwise ask Jev a Choice whose options are that node’s children. Option **keys** are child `id`s; option **text** is `label: description`.
4. Record the sibling simplex (`p(child | parent)`, sums to 1) and Jev’s argmax / confidence.
5. Path mass: `P(child) = P(parent) × p(child | parent)`.
6. Recurse into every child with `p(child | parent) >= cutoff`.

**Cutoff `0`** is a full tree walk: even a child with probability `0` is still expanded. A higher cutoff skips low-mass branches; those children keep their path mass, but their descendants are not queried.

Two different “probabilities”:

- **Sibling probability** — Jev’s distribution at one parent (`WalkResult.distributions`).
- **Path mass** — product from the root (`WalkResult.node_mass`).

The walk does **not** follow only the winner. Argmax is recorded; descent is cutoff.

## API key

Do not commit the key. Put it in **`TYPESAFE_API_KEY`**. Create one at https://console.typesafe.ai/keys

```bash
export TYPESAFE_API_KEY=...
```

Or a gitignored `.env` in this directory:

```
TYPESAFE_API_KEY=...
```

```bash
uv run --env-file .env python demo.py
```

The process does not load `.env` by itself. Unit tests never need a key. `tests/test_live.py` skips until the variable is set.

## Setup

Needs [uv](https://docs.astral.sh/uv/).

```bash
uv sync --group dev
uv run pytest
uv run python demo.py --cutoff 0
uv run python demo.py --cutoff 0.3 --post p1
```
