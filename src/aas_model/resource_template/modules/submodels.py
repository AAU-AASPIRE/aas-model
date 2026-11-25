"""The submodels of a resource as the resource ontology ARSO describes it.

The classes of ARSO's own submodels are generated (``aas_model.submodel_templates.arso``). Declared
here is what they leave open, and the changes to IDTA templates a module needs:

- **Skills**: a skill under a name of its own (``ModuleSkill``, ``submodel_templates.skills``, shared with the
  stations).
- **Capability Description** (IDTA 02020): the lab's extension, shared with the stations
  (``aas_model.submodel_templates.capability_description``).
- **Asset Interfaces Description**: one OPC UA server, no MQTT.
- **Hierarchical Structures**: parts that have parts in turn.
"""

from __future__ import annotations

from typing import Dict, Optional

from aas_pydantic import Property
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
from aas_model.submodel_templates.arso.control_configuration import ControlConfiguration
# The Capability Description as the modules state it is the lab's extension of IDTA 02020, which the stations
# use too; imported here, where modreg finds it.
from aas_model.submodel_templates.capability_description import (  # noqa: F401
    BasicConstraintContainer, ModuleCapabilityContainer, ModuleCapabilityDescription, ModuleCapabilityRelations,
    ModuleCapabilitySet, ModuleConstraintSet, RealizedBySkill, SameAs, StatedProperty, StatedPropertySet,
)


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

# ModuleSkill and ModuleSkills are every resource's (``submodel_templates.skills``); imported here, where modreg
# finds them.
from aas_model.submodel_templates.skills import ModuleSkill, ModuleSkills  # noqa: E402,F401


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
