"""
Execution semantics — what a capability needs and changes, inside IDTA 02020 (plans/kg-planning-execution-PLAN.md, 4.2).

A capability states what it needs and changes in the places IDTA 02020 has for it, extended where it has none
(``capability_description`` composes them into a CapabilityContainer):

::

    CapabilityContainer
    ├── Capability
    ├── Subjects                         (lab) who takes part, one ReferenceElement each
    ├── PropertySet                      (02020) the capability's properties, and the properties of its subjects
    │   └── <property>                   a subject's is the same as that subject's (SameProperty ``OfSubject``)
    └── CapabilityRelations
        ├── ConstraintSet                (02020)
        │   └── <condition>              PropertyConstraintContainer: PropertyConditionalType Pre / Invariant / Post,
        │                                a CustomConstraint holding one term, ConstraintHasProperty to what it reads
        └── EffectSet                    (lab)
            └── <effect>                 EffectContainer: EffectTimingType Start / During / End, an Effect holding
                                         one term, EffectHasProperty to what it changes

**Subjects** are ReferenceElements: the idShort is the name a planning domain gives the parameter, the semantic id
the role (Self, Component, Product, Carrier, a quantified Variable), the value what the subject is: an AAS (Self,
a component), the Operation variable a run-time subject arrives in (a unit), or nothing (a parameter nothing binds
at this level, or a quantified variable). What kind of thing it is (a container, a shuttle) rides as a
supplemental semantic id.

**Properties.** A term is about a property in the capability's PropertySet. A property of a subject (a unit's
ContentVolume, an axis's Position) is a PropertyContainer whose value's supplemental semantic id is its meaning and
whose SameProperty ``OfSubject`` names the subject; its value, where it has one, is the range it takes. Matching
reads a property's value; a property without one is state, which the state store holds.

**Terms.** A term is an SMC whose semantic id says what it is:

- ``Condition`` / ``Effect``: ``Property`` references the PropertySet entry's value; ``Operator`` is one of
  the operators below; the operand is exactly one of ``Value`` (a literal), ``ValueReference`` (a parameter, a
  property, a subject) or ``Formula`` with its ``Uses``. An End effect may carry a ``Rate``: the change runs
  continuously at that rate until the end.
- ``And``, ``Or``, ``Not``, ``Exists``, ``ForAll`` combine conditions; ``And``, ``ForAll``, ``When`` and
  ``OneOf`` combine effects. The conditions of one ConditionalType, and the effects of one timing, all hold (an
  implicit And across containers). A quantifier's ``Variable`` references a Subject with role Variable.

The classes are named apart from other templates' (``StateCondition``): aas_pydantic reads an element back as the
class its dump names. The idShorts of terms (``Term``) carry no meaning; only those in ``Uses`` do: they are the
names the formula uses. The formula is the only text: arithmetic over those names, numbers and ``pi``. Everything
else is a reference or a vocabulary id, so nothing is matched by name. What a consumer can evaluate is checked by
the validator of the shared execution package, not here.
"""

from __future__ import annotations

from typing import Dict, Optional, TypeAlias, Union

from aas_pydantic import Key, ModelReference, Property, ReferenceElement, RelationshipElement, SubmodelElementCollection

from aas_model.constants import (
    EXECUTION_AND, EXECUTION_BODY, EXECUTION_CONDITION, EXECUTION_CONDITION_OPERATOR, EXECUTION_EFFECT,
    EXECUTION_EFFECT_CONTAINER, EXECUTION_EFFECT_DEFINITION, EXECUTION_EFFECT_HAS_PROPERTY, EXECUTION_EFFECT_OPERATOR,
    EXECUTION_EFFECT_PROPERTY_RELATIONS, EXECUTION_EFFECT_SET, EXECUTION_EFFECT_TIMING, EXECUTION_EXISTS,
    EXECUTION_FOR_ALL, EXECUTION_FORMULA_USE, EXECUTION_FORMULA_USES, EXECUTION_NOT, EXECUTION_ONE_OF, EXECUTION_OR,
    EXECUTION_OUTCOME, EXECUTION_QUANTIFIED_VARIABLE, EXECUTION_RATE, EXECUTION_SUBJECT_CARRIER,
    EXECUTION_SUBJECT_COMPONENT, EXECUTION_SUBJECT_PRODUCT, EXECUTION_SUBJECT_SELF, EXECUTION_SUBJECT_VARIABLE,
    EXECUTION_SUBJECTS, EXECUTION_TERM_FORMULA, EXECUTION_TERM_PROPERTY, EXECUTION_TERM_VALUE,
    EXECUTION_TERM_VALUE_REFERENCE, EXECUTION_WHEN, EXECUTION_WHEN_CONDITION, EXECUTION_WHEN_THEN,
)


# ── Subjects ─────────────────────────────────────────────────────────────────

class SelfSubject(ReferenceElement):
    """The resource owning the capability, and so the invoked Operation: its own AAS."""
    semantic_id: str = EXECUTION_SUBJECT_SELF
    description: str = "The resource offering the capability."
    value: ModelReference = ModelReference(key=(Key(type_="AssetAdministrationShell", value="{aas_id}"),))


class ComponentSubject(ReferenceElement):
    """A component of the resource: the component's AAS."""
    semantic_id: str = EXECUTION_SUBJECT_COMPONENT
    description: str = "A component of the resource."


class ProductSubject(ReferenceElement):
    """A unit of a product, known only at run time: the Operation variable it arrives in, or nothing where no
    Operation of this capability carries it."""
    KEEP_WITHOUT_VALUE = True
    semantic_id: str = EXECUTION_SUBJECT_PRODUCT
    description: str = "A unit of a product."


class CarrierSubject(ReferenceElement):
    """A carrier that is not the resource itself (a shuttle a unit rides): the Operation variable it arrives in."""
    KEEP_WITHOUT_VALUE = True
    semantic_id: str = EXECUTION_SUBJECT_CARRIER
    description: str = "A carrier taking part."


class VariableSubject(ReferenceElement):
    """A quantified variable: no value; the type it ranges over rides as a supplemental semantic id."""
    KEEP_WITHOUT_VALUE = True
    semantic_id: str = EXECUTION_SUBJECT_VARIABLE
    description: str = "A variable a quantifier ranges over."


ExecutionSubject = Union[SelfSubject, ComponentSubject, ProductSubject, CarrierSubject, VariableSubject]


class Subjects(SubmodelElementCollection):
    id_short: str = "Subjects"
    semantic_id: str = EXECUTION_SUBJECTS
    description: str = "Who takes part, each named as the planning domain's parameter is."
    subject: Dict[str, ExecutionSubject] = {}

Subjects_t: TypeAlias = Subjects  # a field may share the class's id_short


# ── Atoms ────────────────────────────────────────────────────────────────────

class TermProperty(ReferenceElement):
    id_short: str = "Property"
    semantic_id: str = EXECUTION_TERM_PROPERTY
    description: str = "The property the term is about: the value of an entry of the capability's PropertySet."

TermProperty_t: TypeAlias = TermProperty  # a field may share the class's id_short


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
    """One name of the formula (its idShort) and what it stands for: a property of the capability (a PropertySet
    entry's value, a subject's property among them) or an Operation variable."""
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
    """One property compared with an operand."""
    semantic_id: str = EXECUTION_CONDITION
    Property: TermProperty_t = TermProperty()
    Operator: ConditionOperator_t = ConditionOperator()
    Value: Optional[TermValue_t] = None
    ValueReference: Optional[TermValueReference_t] = None
    Formula: Optional[TermFormula_t] = None
    Uses: Optional[FormulaUses_t] = None


class StateEffect(SubmodelElementCollection):
    """One property changed."""
    semantic_id: str = EXECUTION_EFFECT
    Property: TermProperty_t = TermProperty()
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
    description: str = "The Subject (role Variable) the quantifier ranges over."

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


# ── Effects: the EffectSet beside the ConstraintSet ──────────────────────────

class EffectTimingType(Property):
    """When the effect applies: as the action starts, while it runs (a definition, assign only), as it ends."""
    id_short: str = "EffectTimingType"
    semantic_id: str = EXECUTION_EFFECT_TIMING
    value_type: str = "xs:string"
    FORM_CHOICES = ("Start", "During", "End")

EffectTimingType_t: TypeAlias = EffectTimingType  # a field may share the class's id_short


class EffectDefinition(SubmodelElementCollection):
    """The effect: one term (an effect, or And, ForAll, When, OneOf of effects)."""
    id_short: str = "Effect"
    semantic_id: str = EXECUTION_EFFECT_DEFINITION
    term: Dict[str, EffectTerm] = {}

EffectDefinition_t: TypeAlias = EffectDefinition  # a field may share the class's id_short


class EffectHasProperty(RelationshipElement):
    """Relates the Effect as first element to a property it changes (a PropertySet entry's value) as second, as
    02020's ConstraintHasProperty does for a constraint."""
    semantic_id: str = EXECUTION_EFFECT_HAS_PROPERTY
    first: ModelReference = ModelReference()
    second: ModelReference = ModelReference()

EffectHasProperty_t: TypeAlias = EffectHasProperty  # a field shares the class's name


class EffectPropertyRelations(SubmodelElementCollection):
    id_short: str = "EffectPropertyRelations"
    semantic_id: str = EXECUTION_EFFECT_PROPERTY_RELATIONS
    description: str = "The properties the effect changes."
    EffectHasProperty: Dict[str, EffectHasProperty_t] = {}

EffectPropertyRelations_t: TypeAlias = EffectPropertyRelations  # a field may share the class's id_short


class EffectContainer(SubmodelElementCollection):
    """One effect of the capability, as a PropertyConstraintContainer is one constraint."""
    semantic_id: str = EXECUTION_EFFECT_CONTAINER
    EffectTimingType: EffectTimingType_t
    Effect: EffectDefinition_t
    EffectPropertyRelations: EffectPropertyRelations_t

EffectContainer_t: TypeAlias = EffectContainer  # a field shares the class's name


class EffectSet(SubmodelElementCollection):
    id_short: str = "EffectSet"
    semantic_id: str = EXECUTION_EFFECT_SET
    description: str = "What the capability changes, one EffectContainer per effect."
    EffectContainer: Dict[str, EffectContainer_t] = {}

EffectSet_t: TypeAlias = EffectSet  # a field may share the class's id_short


# ── Resolve forward references (the term tree is recursive) ──
for _model in (Subjects, StateCondition, StateEffect, And, Or, Not, Body, Exists, ForAll, EffectAnd, EffectBody,
               EffectForAll, WhenCondition, WhenThen, When, Outcome, OneOfEffects, EffectDefinition, EffectContainer,
               EffectSet):
    _model.model_rebuild()
