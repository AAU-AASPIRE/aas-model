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

from typing import ClassVar, Dict, Optional, TypeAlias

from aas_pydantic import Property
from aas_pydantic.submodel_templates.hierarchical_structures import (
    ArcheType, ArcheType_t, EntryNode, HierarchicalStructures, Node,
)
from aas_pydantic import MultiLanguageProperty
from aas_pydantic.aas_model import AasIdString
from aas_pydantic.submodel_templates.nameplate import (
    AddressInformation, AddressInformation_t, CityTown, CityTown_t, CompanyLogo, CompanyLogo_t, CountryOfOrigin,
    CountryOfOrigin_t, ManufacturerName, ManufacturerName_t, ManufacturerProductDesignation,
    ManufacturerProductDesignation_t, ManufacturerProductFamily, ManufacturerProductRoot, ManufacturerProductRoot_t,
    ManufacturerProductType, NationalCode, NationalCode_t, OrderCodeOfManufacturer, OrderCodeOfManufacturer_t, Street,
    Street_t, URIOfTheProduct, URIOfTheProduct_t, YearOfConstruction, YearOfConstruction_t, Zipcode, Zipcode_t,
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


# The lab's AddressInformation adds the company and the department, which the Nameplate's AddressInformation (the
# SMT drop-in) leaves out, as the Contact Information template (IDTA 02002) states them: the same semantic ids.
class Company(MultiLanguageProperty):
    id_short: AasIdString = "Company"
    semantic_id: str = "0173-1#02-AAW001#001"

Company_t: TypeAlias = Company  # a field may share the class's id_short


class Department(MultiLanguageProperty):
    id_short: AasIdString = "Department"
    semantic_id: str = "0173-1#02-AAO127#003"

Department_t: TypeAlias = Department  # a field may share the class's id_short


class LabAddressInformation(AddressInformation):
    """Where the AP2030 Project is: Aalborg University, its Department of Materials and Production and the Robotics &
    Automation Group, at the lab's address."""
    Company: Company_t = Company(value={"en": "Aalborg University"})
    Department: Department_t = Department(
        value={"en": "Department of Materials and Production, Robotics & Automation Group"})
    Street: Street_t = Street(value={"en": "Fibigerstræde 14"})
    Zipcode: Zipcode_t = Zipcode(value={"en": "9220"})
    CityTown: CityTown_t = CityTown(value={"en": "Aalborg Øst"})
    NationalCode: NationalCode_t = NationalCode(value={"en": "DK"})


# The AP2030 logo, an asset of the package (``aas_model/assets``): registration uploads it as the attachment of each
# CompanyLogo that names it.
AP2030_LOGO = "AP2030-logo.png"


class LabNameplate(ResourceNameplate):
    """The nameplate of an asset the AP2030 Project builds itself: the project as manufacturer, Aalborg University and
    its department and group in the address, and the project's logo. Its product hierarchy is what the asset is in the
    ontology, read from its asset type (``derive_from``): ManufacturerProductRoot the CSS class (Resource, Product),
    ManufacturerProductFamily the ARSO kind (Module, Component, System; Software), ManufacturerProductType the kind of
    resource (LoadingStation, FillingModule). An asset states its designation (``lab_nameplate``); its URI is its AAS
    id."""
    # The resource or product whose nameplate this is fills the product hierarchy from its asset type.
    DERIVES_PRODUCT_HIERARCHY: ClassVar[bool] = True
    URIOfTheProduct: URIOfTheProduct_t = URIOfTheProduct(value="{aas_id}")
    ManufacturerName: ManufacturerName_t = ManufacturerName(value={"en": "AP2030 Project"})
    ManufacturerProductDesignation: ManufacturerProductDesignation_t = ManufacturerProductDesignation(
        value={"en": "Pharmaceutical Processing Resource"})
    AddressInformation: AddressInformation_t = LabAddressInformation()
    OrderCodeOfManufacturer: OrderCodeOfManufacturer_t = OrderCodeOfManufacturer(value="")
    YearOfConstruction: YearOfConstruction_t = YearOfConstruction(value="2026")
    CountryOfOrigin: CountryOfOrigin_t = CountryOfOrigin(value="DK")
    CompanyLogo: CompanyLogo_t = CompanyLogo(value=AP2030_LOGO)

    def derive_from(self, asset_type: str) -> None:
        """Fill the product hierarchy the nameplate does not state from ``asset_type`` (``<BASE_URL>/Resource/Module/
        LoadingStation``: Resource, Module, LoadingStation; ``<BASE_URL>/Product``: Product)."""
        if not asset_type.startswith(BASE_URL + "/"):
            return
        path = asset_type[len(BASE_URL) + 1:].split("/")
        if self.ManufacturerProductRoot is None:
            self.ManufacturerProductRoot = ManufacturerProductRoot(value={"en": path[0]})
        if len(path) > 1 and self.ManufacturerProductFamily is None:
            self.ManufacturerProductFamily = ManufacturerProductFamily(value={"en": path[1]})
        if len(path) > 2 and self.ManufacturerProductType is None:
            self.ManufacturerProductType = ManufacturerProductType(value=path[-1])


def lab_nameplate(designation: str, **values) -> LabNameplate:
    """The lab's nameplate of one asset with its designation ("Loading station of the AP2030 filling line"); the
    product hierarchy follows from the asset's type."""
    return LabNameplate(ManufacturerProductDesignation=ManufacturerProductDesignation(value={"en": designation}),
                        **values)


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
