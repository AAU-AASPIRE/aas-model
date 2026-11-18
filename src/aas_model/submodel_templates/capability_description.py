"""
Capability Description — the IDTA template (02020) as the lab's resources state it.

The generated template (``aas_pydantic.submodel_templates.capability_description``) stays pristine. What a
resource states differently, the stations and the modules (ARSO) alike:

- a capability is realized by a skill of the same AAS or of a component's (``RealizedBySkill``: a model
  reference, where IDTA leaves an external one);
- a property is the variable of the resource it is (``SameAs``), so that capabilities naming it talk of
  one state;
- a property constraint is a ``BasicConstraint`` expression;
- a CapabilityContainer may also hold an ``Execution``: what the capability needs and changes when it runs
  (``execution``).

The two kinds of constraint answer different questions: the ConstraintSet holds the capability's
characteristics (ranges, tolerances, formats) and is what matching reads; the Execution holds the conditions
on and the effects to the state of the subjects taking part, and is what the planners, the behaviour tree and
the DMP read. Everything else keeps its IDTA ids, so a consumer of the standard template reads the container as
before and ignores the extension. The meaning of a capability (``lab:Filling``) rides as a supplemental
semantic id on its Capability element.

The classes are named after the modules, where ARSO introduced them (``ModuleCapabilityDescription``); the
stations state their capabilities with the same ones.
"""

from __future__ import annotations

from typing import Dict, Optional, TypeAlias

from aas_pydantic import ModelReference
from aas_pydantic.submodel_templates import capability_description as cd

from aas_model.submodel_templates.execution import Execution

Execution_t: TypeAlias = Execution  # the field shares the class's id_short


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
    """A property constraint in the form a resource states it (ARSO 0.11): a BasicConstraint, an
    expression over the capability's properties. IDTA 02020 has exactly one of four forms; the
    generated class asks for all four."""
    CustomConstraint: Optional[cd.CustomConstraint] = None
    OCLConstraint: Optional[cd.OCLConstraint] = None
    OperationConstraint: Optional[cd.OperationConstraint] = None


class ModuleConstraintSet(cd.ConstraintSet):
    PropertyConstraintContainer: Dict[str, BasicConstraintContainer] = {}


class ModuleCapabilityRelations(cd.CapabilityRelations):
    CapabilityRealizedBy: Dict[str, RealizedBySkill] = {}
    ConstraintSet: Dict[str, ModuleConstraintSet] = {}


class ModuleCapabilityContainer(cd.CapabilityContainer):
    """One capability: its properties, its relations and, where it is stated, what it needs and changes."""
    PropertySet: Dict[str, StatedPropertySet] = {}
    CapabilityRelations: Optional[ModuleCapabilityRelations] = None
    Execution: Optional[Execution_t] = None


class ModuleCapabilitySet(cd.CapabilitySet):
    CapabilityContainer: Dict[str, ModuleCapabilityContainer] = {}


class ModuleCapabilityDescription(cd.CapabilityDescription):
    """The capabilities a resource offers, each realized by one of its skills, and in a set per
    component the capabilities of its components, each realized by a primitive (ARSO 0.11)."""
    CapabilitySet: Dict[str, ModuleCapabilitySet] = {}


ModuleCapabilityContainer.model_rebuild()
ModuleCapabilitySet.model_rebuild()
ModuleCapabilityDescription.model_rebuild()
