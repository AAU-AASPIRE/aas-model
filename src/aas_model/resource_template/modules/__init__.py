"""Resources as the resource ontology ARSO describes them: module, component, production system.

``docs/lab-submodels/`` describes their submodels; ``docs/lab-aas.md`` the AASs.
"""

from .asset import RESOURCE, ArsoResource, Component, Module, ProductionSystem
from .submodels import (
    BasicConstraintContainer, LabNameplate, lab_nameplate, LocatedEntryNode, LocatedNode, LocatedStructures, ModuleCapabilityContainer,
    ModuleCapabilityDescription, ModuleCapabilityRelations, ModuleCapabilitySet, ModuleConstraintSet,
    ModuleControlConfiguration, ModuleInterfaces, ModuleSkill, ModuleSkills, RealizedBySkill, SameAs,
    StatedProperty, StatedPropertySet,
)

__all__ = [
    "RESOURCE", "ArsoResource", "Component", "Module", "ProductionSystem",
    "BasicConstraintContainer", "LabNameplate", "lab_nameplate", "LocatedEntryNode", "LocatedNode", "LocatedStructures",
    "ModuleCapabilityContainer", "ModuleCapabilityDescription", "ModuleCapabilityRelations",
    "ModuleCapabilitySet", "ModuleConstraintSet", "ModuleControlConfiguration", "ModuleInterfaces",
    "ModuleSkill", "ModuleSkills", "RealizedBySkill", "SameAs", "StatedProperty", "StatedPropertySet",
]
