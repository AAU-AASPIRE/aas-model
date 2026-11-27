# The execution model: specification

> **Draft 1, 26 Nov 2026.** Phase 0 of the execution plan (`aaspire-internal/docs/execution-plan.md`, section 5):
> the contract the shared package (reader, formula parser, validator, evaluators), modplan, the line planner and the
> behaviour tree's compiler build against. It restates decisions D1 to D38 and section 4.2 of the plan as rules, and
> states what the plan left open where Phase 1 needs an answer. Answers marked **Provisional** are this draft's (open
> questions 6, 13 and 16); they hold until the ARSO owners agree or change them. aas-model's templates
> (`submodel_templates/execution.py`, `knowledge.py`, `batch.py`) implement the structure; where this text and
> they differ, section 16 lists it.
>
> "Must" is a rule the validator checks (its code in brackets, section 11); "should" is advice it may warn about.

## 1. Scope

The execution model says, for each capability, **who takes part** (Subjects), **what must hold** (ConditionSet) and
**what changes** (EffectSet), over the symbolic state of the world: state variables, each a property of a subject.
One model serves module-level skill planning (modplan), line-level planning (the line planner, in every formalism of
D22) and execution (the behaviour tree, through what the planner compiles).

| Reads the term trees | Does not |
|---|---|
| The shared package (reader, validator, evaluators); modplan; the line planner and its compilers (PDDL, FOND, SPARQL, call nodes) | The DMP (D2): it maps skills and writes observed state. The BT controller (D24): it runs the queries, updates and Translations the planner compiled |

Out of scope: the device contract (Skills `Conditions`, `Completion`; D21), 02020's `ConstraintSet` (D5, used for
matching only), and how the tree is built (Phases 6 and 7).

## 2. Identifiers

- **Structure** (what an element is) is its semanticId. The execution model's are under
  `https://smartproductionlab.aau.dk/execution/` (`exec:` below) with a version suffix: `exec:Condition` is
  `https://smartproductionlab.aau.dk/execution/Condition/1/0`. State declarations use `…/state/` and
  `…/variables/Knowledge/1/0`; goals `…/goal/Condition/1/0`.
- **Meaning** (which property, which outcome, what a requirement is) is a supplemental semanticId from the lab
  vocabulary (`lab:` = `https://smartproductionlab.aau.dk/semantics/`, AAU-AASPIRE/ontologies). Nothing is
  matched by idShort or display name, with one exception: the idShorts in `Uses` are the names a formula uses.
- **Provisional (open question 6).** The `exec:` IRIs stay as they are until the ARSO owners decide between
  `arso:` and `pprl:`; a rename is then a one-to-one table in the reader, not a change of the model. The shared
  package lives in aas-model as `aas_model.execution`, with no dependency on the rest of aas-model beyond its
  constants, so it can move to its own package if the lab wants one.

## 3. Where the model lives

```
CapabilityContainer
├─ Capability · PropertySet                    02020 (PropertySet: the capability's properties)
└─ CapabilityRelations
   ├─ RealizedBy · ComposedOfSet · GeneralizedBySet          02020
   ├─ ConstraintSet                            02020, as IDTA has it; not part of this model (D5)
   ├─ Subjects                                 SML of ReferenceElements (section 4)
   ├─ ConditionSet   Pre · Invariant · Post    terms (section 5)
   ├─ EffectSet      Start · During · End      terms
   ├─ Duration       Value | Formula + Uses    seconds (section 5.7)
   └─ Translation    Call · Reply              Lua Blobs, for the behaviour tree (section 9)
```

Besides capabilities, terms appear in a **Goal** (a submodel of any AAS that states one, e.g. a batch: `Subjects`
and `Condition`, section 8), and state is declared in the **Knowledge** of an AAS's Variables (section 7).

A capability is read **on its own**: everything it means is in its own CapabilityRelations (D32). GeneralizedBy and
the class semanticId record where its terms come from; no consumer merges across them (section 10).

## 4. Subjects

`Subjects` is an ordered SML (`semanticIdListElement` `exec:Subject`) of ReferenceElements. Its items have no
idShort (AASd-120); terms and scripts refer to a subject by its **index**. Each item must have an English
displayName [`structure.subject-name`] saying who it is ("Unit being filled"); a planner names its parameters after
them.

| Kind | Value | Bound by | Example |
|---|---|---|---|
| **Fixed** | ModelReference to an AAS (Self, a component) or to an element of the capability's own AAS (a module's own transfer point) | the model | `This module → FillingModuleAAS` |
| **Run-time** | ExternalReference to the semantic id of what it stands for: the products' asset type, the shuttles' asset type, a place kind (`lab:TransferPoint`) | the planner (which one), the behaviour tree (binds it; a unit is the IRI its instance minted, D35) | `Unit being filled → …/Product` |
| **Requirement** | ExternalReference to a meaning (`lab:FillVolume`); the item carries the supplemental semanticId `exec:Subject/Requirement` | the tree builder: the element of the batch's product type with that meaning (D19) | `Required fill volume → lab:FillVolume` |

- What a run-time subject stands for is matched by prefix where the identifier is hierarchical (an asset type
  `…/Resource/Component/Shuttle/Planar` is a `…/Resource/Component/Shuttle`), by `rdfs:subClassOf*` and
  `owl:equivalentClass` (either way) where it is a vocabulary class (D7; vocabulary 0.11 makes `lab:Occupying` the
  same class as `lab:Receiving`).
- A subject is bound to the narrowest element a script or term needs, never a whole AAS where one element will do.
- Subjects hold the action's **parameters** only. A quantifier's variable is not a subject (section 5.3).

## 5. Terms

A term is an SMC whose semanticId is its kind [`structure.kind`]. Terms have ordering idShorts (`Term_00`) that
carry no meaning, and should have a displayName saying what they state ("Unit held here"). Several terms directly
under a phase (Pre, End, …) or a container (Body, Then, an Outcome) form an implicit And. Terms nest freely within
the rules of 5.2.

### 5.1 Atoms: `exec:Condition` and `exec:Effect`

One property of one subject. Children:

| Child | semanticId | Content |
|---|---|---|
| (the term itself) | `exec:Condition` or `exec:Effect` | its **property**: exactly one supplemental semanticId, a vocabulary property [`structure.meaning`] |
| `Subject` | `exec:Term/Subject` | ModelReference to an item of the capability's (or goal's) Subjects, or to the `Variable` of an enclosing quantifier [`reference.subject`] |
| `Operator` | `exec:Condition/Operator` or `exec:Effect/Operator` | one of the operators of 5.4, as a string |
| operand | | exactly one of `Value`, `ValueReference`, `Formula` + `Uses`; none for `measured`, `unchanged` and `clear` [`structure.operand`] |
| `Rate` | `exec:Effect/Rate` | End effects only, optional [`structure.rate`]: a reference to the rate the change runs at |

**Operands.**

| Operand | Form | Resolves to |
|---|---|---|
| `Value` | Property; its valueType matches the property's value type (`xs:double` for number, `xs:boolean`, `xs:string`, `xs:anyURI` for reference) [`operand.type`] | a literal; a reference value is a vocabulary individual or an IRI (`lab:InTolerance`) |
| `ValueReference` to a Subjects item | ModelReference ending in `Subjects/<i>` | the subject's bound identity (`HeldBy := This module`) |
| `ValueReference` to an Operation variable | ModelReference passing through an Operation (`Skills/Dispensing/Start/Start/Volume`) | the value the call sent (input) or the device answered (output); known when the call is made or answered |
| `ValueReference` to another element | ModelReference to a Property or Range of an AAS: a PropertySet `Value`, a step binding of a composite skill, another capability's `Duration/Value` | a constant, read with the model |
| `Formula` + `Uses` | section 5.5 | a number |

A `Use` is a ReferenceElement whose idShort is the alias; its value is any of the references above, or a **subject's
property**: a reference to a Subjects item (or quantifier Variable) with the property's meaning as the Use's
supplemental semanticId (`RimHeight → Subjects/1`, `lab:RimHeight`). That reads the subject's state variable (or, for
a unit, a constant of its product type: section 7).

A reference never points at a state variable's declaration; state is read through a subject and a meaning.

**Rate** references an Operation variable or a constant: the change runs continuously at that rate (per second, in
the property's unit) from start to end.

### 5.2 Connectives

| Kind | Children | In conditions | In effects |
|---|---|---|---|
| `exec:And` | terms | yes | yes |
| `exec:Or` | terms (≥ 2) | yes | no |
| `exec:Not` | exactly one term [`structure.not-arity`] | yes | no |
| `exec:Exists` | `Variable`, `Body` (terms) | yes | no |
| `exec:ForAll` | `Variable`, `Body` (terms) | yes | yes |
| `exec:When` | `Condition` (condition terms), `Then` (effect terms) | no | yes |
| `exec:OneOf` | `Outcome`s (≥ 2), each an SMC of effect terms with its meaning as supplemental semanticId; the OneOf has its own meaning (what is decided: `lab:FillResult`) | no | End only |

A condition kind under an EffectSet phase (outside a When's `Condition`), or an effect kind under a ConditionSet
phase or a Goal, is an error [`structure.placement`]. A OneOf must not nest in another OneOf, a When or a ForAll
[`structure.placement`].

### 5.3 Quantifiers (Provisional, open question 16)

A quantifier declares its own variable: `Variable` (`exec:Variable`) is a ReferenceElement **inside the
quantifier** whose value is an ExternalReference to what it ranges over (as a run-time subject's is), with a
displayName ("Any vial on the tray"). Atoms in its `Body` name it as their `Subject` (or in a Use) by a
ModelReference to that `Variable` element. Scope is containment: a reference to the Variable of a quantifier that
does not enclose the term is an error [`reference.scope`].

The variable ranges over the objects of that kind **in the problem**: for a planner, the objects of its problem; at
run time, the subjects the state store knows of that kind. The behaviour tree never binds a quantifier's variable;
the compiled query does.

This replaces aas-model's current `QuantifiedVariable`, which references an item of Subjects (section 16). No
example uses a quantifier yet.

### 5.4 Operators

| Operator | Property | Where | Operand | Meaning |
|---|---|---|---|---|
| `equal`, `notEqual` | single | conditions | any | the value equals / differs from the operand |
| `less`, `lessOrEqual`, `greater`, `greaterOrEqual` | single, number | conditions | number | comparison |
| `unchanged` | single | Invariant only [`operator.unchanged`] | none | a lock: nothing else changes the value while the action runs |
| `contains`, `notContains` | set | conditions | one value | membership |
| `assign` | single | effects | any | the value becomes the operand |
| `increase`, `decrease` | single, number | effects (not During) | number | the value changes by the operand |
| `measured` | single | End effects | none | the value becomes known; which value is not known before |
| `clear` | single | effects (not During) | none | the variable has no value afterwards (a station no longer serves anyone) |
| `add`, `remove` | set | effects (not During) | one value | the value joins / leaves the set |

The operator must suit the property's cardinality and value type in the vocabulary [`operator.cardinality`];
During allows only `assign` [`operator.during`]. A condition on a property that some effect makes `measured`
should not use `equal` [`operator.equal-measured`, warning]: compare with a range, or branch on the classification.

### 5.5 Formulas

The only text in the model (W3C EBNF):

```ebnf
Formula    ::= Term ( ( "+" | "-" ) Term )*
Term       ::= Factor ( ( "*" | "/" ) Factor )*
Factor     ::= Number | "pi" | Alias | "(" Formula ")" | "-" Factor
Number     ::= Digit+ ( "." Digit+ )? ( [eE] [+-]? Digit+ )?
Alias      ::= [A-Za-z_] [A-Za-z0-9_]*     /* an idShort in this term's Uses; "pi" is not an alias */
```

Whitespace between tokens is ignored. Every alias must be declared in `Uses` [`formula.alias`], every Use should be
used [`formula.unused`, warning], and the formula must parse [`formula.syntax`]. Numbers are in the unit of the
property the term is about (its concept description); literals carry no units, and the author converts
(`1000 * ContentVolume` for mL to mm³). A formula is linear in every alias that names a state variable some effect
in the domain changes [`formula.linear`] (multiplying two such aliases, or dividing by one, is refused; constants
may multiply and divide freely). The one-line view (`end Unit.ContentVolume += Volume`) is generated for tests,
logs and documentation and never stored.

### 5.6 Phases and their meaning

The **state** is a partial function from (subject, property) to a value (single-valued) or a set of values. No value
means **unknown**, not false.

- **Conditions.** `Pre` must hold when the action starts, `Invariant` throughout, `Post` when it has ended
  (checked, not caused: a Post the effects do not establish is a failed action). An atom over an unknown value is
  **false**, whatever its operator (`notEqual` included); `Not` is true where its term is false. So
  `Not(ContentVolume = 0)` holds for a unit whose content is unknown, and `ContentVolume ≠ 0` does not.
- **Effects.** All effects of one phase are computed from the state before that phase and applied together (as in
  PDDL): Start effects when the action starts, End effects when it ends, each phase as one write (D16). Two effects
  of one phase that assign the same variable different values are an error where the validator can see it
  [`effect.conflict`]. `increase` or `decrease` of an unknown value is a run-time error of the action.
- **Planners** read an unknown value the same way: the condition is false, so it is a goal to establish like any
  other false condition, never assumed to hold (modplan's `holds` answers None for it today and plans it so).
- **During** effects are definitions that hold while the action runs (`OutletImmersion` as a function of position
  and content); they are never written and end with the action.
- **When** applies its `Then` if its `Condition` holds in the state before the phase.
- **OneOf** (End only): exactly one Outcome happens; the capability's `Reply` names which (D34). Its effects apply
  with the other End effects.
- **Failure.** A call that fails (the Reply returns an error) applies no End effects; the Start effects stay
  applied. A FOND compilation may model each declared skill error as an outcome with no End effects (D23).
- **Effects on observed or derived variables** are expectations, never writes (D36, D37): the behaviour tree waits,
  with a timeout, until the store shows them. For a planner they are effects like any other.
- **ForAll** in effects applies its Body once per object in range.

### 5.7 Duration

The action's duration, in seconds, is, in this order:
1. the `Duration` element of the CapabilityRelations (`Value`, or `Formula` + `Uses`), if there is one;
2. otherwise, from the End effects with a Rate: `|operand| / rate` for `increase` and `decrease`,
   `|operand − value at start| / rate` for `assign`; the longest of them;
3. otherwise unknown: consumers that need durations refuse the capability by name (feature `durative`, section 12).

## 6. Example (the module's Dosing, as aas-model has it)

```
Dosing  (FillingModule, AuxiliaryCapabilities)        RealizedBy Pump/Skills/Dispense · GeneralizedBy Pump's Dosing
  S0 Needle axis           → FillingLinearAxisAAS                 (fixed)
  S1 Container in the nest → …/Product                            (run-time: a unit)
  Pre        S0.Position ≥ PropertySet/FillPosition                                      "Needle at fill depth"
  Invariant  S0.Position ≥ NestPosition − RimHeight + InsertDepth                        "Needle inside the rim"
               Uses NestPosition → PropertySet/NestPosition · RimHeight → S1 · lab:RimHeight
               InsertDepth → PropertySet/InsertDepth
  During     S1.OutletImmersion := Position − NestPosition + InnerBottomHeight
                                   + 1000 · ContentVolume / (pi · InnerDiameter² / 4)    "Outlet immersion"
```

The slice written out completely is in section 14.

## 7. State declarations (`Variables/Knowledge`)

The Knowledge (`…/variables/Knowledge/1/0`, an SMC of an AAS's Variables) declares the state variables of a subject,
and where they are kept:

| Child | Content |
|---|---|
| a `StateVariable` per variable (`…/state/StateVariable/1/0`) | its meaning as supplemental semanticId; `Subject` (ModelReference: the AAS itself, or an element of it such as a coordinate; none in a product type, whose variables are about each unit); `ValueType` and `Cardinality` (copied from the vocabulary, must agree with it [`declaration.vocabulary`]); `Initial` (optional) |
| `Target` (`…/state/SparqlTarget/1/0`) | `Endpoint` and `Graph` of the state store |

- **Value types** (`lab:valueType`): `number`, `boolean`, `string`, `reference`. **Cardinality**
  (`lab:cardinality`): `single` or `set`. A property used in a term without both in the vocabulary is an error
  [`declaration.vocabulary`] (D14).
- **Kinds** (D36). A variable is **observed** if exactly one AIMC mapping of the same AAS sinks into it, **derived**
  if its meaning is `lab:derived` in the vocabulary (no mapping, no `Initial`), and **asserted** otherwise. Two
  mappings sinking into one variable, or a mapping sinking into a derived one, is an error [`declaration.kind`].
- **Resolution.** Every (subject, property) an atom or Use reads or changes must resolve to a declaration
  [`declaration.missing`]: for a fixed subject, a StateVariable of its AAS's Knowledge whose Subject is that AAS or
  element; for a unit, the product type's Knowledge (checked when the batch is known); for a run-time resource
  subject, the Knowledge of each AAS it may be bound to (checked when the planner grounds it). A Use may also read a
  **constant** of a unit (`RimHeight`, `InnerDiameter`): a Property of the product type with that meaning, outside the
  Knowledge.
- An effect must target a declared state variable [`effect.target`]; a `BasicConstraint` in a ConstraintSet must
  not name a state property [`constraint.state`] (D5).
- What is stored follows D26: a result is declared, and so stored, only where a term or a goal reads it as a number.

## 8. Goals

A Goal (`…/submodels/Goal/1/0`, in a batch AAS or any AAS that states a task) holds `Subjects` (as in section 4;
a batch's has one run-time subject, the unit) and `Condition` (`…/goal/Condition/1/0`): condition terms, an
implicit And, that must hold at the end. A batch's goal holds for every unit (D10); its operands may reference the
product type's required properties (`ContentVolume = RequiredCapabilities/Filling/PropertySet/FillVolume`).

## 9. Translation (summary; D34, D38)

A capability the behaviour tree runs is realized by exactly one Operation [`translation.realized-by`] and carries
`Translation` with two Lua 5.2 Blobs in the lab's profile (D38): `call(subjects, properties)` returns a value
for every input it sends, by the Operation's idShorts (or `{reference = …}` in a slot with `AcceptsReference`,
D27); `reply(outputs, subjects, properties)` returns `{ok = true, outcome = <Outcome idShort>}` (`outcome` only
where the End effects hold a OneOf) or `{ok = false, error = <SkillError idShort>}`. Scripts are pure: they never
read or write state themselves. `call` must cover exactly the Operation's inputs and `reply` may only name declared
outcomes and errors [`translation.coverage`]; this is checked on the shared test vectors (group F), and
statically by the line planner's compiler. A capability run only as a step of a composite skill has no Translation.
aas-model's `submodel_templates/execution.py` documents the tables the host fills.

## 10. Levels and specialization (Provisional, open question 13)

Facts are authored once, at the lowest level where they are true (D20); every AAS carries the **generated merge**
(D32): vocabulary class → component capability (GeneralizedBy) → the capability's own terms. Consumers read one
capability and never merge.

The validator checks that a specializing capability **only narrows and adds**:
- **Subjects correspond by identity**, not by position: a general subject corresponds to the specific subject with
  the same reference (the same AAS, or the same semantic id it stands for, the n-th of a kind to the n-th). A
  general Self (the component's own AAS) corresponds to the specific subject that references that component's AAS,
  if there is one. A general subject without a counterpart must be added to the specific's Subjects in the merge.
- **Every general term** has, under the corresponding subjects, an equal or **tighter** term in the same phase:
  a tighter comparison bound (`≥ 5` for `≥ 3`), a subset of allowed values, an added conjunct. A term that widens or
  contradicts is an error [`level.widening`].
- **Completeness:** a general term with no counterpart at all is reported [`level.incomplete`]. **This is a
  warning until Phase 13's generator writes the supersets:** today the filling module's Dosing and Weighing do not
  carry the pump's and scale's End effects, and their subjects differ (the module's Dosing has the needle axis where
  the pump's has the pump).
- A **derived** offered capability (modplan compose) must re-derive from its parts and steps [`level.derived`];
  checked from Phase 5.

## 11. Validation rules

The validator reports every violation it finds (not only the first), each as a code, a severity and the idShort
path of the element. Fixture group D holds one invalid model per code.

| Code | Severity | Rule | Section |
|---|---|---|---|
| `structure.kind` | error | a term's semanticId is a known kind; its children are the kind's | 5 |
| `structure.meaning` | error | an atom has exactly one supplemental semanticId, a vocabulary property | 5.1 |
| `structure.operand` | error | exactly one operand, or none for `measured`, `unchanged`, `clear` | 5.1 |
| `structure.rate` | error | Rate only on End effects | 5.1 |
| `structure.not-arity` | error | Not has exactly one term | 5.2 |
| `structure.placement` | error | condition kinds in conditions, effect kinds in effects; OneOf at End, not nested | 5.2 |
| `structure.subject-name` | error | every Subjects item has an English displayName | 4 |
| `reference.unresolved` | error | every reference resolves | 5.1 |
| `reference.subject` | error | an atom's Subject is an item of Subjects or an enclosing quantifier's Variable | 5.1 |
| `reference.scope` | error | a quantifier's Variable is used only inside it | 5.3 |
| `operand.type` | error | a literal's valueType matches the property's value type | 5.1 |
| `operator.cardinality` | error | the operator suits the property's cardinality and value type | 5.4 |
| `operator.unchanged` | error | `unchanged` only in Invariant | 5.4 |
| `operator.during` | error | During only `assign` | 5.4 |
| `operator.equal-measured` | warning | no `equal` on a measured property | 5.4 |
| `formula.syntax` | error | the formula parses | 5.5 |
| `formula.alias` | error | every alias is declared in Uses | 5.5 |
| `formula.unused` | warning | every Use is used | 5.5 |
| `formula.linear` | error | linear in the states that change | 5.5 |
| `effect.conflict` | error | no two assigns of one variable in one phase | 5.6 |
| `effect.target` | error | an effect targets a declared state variable | 7 |
| `declaration.vocabulary` | error | value type and cardinality come from the vocabulary and agree with it | 7 |
| `declaration.kind` | error | at most one mapping sinks into a variable; none into a derived one | 7 |
| `declaration.missing` | error | every (subject, property) resolves to a declaration | 7 |
| `constraint.state` | error | no BasicConstraint names a state property | 7 |
| `translation.realized-by` | error | a capability with a Translation is realized by exactly one Operation | 9 |
| `translation.coverage` | error | Call covers the inputs; Reply names declared outcomes and errors | 9 |
| `level.widening` | error | a specialization only narrows and adds | 10 |
| `level.incomplete` | warning (error from Phase 13) | a specialization carries every general term | 10 |
| `level.derived` | error (from Phase 5) | a derived capability re-derives | 10 |

## 12. Features and consumer profiles

The validator records the features each capability uses (rule 7 of the plan's 4.2.8). Each consumer states which it
supports and refuses a capability that uses another, naming the feature (D22: what a compilation relaxes goes to its
LossReport; what it cannot relax safely it refuses).

| Feature | Used by |
|---|---|
| `negative-conditions` | `Not` |
| `disjunctive-conditions` | `Or` |
| `existential-conditions`, `universal-conditions` | `Exists`, `ForAll` in conditions |
| `universal-effects`, `conditional-effects` | `ForAll` in effects, `When` |
| `numeric` | comparisons other than equal/notEqual, `increase`, `decrease`, formulas over state |
| `durative` | `Invariant`, `During`, `Start` effects, a known duration |
| `continuous` | a `Rate` |
| `non-deterministic` | `OneOf`, `measured` |
| `set-valued` | `contains`, `notContains`, `add`, `remove` |
| `locks` | `unchanged` |

| Consumer | Supports | Notes |
|---|---|---|
| modplan | numeric, durative, continuous, locks, negative and conjunctive conditions | refuses `Or` (or `Not` over a comparison) in an Invariant over a state that changes at a rate (its event-based checker is exact only for conjunctions of linear conditions) |
| line planner, FOND | non-deterministic, negative, disjunctive, existential, universal, conditional, set-valued | numeric only where finite (D29); durative relaxed to instants (LossReport) |
| line planner, PDDL 2.1 temporal | numeric, durative, continuous (linear) | non-deterministic refused |
| behaviour-tree compiler | everything a SPARQL ASK or update can express | `During` is not compiled (definitions for planning only); `unchanged` becomes a monitored Invariant |

## 13. The state store

The store is Oxigraph (execution plan 4.1, chosen 26 Nov), reached with SPARQL 1.1 Protocol and Update.

| Graph | Holds | Written by |
|---|---|---|
| `https://smartproductionlab.aau.dk/state` | the current state: `<subject> <property> value`, the property being the variable's meaning | the DMP (observed), the behaviour tree (asserted) |
| `…/state/provenance` | one provenance record per (subject, property) | the same writers |
| `…/state/vocabulary` | the lab vocabulary, replaced on every start | the state-store loader |

- **Values.** number: `xsd:double`; boolean: `xsd:boolean`; string: `xsd:string`; reference: an IRI. A
  single-valued variable has at most one triple; a set-valued one a triple per member. No triple: unknown. Subjects
  are the AAS id, the element's IRI, or a unit's `urn:uuid:<uuid>` (D35).
- **Provenance record** `urn:dmp:state:<sha-256(subject, newline, property)>` (as the DMP writes it today,
  namespace `https://smartproductionlab.aau.dk/dmp/state#`): `subject`, `property`, `writer`, `source` (the
  mapping, or the call), `session`, `time`. **Provisional:** the behaviour tree writes the same record with writer
  `bt:<instance>` and source the invocation; `owner` (the subject's AAS, or a unit's batch) and the TSDB point of a
  measured result (plan 4.1) are still to be added to both writers.
- **Writes.** A writer replaces a variable's values as a whole, in one update with its provenance; the behaviour
  tree writes one effect phase as one update (D16), so the store never holds half an effect.
- **Derived state** is computed by queries, never stored. `lab:Location` of a carrier is the place whose projected
  position (`lab:AbsoluteX`, `lab:AbsoluteY`) lies within its kind's `lab:placeTolerance` of the carrier's, compared
  as squared distances; no such place: unknown.
- **Custody** chains are SPARQL property paths over `lab:HeldBy`.
- **Open:** the terms for a unit's product type and batch (open question 3), written when a unit is admitted (D35).

## 14. The slice on paper

The slice is one dispensing station and one planar shuttle. aas-model models dispensing twice: the AP2030
`dispensingStation` (one Dispensing capability, no components) and the filling module with its linear axis, pump and
scale. The slice uses the filling module, the one with components, specializations and a OneOf. One-line view, generated from aas-model's examples (`examples/aas/`, and `planarShuttle1` built from
`RESOURCE_FACTORIES`) on 26 Nov:

```
Batch Vial2mLBatch0001 · ProductType Vial2mL · Quantity 3
Goal       [S0 The unit → …/Product]
           S0.ContentVolume = Vial2mL/RequiredCapabilities/Filling/PropertySet/FillVolume · S0.Weighed = true

Shuttle1.MoveToPosition         [S0 This shuttle (fixed) · S1 Target place → lab:TransferPoint]
  End        S0.Location := S1                          derived: the tree waits until the store shows it
  Duration   3.0

FillingModule.Occupying         [S0 This module · S1 Transfer point (fixed, its own) · S2 Delivering shuttle → Shuttle
                                 · S3 Unit received → Product]
  Pre        S2.Location = S1 · S3.HeldBy = S2
  End        S3.HeldBy := S0                            asserted: the tree writes it
             S0.OccupiedBy := S3                        asserted here (no queue reported, open question 24);
                                                        observed at a station with a queue
  Duration   2.0

FillingModule.Filling           [S0 This module · S1 Unit being filled → Product
                                 · S2 Required fill volume (requirement, lab:FillVolume)
                                 · S3 Required fill weight (requirement, lab:FillWeight)]
  Pre        S1.ContentVolume = 0.0
  Invariant  S1.HeldBy = S0
  End        S1.ContentVolume += Dispensing.Volume  rate (the dosing step's FlowRate)
             S1.Weighed := true · S1.FillWeight measured
             OneOf lab:FillResult   InTolerance:    S1.FillResult := lab:InTolerance
                                    OutOfTolerance: S1.FillResult := lab:OutOfTolerance
  Duration   2 · Position / Speed + Volume / FlowRate + Weighing
  Translation  call: { Volume = subjects[3].value }
               reply: ErrorID ≠ 0 → error · Weight within subjects[4].value → InTolerance, else OutOfTolerance

FillingModule.Releasing         [S0 This module · S1 Transfer point · S2 Collecting shuttle · S3 Unit released]
  Pre        S2.Location = S1 · S3.HeldBy = S0 · S0.OccupiedBy = S3
  End        S3.HeldBy := S2 · S0.OccupiedBy clear
  Duration   2.0
```

**A plan** for one unit u, from `u.HeldBy = Shuttle1`, `u.ContentVolume = 0` (its initial value):
MoveToPosition(Shuttle1, TP) → Occupying(Module, TP, Shuttle1, u) → Filling(Module, u, FillVolume, FillWeight)
→ Releasing(Module, TP, Shuttle1, u). Each Pre is established by the effects before it; the goal holds after Filling
in both outcomes (the plan does not branch, since the goal does not read FillResult). Features used: numeric,
durative, continuous, non-deterministic.

**The derived offered capability** (Filling, from the module's composite `Dispensing`: position the needle, dose,
retract, weigh; Phase 5 makes modplan compose write it):

| Filling's term | Derived from |
|---|---|
| End `ContentVolume += Volume` rate FlowRate | the pump's Dosing End effect, with the step's bound FlowRate |
| End `Weighed := true` | Dosing sets false, Weighing sets true afterwards: the later one wins |
| End `FillWeight measured` | the scale's Weighing |
| Invariant `HeldBy = S0` | composition rule: the unit stays at the module throughout (plan 4.2.5) |
| Duration | the steps in sequence: two needle moves (`Position / Speed` each), dosing (`Volume / FlowRate`), weighing |
| the needle's Pre and Invariants | internal: established and kept by the steps; the needle starts and ends at rest |
| OneOf FillResult | **not derived**: generated at line level from the product's required FillWeight (D23) |
| Pre `ContentVolume = 0` | **not derivable from the parts**: no step needs it. It comes from the class: the vocabulary already states it on `lab:Filling` (`pprl:pre` "= 0.0", with `pprl:post` "= FillVolume"), as an expression string; Phase 13 turns it into structured terms (D32) |

So the slice is expressible end to end, with two findings for Phase 1: the OneOf and Filling's Pre come from levels
other than the module's parts (the line, and the class), and the module's specializations are not yet complete supersets (section 10).

## 15. The canonical reading (fixtures)

The shared fixtures (`aas-model/tests/fixtures/execution/<nn-name>/`) state what a reader must read from an AAS, in a
form no language owns, so the Python package now and other readers later are tested against the same files. Each
fixture holds:

| File | Content |
|---|---|
| `aas.json` | an AAS environment (AAS JSON), built by `build.py` beside the fixtures from aas-model's classes; the test regenerates it and compares, so it never drifts from the templates |
| `expected.json` | the canonical reading below, or the expected findings of the validator |
| `vocabulary.ttl` | optional: terms the fixture needs beyond the lab vocabulary (a set-valued property), in `urn:fixture:` |

**Reading.** One object per capability, keyed by its idShort path from the submodel
(`"CapabilityDescription/OfferedCapabilities/Filling"`), or `"goal"` for a Goal. A fixture's environment keeps
these paths unique across its AASs (a reader of a whole line keys by AAS id and path):

```json
{
  "capabilities": {
    "CapabilityDescription/AuxiliaryCapabilities/Dosing": {
      "aas": "https://smartproductionlab.aau.dk/aas/FixtureAAS",
      "meaning": "lab:Dosing",
      "subjects": [
        {"name": "This module", "fixed": "https://smartproductionlab.aau.dk/aas/FixtureAAS"},
        {"name": "Unit", "standsFor": "https://smartproductionlab.aau.dk/Product"},
        {"name": "Required fill volume", "requirement": "lab:FillVolume"}
      ],
      "pre": [], "invariant": [], "post": [], "start": [], "during": [], "end": [],
      "duration": null,
      "features": ["numeric"]
    }
  },
  "goal": null,
  "knowledge": [],
  "findings": []
}
```

- **IRIs** are written with the prefixes `lab:` (`https://smartproductionlab.aau.dk/semantics/`), `exec:` (the
  execution model's, without the version suffix) and `fixture:` (`urn:fixture:`); any other IRI in full.
- **Terms** are in idShort order. An atom is `{"condition": {…}}` or `{"effect": {…}}` with `subject` (a
  reference: `{"subject": i}` or `{"variable": "v0"}`), `property`, `op`, `operand` (absent where there is none) and,
  for an effect, `rate` (an operand, or absent). Connectives: `{"and": [terms]}`, `{"or": […]}`, `{"not": term}`,
  `{"exists": {"variable": V, "body": […]}}`, `{"forall": {…}}`, `{"when": {"if": […], "then": […]}}`,
  `{"oneOf": {"meaning": IRI, "outcomes": [{"id": idShort, "meaning": IRI, "effects": […]}]}}`. A quantifier's
  `V` is `{"id": "v0", "name": "…", "standsFor": IRI}`, numbered in document order across the capability.
- **Operands:** `{"number": 2.0}`, `{"boolean": true}`, `{"string": "…"}`, `{"iri": "lab:InTolerance"}` (literals);
  `{"subject": i}` or `{"variable": "v0"}` (an identity); `{"parameter": {"operation": "<idShort path>", "variable":
  "<idShort>"}}` (an Operation variable, its path from the Skills submodel's idShort through the Operation:
  `Skills/Dispense/Start/Start`, the command's collection, then its Operation); `{"element": "<idShort path>"}` (a constant of the same AAS, its path from the
  submodel's idShort; of another AAS `{"element": "<submodel id>#<idShortPath>"}`, the form of section 13); `{"state": {"subject": i,
  "property": IRI}}` (a subject's property, in Uses only); `{"formula": AST, "uses": {"Alias": operand}}` with AST
  `{"number": x}`, `{"pi": true}`, `{"alias": "X"}`, `{"neg": AST}`, `{"+": [AST, AST]}` (also `-`, `*`, `/`),
  left-associative as parsed.
- **Duration:** an operand, or `null` where none is stated (5.7's rule 2 is an evaluator's, not the reader's).
- **Identities** of elements (a fixed subject that is an element, a Knowledge variable's subject) are written as the
  state store names them (section 13): `<submodel id>#<idShortPath>`, the path without the submodel's idShort.
- **Features:** sorted names of section 12. `numeric` counts a formula only where a Use reads a subject's state;
  `durative` counts an explicit Duration, an Invariant, a During or a Start effect, not a duration a Rate implies.
- **Not in the reading:** RealizedBy, GeneralizedBy and ComposedOf (the validator reads them; the rules of
  sections 9 and 10 report through findings). A container without CapabilityRelations (a product's required
  capability) has no entry.
- **Knowledge:** `[{"aas": id, "subject": IRI or null, "property": IRI, "valueType": …, "cardinality": …, "initial":
  operand or null, "kind": "observed" | "asserted" | "derived"}]` for every StateVariable of the environment, sorted by
  aas, subject, property.
- **Goal:** `{"aas": id, "subjects": […], "condition": [terms]}`.
- **Findings:** `[{"code": "…", "severity": "error" | "warning", "path": "<idShort path of the element>"}]`, sorted
  by path, then code. The path is that of the smallest element the rule is about (the `Operator`, the `Subject`,
  the term); `effect.conflict` names the later term, `level.incomplete` the specialization's phase. `effect.target`
  is reported for an effect without a declaration, `declaration.missing` for a read. A valid fixture has none; an invalid fixture (group D) states exactly its one finding and
  may leave the rest of the reading out.

## 16. Where aas-model differs, and what Phase 1 changes

- **Quantifier variables** (5.3): `QuantifiedVariable` references a Subjects item; it becomes an ExternalReference
  inside the quantifier, with a displayName. No example is affected.
- **`clear`** is implemented in aas-model but was missing from the plan's operator list; it is part of this spec.
- **Specializations** are not complete supersets (section 10); `level.incomplete` stays a warning until Phase 13.
- **The plan's 4.2.3 and 4.2.8** are superseded by this document; the plan points here.

## 17. Left open (for later phases)

| Question | What remains | Needed by |
|---|---|---|
| 1 | deadlock between instances; how long a unit waits in a queue | Phase 7 |
| 3 | vocabulary terms for a unit's product type and batch | Phase 7 (admission) |
| 4 | the behaviour tree's crash window; where the call journal lives | Phase 8 |
| 5 | tick rate for Invariants; subject bindings in the tree XML | Phase 7 |
| 7 | validity ranges of derived capabilities | Phase 5 |
| 8 | a Reply naming neither outcome nor error: node or controller failure | Phase 7 |
| 21 | type-level terms in RDF | Phase 13 |
| 24 | custody: `OccupiedBy` or `Occupancy`/`Capacity`; modules without a queue | before Phases 6 and 7 |
| — | this spec's terms (Subjects, ConditionSet, EffectSet, Duration, Translation, the term kinds) in ARSO's capabilities module: `ARSO/Modules/capabilities.ttl` (0.14) describes only 02020's structure | Phase 0 agreement |
