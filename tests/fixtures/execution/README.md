# The shared execution fixtures

Small AAS environments and what a reader of the execution model must read from each, so that the Python package now and
other readers later are tested against the same files. The contract is section 15 ("The canonical reading") of
[docs/execution-model.md](../../../docs/execution-model.md); the terms are those of its sections 4 to 12.

| File | Content |
|---|---|
| `aas.json` | the AAS environment, written by `build.py` from aas-model's classes (never edited by hand) |
| `expected.json` | the reading, or for group D the one finding: **written by hand and normative**; when it and a reader differ, the reader is wrong (or the spec is: say so) |
| `vocabulary.ttl` | only where the fixture needs a term the lab vocabulary lacks (a07: a set-valued property), in `urn:fixture:` |

## Groups

- **A, atoms** (a01 to a14): every operand and operator form of one condition or effect: literals, parameters,
  capability properties, subjects, formulas and Uses, sets, unchanged, increase and decrease, measured and clear, Rate,
  During, Duration.
- **B, connectives** (b01 to b07): implicit and explicit And, Or, Not, Exists, ForAll (condition and effect), When, OneOf.
- **C**: every kind of subject (c01), Knowledge of the three kinds (c02), a batch's Goal (c03), a specialization that
  is a complete superset (c04).
- **D, invalid** (d01 to d29): one model per code of section 11's table, named `d<nn>-<code, dots as dashes>`, each
  breaking that one rule; `expected.json` is `{"findings": [one finding]}`. `level.derived` has none: it is checked
  from Phase 5 (modplan's compose), and needs a derived capability and its parts.

A finding's path is the idShort path from the submodel of the smallest element the rule is about: the term for
the structure and declaration rules, its `Subject`, `ValueReference`, `Rate`, `Operator`, `Value` or `Formula` element where the rule is about that
(an Uses entry for `formula.unused`), the later term for `effect.conflict`, the phase for `level.incomplete`.

## Rebuild and test

    python tests/fixtures/execution/build.py           # rewrites every aas.json
    python -m pytest tests/test_execution_fixtures.py  # aas.json is what build.py writes, reads back with BaSyx,
                                                       # every expected.json is well-formed, group D has one finding each

Add a fixture: a function in `build.py` registered with `@fixture("<nn-name>")`, then its `expected.json` by hand.
