"""The 2 mL vial with the Production Sequence 4.0 (proposed,
``docs/lab-submodels/ProductionSequence4.md``): the reference vial of iec61499-mgmt-py
(``cell/examples/products/vial_2ml.py``), with two changes.

1. The cap is the flip-off seal, a subassembly bought in, with an AAS of its own
   (``flip_off_seal.py``): an aluminium crimp seal with a plastic button. In the bill of material it
   is ``FlipOffSeal`` (a SelfManagedEntity, by asset id) in place of ``Cap``.
2. The recipe is a Production Sequence 4.0 of the archetype Assembly: one partial block whose steps
   are ordered by After alone. GMP fixes the order, so the graph is a chain:

       Filling ──> Stoppering ──> Capping ──> Inspection

   Stoppering makes the press fit of stopper and vial, Capping the crimp of seal and vial; each
   joint (an AnnotatedRelationshipElement) sits in the step that makes it. Filling makes no joint:
   it incorporates the liquid.

Nameplate, Process Parameters and Capability Description are those of the reference vial, element
for element (Capping's material is the seal). The AAS keeps the reference vial's ids: loaded on a
server, it replaces it.
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
    NationalCode, OrderCodeOfManufacturer, Street, URIOfTheProduct, YearOfConstruction, Zipcode,
)

AAS_ID = f"{BASE_URL}/aas/Vial2mLAAS"
ASSET_ID = f"{BASE_URL}/assets/Vial2mL"
PROCESSES = f"{AAS_ID}/submodels/ProcessParameters"
BILL = f"{AAS_ID}/submodels/HierarchicalStructures"
CAPABILITIES = f"{AAS_ID}/submodels/CapabilityDescription"
# What a value means: the lab's vocabulary (ontology/Vocabulary).
MEANS = f"{BASE_URL}/semantics"
CAPABILITY = "https://admin-shell.io/idta/CapabilityDescription/Capability/1/0"
REQUIRED = "https://admin-shell.io/idta/CapabilityDescription/CapabilityRoleQualifier/Required/1/0"
ASSEMBLY = sequence_id(AAS_ID, "Assembly")
SEAL_ASSET = f"{BASE_URL}/assets/FlipOffSeal13mm"


def reference(*keys: tuple[str, str]) -> ModelReference:
    """A model reference along ``keys``: (type, value) pairs."""
    return ModelReference(key=tuple(Key(type_=kind, value=value) for kind, value in keys))


def unit(symbol: str) -> list[Qualifier]:
    """The qualifier that states a value's unit."""
    return [Qualifier(type_="Unit", value=symbol, kind="ConceptQualifier")]


def vial_2ml() -> Product:
    return Product(
        id_short="Vial2mLAAS", id=AAS_ID,
        description="A 2 mL vial, filled, stoppered, sealed and inspected (Production Sequence 4.0)",
        display_name={"en": "Vial 2 mL"},

        # ── Nameplate (IDTA 02006): what the product is ─────────────────────────────────────────
        nameplate=Nameplate(
            id_short="Nameplate",
            URIOfTheProduct=URIOfTheProduct(value=ASSET_ID),
            ManufacturerName=ManufacturerName(value={"en": "AAU Smart Production Lab"}),
            ManufacturerProductDesignation=ManufacturerProductDesignation(value={"en": "Filled vial 2 mL"}),
            AddressInformation=AddressInformation(
                Street=Street(value={"en": "Fibigerstræde 14"}), Zipcode=Zipcode(value={"en": "9220"}),
                CityTown=CityTown(value={"en": "Aalborg Øst"}), NationalCode=NationalCode(value={"en": "DK"})),
            OrderCodeOfManufacturer=OrderCodeOfManufacturer(value="VIAL-2ML"),
            YearOfConstruction=YearOfConstruction(value="2026"),
            CountryOfOrigin=CountryOfOrigin(value="DK"),
        ),

        # ── Hierarchical Structures (IDTA 02011): the bill of material ──────────────────────────
        # One vial, 2 mL of liquid, one stopper, one flip-off seal. A part states how much of it the product
        # holds and in which unit (IDTA counts parts only).
        hierarchical_structures=BillOfMaterial(
            id_short="HierarchicalStructures", ArcheType=ArcheType(value="OneDown"),
            EntryNode=ProductEntry(
                display_name={"en": "Vial 2 mL"}, global_asset_id=ASSET_ID,
                Node={
                    "Vial": ProductPart(id_short="Vial", display_name={"en": "Glass vial 2R"},
                                        Quantity=PartQuantity(value="1.0"), QuantityUnit=PartQuantityUnit(value="piece")),
                    "Liquid": ProductPart(id_short="Liquid", display_name={"en": "Demo liquid"},
                                          Quantity=PartQuantity(value="2.0"), QuantityUnit=PartQuantityUnit(value="mL")),
                    "Stopper": ProductPart(id_short="Stopper", display_name={"en": "Rubber stopper 13 mm"},
                                           Quantity=PartQuantity(value="1.0"), QuantityUnit=PartQuantityUnit(value="piece")),
                    # Bought in: the seal has an AAS of its own, found by its asset id.
                    "FlipOffSeal": ProductPart(id_short="FlipOffSeal", entity_type="SelfManagedEntity",
                                               global_asset_id=SEAL_ASSET, display_name={"en": "Flip-off seal 13 mm"},
                                               Quantity=PartQuantity(value="1.0"), QuantityUnit=PartQuantityUnit(value="piece")),
                },
            ),
        ),

        # ── Process Parameters (IDTA 02031-1 and the lab's extension) ───────────────────────────
        # Each process: the product's values for it, the materials it uses, the capability it
        # requires. A binding in the process AAS hands a value from here to a skill's input.
        process_parameters=pp.ProcessParameters(
            id_short="ProcessParameters",
            Processes=pp.Processes(Process={
                "Filling": pp.Process(
                    id_short="Filling",
                    ProcessId=pp.ProcessId(value="Filling"),
                    ProcessName=pp.ProcessName(value="Filling"),
                    ProcessDescription=pp.ProcessDescription(value={"en": "Fill 2 mL of liquid into the open vial"}),
                    PlannedProcessTime=pp.PlannedProcessTime(value="PT10S"),
                    ProductParameters=pp.ProductParameters(Parameter={
                        "ContainerType": pp.Parameter(id_short="ContainerType", semantic_id=f"{MEANS}/ContainerType",
                                                      value="vial"),
                        "GraspDiameter": pp.Parameter(id_short="GraspDiameter", semantic_id=f"{MEANS}/GraspDiameter",
                                                      value="16.0", value_type="xs:double", qualifiers=unit("mm")),
                        "FillVolume": pp.Parameter(id_short="FillVolume", semantic_id=f"{MEANS}/FillVolume",
                                                   value="2.0", value_type="xs:double", qualifiers=unit("mL")),
                    }),
                    ProcessParameters=pp.ProcessParameterGroup(),
                    ResourceParameters=pp.ResourceParameters(),
                    ProcessBoM=pp.ProcessBoM(MaterialUse={
                        # The vial is what is worked on; the liquid goes into it, as much as FillVolume.
                        "Vial": pp.MaterialUse(
                            id_short="Vial",
                            MaterialReference=pp.MaterialReference(value=reference(
                                ("Submodel", BILL), ("Entity", "EntryNode"), ("Entity", "Vial"))),
                            Role=pp.Role(value="workpiece"), Quantity=pp.Quantity(value="1.0"), Unit=pp.Unit(value="piece")),
                        "Liquid": pp.MaterialUse(
                            id_short="Liquid",
                            MaterialReference=pp.MaterialReference(value=reference(
                                ("Submodel", BILL), ("Entity", "EntryNode"), ("Entity", "Liquid"))),
                            Role=pp.Role(value="incorporated"),
                            QuantityParameterReference=pp.QuantityParameterReference(value=reference(
                                ("Submodel", PROCESSES), ("SubmodelElementCollection", "Processes"),
                                ("SubmodelElementCollection", "Filling"),
                                ("SubmodelElementCollection", "ProductParameters"), ("Property", "FillVolume")))),
                    }),
                    RequiredCapability=pp.RequiredCapability(value=reference(
                        ("Submodel", CAPABILITIES), ("SubmodelElementCollection", "RequiredCapabilities"),
                        ("SubmodelElementCollection", "Filling"), ("Capability", "Capability"))),
                ),
                "Stoppering": pp.Process(
                    id_short="Stoppering",
                    ProcessId=pp.ProcessId(value="Stoppering"),
                    ProcessName=pp.ProcessName(value="Stoppering"),
                    ProcessDescription=pp.ProcessDescription(value={"en": "Place the stopper on the filled vial and press it in"}),
                    PlannedProcessTime=pp.PlannedProcessTime(value="PT5S"),
                    ProductParameters=pp.ProductParameters(Parameter={
                        "ContainerType": pp.Parameter(id_short="ContainerType", semantic_id=f"{MEANS}/ContainerType",
                                                      value="vial"),
                        "GraspDiameter": pp.Parameter(id_short="GraspDiameter", semantic_id=f"{MEANS}/GraspDiameter",
                                                      value="16.0", value_type="xs:double", qualifiers=unit("mm")),
                        "StopperDiameter": pp.Parameter(id_short="StopperDiameter", semantic_id=f"{MEANS}/StopperDiameter",
                                                        value="13.0", value_type="xs:double", qualifiers=unit("mm")),
                    }),
                    ProcessParameters=pp.ProcessParameterGroup(),
                    ResourceParameters=pp.ResourceParameters(),
                    ProcessBoM=pp.ProcessBoM(MaterialUse={
                        "Stopper": pp.MaterialUse(
                            id_short="Stopper",
                            MaterialReference=pp.MaterialReference(value=reference(
                                ("Submodel", BILL), ("Entity", "EntryNode"), ("Entity", "Stopper"))),
                            Role=pp.Role(value="incorporated"), Quantity=pp.Quantity(value="1.0"), Unit=pp.Unit(value="piece")),
                    }),
                    RequiredCapability=pp.RequiredCapability(value=reference(
                        ("Submodel", CAPABILITIES), ("SubmodelElementCollection", "RequiredCapabilities"),
                        ("SubmodelElementCollection", "Stoppering"), ("Capability", "Capability"))),
                ),
                "Capping": pp.Process(
                    id_short="Capping",
                    ProcessId=pp.ProcessId(value="Capping"),
                    ProcessName=pp.ProcessName(value="Capping"),
                    ProcessDescription=pp.ProcessDescription(value={"en": "Put the flip-off seal on the stoppered vial and crimp it"}),
                    PlannedProcessTime=pp.PlannedProcessTime(value="PT5S"),
                    ProductParameters=pp.ProductParameters(Parameter={
                        "ContainerType": pp.Parameter(id_short="ContainerType", semantic_id=f"{MEANS}/ContainerType",
                                                      value="vial"),
                        "GraspDiameter": pp.Parameter(id_short="GraspDiameter", semantic_id=f"{MEANS}/GraspDiameter",
                                                      value="16.0", value_type="xs:double", qualifiers=unit("mm")),
                        "CapDiameter": pp.Parameter(id_short="CapDiameter", semantic_id=f"{MEANS}/CapDiameter",
                                                    value="13.0", value_type="xs:double", qualifiers=unit("mm")),
                    }),
                    ProcessParameters=pp.ProcessParameterGroup(),
                    ResourceParameters=pp.ResourceParameters(),
                    ProcessBoM=pp.ProcessBoM(MaterialUse={
                        "FlipOffSeal": pp.MaterialUse(
                            id_short="FlipOffSeal",
                            MaterialReference=pp.MaterialReference(value=reference(
                                ("Submodel", BILL), ("Entity", "EntryNode"), ("Entity", "FlipOffSeal"))),
                            Role=pp.Role(value="incorporated"), Quantity=pp.Quantity(value="1.0"), Unit=pp.Unit(value="piece")),
                    }),
                    RequiredCapability=pp.RequiredCapability(value=reference(
                        ("Submodel", CAPABILITIES), ("SubmodelElementCollection", "RequiredCapabilities"),
                        ("SubmodelElementCollection", "Capping"), ("Capability", "Capability"))),
                ),
                "Inspection": pp.Process(
                    id_short="Inspection",
                    ProcessId=pp.ProcessId(value="Inspection"),
                    ProcessName=pp.ProcessName(value="Inspection"),
                    ProcessDescription=pp.ProcessDescription(value={"en": "Inspect the closed vial and decide whether it passes"}),
                    PlannedProcessTime=pp.PlannedProcessTime(value="PT3S"),
                    ProductParameters=pp.ProductParameters(Parameter={
                        "ContainerType": pp.Parameter(id_short="ContainerType", semantic_id=f"{MEANS}/ContainerType",
                                                      value="vial"),
                        "GraspDiameter": pp.Parameter(id_short="GraspDiameter", semantic_id=f"{MEANS}/GraspDiameter",
                                                      value="16.0", value_type="xs:double", qualifiers=unit("mm")),
                        "InspectionMethod": pp.Parameter(id_short="InspectionMethod", semantic_id=f"{MEANS}/InspectionMethod",
                                                         value="vision"),
                    }),
                    ProcessParameters=pp.ProcessParameterGroup(),
                    ResourceParameters=pp.ResourceParameters(),
                    ProcessBoM=pp.ProcessBoM(),
                    RequiredCapability=pp.RequiredCapability(value=reference(
                        ("Submodel", CAPABILITIES), ("SubmodelElementCollection", "RequiredCapabilities"),
                        ("SubmodelElementCollection", "Inspection"), ("Capability", "Capability"))),
                ),
            }),
        ),

        # ── Capability Description (IDTA 02020, role Required) ───────────────────────────────────
        # What each process requires of a resource, with the product's values: a resource offers a
        # capability of the same meaning (supplemental id) whose properties cover these. The fill
        # error is a range: at most 0.1 mL either way.
        capability_description=cd.CapabilityDescription(
            id_short="CapabilityDescription",
            CapabilitySet={"RequiredCapabilities": cd.CapabilitySet(
                id_short="RequiredCapabilities",
                CapabilityContainer={
                    "Filling": cd.CapabilityContainer(
                        id_short="Filling",
                        Capability=Capability(
                            id_short="Capability", semantic_id=CAPABILITY, supplemental_semantic_ids=[f"{MEANS}/Filling"],
                            display_name={"en": "Filling"},
                            qualifiers=[Qualifier(type_="CapabilityRoleQualifier/Required", value="true",
                                                  semantic_id=REQUIRED, kind="ConceptQualifier")]),
                        PropertySet={"PropertySet": cd.PropertySet(PropertyContainer={
                            "ContainerType": cd.PropertyContainer(id_short="ContainerType", PropertyProperty={
                                "Value": cd.PropertyProperty(id_short="Value", display_name={"en": "ContainerType"},
                                                             supplemental_semantic_ids=[f"{MEANS}/ContainerType"],
                                                             value="vial")}),
                            "GraspDiameter": cd.PropertyContainer(id_short="GraspDiameter", PropertyProperty={
                                "Value": cd.PropertyProperty(id_short="Value", display_name={"en": "GraspDiameter"},
                                                             supplemental_semantic_ids=[f"{MEANS}/GraspDiameter"],
                                                             value="16.0", value_type="xs:double", qualifiers=unit("mm"))}),
                            "FillVolume": cd.PropertyContainer(id_short="FillVolume", PropertyProperty={
                                "Value": cd.PropertyProperty(id_short="Value", display_name={"en": "FillVolume"},
                                                             supplemental_semantic_ids=[f"{MEANS}/FillVolume"],
                                                             value="2.0", value_type="xs:double", qualifiers=unit("mL"))}),
                            "AbsoluteFillError": cd.PropertyContainer(id_short="AbsoluteFillError", PropertyRange={
                                "Value": cd.PropertyRange(id_short="Value", display_name={"en": "AbsoluteFillError"},
                                                          supplemental_semantic_ids=[f"{MEANS}/AbsoluteFillError"],
                                                          min="0.0", max="0.1", value_type="xs:double", qualifiers=unit("mL"))}),
                        })},
                    ),
                    "Stoppering": cd.CapabilityContainer(
                        id_short="Stoppering",
                        Capability=Capability(
                            id_short="Capability", semantic_id=CAPABILITY, supplemental_semantic_ids=[f"{MEANS}/Stoppering"],
                            display_name={"en": "Stoppering"},
                            qualifiers=[Qualifier(type_="CapabilityRoleQualifier/Required", value="true",
                                                  semantic_id=REQUIRED, kind="ConceptQualifier")]),
                        PropertySet={"PropertySet": cd.PropertySet(PropertyContainer={
                            "ContainerType": cd.PropertyContainer(id_short="ContainerType", PropertyProperty={
                                "Value": cd.PropertyProperty(id_short="Value", display_name={"en": "ContainerType"},
                                                             supplemental_semantic_ids=[f"{MEANS}/ContainerType"],
                                                             value="vial")}),
                            "GraspDiameter": cd.PropertyContainer(id_short="GraspDiameter", PropertyProperty={
                                "Value": cd.PropertyProperty(id_short="Value", display_name={"en": "GraspDiameter"},
                                                             supplemental_semantic_ids=[f"{MEANS}/GraspDiameter"],
                                                             value="16.0", value_type="xs:double", qualifiers=unit("mm"))}),
                            "StopperDiameter": cd.PropertyContainer(id_short="StopperDiameter", PropertyProperty={
                                "Value": cd.PropertyProperty(id_short="Value", display_name={"en": "StopperDiameter"},
                                                             supplemental_semantic_ids=[f"{MEANS}/StopperDiameter"],
                                                             value="13.0", value_type="xs:double", qualifiers=unit("mm"))}),
                        })},
                    ),
                    "Capping": cd.CapabilityContainer(
                        id_short="Capping",
                        Capability=Capability(
                            id_short="Capability", semantic_id=CAPABILITY, supplemental_semantic_ids=[f"{MEANS}/Capping"],
                            display_name={"en": "Capping"},
                            qualifiers=[Qualifier(type_="CapabilityRoleQualifier/Required", value="true",
                                                  semantic_id=REQUIRED, kind="ConceptQualifier")]),
                        PropertySet={"PropertySet": cd.PropertySet(PropertyContainer={
                            "ContainerType": cd.PropertyContainer(id_short="ContainerType", PropertyProperty={
                                "Value": cd.PropertyProperty(id_short="Value", display_name={"en": "ContainerType"},
                                                             supplemental_semantic_ids=[f"{MEANS}/ContainerType"],
                                                             value="vial")}),
                            "GraspDiameter": cd.PropertyContainer(id_short="GraspDiameter", PropertyProperty={
                                "Value": cd.PropertyProperty(id_short="Value", display_name={"en": "GraspDiameter"},
                                                             supplemental_semantic_ids=[f"{MEANS}/GraspDiameter"],
                                                             value="16.0", value_type="xs:double", qualifiers=unit("mm"))}),
                            "CapDiameter": cd.PropertyContainer(id_short="CapDiameter", PropertyProperty={
                                "Value": cd.PropertyProperty(id_short="Value", display_name={"en": "CapDiameter"},
                                                             supplemental_semantic_ids=[f"{MEANS}/CapDiameter"],
                                                             value="13.0", value_type="xs:double", qualifiers=unit("mm"))}),
                        })},
                    ),
                    "Inspection": cd.CapabilityContainer(
                        id_short="Inspection",
                        Capability=Capability(
                            id_short="Capability", semantic_id=CAPABILITY, supplemental_semantic_ids=[f"{MEANS}/Inspection"],
                            display_name={"en": "Inspection"},
                            qualifiers=[Qualifier(type_="CapabilityRoleQualifier/Required", value="true",
                                                  semantic_id=REQUIRED, kind="ConceptQualifier")]),
                        PropertySet={"PropertySet": cd.PropertySet(PropertyContainer={
                            "ContainerType": cd.PropertyContainer(id_short="ContainerType", PropertyProperty={
                                "Value": cd.PropertyProperty(id_short="Value", display_name={"en": "ContainerType"},
                                                             supplemental_semantic_ids=[f"{MEANS}/ContainerType"],
                                                             value="vial")}),
                            "GraspDiameter": cd.PropertyContainer(id_short="GraspDiameter", PropertyProperty={
                                "Value": cd.PropertyProperty(id_short="Value", display_name={"en": "GraspDiameter"},
                                                             supplemental_semantic_ids=[f"{MEANS}/GraspDiameter"],
                                                             value="16.0", value_type="xs:double", qualifiers=unit("mm"))}),
                            "InspectionMethod": cd.PropertyContainer(id_short="InspectionMethod", PropertyProperty={
                                "Value": cd.PropertyProperty(id_short="Value", display_name={"en": "InspectionMethod"},
                                                             supplemental_semantic_ids=[f"{MEANS}/InspectionMethod"],
                                                             value="vision")}),
                        })},
                    ),
                },
            )},
        ),

        # ── Production Sequence 4.0, archetype Assembly ─────────────────────────────────────────
        assembly_sequence=assembly(),
    )


# ---- the Production Sequence 4.0 ------------------------------------------------------------------
def part(name: str) -> ModelReference:
    """An entity of the vial's bill of material."""
    return reference(("Submodel", BILL), ("Entity", "EntryNode"), ("Entity", name))


def process(name: str) -> ps4.ProcessReference:
    return ps4.ProcessReference(value=reference(
        ("Submodel", PROCESSES), ("SubmodelElementCollection", "Processes"), ("SubmodelElementCollection", name)))


def step(sequence: str, name: str) -> ModelReference:
    """A step of the partial block (Step_0000) of ``sequence``: an end of a ProcessOrder."""
    return reference(("Submodel", sequence), ("SubmodelElementCollection", "Steps"), ("SubmodelElementCollection", "Step_0000"),
                     ("SubmodelElementCollection", "Steps"), ("SubmodelElementCollection", name))


def assembly() -> ps4.ProductionSequence:
    return ps4.ProductionSequence(
        id=ASSEMBLY, id_short="ProductionSequenceAssembly",
        display_name={"en": "Vial 2 mL: filling and closing"},
        ArcheType=ps4.ArcheType(value="Assembly"),
        Revision=ps4.Revision(value="1"),
        Name=ps4.Name(value="Vial 2 mL"),
        Subject=ps4.Subject(value=reference(("AssetAdministrationShell", AAS_ID))),
        Steps=ps4.Steps(Step={
            "Step_0000": ps4.Step(
                id_short="Step_0000", NodeId=ps4.NodeId(value="FillAndClose"), Kind=ps4.Kind(value="partial"),
                Name=ps4.StepName(value="Fill and close the vial"), Order=ps4.Order(value="0"),
                ProcessOrders=ps4.ProcessOrders(ProcessOrder={
                    "ProcessOrder_0000": ps4.ProcessOrder(
                        id_short="ProcessOrder_0000", first=step(ASSEMBLY, "Step_0000"),
                        second=step(ASSEMBLY, "Step_0001"), Reason=ps4.Reason(value="the vial is filled before it is closed")),
                    "ProcessOrder_0001": ps4.ProcessOrder(
                        id_short="ProcessOrder_0001", first=step(ASSEMBLY, "Step_0001"),
                        second=step(ASSEMBLY, "Step_0002"), Reason=ps4.Reason(value="the seal is crimped over the stopper")),
                    "ProcessOrder_0002": ps4.ProcessOrder(
                        id_short="ProcessOrder_0002", first=step(ASSEMBLY, "Step_0002"),
                        second=step(ASSEMBLY, "Step_0003"), Reason=ps4.Reason(value="the closed vial is inspected (GMP)")),
                }),
                Steps=ps4.Steps(Step={

                    # Filling: nothing before it; no joint (the liquid is incorporated).
                    "Step_0000": ps4.Step(
                        id_short="Step_0000", NodeId=ps4.NodeId(value="Filling"), Kind=ps4.Kind(value="step"),
                        Name=ps4.StepName(value="Filling"), Order=ps4.Order(value="0"),
                        EstimatedDuration=ps4.EstimatedDuration(value="12"),
                        ProcessReference=process("Filling")),

                    # Stoppering: after Filling; makes the press fit of stopper and vial.
                    "Step_0001": ps4.Step(
                        id_short="Step_0001", NodeId=ps4.NodeId(value="Stoppering"), Kind=ps4.Kind(value="step"),
                        Name=ps4.StepName(value="Stoppering"), Order=ps4.Order(value="1"),
                        EstimatedDuration=ps4.EstimatedDuration(value="6"),
                        ProcessReference=process("Stoppering"),
                        Joints=ps4.Joints(Joint={
                            "J_Stopper": ps4.Joint(
                                id_short="J_Stopper", display_name={"en": "Stopper pressed into the vial"},
                                supplemental_semantic_ids=[f"{MEANS}/PressFitJoint"],
                                first=part("Stopper"), second=part("Vial"),
                                JointType=ps4.JointType(value="PressFit"), JointStandard=ps4.JointStandard(value="DIN 8593-3")),
                        })),

                    # Capping: after Stoppering; makes the crimp of seal and vial.
                    "Step_0002": ps4.Step(
                        id_short="Step_0002", NodeId=ps4.NodeId(value="Capping"), Kind=ps4.Kind(value="step"),
                        Name=ps4.StepName(value="Capping"), Order=ps4.Order(value="2"),
                        EstimatedDuration=ps4.EstimatedDuration(value="8"),
                        ProcessReference=process("Capping"),
                        Joints=ps4.Joints(Joint={
                            "J_Seal": ps4.Joint(
                                id_short="J_Seal", display_name={"en": "Seal crimped onto the vial"},
                                supplemental_semantic_ids=[f"{MEANS}/CrimpedJoint"],
                                first=part("FlipOffSeal"), second=part("Vial"),
                                JointType=ps4.JointType(value="Crimp"), JointStandard=ps4.JointStandard(value="DIN 8593-5")),
                        })),

                    # Inspection: after Capping; declares the two cameras' results.
                    "Step_0003": ps4.Step(
                        id_short="Step_0003", NodeId=ps4.NodeId(value="Inspection"), Kind=ps4.Kind(value="step"),
                        Name=ps4.StepName(value="Inspection"), Order=ps4.Order(value="3"),
                        EstimatedDuration=ps4.EstimatedDuration(value="4"),
                        ProcessReference=process("Inspection"),
                        Outputs=ps4.Outputs(Output={
                            "Output_0000": ps4.Output(
                                id_short="Output_0000", OutputId=ps4.OutputId(value="TopPassed"),
                                Name=ps4.OutputName(value="Top camera passed"), DataType=ps4.DataType(value="boolean")),
                            "Output_0001": ps4.Output(
                                id_short="Output_0001", OutputId=ps4.OutputId(value="SidePassed"),
                                Name=ps4.OutputName(value="Side camera passed"), DataType=ps4.DataType(value="boolean")),
                        })),
                })),
        }))
