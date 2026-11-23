"""
Capability Description — the IDTA template (02020) as the lab's resources state it.

The generated template (``aas_pydantic.submodel_templates.capability_description``) stays pristine. What a
resource states differently, the stations and the modules (ARSO) alike:

- a capability is realized by a skill of the same AAS or of a component's (``RealizedBySkill``: a model
  reference, where IDTA leaves an external one);
- a property is the same as another (``SameAs``): a variable of the resource, or, named ``OfSubject``, a
  subject of the capability, whose property of the same meaning it is;
- a property constraint is either a ``BasicConstraint`` expression over the capability's properties
  (``BasicConstraintContainer``: a characteristic, what matching reads) or a ``CustomConstraint`` holding a term
  on the state of its subjects (``StateConstraintContainer``: a condition, what the planners, the behaviour tree
  and the DMP read), its PropertyConditionalType saying when it holds;
- a CapabilityContainer names who takes part (``Subjects``), and its CapabilityRelations hold, beside the
  ConstraintSet, what the capability changes (``EffectSet``). Both are the lab's (``execution``).

Everything else keeps its IDTA ids, so a consumer of the standard template reads the container as before and
ignores the extension. The meaning of a capability (``lab:Filling``) rides as a supplemental semantic id on its
Capability element.

The classes are named after the modules, where ARSO introduced them (``ModuleCapabilityDescription``); the
stations state their capabilities with the same ones.
"""

from __future__ import annotations

from typing import Dict, List, Optional, TypeAlias, Union

from aas_pydantic import ModelReference
from aas_pydantic.submodel_templates import capability_description as cd

from aas_model.constants import EXECUTION_STATE_CONSTRAINT
from aas_model.submodel_templates.execution import ConditionTerm, EffectSet, Subjects

EffectSet_t: TypeAlias = EffectSet  # the field shares the class's id_short
Subjects_t: TypeAlias = Subjects  # the field shares the class's id_short


class RealizedBySkill(cd.CapabilityRealizedBy):
    """IDTA 02020 leaves the skill open (an external reference); ARSO wants a skill of the same AAS
    or of a component's (its primitive), so here it is a model reference to it."""
    second: ModelReference = ModelReference()


class SameAs(cd.SameProperty):
    """IDTA 02020 leaves both ends open; here the property's value (first) names what it is the same as (second):
    the variable of the resource it is, so that the capabilities naming it talk of one state; or, as
    ``OfSubject``, an entry of the capability's Subjects: the property is that subject's property of the meaning
    the value carries (a unit's ContentVolume)."""
    first: ModelReference = ModelReference()
    second: ModelReference = ModelReference()


class StatedProperty(cd.PropertyContainer):
    SameProperty: Dict[str, SameAs] = {}


class StatedPropertySet(cd.PropertySet):
    PropertyContainer: Dict[str, StatedProperty] = {}


class HasProperty(cd.ConstraintHasProperty):
    """The constraint (first) and a property it reads (second, a PropertySet entry's value), as model references."""
    first: ModelReference = ModelReference()
    second: ModelReference = ModelReference()


class StatedConstraintPropertyRelations(cd.ConstraintPropertyRelations):
    ConstraintHasProperty: Dict[str, HasProperty] = {}

StatedConstraintPropertyRelations_t: TypeAlias = StatedConstraintPropertyRelations  # the field's id_short


class BasicConstraintContainer(cd.PropertyConstraintContainer):
    """A property constraint in the form a resource states a characteristic (ARSO 0.11): a BasicConstraint, an
    expression over the capability's properties. IDTA 02020 has exactly one of four forms; the generated class
    asks for all four."""
    CustomConstraint: Optional[cd.CustomConstraint] = None
    OCLConstraint: Optional[cd.OCLConstraint] = None
    OperationConstraint: Optional[cd.OperationConstraint] = None


class StateConditionalType(cd.PropertyConditionalType):
    """When the condition holds (02020's PropertyConditionalType): before the capability is applied, while it
    runs, after it, or in several of these."""
    value: str = "Pre"
    FORM_CHOICES = ("Pre", "Post", "Invariant", "PrePost", "PreInvariant", "InvariantPost", "PrePostInvariant")

StateConditionalType_t: TypeAlias = StateConditionalType  # the field's id_short


class StateConstraint(cd.CustomConstraint):
    """02020's freely defined constraint, here one term on the state of the capability's subjects (a condition, or
    And, Or, Not, Exists, ForAll of conditions). The supplemental semantic id says it is one."""
    supplemental_semantic_ids: List[str] = [EXECUTION_STATE_CONSTRAINT]
    value: Dict[str, ConditionTerm] = {}

StateConstraint_t: TypeAlias = StateConstraint  # the field's id_short


class StateConstraintContainer(cd.PropertyConstraintContainer):
    """A condition of the capability: a CustomConstraint holding its term, when it holds, and the properties it
    reads."""
    BasicConstraint: Optional[cd.BasicConstraint] = None
    CustomConstraint: StateConstraint_t
    OCLConstraint: Optional[cd.OCLConstraint] = None
    OperationConstraint: Optional[cd.OperationConstraint] = None
    ConstraintType: cd.ConstraintType = cd.ConstraintType(value="CustomConstraint")
    PropertyConditionalType: StateConditionalType_t
    ConstraintPropertyRelations: StatedConstraintPropertyRelations_t


class ModuleConstraintSet(cd.ConstraintSet):
    PropertyConstraintContainer: Dict[str, Union[BasicConstraintContainer, StateConstraintContainer]] = {}


class ModuleCapabilityRelations(cd.CapabilityRelations):
    CapabilityRealizedBy: Dict[str, RealizedBySkill] = {}
    ConstraintSet: Dict[str, ModuleConstraintSet] = {}
    EffectSet: Optional[EffectSet_t] = None


class ModuleCapabilityContainer(cd.CapabilityContainer):
    """One capability: who takes part, its properties and its relations, with what it needs and changes."""
    Subjects: Optional[Subjects_t] = None
    PropertySet: Dict[str, StatedPropertySet] = {}
    CapabilityRelations: Optional[ModuleCapabilityRelations] = None


class ModuleCapabilitySet(cd.CapabilitySet):
    CapabilityContainer: Dict[str, ModuleCapabilityContainer] = {}


class ModuleCapabilityDescription(cd.CapabilityDescription):
    """The capabilities a resource offers, each realized by one of its skills, and in a set per
    component the capabilities of its components, each realized by a primitive (ARSO 0.11)."""
    CapabilitySet: Dict[str, ModuleCapabilitySet] = {}


for _model in (StateConstraint, StateConstraintContainer, ModuleConstraintSet, ModuleCapabilityRelations,
               ModuleCapabilityContainer, ModuleCapabilitySet, ModuleCapabilityDescription):
    _model.model_rebuild()
