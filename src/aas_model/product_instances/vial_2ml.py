"""The 2 mL vial: a product type of the example line, its AAS (ISA-88's general recipe).

What it is: a 2R glass vial (16 mm across where a gripper holds it) holding 2 mL of a demo liquid, closed with a
13 mm rubber stopper and a 13 mm crimp cap. What it needs: filling, stoppering, capping and inspection, in that
order. The recipe names no equipment: which module carries out each step is the process AAS's.

Ported from iec61499-mgmt-py (``cell/examples/products/vial_2ml.py``, the values of the process sequence
planner's pharma example), with what the execution model adds:

- the required capabilities in the lab's Capability Description extension (``ModuleCapabilityDescription``);
- **Variables** with its **Knowledge**: the state of a unit of the vial that capabilities change (its content, its custody,
  whether it is weighed, stoppered, capped, inspected), what a unit starts with, and the store the values are
  kept in; and the vial's geometry (inner diameter, inner bottom and rim heights), which the filling module's
  formulas use. The geometry is the nominal 2R vial of ISO 8362-1 (16 mm across, 1 mm wall, 35 mm high, a
  bottom of about 0.7 mm): placeholders until the vial is measured.
"""

from aas_pydantic import Capability, Key, ModelReference, Qualifier
from aas_pydantic.submodel_templates.capability_description import PropertyProperty, PropertyRange
from aas_pydantic.submodel_templates.nameplate import (
    ManufacturerProductDesignation, OrderCodeOfManufacturer, URIOfTheProduct,
)

from aas_model.constants import BASE_URL, LAB
from aas_model.product_template import (
    BillOfMaterial, PartQuantity, PartQuantityUnit, Product, ProductEntry, ProductNameplate, ProductPart, plan_id,
)
from aas_model.submodel_templates.capability_description import (
    ModuleCapabilityContainer, ModuleCapabilityDescription, ModuleCapabilitySet, StatedProperty, StatedPropertySet,
)
from aas_model.submodel_templates.product import process_parameters as pp, production_sequence as ps
from aas_model.submodel_templates.knowledge import Knowledge, StateVariable, StateVariableInitial
from aas_model.submodel_templates.variables import Variables

SMC = "SubmodelElementCollection"
AAS_ID = f"{BASE_URL}/aas/Vial2mLAAS"
ASSET_ID = f"{BASE_URL}/assets/Vial2mL"
IDTA_CAPABILITY = "https://admin-shell.io/idta/CapabilityDescription/Capability/1/0"
REQUIRED = "https://admin-shell.io/idta/CapabilityDescription/CapabilityRoleQualifier/Required/1/0"
# The unit a value is in (a qualifier, as the planner writes it).
MM = "mm"
ML = "mL"

SHELL = Key(type_="AssetAdministrationShell", value=AAS_ID)
PROCESSES = Key(type_="Submodel", value=f"{AAS_ID}/submodels/ProcessParameters")
BILL_ENTRY = (Key(type_="Submodel", value=f"{AAS_ID}/submodels/HierarchicalStructures"),
              Key(type_="Entity", value="EntryNode"))
REQUIRED_SET = (Key(type_="Submodel", value=f"{AAS_ID}/submodels/CapabilityDescription"),
                Key(type_=SMC, value="RequiredCapabilities"))
CAPABILITY_KEY = Key(type_="Capability", value="Capability")


def vial_2ml() -> Product:
    return Product(
        id_short="Vial2mLAAS", id=AAS_ID,
        description="A 2 mL vial, filled, stoppered, capped and inspected",
        display_name={"en": "Vial 2 mL"},

        # ── Nameplate (IDTA 02006): what the product is ─────────────────────────────────────────────────────
        nameplate=ProductNameplate(
            URIOfTheProduct=URIOfTheProduct(value=ASSET_ID),
            ManufacturerProductDesignation=ManufacturerProductDesignation(value={"en": "Filled vial 2 mL"}),
            OrderCodeOfManufacturer=OrderCodeOfManufacturer(value="VIAL-2ML"),
        ),

        # ── Hierarchical Structures (IDTA 02011): the bill of material ──────────────────────────────────────
        hierarchical_structures=BillOfMaterial(EntryNode=ProductEntry(
            display_name={"en": "Vial 2 mL"}, global_asset_id=ASSET_ID,
            Node={
                "Vial": ProductPart(display_name={"en": "Glass vial 2R"},
                                    Quantity=PartQuantity(value="1.0"),
                                    QuantityUnit=PartQuantityUnit(value="piece")),
                "Liquid": ProductPart(display_name={"en": "Demo liquid"},
                                      Quantity=PartQuantity(value="2.0"),
                                    QuantityUnit=PartQuantityUnit(value="mL")),
                "Stopper": ProductPart(display_name={"en": "Rubber stopper 13 mm"},
                                       Quantity=PartQuantity(value="1.0"),
                                    QuantityUnit=PartQuantityUnit(value="piece")),
                "Cap": ProductPart(display_name={"en": "Crimp cap 13 mm"},
                                   Quantity=PartQuantity(value="1.0"),
                                    QuantityUnit=PartQuantityUnit(value="piece")),
            },
        )),

        # ── Process Parameters (IDTA 02031-1 and the lab's extension) ───────────────────────────────────────
        process_parameters=pp.ProcessParameters(
            id_short="ProcessParameters", Processes=pp.Processes(Process={
                "Filling": pp.Process(
                    ProcessId=pp.ProcessId(value="Filling"), ProcessName=pp.ProcessName(value="Filling"),
                    ProcessDescription=pp.ProcessDescription(value={"en": "Fill 2 mL of liquid into the open vial"}),
                    PlannedProcessTime=pp.PlannedProcessTime(value="PT10S"),
                    ProductParameters=pp.ProductParameters(Parameter={
                        "ContainerType": pp.Parameter(
                            semantic_id=f"{LAB}ContainerType", value="vial"),
                        "GraspDiameter": pp.Parameter(
                            semantic_id=f"{LAB}GraspDiameter", value="16.0", value_type="xs:double",
                            qualifiers=[Qualifier(type_="Unit", value=MM, kind="ConceptQualifier")]),
                        "FillVolume": pp.Parameter(
                            semantic_id=f"{LAB}FillVolume", value="2.0", value_type="xs:double",
                            qualifiers=[Qualifier(type_="Unit", value=ML, kind="ConceptQualifier")]),
                    }),
                    ProcessParameters=pp.ProcessParameterGroup(), ResourceParameters=pp.ResourceParameters(),
                    ProcessBoM=pp.ProcessBoM(MaterialUse={
                        # The vial is what is worked on; the liquid goes into it, as much as FillVolume.
                        "Vial": pp.MaterialUse(
                            MaterialReference=pp.MaterialReference(value=ModelReference(
                                key=(*BILL_ENTRY, Key(type_="Entity", value="Vial")))),
                            Role=pp.Role(value="workpiece"), Quantity=pp.Quantity(value="1.0"),
                            Unit=pp.Unit(value="piece")),
                        "Liquid": pp.MaterialUse(
                            MaterialReference=pp.MaterialReference(value=ModelReference(
                                key=(*BILL_ENTRY, Key(type_="Entity", value="Liquid")))),
                            Role=pp.Role(value="incorporated"),
                            QuantityParameterReference=pp.QuantityParameterReference(value=ModelReference(key=(
                                PROCESSES, Key(type_=SMC, value="Processes"), Key(type_=SMC, value="Filling"),
                                Key(type_=SMC, value="ProductParameters"),
                                Key(type_="Property", value="FillVolume"))))),
                    }),
                    RequiredCapability=pp.RequiredCapability(value=ModelReference(
                        key=(*REQUIRED_SET, Key(type_=SMC, value="Filling"), CAPABILITY_KEY))),
                ),
                "Stoppering": pp.Process(
                    ProcessId=pp.ProcessId(value="Stoppering"), ProcessName=pp.ProcessName(value="Stoppering"),
                    ProcessDescription=pp.ProcessDescription(
                        value={"en": "Place the stopper on the filled vial and press it in"}),
                    PlannedProcessTime=pp.PlannedProcessTime(value="PT5S"),
                    ProductParameters=pp.ProductParameters(Parameter={
                        "ContainerType": pp.Parameter(
                            semantic_id=f"{LAB}ContainerType", value="vial"),
                        "GraspDiameter": pp.Parameter(
                            semantic_id=f"{LAB}GraspDiameter", value="16.0", value_type="xs:double",
                            qualifiers=[Qualifier(type_="Unit", value=MM, kind="ConceptQualifier")]),
                        "StopperDiameter": pp.Parameter(
                            semantic_id=f"{LAB}StopperDiameter", value="13.0", value_type="xs:double",
                            qualifiers=[Qualifier(type_="Unit", value=MM, kind="ConceptQualifier")]),
                    }),
                    ProcessParameters=pp.ProcessParameterGroup(), ResourceParameters=pp.ResourceParameters(),
                    ProcessBoM=pp.ProcessBoM(MaterialUse={
                        "Stopper": pp.MaterialUse(
                            MaterialReference=pp.MaterialReference(value=ModelReference(
                                key=(*BILL_ENTRY, Key(type_="Entity", value="Stopper")))),
                            Role=pp.Role(value="incorporated"), Quantity=pp.Quantity(value="1.0"),
                            Unit=pp.Unit(value="piece")),
                    }),
                    RequiredCapability=pp.RequiredCapability(value=ModelReference(
                        key=(*REQUIRED_SET, Key(type_=SMC, value="Stoppering"), CAPABILITY_KEY))),
                ),
                "Capping": pp.Process(
                    ProcessId=pp.ProcessId(value="Capping"), ProcessName=pp.ProcessName(value="Capping"),
                    ProcessDescription=pp.ProcessDescription(
                        value={"en": "Put the cap on the stoppered vial and crimp it"}),
                    PlannedProcessTime=pp.PlannedProcessTime(value="PT5S"),
                    ProductParameters=pp.ProductParameters(Parameter={
                        "ContainerType": pp.Parameter(
                            semantic_id=f"{LAB}ContainerType", value="vial"),
                        "GraspDiameter": pp.Parameter(
                            semantic_id=f"{LAB}GraspDiameter", value="16.0", value_type="xs:double",
                            qualifiers=[Qualifier(type_="Unit", value=MM, kind="ConceptQualifier")]),
                        "CapDiameter": pp.Parameter(
                            semantic_id=f"{LAB}CapDiameter", value="13.0", value_type="xs:double",
                            qualifiers=[Qualifier(type_="Unit", value=MM, kind="ConceptQualifier")]),
                    }),
                    ProcessParameters=pp.ProcessParameterGroup(), ResourceParameters=pp.ResourceParameters(),
                    ProcessBoM=pp.ProcessBoM(MaterialUse={
                        "Cap": pp.MaterialUse(
                            MaterialReference=pp.MaterialReference(value=ModelReference(
                                key=(*BILL_ENTRY, Key(type_="Entity", value="Cap")))),
                            Role=pp.Role(value="incorporated"), Quantity=pp.Quantity(value="1.0"),
                            Unit=pp.Unit(value="piece")),
                    }),
                    RequiredCapability=pp.RequiredCapability(value=ModelReference(
                        key=(*REQUIRED_SET, Key(type_=SMC, value="Capping"), CAPABILITY_KEY))),
                ),
                "Inspection": pp.Process(
                    ProcessId=pp.ProcessId(value="Inspection"), ProcessName=pp.ProcessName(value="Inspection"),
                    ProcessDescription=pp.ProcessDescription(
                        value={"en": "Inspect the closed vial and decide whether it passes"}),
                    PlannedProcessTime=pp.PlannedProcessTime(value="PT3S"),
                    ProductParameters=pp.ProductParameters(Parameter={
                        "ContainerType": pp.Parameter(
                            semantic_id=f"{LAB}ContainerType", value="vial"),
                        "GraspDiameter": pp.Parameter(
                            semantic_id=f"{LAB}GraspDiameter", value="16.0", value_type="xs:double",
                            qualifiers=[Qualifier(type_="Unit", value=MM, kind="ConceptQualifier")]),
                        "InspectionMethod": pp.Parameter(
                            semantic_id=f"{LAB}InspectionMethod", value="vision"),
                    }),
                    ProcessParameters=pp.ProcessParameterGroup(), ResourceParameters=pp.ResourceParameters(),
                    ProcessBoM=pp.ProcessBoM(),
                    RequiredCapability=pp.RequiredCapability(value=ModelReference(
                        key=(*REQUIRED_SET, Key(type_=SMC, value="Inspection"), CAPABILITY_KEY))),
                ),
            })),

        # ── Capability Description (IDTA 02020, role Required) ──────────────────────────────────────────────
        # What each process requires of a resource, with the product's values: a resource offers a capability
        # of the same meaning whose properties cover these. The fill error is a range: at most 0.1 mL.
        capability_description=ModuleCapabilityDescription(id_short="CapabilityDescription", CapabilitySet={
            "RequiredCapabilities": ModuleCapabilitySet(CapabilityContainer={
                "Filling": ModuleCapabilityContainer(
                    Capability=Capability(
                        semantic_id=IDTA_CAPABILITY, supplemental_semantic_ids=[f"{LAB}Filling"],
                        qualifiers=[Qualifier(type_="CapabilityRoleQualifier/Required", value="true",
                                              semantic_id=REQUIRED, kind="ConceptQualifier")]),
                    PropertySet={"PropertySet": StatedPropertySet(PropertyContainer={
                        "ContainerType": StatedProperty(PropertyProperty={"Value": PropertyProperty(
                            value="vial", supplemental_semantic_ids=[f"{LAB}ContainerType"])}),
                        "GraspDiameter": StatedProperty(PropertyProperty={"Value": PropertyProperty(
                            value="16.0", value_type="xs:double", supplemental_semantic_ids=[f"{LAB}GraspDiameter"],
                            qualifiers=[Qualifier(type_="Unit", value=MM, kind="ConceptQualifier")])}),
                        "FillVolume": StatedProperty(PropertyProperty={"Value": PropertyProperty(
                            value="2.0", value_type="xs:double", supplemental_semantic_ids=[f"{LAB}FillVolume"],
                            qualifiers=[Qualifier(type_="Unit", value=ML, kind="ConceptQualifier")])}),
                        "AbsoluteFillError": StatedProperty(PropertyRange={"Value": PropertyRange(
                            min="0.0", max="0.1", value_type="xs:double",
                            supplemental_semantic_ids=[f"{LAB}AbsoluteFillError"],
                            qualifiers=[Qualifier(type_="Unit", value=ML, kind="ConceptQualifier")])}),
                        # The result a filled vial is checked against: what its weight may be (2.0 mL of a liquid of
                        # density 1.0 g/mL, at most 0.1 mL off). A planner classifies the measured FillWeight against
                        # it (FillResult: in or out of tolerance), the outcomes its plan branches on (D23).
                        "FillWeight": StatedProperty(PropertyRange={"Value": PropertyRange(
                            min="1.9", max="2.1", value_type="xs:double",
                            supplemental_semantic_ids=[f"{LAB}FillWeight"],
                            qualifiers=[Qualifier(type_="Unit", value="g", kind="ConceptQualifier")])}),
                    })},
                ),
                "Stoppering": ModuleCapabilityContainer(
                    Capability=Capability(
                        semantic_id=IDTA_CAPABILITY, supplemental_semantic_ids=[f"{LAB}Stoppering"],
                        qualifiers=[Qualifier(type_="CapabilityRoleQualifier/Required", value="true",
                                              semantic_id=REQUIRED, kind="ConceptQualifier")]),
                    PropertySet={"PropertySet": StatedPropertySet(PropertyContainer={
                        "ContainerType": StatedProperty(PropertyProperty={"Value": PropertyProperty(
                            value="vial", supplemental_semantic_ids=[f"{LAB}ContainerType"])}),
                        "GraspDiameter": StatedProperty(PropertyProperty={"Value": PropertyProperty(
                            value="16.0", value_type="xs:double", supplemental_semantic_ids=[f"{LAB}GraspDiameter"],
                            qualifiers=[Qualifier(type_="Unit", value=MM, kind="ConceptQualifier")])}),
                        "StopperDiameter": StatedProperty(PropertyProperty={"Value": PropertyProperty(
                            value="13.0", value_type="xs:double", supplemental_semantic_ids=[f"{LAB}StopperDiameter"],
                            qualifiers=[Qualifier(type_="Unit", value=MM, kind="ConceptQualifier")])}),
                    })},
                ),
                "Capping": ModuleCapabilityContainer(
                    Capability=Capability(
                        semantic_id=IDTA_CAPABILITY, supplemental_semantic_ids=[f"{LAB}Capping"],
                        qualifiers=[Qualifier(type_="CapabilityRoleQualifier/Required", value="true",
                                              semantic_id=REQUIRED, kind="ConceptQualifier")]),
                    PropertySet={"PropertySet": StatedPropertySet(PropertyContainer={
                        "ContainerType": StatedProperty(PropertyProperty={"Value": PropertyProperty(
                            value="vial", supplemental_semantic_ids=[f"{LAB}ContainerType"])}),
                        "GraspDiameter": StatedProperty(PropertyProperty={"Value": PropertyProperty(
                            value="16.0", value_type="xs:double", supplemental_semantic_ids=[f"{LAB}GraspDiameter"],
                            qualifiers=[Qualifier(type_="Unit", value=MM, kind="ConceptQualifier")])}),
                        "CapDiameter": StatedProperty(PropertyProperty={"Value": PropertyProperty(
                            value="13.0", value_type="xs:double", supplemental_semantic_ids=[f"{LAB}CapDiameter"],
                            qualifiers=[Qualifier(type_="Unit", value=MM, kind="ConceptQualifier")])}),
                    })},
                ),
                "Inspection": ModuleCapabilityContainer(
                    Capability=Capability(
                        semantic_id=IDTA_CAPABILITY, supplemental_semantic_ids=[f"{LAB}Inspection"],
                        qualifiers=[Qualifier(type_="CapabilityRoleQualifier/Required", value="true",
                                              semantic_id=REQUIRED, kind="ConceptQualifier")]),
                    PropertySet={"PropertySet": StatedPropertySet(PropertyContainer={
                        "ContainerType": StatedProperty(PropertyProperty={"Value": PropertyProperty(
                            value="vial", supplemental_semantic_ids=[f"{LAB}ContainerType"])}),
                        "GraspDiameter": StatedProperty(PropertyProperty={"Value": PropertyProperty(
                            value="16.0", value_type="xs:double", supplemental_semantic_ids=[f"{LAB}GraspDiameter"],
                            qualifiers=[Qualifier(type_="Unit", value=MM, kind="ConceptQualifier")])}),
                        "InspectionMethod": StatedProperty(PropertyProperty={"Value": PropertyProperty(
                            value="vision", supplemental_semantic_ids=[f"{LAB}InspectionMethod"])}),
                    })},
                ),
            }),
        }),

        # ── Production Sequence (the planner's recipe): four steps in order, no equipment ───────────────────
        production_sequence=ps.ProductionSequence(
            id_short="ProductionSequence", id=plan_id(AAS_ID),
            PlanSchema=ps.PlanSchema(value="production-sequence/2.0"), Revision=ps.Revision(value="1"),
            SequenceId=ps.SequenceId(value="product"), Name=ps.Name(value="Vial 2 mL"), Role=ps.Role(value="Primary"),
            Subject=ps.Subject(value=ModelReference(key=(SHELL,))),
            Steps=ps.Steps(Step={
            "Step_0000": ps.Step(
                NodeId=ps.NodeId(value="Filling"), Kind=ps.Kind(value="step"), Name=ps.Name(value="Filling"),
                Order=ps.Order(value="0"), ProcessOwner=ps.ProcessOwner(value=ModelReference(key=(SHELL,))),
                ProcessReference=ps.ProcessReference(value=ModelReference(
                    key=(PROCESSES, Key(type_=SMC, value="Processes"), Key(type_=SMC, value="Filling")))),
                RequiredCapabilities=ps.RequiredCapabilities(
                    RequiredCapability={"Filling": ps.RequiredCapability(value=ModelReference(
                        key=(*REQUIRED_SET, Key(type_=SMC, value="Filling"), CAPABILITY_KEY)))}),
            ),
            "Step_0001": ps.Step(
                NodeId=ps.NodeId(value="Stoppering"), Kind=ps.Kind(value="step"), Name=ps.Name(value="Stoppering"),
                Order=ps.Order(value="1"), ProcessOwner=ps.ProcessOwner(value=ModelReference(key=(SHELL,))),
                ProcessReference=ps.ProcessReference(value=ModelReference(
                    key=(PROCESSES, Key(type_=SMC, value="Processes"), Key(type_=SMC, value="Stoppering")))),
                RequiredCapabilities=ps.RequiredCapabilities(
                    RequiredCapability={"Stoppering": ps.RequiredCapability(value=ModelReference(
                        key=(*REQUIRED_SET, Key(type_=SMC, value="Stoppering"), CAPABILITY_KEY)))}),
            ),
            "Step_0002": ps.Step(
                NodeId=ps.NodeId(value="Capping"), Kind=ps.Kind(value="step"), Name=ps.Name(value="Capping"),
                Order=ps.Order(value="2"), ProcessOwner=ps.ProcessOwner(value=ModelReference(key=(SHELL,))),
                ProcessReference=ps.ProcessReference(value=ModelReference(
                    key=(PROCESSES, Key(type_=SMC, value="Processes"), Key(type_=SMC, value="Capping")))),
                RequiredCapabilities=ps.RequiredCapabilities(
                    RequiredCapability={"Capping": ps.RequiredCapability(value=ModelReference(
                        key=(*REQUIRED_SET, Key(type_=SMC, value="Capping"), CAPABILITY_KEY)))}),
            ),
            "Step_0003": ps.Step(
                NodeId=ps.NodeId(value="Inspection"), Kind=ps.Kind(value="step"), Name=ps.Name(value="Inspection"),
                Order=ps.Order(value="3"), ProcessOwner=ps.ProcessOwner(value=ModelReference(key=(SHELL,))),
                ProcessReference=ps.ProcessReference(value=ModelReference(
                    key=(PROCESSES, Key(type_=SMC, value="Processes"), Key(type_=SMC, value="Inspection")))),
                RequiredCapabilities=ps.RequiredCapabilities(
                    RequiredCapability={"Inspection": ps.RequiredCapability(value=ModelReference(
                        key=(*REQUIRED_SET, Key(type_=SMC, value="Inspection"), CAPABILITY_KEY)))}),
            ),
            }),
        ),

        # ── Variables/Knowledge: the state of a unit, and the vial's geometry ───────────────────────────────
        # A unit starts empty, in no one's custody, and not yet weighed, stoppered, capped or inspected; what it
        # weighs is unknown until it is weighed. The geometry never changes: no effect writes it.
        variables=Variables(id_short="Variables", Knowledge=Knowledge(variable={
            "InnerDiameter": StateVariable(supplemental_semantic_ids=[f"{LAB}InnerDiameter"],
                                           Initial=StateVariableInitial(value="14.0", value_type="xs:double")),
            "InnerBottomHeight": StateVariable(supplemental_semantic_ids=[f"{LAB}InnerBottomHeight"],
                                               Initial=StateVariableInitial(value="0.7", value_type="xs:double")),
            "RimHeight": StateVariable(supplemental_semantic_ids=[f"{LAB}RimHeight"],
                                       Initial=StateVariableInitial(value="35.0", value_type="xs:double")),
            "ContentVolume": StateVariable(supplemental_semantic_ids=[f"{LAB}ContentVolume"],
                                           Initial=StateVariableInitial(value="0.0", value_type="xs:double")),
            "OutletImmersion": StateVariable(supplemental_semantic_ids=[f"{LAB}OutletImmersion"]),
            "HeldBy": StateVariable(supplemental_semantic_ids=[f"{LAB}HeldBy"]),
            "FillWeight": StateVariable(supplemental_semantic_ids=[f"{LAB}FillWeight"]),
            # Whether the measured fill is within the requirement (lab:InTolerance / lab:OutOfTolerance): unknown
            # until the unit is weighed and the result classified.
            "FillResult": StateVariable(supplemental_semantic_ids=[f"{LAB}FillResult"]),
            "Weighed": StateVariable(supplemental_semantic_ids=[f"{LAB}Weighed"],
                                     Initial=StateVariableInitial(value="false", value_type="xs:boolean")),
            "Stoppered": StateVariable(supplemental_semantic_ids=[f"{LAB}Stoppered"],
                                       Initial=StateVariableInitial(value="false", value_type="xs:boolean")),
            "Capped": StateVariable(supplemental_semantic_ids=[f"{LAB}Capped"],
                                    Initial=StateVariableInitial(value="false", value_type="xs:boolean")),
            "Inspected": StateVariable(supplemental_semantic_ids=[f"{LAB}Inspected"],
                                       Initial=StateVariableInitial(value="false", value_type="xs:boolean")),
        })),
    )
