"""
Execution — what a capability needs and changes, as a tree of terms (plans/kg-planning-execution-PLAN.md, 4.2).

An SMC next to the IDTA ConstraintSet in a CapabilityContainer (``capability_description``). The ConstraintSet
keeps the capability's characteristics for matching; Execution says what the capability needs and changes when it
runs, for the planners, the behaviour tree and the DMP.

The world is a set of subjects whose properties have one value at a time (a set of values where the vocabulary
declares the property set-valued). An action names who takes part (Subjects), what must hold (Conditions: Pre at
its start, Invariant throughout, Post at its end) and what it changes (Effects: Start, During, End).

Structure::

    Execution
    ├── Subjects                 who takes part: Self, a component, a unit, a carrier
    │   └── <subject>            Subject: Role, Binding (the Operation variable a run-time subject arrives in)
    ├── Conditions
    │   ├── Pre                  terms, all of which hold at the start
    │   ├── Invariant            ... throughout
    │   └── Post                 ... at the end (derived from End effects where it is a plain assignment)
    ├── Effects
    │   ├── Start                effect terms applied when the action starts
    │   ├── During               definitions that hold while it runs
    │   └── End                  effect terms applied when it ends
    └── Provenance               on a derived Execution: what it was derived from, and its fingerprint

A term is an SMC whose semantic id says what it is:

- ``Condition`` / ``Effect``: one property of one subject. The property rides as a supplemental semantic id
  (the lab vocabulary); ``Subject`` references an entry of Subjects (or a quantified Variable); ``Operator``
  is one of the operators below; the operand is exactly one of ``Value`` (a literal), ``ValueReference``
  (a parameter, a named value, another subject) or ``Formula`` with its ``Uses``. An End effect may carry
  a ``Rate``: the change runs continuously at that rate until the end.
- ``And``, ``Or``, ``Not``, ``Exists``, ``ForAll`` combine conditions; ``And``, ``ForAll``,
  ``When`` and ``OneOf`` combine effects. Several terms directly under Pre, End, ... all hold (an implicit
  And). ``Not`` holds one term; a quantifier holds its ``Variable`` and ``Body``; ``When`` its
  ``Condition`` and ``Then``; ``OneOf`` its ``Outcome``s.

The classes are named apart from other templates' (``StateCondition``, ``PreTerms``): aas_pydantic reads an
element back as the class its dump names, among all classes of the package. The idShorts of terms
(``Term_00``) carry no meaning and their order none either; only the idShorts in
``Uses`` do: they are the names the formula uses. The formula is the only text: arithmetic over those names,
numbers and ``pi``. Everything else is a reference or a vocabulary id, so nothing is matched by name. What a
consumer can evaluate (disjunction, quantifiers, conditional effects, durations, non-determinism) is checked by
the validator of the shared execution package, not here.
"""

from __future__ import annotations

from typing import Dict, Optional, TypeAlias, Union

from aas_pydantic import Property, ReferenceElement, SubmodelElementCollection

from aas_model.constants import (
    EXECUTION, EXECUTION_AND, EXECUTION_BODY, EXECUTION_CONDITION, EXECUTION_CONDITION_OPERATOR,
    EXECUTION_CONDITIONS, EXECUTION_DERIVED_FROM, EXECUTION_DURING, EXECUTION_EFFECT, EXECUTION_EFFECT_OPERATOR,
    EXECUTION_EFFECTS, EXECUTION_END, EXECUTION_EXISTS, EXECUTION_FINGERPRINT, EXECUTION_FOR_ALL,
    EXECUTION_FORMULA_USE, EXECUTION_FORMULA_USES, EXECUTION_INVARIANT, EXECUTION_NOT, EXECUTION_ONE_OF,
    EXECUTION_OR, EXECUTION_OUTCOME, EXECUTION_POST, EXECUTION_PRE, EXECUTION_PROVENANCE, EXECUTION_RATE,
    EXECUTION_START, EXECUTION_SUBJECT, EXECUTION_SUBJECT_BINDING, EXECUTION_SUBJECT_ROLE, EXECUTION_SUBJECTS,
    EXECUTION_TERM_FORMULA, EXECUTION_TERM_SUBJECT, EXECUTION_TERM_VALUE, EXECUTION_TERM_VALUE_REFERENCE,
    EXECUTION_WHEN, EXECUTION_WHEN_CONDITION, EXECUTION_WHEN_THEN,
)


# ── Subjects ─────────────────────────────────────────────────────────────────

class SubjectRole(Property):
    """Who the subject is: the resource owning the invoked Operation (Self), one of its components, a unit of a
    product, a carrier, or a quantified variable."""
    id_short: str = "Role"
    semantic_id: str = EXECUTION_SUBJECT_ROLE
    description: str = "The subject's role in the action."
    FORM_CHOICES = ("Self", "Component", "Product", "Carrier", "Variable")

SubjectRole_t: TypeAlias = SubjectRole  # a field may share the class's id_short


class SubjectBinding(ReferenceElement):
    """Where the subject comes from: for a component, the component; for a subject only known at run time, the
    Operation variable it arrives in. Self needs none: it is the AAS owning the invoked Operation."""
    id_short: str = "Binding"
    semantic_id: str = EXECUTION_SUBJECT_BINDING
    description: str = "The element this subject is: a component, or the Operation variable that carries it."

SubjectBinding_t: TypeAlias = SubjectBinding  # a field may share the class's id_short


class ExecutionSubject(SubmodelElementCollection):
    """One subject of the action. What kind of thing it is (a container, a shuttle) rides as a supplemental
    semantic id."""
    semantic_id: str = EXECUTION_SUBJECT
    description: str = "A subject of the action."
    Role: SubjectRole_t = SubjectRole()
    Binding: Optional[SubjectBinding_t] = None

ExecutionSubject_t: TypeAlias = ExecutionSubject  # a field may share the class's id_short


class Subjects(SubmodelElementCollection):
    id_short: str = "Subjects"
    semantic_id: str = EXECUTION_SUBJECTS
    description: str = "Who takes part in the action, keyed by the name terms refer to."
    subject: Dict[str, ExecutionSubject] = {}

Subjects_t: TypeAlias = Subjects  # a field may share the class's id_short


# ── Atoms ────────────────────────────────────────────────────────────────────

class TermSubject(ReferenceElement):
    id_short: str = "Subject"
    semantic_id: str = EXECUTION_TERM_SUBJECT
    description: str = "The subject whose property the term is about: an entry of Subjects or a quantified Variable."

TermSubject_t: TypeAlias = TermSubject  # a field may share the class's id_short


class ConditionOperator(Property):
    """How the property compares with the operand. ``unchanged`` (Invariant only) is a lock: nothing else may
    change the value while the action runs; contains and notContains are for set-valued properties."""
    id_short: str = "Operator"
    semantic_id: str = EXECUTION_CONDITION_OPERATOR
    FORM_CHOICES = (
        "equal", "notEqual", "less", "lessOrEqual", "greater", "greaterOrEqual", "unchanged", "contains",
        "notContains",
    )

ConditionOperator_t: TypeAlias = ConditionOperator  # a field may share the class's id_short


class EffectOperator(Property):
    """What the effect does to the property. ``measured``: the value becomes known (no operand); add and
    remove are for set-valued properties."""
    id_short: str = "Operator"
    semantic_id: str = EXECUTION_EFFECT_OPERATOR
    FORM_CHOICES = ("assign", "increase", "decrease", "measured", "add", "remove")

EffectOperator_t: TypeAlias = EffectOperator  # a field may share the class's id_short


class TermValue(Property):
    """A literal operand, in the unit of the property; its valueType is the property's."""
    id_short: str = "Value"
    semantic_id: str = EXECUTION_TERM_VALUE

TermValue_t: TypeAlias = TermValue  # a field may share the class's id_short


class TermValueReference(ReferenceElement):
    """An operand that is an element: an Operation variable (a parameter), a property of the capability (a named
    value), another subject."""
    id_short: str = "ValueReference"
    semantic_id: str = EXECUTION_TERM_VALUE_REFERENCE

TermValueReference_t: TypeAlias = TermValueReference  # a field may share the class's id_short


class TermFormula(Property):
    """An arithmetic operand: numbers, ``pi``, + - * / and brackets over the names declared in Uses."""
    id_short: str = "Formula"
    semantic_id: str = EXECUTION_TERM_FORMULA
    value_type: str = "xs:string"

TermFormula_t: TypeAlias = TermFormula  # a field may share the class's id_short


class FormulaUse(ReferenceElement):
    """One name of the formula (its idShort) and the element it stands for."""
    semantic_id: str = EXECUTION_FORMULA_USE


class FormulaUses(SubmodelElementCollection):
    id_short: str = "Uses"
    semantic_id: str = EXECUTION_FORMULA_USES
    description: str = "The names the formula uses, each the element it stands for."
    use: Dict[str, FormulaUse] = {}

FormulaUses_t: TypeAlias = FormulaUses  # a field may share the class's id_short


class Rate(ReferenceElement):
    """The rate the End effect's change runs at until the end (a FlowRate for a ContentVolume): an Operation
    variable or a property of the capability."""
    id_short: str = "Rate"
    semantic_id: str = EXECUTION_RATE

Rate_t: TypeAlias = Rate  # a field may share the class's id_short


class StateCondition(SubmodelElementCollection):
    """One property of one subject compared with an operand. The property rides as a supplemental semantic id."""
    semantic_id: str = EXECUTION_CONDITION
    Subject: TermSubject_t = TermSubject()
    Operator: ConditionOperator_t = ConditionOperator()
    Value: Optional[TermValue_t] = None
    ValueReference: Optional[TermValueReference_t] = None
    Formula: Optional[TermFormula_t] = None
    Uses: Optional[FormulaUses_t] = None


class StateEffect(SubmodelElementCollection):
    """One property of one subject changed. The property rides as a supplemental semantic id."""
    semantic_id: str = EXECUTION_EFFECT
    Subject: TermSubject_t = TermSubject()
    Operator: EffectOperator_t = EffectOperator()
    Value: Optional[TermValue_t] = None
    ValueReference: Optional[TermValueReference_t] = None
    Formula: Optional[TermFormula_t] = None
    Uses: Optional[FormulaUses_t] = None
    Rate: Optional[Rate_t] = None


# ── Connectives ──────────────────────────────────────────────────────────────

class And(SubmodelElementCollection):
    semantic_id: str = EXECUTION_AND
    description: str = "All of its terms hold."
    term: Dict[str, "ConditionTerm"] = {}


class Or(SubmodelElementCollection):
    semantic_id: str = EXECUTION_OR
    description: str = "At least one of its terms holds."
    term: Dict[str, "ConditionTerm"] = {}


class Not(SubmodelElementCollection):
    semantic_id: str = EXECUTION_NOT
    description: str = "Its one term does not hold."
    term: Dict[str, "ConditionTerm"] = {}


class Body(SubmodelElementCollection):
    id_short: str = "Body"
    semantic_id: str = EXECUTION_BODY
    term: Dict[str, "ConditionTerm"] = {}

Body_t: TypeAlias = Body  # a field may share the class's id_short


class Exists(SubmodelElementCollection):
    """The Body holds for at least one value of the Variable: a Subject with Role Variable whose supplemental
    semantic id is the type it ranges over."""
    semantic_id: str = EXECUTION_EXISTS
    Variable: ExecutionSubject_t
    Body: Body_t


class ForAll(SubmodelElementCollection):
    """The Body holds for every value of the Variable."""
    semantic_id: str = EXECUTION_FOR_ALL
    Variable: ExecutionSubject_t
    Body: Body_t


ConditionTerm = Union[StateCondition, And, Or, Not, Exists, ForAll]


class EffectAnd(SubmodelElementCollection):
    semantic_id: str = EXECUTION_AND
    description: str = "All of its effects apply."
    term: Dict[str, "EffectTerm"] = {}


class EffectBody(SubmodelElementCollection):
    id_short: str = "Body"
    semantic_id: str = EXECUTION_BODY
    term: Dict[str, "EffectTerm"] = {}

EffectBody_t: TypeAlias = EffectBody  # a field may share the class's id_short


class EffectForAll(SubmodelElementCollection):
    """The Body's effects apply for every value of the Variable."""
    semantic_id: str = EXECUTION_FOR_ALL
    Variable: ExecutionSubject_t
    Body: EffectBody_t


class WhenCondition(SubmodelElementCollection):
    id_short: str = "Condition"
    semantic_id: str = EXECUTION_WHEN_CONDITION
    term: Dict[str, ConditionTerm] = {}

WhenCondition_t: TypeAlias = WhenCondition  # a field may share the class's id_short


class WhenThen(SubmodelElementCollection):
    id_short: str = "Then"
    semantic_id: str = EXECUTION_WHEN_THEN
    term: Dict[str, "EffectTerm"] = {}

WhenThen_t: TypeAlias = WhenThen  # a field may share the class's id_short


class When(SubmodelElementCollection):
    """A conditional effect: Then applies where Condition holds when the effect applies."""
    semantic_id: str = EXECUTION_WHEN
    Condition: WhenCondition_t
    Then: WhenThen_t


class Outcome(SubmodelElementCollection):
    """One possible outcome and its effects; what it means (in tolerance, out of tolerance) rides as a
    supplemental semantic id."""
    semantic_id: str = EXECUTION_OUTCOME
    term: Dict[str, "EffectTerm"] = {}


class OneOfEffects(SubmodelElementCollection):
    """Exactly one of its outcomes happens; which is known only once the action has ended (FOND oneof)."""
    semantic_id: str = EXECUTION_ONE_OF
    outcome: Dict[str, Outcome] = {}


EffectTerm = Union[StateEffect, EffectAnd, EffectForAll, When, OneOfEffects]


# ── Time points ──────────────────────────────────────────────────────────────

class PreTerms(SubmodelElementCollection):
    id_short: str = "Pre"
    semantic_id: str = EXECUTION_PRE
    description: str = "What holds when the action starts."
    term: Dict[str, ConditionTerm] = {}

PreTerms_t: TypeAlias = PreTerms  # a field may share the class's id_short


class InvariantTerms(SubmodelElementCollection):
    id_short: str = "Invariant"
    semantic_id: str = EXECUTION_INVARIANT
    description: str = "What holds while the action runs."
    term: Dict[str, ConditionTerm] = {}

InvariantTerms_t: TypeAlias = InvariantTerms  # a field may share the class's id_short


class PostTerms(SubmodelElementCollection):
    id_short: str = "Post"
    semantic_id: str = EXECUTION_POST
    description: str = "What holds when the action has ended."
    term: Dict[str, ConditionTerm] = {}

PostTerms_t: TypeAlias = PostTerms  # a field may share the class's id_short


class ExecutionConditions(SubmodelElementCollection):
    id_short: str = "Conditions"
    semantic_id: str = EXECUTION_CONDITIONS
    Pre: Optional[PreTerms_t] = None
    Invariant: Optional[InvariantTerms_t] = None
    Post: Optional[PostTerms_t] = None

ExecutionConditions_t: TypeAlias = ExecutionConditions  # a field may share the class's id_short


class StartTerms(SubmodelElementCollection):
    id_short: str = "Start"
    semantic_id: str = EXECUTION_START
    description: str = "What changes when the action starts."
    term: Dict[str, EffectTerm] = {}

StartTerms_t: TypeAlias = StartTerms  # a field may share the class's id_short


class DuringTerms(SubmodelElementCollection):
    id_short: str = "During"
    semantic_id: str = EXECUTION_DURING
    description: str = "What is defined while the action runs (assign only)."
    term: Dict[str, EffectTerm] = {}

DuringTerms_t: TypeAlias = DuringTerms  # a field may share the class's id_short


class EndTerms(SubmodelElementCollection):
    id_short: str = "End"
    semantic_id: str = EXECUTION_END
    description: str = "What changes when the action ends."
    term: Dict[str, EffectTerm] = {}

EndTerms_t: TypeAlias = EndTerms  # a field may share the class's id_short


class ExecutionEffects(SubmodelElementCollection):
    id_short: str = "Effects"
    semantic_id: str = EXECUTION_EFFECTS
    Start: Optional[StartTerms_t] = None
    During: Optional[DuringTerms_t] = None
    End: Optional[EndTerms_t] = None

ExecutionEffects_t: TypeAlias = ExecutionEffects  # a field may share the class's id_short


# ── Provenance of a derived Execution ────────────────────────────────────────

class DerivedFrom(ReferenceElement):
    semantic_id: str = EXECUTION_DERIVED_FROM
    description: str = "An element this Execution was derived from (a component's Execution, a skill's steps)."


class Fingerprint(Property):
    id_short: str = "Fingerprint"
    semantic_id: str = EXECUTION_FINGERPRINT
    description: str = "The fingerprint of what it was derived from; the validator re-derives it and compares."

Fingerprint_t: TypeAlias = Fingerprint  # a field may share the class's id_short


class Provenance(SubmodelElementCollection):
    id_short: str = "Provenance"
    semantic_id: str = EXECUTION_PROVENANCE
    description: str = "Present on a derived Execution only: authored Executions have none."
    derived_from: Dict[str, DerivedFrom] = {}
    Fingerprint: Fingerprint_t = Fingerprint()

Provenance_t: TypeAlias = Provenance  # a field may share the class's id_short


# ── Execution ────────────────────────────────────────────────────────────────

class Execution(SubmodelElementCollection):
    id_short: str = "Execution"
    semantic_id: str = EXECUTION
    description: str = "What the capability needs and changes when it runs."
    Subjects: Subjects_t = Subjects()
    Conditions: Optional[ExecutionConditions_t] = None
    Effects: Optional[ExecutionEffects_t] = None
    Provenance: Optional[Provenance_t] = None


# ── Resolve forward references (the term tree is recursive) ──
ExecutionSubject.model_rebuild()
Subjects.model_rebuild()
StateCondition.model_rebuild()
StateEffect.model_rebuild()
And.model_rebuild()
Or.model_rebuild()
Not.model_rebuild()
Body.model_rebuild()
Exists.model_rebuild()
ForAll.model_rebuild()
EffectAnd.model_rebuild()
EffectBody.model_rebuild()
EffectForAll.model_rebuild()
WhenCondition.model_rebuild()
WhenThen.model_rebuild()
When.model_rebuild()
Outcome.model_rebuild()
OneOfEffects.model_rebuild()
PreTerms.model_rebuild()
InvariantTerms.model_rebuild()
PostTerms.model_rebuild()
ExecutionConditions.model_rebuild()
StartTerms.model_rebuild()
DuringTerms.model_rebuild()
EndTerms.model_rebuild()
ExecutionEffects.model_rebuild()
Provenance.model_rebuild()
Execution.model_rebuild()
