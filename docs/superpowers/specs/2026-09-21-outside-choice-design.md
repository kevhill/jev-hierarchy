# Outside choice and absorbed mass

Date: 2026-09-21

## Goal

Optional walk mode that injects an opt-out **Choice** at each internal node, then bubbles named-child mass up so parent mass is not inflated by that opt-out.

## Flag

```python
walk_hierarchy(state, hierarchy, cutoff, *, client, outside_choice=False)
```

Keyword-only. Default preserves today’s forced Choice among named children only.

This is **not** nested logit / GEV: no inclusive value, no \(\lambda\), no estimated RUM likelihood. The name rhymes with the discrete-choice “outside option” (opt-out of the listed set). Call it out in the `walk_hierarchy` docstring.

## Injected option

At every queried internal node, when `outside_choice=True`, append one extra criterion:

- label: `none`
- description: `None of the other choices apply`
- criteria text: `none: None of the other choices apply` (same `label: description` pattern as real children)

Parent context stays in the Choice instructions (`Which child of '{label}'…`).

## Identity

The option is **not** a taxonomy `Node`. Do not use `node_id("none", …)` — that hash would collide across parents.

Key: `outside_choice_id(parent_id) -> "outside:{parent_id}"`. SHA-256 node ids are hex and contain no colon, so these keys cannot collide with `Node.id`.

Reruns still match categories by real node ids. Outside mass is bookkeeping on the parent.

## Walk policy

Cutoff is unchanged: recurse into a **named** child iff `p(child | parent) >= cutoff`. The outside key is never recursed into (it is not a node). If none takes most of the simplex, named children often fall below cutoff — same stop, no extra heuristic.

Record `node_mass[outside_choice_id(parent)] = m↓(parent) × p(none | parent)` even when that probability is below cutoff (same as named children).

## Absorbed mass

After the walk, `WalkResult.absorbed_mass` is path mass with outside **not** folded into parents. The same cutoff that skips descent also skips absorption:

- named leaf: `m↑ = m↓` (the parent Choice already allocated that leaf, including vs `none`)
- internal node never queried (below cutoff): `m↑ = 0` — it never faced an outside Choice
- queried internal: `m↑(parent) = Σ m↑(named children)`
- outside keys are absent from `absorbed_mass`

Then `m↓(P) − m↑(P)` is mass that landed on some outside choice **or** on unexplored branches in `P`’s subtree. Local outside mass is `node_mass[outside_choice_id(P.id)]` when `P` was queried.

Always fill `absorbed_mass` (even when `outside_choice=False`). With cutoff `0`, every internal is queried, so without an outside choice `m↑` still matches tree `node_mass`.

## Tests

Scripted client: default `False` keeps criteria = named children only; `True` adds the parent-scoped key and copy; outside ids differ per parent; outside is not in `queried`; cutoff still skips low named children; `absorbed_mass` excludes outside.
