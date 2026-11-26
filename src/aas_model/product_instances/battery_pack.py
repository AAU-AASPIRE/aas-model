"""An EV battery pack, remanufactured: its AAS with the Production Sequence 4.0 (proposed,
``docs/lab-submodels/ProductionSequence4.md``).

What it is: one pack, an instance (it comes back used), of a housing, a cover held by 12 screws, an
HV connector on the BMS, busbars over four battery modules. Each module is a subassembly with an
AAS of its own (``battery_module.py``).

What it needs, taken apart (Disassembly):

    UnscrewCover ──┐
                   ├──> RemoveBusbars ──> BatteryModule1..4 (each its own sequence, at once)
    UnplugHV ──────┤
                   └──> RemoveBMS

and closed again (Assembly), the joints referred to, not defined a second time:

    PlaceBMS ──> PlugHV ──┐
                          ├──> ScrewCover
    BoltBusbars ──────────┘

The Hierarchical Structures hold the parts only. Each joint (an AnnotatedRelationshipElement, the
colleagues' JointConnection) sits in the step that breaks it; its first and second are entities of
the bill of material. The recipe names no equipment: that is the process AAS's
(``battery_pack_on_disassembly_cell.py``).

Every submodel is written with aas-model's classes, element by element; the sequences with those
of ``production_sequence_4``.
"""
from __future__ import annotations

from aas_model.constants import BASE_URL
from aas_model.product_template import (
    BillOfMaterial, ProductPart, PartQuantity, PartQuantityUnit, Product, ProductEntry, sequence_id,
)
from aas_model.submodel_templates.product import process_parameters as pp
from aas_model.submodel_templates.product import production_sequence_4 as ps4
from aas_pydantic import Capability, Key, ModelReference, Qualifier
from aas_pydantic.submodel_templates import capability_description as cd
from aas_pydantic.submodel_templates.hierarchical_structures import ArcheType
from aas_pydantic.submodel_templates.nameplate import (
    AddressInformation, CityTown, CountryOfOrigin, ManufacturerName, ManufacturerProductDesignation, Nameplate,
    NationalCode, OrderCodeOfManufacturer, SerialNumber, Street, URIOfTheProduct, YearOfConstruction, Zipcode,
)

AAS_ID = f"{BASE_URL}/aas/BatteryPackAAS"
ASSET_ID = f"{BASE_URL}/assets/BatteryPack/SN-0042"
PROCESSES = f"{AAS_ID}/submodels/ProcessParameters"
BILL = f"{AAS_ID}/submodels/HierarchicalStructures"
CAPABILITIES = f"{AAS_ID}/submodels/CapabilityDescription"
DISASSEMBLY = sequence_id(AAS_ID, "Disassembly")
ASSEMBLY = sequence_id(AAS_ID, "Assembly")
MODULES = [f"{BASE_URL}/aas/BatteryModule{n}AAS" for n in (1, 2, 3, 4)]
MODULE_ASSETS = [f"{BASE_URL}/assets/BatteryModule/SN-0042-{n}" for n in (1, 2, 3, 4)]
MEANS = f"{BASE_URL}/semantics"
CAPABILITY = "https://admin-shell.io/idta/CapabilityDescription/Capability/1/0"
REQUIRED = "https://admin-shell.io/idta/CapabilityDescription/CapabilityRoleQualifier/Required/1/0"
# The pack and its modules come back used: each AAS is of an instance, with its serial number.
ASSET_KIND = "Instance"


# ---- references and units -----------------------------------------------------------------------------
def reference(*keys: tuple[str, str]) -> ModelReference:
    """A model reference along ``keys``: (type, value) pairs."""
    return ModelReference(key=tuple(Key(type_=kind, value=value) for kind, value in keys))


def unit(symbol: str) -> list[Qualifier]:
    """The qualifier that states a value's unit."""
    return [Qualifier(type_="Unit", value=symbol, kind="ConceptQualifier")]


def required() -> list[Qualifier]:
    """The qualifier that makes a capability a required one."""
    return [Qualifier(type_="CapabilityRoleQualifier/Required", value="true", semantic_id=REQUIRED, kind="ConceptQualifier")]


# ---- the pack ----------------------------------------------------------------------------------------
def battery_pack() -> Product:
    return Product(
        id_short="BatteryPackAAS", id=AAS_ID,
        description="An EV battery pack, returned for remanufacturing: taken apart, its modules tested, closed again",
        display_name={"en": "Battery pack SN-0042"},

        # ── Nameplate (IDTA 02006): an instance, with its serial number ─────────────────────────
        nameplate=Nameplate(
            id_short="Nameplate",
            URIOfTheProduct=URIOfTheProduct(value=ASSET_ID),
            ManufacturerName=ManufacturerName(value={"en": "Demo EV maker"}),
            ManufacturerProductDesignation=ManufacturerProductDesignation(value={"en": "Battery pack, 4 modules"}),
            AddressInformation=AddressInformation(
                Street=Street(value={"en": "Demo street 1"}), Zipcode=Zipcode(value={"en": "9220"}),
                CityTown=CityTown(value={"en": "Aalborg Øst"}), NationalCode=NationalCode(value={"en": "DK"})),
            OrderCodeOfManufacturer=OrderCodeOfManufacturer(value="PACK-4M"),
            SerialNumber=SerialNumber(value="SN-0042"),
            YearOfConstruction=YearOfConstruction(value="2019"),
            CountryOfOrigin=CountryOfOrigin(value="DE"),
        ),

        # ── Hierarchical Structures (IDTA 02011): the parts only ────────────────────────────────
        # The four modules have AASs of their own (SelfManagedEntity, by asset id). No joint here:
        # each joint is held by the step that breaks it (the Production Sequences below).
        hierarchical_structures=BillOfMaterial(
            id_short="HierarchicalStructures", ArcheType=ArcheType(value="OneDown"),
            EntryNode=ProductEntry(
                display_name={"en": "Battery pack"}, global_asset_id=ASSET_ID,
                Node={
                    "Housing": ProductPart(id_short="Housing", display_name={"en": "Pack housing"},
                                           Quantity=PartQuantity(value="1.0"), QuantityUnit=PartQuantityUnit(value="piece")),
                    "Cover": ProductPart(id_short="Cover", display_name={"en": "Pack cover"},
                                         Quantity=PartQuantity(value="1.0"), QuantityUnit=PartQuantityUnit(value="piece")),
                    "CoverScrew": ProductPart(id_short="CoverScrew", display_name={"en": "Cover screw M5"},
                                              Quantity=PartQuantity(value="12.0"), QuantityUnit=PartQuantityUnit(value="piece")),
                    "HVConnector": ProductPart(id_short="HVConnector", display_name={"en": "HV connector"},
                                               Quantity=PartQuantity(value="1.0"), QuantityUnit=PartQuantityUnit(value="piece")),
                    "BMS": ProductPart(id_short="BMS", display_name={"en": "Battery management system"},
                                       Quantity=PartQuantity(value="1.0"), QuantityUnit=PartQuantityUnit(value="piece")),
                    "Busbars": ProductPart(id_short="Busbars", display_name={"en": "Busbars"},
                                           Quantity=PartQuantity(value="1.0"), QuantityUnit=PartQuantityUnit(value="set")),
                    "BatteryModule1": ProductPart(id_short="BatteryModule1", entity_type="SelfManagedEntity",
                                                  global_asset_id=MODULE_ASSETS[0], display_name={"en": "Battery module 1"},
                                                  Quantity=PartQuantity(value="1.0"), QuantityUnit=PartQuantityUnit(value="piece")),
                    "BatteryModule2": ProductPart(id_short="BatteryModule2", entity_type="SelfManagedEntity",
                                                  global_asset_id=MODULE_ASSETS[1], display_name={"en": "Battery module 2"},
                                                  Quantity=PartQuantity(value="1.0"), QuantityUnit=PartQuantityUnit(value="piece")),
                    "BatteryModule3": ProductPart(id_short="BatteryModule3", entity_type="SelfManagedEntity",
                                                  global_asset_id=MODULE_ASSETS[2], display_name={"en": "Battery module 3"},
                                                  Quantity=PartQuantity(value="1.0"), QuantityUnit=PartQuantityUnit(value="piece")),
                    "BatteryModule4": ProductPart(id_short="BatteryModule4", entity_type="SelfManagedEntity",
                                                  global_asset_id=MODULE_ASSETS[3], display_name={"en": "Battery module 4"},
                                                  Quantity=PartQuantity(value="1.0"), QuantityUnit=PartQuantityUnit(value="piece")),
                },
            ),
        ),

        # ── Process Parameters (IDTA 02031-1 and the lab's extension) ───────────────────────────
        # The joints' parameters live here (the colleagues' JointParams): the step that breaks a
        # joint names its process. Taking apart: Unscrewing, Unplugging, Unbolting, Removing;
        # closing again: Placing, Plugging, Bolting, Screwing.
        process_parameters=pp.ProcessParameters(
            id_short="ProcessParameters",
            Processes=pp.Processes(Process={
                "Unscrewing": pp.Process(
                    id_short="Unscrewing",
                    ProcessId=pp.ProcessId(value="Unscrewing"), ProcessName=pp.ProcessName(value="Unscrewing"),
                    ProcessDescription=pp.ProcessDescription(value={"en": "Loosen the 12 cover screws and lift the cover off"}),
                    PlannedProcessTime=pp.PlannedProcessTime(value="PT60S"),
                    ProductParameters=pp.ProductParameters(Parameter={
                        # The joint's TypeParam: what it takes to loosen a screw that has sat for years.
                        "BreakawayTorque": pp.Parameter(id_short="BreakawayTorque", semantic_id=f"{MEANS}/Torque",
                                                        value="8.0", value_type="xs:double", qualifiers=unit("N·m")),
                        "ScrewSize": pp.Parameter(id_short="ScrewSize", semantic_id=f"{MEANS}/ScrewSize", value="M5"),
                    }),
                    ProcessParameters=pp.ProcessParameterGroup(), ResourceParameters=pp.ResourceParameters(),
                    ProcessBoM=pp.ProcessBoM(MaterialUse={
                        # Taken out: the screws and the cover (role output).
                        "CoverScrew": pp.MaterialUse(
                            id_short="CoverScrew",
                            MaterialReference=pp.MaterialReference(value=reference(
                                ("Submodel", BILL), ("Entity", "EntryNode"), ("Entity", "CoverScrew"))),
                            Role=pp.Role(value="output"), Quantity=pp.Quantity(value="12.0"), Unit=pp.Unit(value="piece")),
                        "Cover": pp.MaterialUse(
                            id_short="Cover",
                            MaterialReference=pp.MaterialReference(value=reference(
                                ("Submodel", BILL), ("Entity", "EntryNode"), ("Entity", "Cover"))),
                            Role=pp.Role(value="output"), Quantity=pp.Quantity(value="1.0"), Unit=pp.Unit(value="piece")),
                    }),
                    RequiredCapability=pp.RequiredCapability(value=reference(
                        ("Submodel", CAPABILITIES), ("SubmodelElementCollection", "RequiredCapabilities"),
                        ("SubmodelElementCollection", "Unscrewing"), ("Capability", "Capability"))),
                ),
                "Unplugging": pp.Process(
                    id_short="Unplugging",
                    ProcessId=pp.ProcessId(value="Unplugging"), ProcessName=pp.ProcessName(value="Unplugging"),
                    ProcessDescription=pp.ProcessDescription(value={"en": "Unplug the HV connector from the BMS"}),
                    PlannedProcessTime=pp.PlannedProcessTime(value="PT10S"),
                    ProductParameters=pp.ProductParameters(Parameter={
                        "PullForce": pp.Parameter(id_short="PullForce", semantic_id=f"{MEANS}/Force",
                                                  value="40.0", value_type="xs:double", qualifiers=unit("N")),
                    }),
                    ProcessParameters=pp.ProcessParameterGroup(), ResourceParameters=pp.ResourceParameters(),
                    ProcessBoM=pp.ProcessBoM(MaterialUse={
                        # The connector stays in the pack, unplugged: it is what is worked on.
                        "HVConnector": pp.MaterialUse(
                            id_short="HVConnector",
                            MaterialReference=pp.MaterialReference(value=reference(
                                ("Submodel", BILL), ("Entity", "EntryNode"), ("Entity", "HVConnector"))),
                            Role=pp.Role(value="workpiece"), Quantity=pp.Quantity(value="1.0"), Unit=pp.Unit(value="piece")),
                    }),
                    RequiredCapability=pp.RequiredCapability(value=reference(
                        ("Submodel", CAPABILITIES), ("SubmodelElementCollection", "RequiredCapabilities"),
                        ("SubmodelElementCollection", "Unplugging"), ("Capability", "Capability"))),
                ),
                "Unbolting": pp.Process(
                    id_short="Unbolting",
                    ProcessId=pp.ProcessId(value="Unbolting"), ProcessName=pp.ProcessName(value="Unbolting"),
                    ProcessDescription=pp.ProcessDescription(value={"en": "Unbolt the busbars from the four modules"}),
                    PlannedProcessTime=pp.PlannedProcessTime(value="PT80S"),
                    ProductParameters=pp.ProductParameters(Parameter={
                        "BreakawayTorque": pp.Parameter(id_short="BreakawayTorque", semantic_id=f"{MEANS}/Torque",
                                                        value="12.0", value_type="xs:double", qualifiers=unit("N·m")),
                        "ScrewSize": pp.Parameter(id_short="ScrewSize", semantic_id=f"{MEANS}/ScrewSize", value="M6"),
                    }),
                    ProcessParameters=pp.ProcessParameterGroup(), ResourceParameters=pp.ResourceParameters(),
                    ProcessBoM=pp.ProcessBoM(MaterialUse={
                        "Busbars": pp.MaterialUse(
                            id_short="Busbars",
                            MaterialReference=pp.MaterialReference(value=reference(
                                ("Submodel", BILL), ("Entity", "EntryNode"), ("Entity", "Busbars"))),
                            Role=pp.Role(value="output"), Quantity=pp.Quantity(value="1.0"), Unit=pp.Unit(value="set")),
                    }),
                    RequiredCapability=pp.RequiredCapability(value=reference(
                        ("Submodel", CAPABILITIES), ("SubmodelElementCollection", "RequiredCapabilities"),
                        ("SubmodelElementCollection", "Unbolting"), ("Capability", "Capability"))),
                ),
                "Removing": pp.Process(
                    id_short="Removing",
                    ProcessId=pp.ProcessId(value="Removing"), ProcessName=pp.ProcessName(value="Removing"),
                    ProcessDescription=pp.ProcessDescription(value={"en": "Lift the BMS out of the housing"}),
                    PlannedProcessTime=pp.PlannedProcessTime(value="PT15S"),
                    ProductParameters=pp.ProductParameters(Parameter={
                        "Mass": pp.Parameter(id_short="Mass", semantic_id=f"{MEANS}/Mass",
                                             value="1.2", value_type="xs:double", qualifiers=unit("kg")),
                    }),
                    ProcessParameters=pp.ProcessParameterGroup(), ResourceParameters=pp.ResourceParameters(),
                    ProcessBoM=pp.ProcessBoM(MaterialUse={
                        "BMS": pp.MaterialUse(
                            id_short="BMS",
                            MaterialReference=pp.MaterialReference(value=reference(
                                ("Submodel", BILL), ("Entity", "EntryNode"), ("Entity", "BMS"))),
                            Role=pp.Role(value="output"), Quantity=pp.Quantity(value="1.0"), Unit=pp.Unit(value="piece")),
                    }),
                    RequiredCapability=pp.RequiredCapability(value=reference(
                        ("Submodel", CAPABILITIES), ("SubmodelElementCollection", "RequiredCapabilities"),
                        ("SubmodelElementCollection", "Removing"), ("Capability", "Capability"))),
                ),
                "Placing": pp.Process(
                    id_short="Placing",
                    ProcessId=pp.ProcessId(value="Placing"), ProcessName=pp.ProcessName(value="Placing"),
                    ProcessDescription=pp.ProcessDescription(value={"en": "Place the BMS back in the housing"}),
                    PlannedProcessTime=pp.PlannedProcessTime(value="PT15S"),
                    ProductParameters=pp.ProductParameters(Parameter={
                        "Mass": pp.Parameter(id_short="Mass", semantic_id=f"{MEANS}/Mass",
                                             value="1.2", value_type="xs:double", qualifiers=unit("kg")),
                    }),
                    ProcessParameters=pp.ProcessParameterGroup(), ResourceParameters=pp.ResourceParameters(),
                    ProcessBoM=pp.ProcessBoM(MaterialUse={
                        "BMS": pp.MaterialUse(
                            id_short="BMS",
                            MaterialReference=pp.MaterialReference(value=reference(
                                ("Submodel", BILL), ("Entity", "EntryNode"), ("Entity", "BMS"))),
                            Role=pp.Role(value="incorporated"), Quantity=pp.Quantity(value="1.0"), Unit=pp.Unit(value="piece")),
                    }),
                    RequiredCapability=pp.RequiredCapability(value=reference(
                        ("Submodel", CAPABILITIES), ("SubmodelElementCollection", "RequiredCapabilities"),
                        ("SubmodelElementCollection", "Placing"), ("Capability", "Capability"))),
                ),
                "Plugging": pp.Process(
                    id_short="Plugging",
                    ProcessId=pp.ProcessId(value="Plugging"), ProcessName=pp.ProcessName(value="Plugging"),
                    ProcessDescription=pp.ProcessDescription(value={"en": "Plug the HV connector into the BMS"}),
                    PlannedProcessTime=pp.PlannedProcessTime(value="PT10S"),
                    ProductParameters=pp.ProductParameters(Parameter={
                        "InsertionForce": pp.Parameter(id_short="InsertionForce", semantic_id=f"{MEANS}/Force",
                                                       value="60.0", value_type="xs:double", qualifiers=unit("N")),
                    }),
                    ProcessParameters=pp.ProcessParameterGroup(), ResourceParameters=pp.ResourceParameters(),
                    ProcessBoM=pp.ProcessBoM(MaterialUse={
                        "HVConnector": pp.MaterialUse(
                            id_short="HVConnector",
                            MaterialReference=pp.MaterialReference(value=reference(
                                ("Submodel", BILL), ("Entity", "EntryNode"), ("Entity", "HVConnector"))),
                            Role=pp.Role(value="workpiece"), Quantity=pp.Quantity(value="1.0"), Unit=pp.Unit(value="piece")),
                    }),
                    RequiredCapability=pp.RequiredCapability(value=reference(
                        ("Submodel", CAPABILITIES), ("SubmodelElementCollection", "RequiredCapabilities"),
                        ("SubmodelElementCollection", "Plugging"), ("Capability", "Capability"))),
                ),
                "Bolting": pp.Process(
                    id_short="Bolting",
                    ProcessId=pp.ProcessId(value="Bolting"), ProcessName=pp.ProcessName(value="Bolting"),
                    ProcessDescription=pp.ProcessDescription(value={"en": "Bolt the busbars onto the four modules"}),
                    PlannedProcessTime=pp.PlannedProcessTime(value="PT80S"),
                    ProductParameters=pp.ProductParameters(Parameter={
                        "TighteningTorque": pp.Parameter(id_short="TighteningTorque", semantic_id=f"{MEANS}/Torque",
                                                         value="10.0", value_type="xs:double", qualifiers=unit("N·m")),
                        "ScrewSize": pp.Parameter(id_short="ScrewSize", semantic_id=f"{MEANS}/ScrewSize", value="M6"),
                    }),
                    ProcessParameters=pp.ProcessParameterGroup(), ResourceParameters=pp.ResourceParameters(),
                    ProcessBoM=pp.ProcessBoM(MaterialUse={
                        "Busbars": pp.MaterialUse(
                            id_short="Busbars",
                            MaterialReference=pp.MaterialReference(value=reference(
                                ("Submodel", BILL), ("Entity", "EntryNode"), ("Entity", "Busbars"))),
                            Role=pp.Role(value="incorporated"), Quantity=pp.Quantity(value="1.0"), Unit=pp.Unit(value="set")),
                    }),
                    RequiredCapability=pp.RequiredCapability(value=reference(
                        ("Submodel", CAPABILITIES), ("SubmodelElementCollection", "RequiredCapabilities"),
                        ("SubmodelElementCollection", "Bolting"), ("Capability", "Capability"))),
                ),
                "Screwing": pp.Process(
                    id_short="Screwing",
                    ProcessId=pp.ProcessId(value="Screwing"), ProcessName=pp.ProcessName(value="Screwing"),
                    ProcessDescription=pp.ProcessDescription(value={"en": "Put the cover on and drive the 12 screws"}),
                    PlannedProcessTime=pp.PlannedProcessTime(value="PT60S"),
                    ProductParameters=pp.ProductParameters(Parameter={
                        "TighteningTorque": pp.Parameter(id_short="TighteningTorque", semantic_id=f"{MEANS}/Torque",
                                                         value="6.0", value_type="xs:double", qualifiers=unit("N·m")),
                        "ScrewSize": pp.Parameter(id_short="ScrewSize", semantic_id=f"{MEANS}/ScrewSize", value="M5"),
                    }),
                    ProcessParameters=pp.ProcessParameterGroup(), ResourceParameters=pp.ResourceParameters(),
                    ProcessBoM=pp.ProcessBoM(MaterialUse={
                        "CoverScrew": pp.MaterialUse(
                            id_short="CoverScrew",
                            MaterialReference=pp.MaterialReference(value=reference(
                                ("Submodel", BILL), ("Entity", "EntryNode"), ("Entity", "CoverScrew"))),
                            Role=pp.Role(value="incorporated"), Quantity=pp.Quantity(value="12.0"), Unit=pp.Unit(value="piece")),
                        "Cover": pp.MaterialUse(
                            id_short="Cover",
                            MaterialReference=pp.MaterialReference(value=reference(
                                ("Submodel", BILL), ("Entity", "EntryNode"), ("Entity", "Cover"))),
                            Role=pp.Role(value="incorporated"), Quantity=pp.Quantity(value="1.0"), Unit=pp.Unit(value="piece")),
                    }),
                    RequiredCapability=pp.RequiredCapability(value=reference(
                        ("Submodel", CAPABILITIES), ("SubmodelElementCollection", "RequiredCapabilities"),
                        ("SubmodelElementCollection", "Screwing"), ("Capability", "Capability"))),
                ),
            }),
        ),

        # ── Capability Description (IDTA 02020, role Required) ───────────────────────────────────
        # A torque the resource must reach (the joint's TypeRange is the offered range it is
        # matched against); the others ask for the capability only.
        capability_description=cd.CapabilityDescription(
            id_short="CapabilityDescription",
            CapabilitySet={"RequiredCapabilities": cd.CapabilitySet(
                id_short="RequiredCapabilities",
                CapabilityContainer={
                    "Unscrewing": cd.CapabilityContainer(
                        id_short="Unscrewing",
                        Capability=Capability(id_short="Capability", semantic_id=CAPABILITY,
                                              supplemental_semantic_ids=[f"{MEANS}/Unscrewing"],
                                              display_name={"en": "Unscrewing"}, qualifiers=required()),
                        PropertySet={"PropertySet": cd.PropertySet(PropertyContainer={
                            "Torque": cd.PropertyContainer(id_short="Torque", PropertyProperty={
                                "Value": cd.PropertyProperty(id_short="Value", display_name={"en": "Torque"},
                                                             supplemental_semantic_ids=[f"{MEANS}/Torque"],
                                                             value="8.0", value_type="xs:double", qualifiers=unit("N·m"))}),
                        })},
                    ),
                    "Unplugging": cd.CapabilityContainer(
                        id_short="Unplugging",
                        Capability=Capability(id_short="Capability", semantic_id=CAPABILITY,
                                              supplemental_semantic_ids=[f"{MEANS}/Unplugging"],
                                              display_name={"en": "Unplugging"}, qualifiers=required()),
                    ),
                    "Unbolting": cd.CapabilityContainer(
                        id_short="Unbolting",
                        Capability=Capability(id_short="Capability", semantic_id=CAPABILITY,
                                              supplemental_semantic_ids=[f"{MEANS}/Unscrewing"],
                                              display_name={"en": "Unbolting"}, qualifiers=required()),
                        PropertySet={"PropertySet": cd.PropertySet(PropertyContainer={
                            "Torque": cd.PropertyContainer(id_short="Torque", PropertyProperty={
                                "Value": cd.PropertyProperty(id_short="Value", display_name={"en": "Torque"},
                                                             supplemental_semantic_ids=[f"{MEANS}/Torque"],
                                                             value="12.0", value_type="xs:double", qualifiers=unit("N·m"))}),
                        })},
                    ),
                    "Removing": cd.CapabilityContainer(
                        id_short="Removing",
                        Capability=Capability(id_short="Capability", semantic_id=CAPABILITY,
                                              supplemental_semantic_ids=[f"{MEANS}/PickAndPlace"],
                                              display_name={"en": "Removing"}, qualifiers=required()),
                    ),
                    "Placing": cd.CapabilityContainer(
                        id_short="Placing",
                        Capability=Capability(id_short="Capability", semantic_id=CAPABILITY,
                                              supplemental_semantic_ids=[f"{MEANS}/PickAndPlace"],
                                              display_name={"en": "Placing"}, qualifiers=required()),
                    ),
                    "Plugging": cd.CapabilityContainer(
                        id_short="Plugging",
                        Capability=Capability(id_short="Capability", semantic_id=CAPABILITY,
                                              supplemental_semantic_ids=[f"{MEANS}/Plugging"],
                                              display_name={"en": "Plugging"}, qualifiers=required()),
                    ),
                    "Bolting": cd.CapabilityContainer(
                        id_short="Bolting",
                        Capability=Capability(id_short="Capability", semantic_id=CAPABILITY,
                                              supplemental_semantic_ids=[f"{MEANS}/Screwing"],
                                              display_name={"en": "Bolting"}, qualifiers=required()),
                        PropertySet={"PropertySet": cd.PropertySet(PropertyContainer={
                            "Torque": cd.PropertyContainer(id_short="Torque", PropertyProperty={
                                "Value": cd.PropertyProperty(id_short="Value", display_name={"en": "Torque"},
                                                             supplemental_semantic_ids=[f"{MEANS}/Torque"],
                                                             value="10.0", value_type="xs:double", qualifiers=unit("N·m"))}),
                        })},
                    ),
                    "Screwing": cd.CapabilityContainer(
                        id_short="Screwing",
                        Capability=Capability(id_short="Capability", semantic_id=CAPABILITY,
                                              supplemental_semantic_ids=[f"{MEANS}/Screwing"],
                                              display_name={"en": "Screwing"}, qualifiers=required()),
                        PropertySet={"PropertySet": cd.PropertySet(PropertyContainer={
                            "Torque": cd.PropertyContainer(id_short="Torque", PropertyProperty={
                                "Value": cd.PropertyProperty(id_short="Value", display_name={"en": "Torque"},
                                                             supplemental_semantic_ids=[f"{MEANS}/Torque"],
                                                             value="6.0", value_type="xs:double", qualifiers=unit("N·m"))}),
                        })},
                    ),
                },
            )},
        ),

        # ── Production Sequences 4.0: Disassembly holds the joints, Assembly refers to them ─────
        disassembly_sequence=disassembly(),
        assembly_sequence=assembly(),
    )


# ---- the Production Sequences 4.0 ------------------------------------------------------------------
def part(name: str) -> ModelReference:
    """An entity of the pack's bill of material."""
    return reference(("Submodel", BILL), ("Entity", "EntryNode"), ("Entity", name))


def process(name: str) -> ps4.ProcessReference:
    """A process of the pack's Process Parameters."""
    return ps4.ProcessReference(value=reference(
        ("Submodel", PROCESSES), ("SubmodelElementCollection", "Processes"), ("SubmodelElementCollection", name)))


def step(sequence: str, name: str) -> ModelReference:
    """A step of the partial block (Step_0000) of ``sequence``: an end of a ProcessOrder."""
    return reference(("Submodel", sequence), ("SubmodelElementCollection", "Steps"), ("SubmodelElementCollection", "Step_0000"),
                     ("SubmodelElementCollection", "Steps"), ("SubmodelElementCollection", name))


def disassembly() -> ps4.ProductionSequence:
    """Taking the pack apart: it holds the joints."""
    return ps4.ProductionSequence(
        id=DISASSEMBLY, id_short="ProductionSequenceDisassembly",
        display_name={"en": "Battery pack: taking apart"},
        ArcheType=ps4.ArcheType(value="Disassembly"),
        Revision=ps4.Revision(value="1"),
        Name=ps4.Name(value="Battery pack, taken apart"),
        Subject=ps4.Subject(value=reference(("AssetAdministrationShell", AAS_ID))),
        Steps=ps4.Steps(Step={
            # One partial block: its steps in any order their After allows.
            "Step_0000": ps4.Step(
                id_short="Step_0000", NodeId=ps4.NodeId(value="OpenPack"), Kind=ps4.Kind(value="partial"),
                Name=ps4.StepName(value="Open the pack"), Order=ps4.Order(value="0"),
                ProcessOrders=ps4.ProcessOrders(ProcessOrder={
                    "ProcessOrder_0000": ps4.ProcessOrder(
                        id_short="ProcessOrder_0000", first=step(DISASSEMBLY, "Step_0000"),
                        second=step(DISASSEMBLY, "Step_0002"), Reason=ps4.Reason(value="the cover is over the busbars")),
                    "ProcessOrder_0001": ps4.ProcessOrder(
                        id_short="ProcessOrder_0001", first=step(DISASSEMBLY, "Step_0001"),
                        second=step(DISASSEMBLY, "Step_0002"), Reason=ps4.Reason(value="the pack is live until the HV connector is out")),
                    "ProcessOrder_0002": ps4.ProcessOrder(
                        id_short="ProcessOrder_0002", first=step(DISASSEMBLY, "Step_0001"),
                        second=step(DISASSEMBLY, "Step_0003"), Reason=ps4.Reason(value="the BMS is held by the HV connector")),
                    "ProcessOrder_0003": ps4.ProcessOrder(
                        id_short="ProcessOrder_0003", first=step(DISASSEMBLY, "Step_0002"),
                        second=step(DISASSEMBLY, "Step_0004"), Reason=ps4.Reason(value="the busbars hold module 1")),
                    "ProcessOrder_0004": ps4.ProcessOrder(
                        id_short="ProcessOrder_0004", first=step(DISASSEMBLY, "Step_0002"),
                        second=step(DISASSEMBLY, "Step_0005"), Reason=ps4.Reason(value="the busbars hold module 2")),
                    "ProcessOrder_0005": ps4.ProcessOrder(
                        id_short="ProcessOrder_0005", first=step(DISASSEMBLY, "Step_0002"),
                        second=step(DISASSEMBLY, "Step_0006"), Reason=ps4.Reason(value="the busbars hold module 3")),
                    "ProcessOrder_0006": ps4.ProcessOrder(
                        id_short="ProcessOrder_0006", first=step(DISASSEMBLY, "Step_0002"),
                        second=step(DISASSEMBLY, "Step_0007"), Reason=ps4.Reason(value="the busbars hold module 4")),
                }),
                Steps=ps4.Steps(Step={

                    # UnscrewCover: nothing before it; breaks the cover's screwed joint.
                    "Step_0000": ps4.Step(
                        id_short="Step_0000", NodeId=ps4.NodeId(value="UnscrewCover"), Kind=ps4.Kind(value="step"),
                        Name=ps4.StepName(value="Unscrew the cover"), Order=ps4.Order(value="0"),
                        EstimatedDuration=ps4.EstimatedDuration(value="90"),
                        ProcessReference=process("Unscrewing"),
                        Joints=ps4.Joints(Joint={
                            "J_Cover": ps4.Joint(
                                id_short="J_Cover", display_name={"en": "Cover to housing, 12 screws M5"},
                                supplemental_semantic_ids=[f"{MEANS}/ScrewedJoint"],
                                first=part("Cover"), second=part("Housing"),
                                JointType=ps4.JointType(value="Screw"), JointStandard=ps4.JointStandard(value="DIN 8593-3")),
                        })),

                    # UnplugHV: nothing before it; breaks the plug between connector and BMS.
                    "Step_0001": ps4.Step(
                        id_short="Step_0001", NodeId=ps4.NodeId(value="UnplugHV"), Kind=ps4.Kind(value="step"),
                        Name=ps4.StepName(value="Unplug the HV connector"), Order=ps4.Order(value="1"),
                        EstimatedDuration=ps4.EstimatedDuration(value="20"),
                        ProcessReference=process("Unplugging"),
                        Joints=ps4.Joints(Joint={
                            "J_HV": ps4.Joint(
                                id_short="J_HV", display_name={"en": "HV connector to BMS"},
                                supplemental_semantic_ids=[f"{MEANS}/PluggedJoint"],
                                first=part("HVConnector"), second=part("BMS"),
                                JointType=ps4.JointType(value="Plug")),
                        })),

                    # RemoveBusbars: after the cover and the HV connector; breaks the four busbar joints.
                    "Step_0002": ps4.Step(
                        id_short="Step_0002", NodeId=ps4.NodeId(value="RemoveBusbars"), Kind=ps4.Kind(value="step"),
                        Name=ps4.StepName(value="Remove the busbars"), Order=ps4.Order(value="2"),
                        EstimatedDuration=ps4.EstimatedDuration(value="120"),
                        ProcessReference=process("Unbolting"),
                        Joints=ps4.Joints(Joint={
                            f"J_Busbar{n}": ps4.Joint(
                                id_short=f"J_Busbar{n}", display_name={"en": f"Busbars to module {n}, bolted M6"},
                                supplemental_semantic_ids=[f"{MEANS}/ScrewedJoint"],
                                first=part("Busbars"), second=part(f"BatteryModule{n}"),
                                JointType=ps4.JointType(value="Bolt"), JointStandard=ps4.JointStandard(value="DIN 8593-3"))
                            for n in (1, 2, 3, 4)
                        })),

                    # RemoveBMS: after the HV connector only.
                    "Step_0003": ps4.Step(
                        id_short="Step_0003", NodeId=ps4.NodeId(value="RemoveBMS"), Kind=ps4.Kind(value="step"),
                        Name=ps4.StepName(value="Remove the BMS"), Order=ps4.Order(value="3"),
                        EstimatedDuration=ps4.EstimatedDuration(value="60"),
                        ProcessReference=process("Removing")),

                    # The four modules: each a call naming the module in the bill of material; its own
                    # Disassembly sequence is found through its AAS. After the busbars; four agents take
                    # them apart at once.
                    **{f"Step_{3 + n:04d}": ps4.Step(
                        id_short=f"Step_{3 + n:04d}", NodeId=ps4.NodeId(value=f"BatteryModule{n}"),
                        Kind=ps4.Kind(value="call"), Name=ps4.StepName(value=f"Take battery module {n} apart"),
                        Order=ps4.Order(value=str(3 + n)),
                        Part=ps4.Part(value=part(f"BatteryModule{n}")))
                       for n in (1, 2, 3, 4)},
                })),
        }))


def assembly() -> ps4.ProductionSequence:
    """Closing the pack again: it refers to the joints of the Disassembly sequence."""
    def joint(name: str) -> ps4.JointReference:
        """A joint the Disassembly sequence defines, referred to by the step that makes it again."""
        where = {"J_Cover": "Step_0000", "J_HV": "Step_0001"}.get(name, "Step_0002")
        return ps4.JointReference(id_short=name, value=reference(
            ("Submodel", DISASSEMBLY), ("SubmodelElementCollection", "Steps"), ("SubmodelElementCollection", "Step_0000"),
            ("SubmodelElementCollection", "Steps"), ("SubmodelElementCollection", where),
            ("SubmodelElementCollection", "Joints"), ("AnnotatedRelationshipElement", name)))

    return ps4.ProductionSequence(
        id=ASSEMBLY, id_short="ProductionSequenceAssembly",
        display_name={"en": "Battery pack: closing again"},
        ArcheType=ps4.ArcheType(value="Assembly"),
        Revision=ps4.Revision(value="1"),
        Name=ps4.Name(value="Battery pack, closed again"),
        Subject=ps4.Subject(value=reference(("AssetAdministrationShell", AAS_ID))),
        Steps=ps4.Steps(Step={
            "Step_0000": ps4.Step(
                id_short="Step_0000", NodeId=ps4.NodeId(value="ClosePack"), Kind=ps4.Kind(value="partial"),
                Name=ps4.StepName(value="Close the pack"), Order=ps4.Order(value="0"),
                ProcessOrders=ps4.ProcessOrders(ProcessOrder={
                    "ProcessOrder_0000": ps4.ProcessOrder(
                        id_short="ProcessOrder_0000", first=step(ASSEMBLY, "Step_0000"),
                        second=step(ASSEMBLY, "Step_0002"), Reason=ps4.Reason(value="the HV connector plugs into the BMS")),
                    "ProcessOrder_0001": ps4.ProcessOrder(
                        id_short="ProcessOrder_0001", first=step(ASSEMBLY, "Step_0001"),
                        second=step(ASSEMBLY, "Step_0003"), Reason=ps4.Reason(value="the cover goes over the busbars")),
                    "ProcessOrder_0002": ps4.ProcessOrder(
                        id_short="ProcessOrder_0002", first=step(ASSEMBLY, "Step_0002"),
                        second=step(ASSEMBLY, "Step_0003"), Reason=ps4.Reason(value="the cover goes over the HV connector")),
                }),
                Steps=ps4.Steps(Step={
                    "Step_0000": ps4.Step(
                        id_short="Step_0000", NodeId=ps4.NodeId(value="PlaceBMS"), Kind=ps4.Kind(value="step"),
                        Name=ps4.StepName(value="Place the BMS"), Order=ps4.Order(value="0"),
                        EstimatedDuration=ps4.EstimatedDuration(value="40"),
                        ProcessReference=process("Placing")),
                    "Step_0001": ps4.Step(
                        id_short="Step_0001", NodeId=ps4.NodeId(value="BoltBusbars"), Kind=ps4.Kind(value="step"),
                        Name=ps4.StepName(value="Bolt the busbars"), Order=ps4.Order(value="1"),
                        EstimatedDuration=ps4.EstimatedDuration(value="120"),
                        ProcessReference=process("Bolting"),
                        Joints=ps4.Joints(JointReference={
                            name: joint(name) for name in ("J_Busbar1", "J_Busbar2", "J_Busbar3", "J_Busbar4")})),
                    "Step_0002": ps4.Step(
                        id_short="Step_0002", NodeId=ps4.NodeId(value="PlugHV"), Kind=ps4.Kind(value="step"),
                        Name=ps4.StepName(value="Plug the HV connector in"), Order=ps4.Order(value="2"),
                        EstimatedDuration=ps4.EstimatedDuration(value="20"),
                        ProcessReference=process("Plugging"),
                        Joints=ps4.Joints(JointReference={"J_HV": joint("J_HV")})),
                    "Step_0003": ps4.Step(
                        id_short="Step_0003", NodeId=ps4.NodeId(value="ScrewCover"), Kind=ps4.Kind(value="step"),
                        Name=ps4.StepName(value="Screw the cover on"), Order=ps4.Order(value="3"),
                        EstimatedDuration=ps4.EstimatedDuration(value="90"),
                        ProcessReference=process("Screwing"),
                        Joints=ps4.Joints(JointReference={"J_Cover": joint("J_Cover")})),
                })),
        }))
