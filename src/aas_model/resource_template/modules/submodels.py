"""The submodels of a resource as the resource ontology ARSO describes it.

The classes of ARSO's own submodels are generated (``aas_model.submodel_templates.arso``). Declared
here is what they leave open, and the changes to IDTA templates a module needs:

- **Skills**: a skill under a name of its own (``ModuleSkill``), so it is not read back as the
  Control Component Instance's ``Skill``.
- **Capability Description** (IDTA 02020): a capability is realized by a skill of the same AAS or of
  a component's (a model reference, where IDTA leaves an external one); a property is the variable
  of the module it is (``SameAs``); a constraint is a ``BasicConstraint`` expression.
- **Asset Interfaces Description**: one OPC UA server, no MQTT.
- **Hierarchical Structures**: parts that have parts in turn.
"""

from __future__ import annotations

from typing import Dict, Optional

from aas_pydantic import ModelReference, Property
from aas_pydantic.submodel_templates import capability_description as cd
from aas_pydantic.submodel_templates.hierarchical_structures import (
    ArcheType, ArcheType_t, EntryNode, HierarchicalStructures, Node,
)
from aas_pydantic.submodel_templates.nameplate import (
    CountryOfOrigin, CountryOfOrigin_t, ManufacturerName, ManufacturerName_t, ManufacturerProductDesignation,
    ManufacturerProductDesignation_t, OrderCodeOfManufacturer, OrderCodeOfManufacturer_t, URIOfTheProduct,
    URIOfTheProduct_t, YearOfConstruction, YearOfConstruction_t,
)

from aas_model.constants import BASE_URL
from aas_model.resource_template.resources import ResourceNameplate
from aas_model.submodel_templates.aid import DmpAssetInterfacesDescription, DmpOpcuaInterface, MqttInterface
from aas_model.submodel_templates.arso import skills
from aas_model.submodel_templates.arso.control_configuration import ControlConfiguration


class LabNameplate(ResourceNameplate):
    """The nameplate of an asset the lab makes itself (its address is ``ResourceNameplate``'s), which a resource
    or a product then states its own values in."""
    URIOfTheProduct: URIOfTheProduct_t = URIOfTheProduct(value=f"{BASE_URL}/product/1")
    ManufacturerName: ManufacturerName_t = ManufacturerName(value={"en": "AAU Smart Production Lab"})
    ManufacturerProductDesignation: ManufacturerProductDesignation_t = ManufacturerProductDesignation(
        value={"en": "Pharmaceutical Processing Resource"})
    OrderCodeOfManufacturer: OrderCodeOfManufacturer_t = OrderCodeOfManufacturer(value="")
    YearOfConstruction: YearOfConstruction_t = YearOfConstruction(value="2026")
    CountryOfOrigin: CountryOfOrigin_t = CountryOfOrigin(value="DK")


# ── Skills ────────────────────────────────────────────────────────────────────

class ModuleSkill(skills.Skill):
    """A skill as its commands (Start, Stop, Abort, Reset), each with the interface action that calls
    it, its Operation and, for a composite, its steps. Named apart from the Control Component
    Instance's ``Skill``: an element is read back as the class its dump names."""


class ModuleSkills(skills.Skills):
    """The Skills submodel: the skills, the module's own commands (``Module``) and the errors."""
    Skill: Dict[str, ModuleSkill] = {}
    Errors: skills.Errors = skills.Errors()


# ── Capability Description ───────────────────────────────────────────────────

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
    PropertySet: Dict[str, StatedPropertySet] = {}
    CapabilityRelations: Optional[ModuleCapabilityRelations] = None


class ModuleCapabilitySet(cd.CapabilitySet):
    CapabilityContainer: Dict[str, ModuleCapabilityContainer] = {}


class ModuleCapabilityDescription(cd.CapabilityDescription):
    """The capabilities a module offers, each realized by one of its skills, and in a set per
    component the capabilities of its components, each realized by a primitive (ARSO 0.11)."""
    CapabilitySet: Dict[str, ModuleCapabilitySet] = {}


# ── Control Configuration ────────────────────────────────────────────────────

class ModuleControlConfiguration(ControlConfiguration):
    """What was built on the module's controller; until it is read, its state is NotRead. Since
    ARSO 0.10 the integrator's record, kept outside the AAS."""
    SyncState: Property = Property(value="NotRead")


# ── Interfaces and structure ─────────────────────────────────────────────────

class ModuleInterfaces(DmpAssetInterfacesDescription):
    """The interfaces of a module: one OPC UA server, no MQTT."""
    InterfaceTemplateForMQTT: Dict[str, MqttInterface] = {}
    InterfaceTemplateForOPCUA: Dict[str, DmpOpcuaInterface] = {"interface_opcua": DmpOpcuaInterface()}


class LocatedNode(Node):
    """A part of an asset, with the parts it has in turn. Where it is, is a coordinate of its
    Variables (``Measurements/Coordinates``), not a statement of the node."""
    Node: Dict[str, "LocatedNode"] = {}


class LocatedEntryNode(EntryNode):
    # The resource itself: its asset's id is its AAS's id (resolved when the AAS is built).
    global_asset_id: str = "{aas_id}"
    Node: Dict[str, LocatedNode] = {}


class LocatedStructures(HierarchicalStructures):
    """Hierarchical Structures with the resource as entry node and its direct parts (OneDown)."""
    EntryNode: LocatedEntryNode = LocatedEntryNode()
    ArcheType: ArcheType_t = ArcheType(value="OneDown")


LocatedNode.model_rebuild()
