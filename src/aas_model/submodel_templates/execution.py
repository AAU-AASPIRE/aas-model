"""
Execution semantics — what a capability needs and changes (plans/kg-planning-execution-PLAN.md, 4.2).

Three SMCs in a CapabilityContainer's CapabilityRelations, beside IDTA 02020's relations (RealizedBy, ComposedOf,
GeneralizedBy) and its ConstraintSet, which the lab leaves as IDTA has it and does not use
(``capability_description`` composes them)::

    CapabilityRelations
    ├── CapabilityRealizedBy, ComposedOfSet, GeneralizedBySet     02020
    ├── ConstraintSet                                             02020, as IDTA has it
    ├── Subjects                 who takes part, one ReferenceElement each
    ├── ConditionSet
    │   ├── Pre                  terms, all of which hold at the start
    │   ├── Invariant            ... throughout
    │   └── Post                 ... at the end
    └── EffectSet
        ├── Start                effect terms applied when the action starts
        ├── During               definitions that hold while it runs (assign only)
        └── End                  effect terms applied when it ends

**Subjects** is a list (SML) of ReferenceElements, in order, each with a display name saying who it is (its items
have no idShort; a term references a subject by its index). The value says what the subject is: a ModelReference
to the AAS or element it is where it is one particular asset or place (Self, the resource's own AAS; a component's
AAS; a module's own transfer point), or an ExternalReference to the semantic id of what it stands for where it is
only known at run time (a unit: the asset type of products; a carrier: the asset type of shuttles; a place: a
transfer point). Who a subject is in a call is the call's: the realizing skill's Operation carries the capability
it executes (``Capability``) and who its subjects are, one item per subject in this list's order
(``Grounding``); the planner, who chose them, fills both.

**Duration**, in the CapabilityRelations beside them, says how long the action takes where no Rate of an End
effect does: a nominal value, or a formula over the capability's properties and the call's parameters.

**Terms.** A term is an SMC whose semantic id says what it is:

- ``Condition`` / ``Effect``: one property of one subject. The property rides as a supplemental semantic id
  (the lab vocabulary); ``Subject`` references an item of Subjects; ``Operator`` is one of the operators
  below; the operand is exactly one of ``Value`` (a literal), ``ValueReference`` (a parameter, a property of
  the capability, a subject) or ``Formula`` with its ``Uses``. An End effect may carry a ``Rate``: the change
  runs continuously at that rate until the end.
- ``And``, ``Or``, ``Not``, ``Exists``, ``ForAll`` combine conditions; ``And``, ``ForAll``, ``When`` and
  ``OneOf`` combine effects; they nest freely. Several terms directly under Pre, End, ... all hold (an implicit
  And). A quantifier's ``Variable`` references the Subject it ranges over; its ``Body`` holds the terms.

The classes are named apart from other templates' (``StateCondition``, ``PreTerms``): aas_pydantic reads an
element back as the class its dump names. The idShorts of terms (``Term_00``) carry no meaning and keep them in
order; a term's display name says in words what it states ("Needle at fill depth"). Only the idShorts in ``Uses``
carry meaning: they are the names the formula uses. The formula is the only text: arithmetic over those names,
numbers and ``pi``. Everything else is a reference or a vocabulary id, so nothing is matched by name. What a
consumer can evaluate is checked by the validator of the shared execution package, not here.
"""

from __future__ import annotations

from typing import ClassVar, Dict, List, Optional, TypeAlias, Union

from aas_pydantic import (
    ExternalReference, Key, ModelReference, Property, ReferenceElement, SubmodelElementCollection, SubmodelElementList,
)

from aas_model.constants import (
    EXECUTION_AND, EXECUTION_BODY, EXECUTION_CONDITION, EXECUTION_CONDITION_OPERATOR, EXECUTION_CONDITION_SET,
    EXECUTION_DURING, EXECUTION_EFFECT, EXECUTION_EFFECT_OPERATOR, EXECUTION_EFFECT_SET, EXECUTION_END,
    EXECUTION_EXISTS, EXECUTION_FOR_ALL, EXECUTION_FORMULA_USE, EXECUTION_FORMULA_USES, EXECUTION_INVARIANT,
    EXECUTION_NOT, EXECUTION_ONE_OF, EXECUTION_OR, EXECUTION_OUTCOME, EXECUTION_POST, EXECUTION_PRE,
    EXECUTION_QUANTIFIED_VARIABLE, EXECUTION_RATE, EXECUTION_START, EXECUTION_SUBJECT, EXECUTION_SUBJECTS,
    EXECUTION_TERM_FORMULA, EXECUTION_TERM_SUBJECT, EXECUTION_TERM_VALUE,
    EXECUTION_TERM_VALUE_REFERENCE, EXECUTION_WHEN, EXECUTION_WHEN_CONDITION, EXECUTION_WHEN_THEN, LAB,
    PRODUCT_ASSET_TYPE, SHUTTLE_ASSET_TYPE, EXECUTION_DURATION,
)


# ── Subjects ─────────────────────────────────────────────────────────────────

class ExecutionSubject(ReferenceElement):
    """Who takes part: an AAS (a ModelReference), or the semantic id of what it stands for (an ExternalReference)."""
    semantic_id: str = EXECUTION_SUBJECT
    description: str = "A subject of the capability."


class SelfSubject(ExecutionSubject):
    """The resource owning the capability, and so the invoked Operation: its own AAS."""
    description: str = "The resource offering the capability."
    value: ModelReference = ModelReference(key=(Key(type_="AssetAdministrationShell", value="{aas_id}"),))


class UnitSubject(ExecutionSubject):
    """A unit of a product, known only at run time: what it stands for is the asset type of products; which unit it
    is, is the call's Grounding."""
    description: str = "A unit of a product."
    value: ExternalReference = ExternalReference(key=(Key(type_="GlobalReference", value=PRODUCT_ASSET_TYPE),))


class CarrierSubject(ExecutionSubject):
    """A carrier, known only at run time (the shuttle that brings or takes a unit): what it stands for is the asset
    type of shuttles; which shuttle it is, is the call's Grounding."""
    description: str = "A carrier."
    value: ExternalReference = ExternalReference(key=(Key(type_="GlobalReference", value=SHUTTLE_ASSET_TYPE),))


class PlaceSubject(ExecutionSubject):
    """A place a shuttle stops at to hand a container over, known only at run time: what it stands for is a
    transfer point (``lab:TransferPoint``, the meaning of such a coordinate in a module's Coordinates), so a module's
    base or mount is no place to send a shuttle to; which transfer point it is, is the call's Grounding."""
    description: str = "A transfer point."
    value: ExternalReference = ExternalReference(key=(Key(type_="GlobalReference", value=f"{LAB}TransferPoint"),))


class Subjects(SubmodelElementList):
    """Who takes part, in order; each item says in its display name who it is ("Container in the nest")."""
    id_short: str = "Subjects"
    semantic_id: str = EXECUTION_SUBJECTS
    description: str = "Who takes part, in order."
    type_value_list_element: str = "ReferenceElement"
    semantic_id_list_element: str = EXECUTION_SUBJECT
    item_type: ClassVar = ExecutionSubject
    value: List[Union[SelfSubject, UnitSubject, CarrierSubject, PlaceSubject, ExecutionSubject]] = []

Subjects_t: TypeAlias = Subjects  # a field may share the class's id_short


# ── Atoms ────────────────────────────────────────────────────────────────────

class TermSubject(ReferenceElement):
    id_short: str = "Subject"
    semantic_id: str = EXECUTION_TERM_SUBJECT
    description: str = "The subject whose property the term is about: an item of Subjects."

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
    """An operand that is an element: an Operation variable (a parameter), a property of the capability, a
    subject."""
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
    """One name of the formula (its idShort) and what it stands for: an element (a property of the capability, an
    Operation variable), or a property of a subject, referenced as the item of Subjects with the property's
    meaning as supplemental semantic id (the unit's ``lab:InnerBottomHeight``)."""
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


class QuantifiedVariable(ReferenceElement):
    id_short: str = "Variable"
    semantic_id: str = EXECUTION_QUANTIFIED_VARIABLE
    description: str = "The Subject the quantifier ranges over (its value: the semantic id of what it ranges over)."

QuantifiedVariable_t: TypeAlias = QuantifiedVariable  # a field may share the class's id_short


class Body(SubmodelElementCollection):
    id_short: str = "Body"
    semantic_id: str = EXECUTION_BODY
    term: Dict[str, "ConditionTerm"] = {}

Body_t: TypeAlias = Body  # a field may share the class's id_short


class Exists(SubmodelElementCollection):
    """The Body holds for at least one value of the Variable."""
    semantic_id: str = EXECUTION_EXISTS
    Variable: QuantifiedVariable_t
    Body: Body_t


class ForAll(SubmodelElementCollection):
    """The Body holds for every value of the Variable."""
    semantic_id: str = EXECUTION_FOR_ALL
    Variable: QuantifiedVariable_t
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
    Variable: QuantifiedVariable_t
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


# ── Duration ─────────────────────────────────────────────────────────────────

class ExecutionDuration(SubmodelElementCollection):
    """How long the action takes, in seconds: a nominal ``Value``, or a ``Formula`` over its ``Uses`` (the
    capability's properties, the call's parameters). Stated where no Rate of an End effect says it; a learned
    duration from the TSDB replaces a nominal one later (D11)."""
    id_short: str = "Duration"
    semantic_id: str = EXECUTION_DURATION
    description: str = "How long the action takes, in seconds."
    Value: Optional[TermValue_t] = None
    Formula: Optional[TermFormula_t] = None
    Uses: Optional[FormulaUses_t] = None

ExecutionDuration_t: TypeAlias = ExecutionDuration  # a field may share the class's id_short


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


class ConditionSet(SubmodelElementCollection):
    id_short: str = "ConditionSet"
    semantic_id: str = EXECUTION_CONDITION_SET
    description: str = "What must hold of the subjects: at the start, throughout, at the end."
    Pre: Optional[PreTerms_t] = None
    Invariant: Optional[InvariantTerms_t] = None
    Post: Optional[PostTerms_t] = None

ConditionSet_t: TypeAlias = ConditionSet  # a field may share the class's id_short


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


class EffectSet(SubmodelElementCollection):
    id_short: str = "EffectSet"
    semantic_id: str = EXECUTION_EFFECT_SET
    description: str = "What the action changes: as it starts, while it runs, as it ends."
    Start: Optional[StartTerms_t] = None
    During: Optional[DuringTerms_t] = None
    End: Optional[EndTerms_t] = None

EffectSet_t: TypeAlias = EffectSet  # a field may share the class's id_short


# ── Resolve forward references (the term tree is recursive) ──
for _model in (Subjects, StateCondition, StateEffect, And, Or, Not, Body, Exists, ForAll, EffectAnd, EffectBody,
               EffectForAll, WhenCondition, WhenThen, When, Outcome, OneOfEffects, PreTerms, InvariantTerms, PostTerms,
               ConditionSet, StartTerms, DuringTerms, EndTerms, EffectSet):
    _model.model_rebuild()
