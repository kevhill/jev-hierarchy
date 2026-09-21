# Recursive Jev classification over a topic tree

TypeSafe [Jev](https://docs.typesafe.ai/) is a System One model: you give it **state** and typed **questions**, and it returns a forced **Choice** — one winner, a probability on every option, and a confidence. It does not generate text.

This library walks those Choices **down a tree** instead of over a flat label set. Core code lives in `src/jev_hierarchy`. The 20 Newsgroups files in `demo.py` are only one example of how to call it.

## Usage

```python
from jev_hierarchy import Node, TypeSafeJevClient, walk_hierarchy
```

**`walk_hierarchy(state, hierarchy, cutoff, *, client)`**

**`state`** is whatever Jev should judge. The walker does not interpret it. It is forwarded unchanged on every Choice, the same way the TypeSafe API accepts state: a string, a JSON object, or an array. A support ticket, an email thread, a structured record, or a newsgroup post are all valid.

**`hierarchy`** is a rooted tree of frozen `Node`s. You build it in your own code; the library does not ship a taxonomy. A node is a category, not the document:

| Field | Role |
| --- | --- |
| `label` | Human name. Shown when you print the tree. |
| `description` | What the category means. This is what Jev reads. |
| `children` | Ordered siblings. Empty ⇒ a **leaf**. |
| `id` | SHA-256 of `{"description", "label"}` (canonical JSON). Not passed in; derived so two nodes with the same name and meaning share an id, and a wording change gets a new id. |

There is no parent pointer. Parenthood is “who listed you in `children`”. Leaves are never sent to Jev. Internal nodes exist only so Jev can be forced to pick among their children.

**`cutoff`** is a walk policy, not a field on `Node`. Compare it to sibling probability `p(child | parent)`.

**`client`** is how you talk to Jev (`TypeSafeJevClient` or a fake in tests).

### Build a tree and walk it

Nest `Node`s. Empty `children` makes a leaf.

```python
from jev_hierarchy import Node, TypeSafeJevClient, walk_hierarchy

tree = Node(
    label="News",
    description="A Usenet-style topical post",
    children=(
        Node(
            label="Science",
            description="Scientific or technical discussion",
            children=(
                Node(label="Space", description="Astronomy, spacecraft, NASA, or orbital mechanics"),
                Node(label="Medicine", description="Health, disease, treatment, or medical advice"),
            ),
        ),
        Node(
            label="Recreation",
            description="Hobbies, vehicles, or sports",
            children=(
                Node(label="Autos", description="Cars, driving, repairs, or automotive products"),
                Node(label="Baseball", description="Baseball games, teams, players, or stats"),
            ),
        ),
    ),
)

client = TypeSafeJevClient(model="jev-latest")
result = walk_hierarchy(
    "Has NASA published a revised date for bringing Perseverance samples back?",
    tree,
    cutoff=0.3,
    client=client,
)

# Path mass at each visited node; sibling simplex at each queried parent.
print(result.node_mass)
print(result.distributions)
print(result.choices)
```

The walk:

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

### API key

Do not commit the key. Put it in **`TYPESAFE_API_KEY`**. Create one at https://console.typesafe.ai/keys

```bash
export TYPESAFE_API_KEY=...
```

Or a gitignored `.env` in this directory:

```
TYPESAFE_API_KEY=...
```

The process does not load `.env` by itself. Pass it with `uv run --env-file .env …`. Unit tests never need a key. `tests/test_live.py` skips until the variable is set.

## Demo

`demo.py` is a script, not part of the library. It classifies short **20 Newsgroups**-style posts with a compact tree (`News` → Computer / Recreation / Science / Talk → eight leaves) defined in that file.

Needs [uv](https://docs.astral.sh/uv/).

```bash
uv sync --group dev
uv run pytest
uv run --env-file .env python demo.py --cutoff 0
uv run --env-file .env python demo.py --cutoff 0.3 --post p1
```

## License

MIT. See [LICENSE](LICENSE).
