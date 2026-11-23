"""
Capability Description — the IDTA template (02020) as the lab's resources state it.

The generated template (``aas_pydantic.submodel_templates.capability_description``) stays pristine. What a
resource states differently, the stations and the modules (ARSO) alike:

- a capability is realized by a skill of the same AAS or of a component's (``RealizedBySkill``: a model
  reference, where IDTA leaves an external one);
- a property is the variable of the resource it is (``SameAs``), so that capabilities naming it talk of one
  state;
- a property constraint is a ``BasicConstraint`` expression; the ConstraintSet is otherwise as IDTA has it, and
  the lab does not use it to say what a capability needs and changes;
- the CapabilityRelations also hold who takes part (``Subjects``), what must hold of them (``ConditionSet``: Pre,
  Invariant, Post) and what the capability changes (``EffectSet``: Start, During, End), as trees of terms
  (``execution``): what the planners, the behaviour tree and the DMP read.

Everything else keeps its IDTA ids, so a consumer of the standard template reads the container as before and
ignores the extension. The meaning of a capability (``lab:Filling``) rides as a supplemental semantic id on its
Capability element.

The classes are named after the modules, where ARSO introduced them (``ModuleCapabilityDescription``); the
stations state their capabilities with the same ones.
"""

from __future__ import annotations

from typing import Dict, Optional, TypeAlias

from aas_pydantic import ModelReference
from aas_pydantic.submodel_templates import capability_description as cd

from aas_model.submodel_templates.execution import ConditionSet, EffectSet, Subjects

ConditionSet_t: TypeAlias = ConditionSet  # the field shares the class's id_short
EffectSet_t: TypeAlias = EffectSet  # the field shares the class's id_short
Subjects_t: TypeAlias = Subjects  # the field shares the class's id_short


class RealizedBySkill(cd.CapabilityRealizedBy):
    """IDTA 02020 leaves the skill open (an external reference); ARSO wants a skill of the same AAS
    or of a component's (its primitive), so here it is a model reference to it."""
    second: ModelReference = ModelReference()


class SameAs(cd.SameProperty):
    """IDTA 02020 leaves both ends open; here the property (first) names the variable of the module
    it is (second), so that the capabilities naming it talk of one state."""
    first: ModelReference = ModelReference()
    second: ModelReference = ModelReference()


class StatedProperty(cd.PropertyContainer):
    SameProperty: Dict[str, SameAs] = {}


class StatedPropertySet(cd.PropertySet):
    PropertyContainer: Dict[str, StatedProperty] = {}


class BasicConstraintContainer(cd.PropertyConstraintContainer):
    """A property constraint in the form a resource states a characteristic (ARSO 0.11): a BasicConstraint, an
    expression over the capability's properties. IDTA 02020 has exactly one of four forms; the generated class
    asks for all four."""
    CustomConstraint: Optional[cd.CustomConstraint] = None
    OCLConstraint: Optional[cd.OCLConstraint] = None
    OperationConstraint: Optional[cd.OperationConstraint] = None


class ModuleConstraintSet(cd.ConstraintSet):
    PropertyConstraintContainer: Dict[str, BasicConstraintContainer] = {}


class ModuleCapabilityRelations(cd.CapabilityRelations):
    CapabilityRealizedBy: Dict[str, RealizedBySkill] = {}
    ConstraintSet: Dict[str, ModuleConstraintSet] = {}
    Subjects: Optional[Subjects_t] = None
    ConditionSet: Optional[ConditionSet_t] = None
    EffectSet: Optional[EffectSet_t] = None


class ModuleCapabilityContainer(cd.CapabilityContainer):
    """One capability: its properties and its relations, with who takes part and what it needs and changes."""
    PropertySet: Dict[str, StatedPropertySet] = {}
    CapabilityRelations: Optional[ModuleCapabilityRelations] = None


class ModuleCapabilitySet(cd.CapabilitySet):
    CapabilityContainer: Dict[str, ModuleCapabilityContainer] = {}


class ModuleCapabilityDescription(cd.CapabilityDescription):
    """The capabilities a resource offers, each realized by one of its skills, and in a set per
    component the capabilities of its components, each realized by a primitive (ARSO 0.11)."""
    CapabilitySet: Dict[str, ModuleCapabilitySet] = {}


for _model in (ModuleConstraintSet, ModuleCapabilityRelations,
               ModuleCapabilityContainer, ModuleCapabilitySet, ModuleCapabilityDescription):
    _model.model_rebuild()
