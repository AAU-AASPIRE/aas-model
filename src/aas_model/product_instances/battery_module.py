"""A battery module of the pack (``battery_pack.py``): a subassembly with an AAS and a Production
Sequence of its own, which the pack's Disassembly sequence calls. Four modules, one AAS each
(``battery_module(1)`` to ``battery_module(4)``): they are instances, each with its own serial number
and, once tested, its own state of health.

Taken apart:

    RemoveLid ──> TestCells ──> StateOfHealth ≥ 80 %?  ── yes ──> SortForReuse
                                                       └─ no ──> SortForRecycling

RemoveLid breaks the lid's clip joint (between two parts of this module, so it is in this module's
sequence, not the pack's). TestCells declares its output StateOfHealth; the decision compares it,
as Production Sequence 3.0 does (Condition, Operand, Expected).

Written like ``battery_pack.py``, with aas-model's classes.
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

from aas_model.product_instances.battery_cell import ASSET_ID as CELL_TYPE

MEANS = f"{BASE_URL}/semantics"
CAPABILITY = "https://admin-shell.io/idta/CapabilityDescription/Capability/1/0"
REQUIRED = "https://admin-shell.io/idta/CapabilityDescription/CapabilityRoleQualifier/Required/1/0"
ASSET_KIND = "Instance"


def ids(n: int) -> dict[str, str]:
    """The ids of module ``n``: its AAS, asset and submodels."""
    aas = f"{BASE_URL}/aas/BatteryModule{n}AAS"
    return {"aas": aas, "asset": f"{BASE_URL}/assets/BatteryModule/SN-0042-{n}",
            "processes": f"{aas}/submodels/ProcessParameters", "bill": f"{aas}/submodels/HierarchicalStructures",
            "capabilities": f"{aas}/submodels/CapabilityDescription", "disassembly": sequence_id(aas, "Disassembly")}


def reference(*keys: tuple[str, str]) -> ModelReference:
    return ModelReference(key=tuple(Key(type_=kind, value=value) for kind, value in keys))


def unit(symbol: str) -> list[Qualifier]:
    return [Qualifier(type_="Unit", value=symbol, kind="ConceptQualifier")]


def required() -> list[Qualifier]:
    return [Qualifier(type_="CapabilityRoleQualifier/Required", value="true", semantic_id=REQUIRED, kind="ConceptQualifier")]


def battery_module(n: int) -> Product:
    i = ids(n)
    return Product(
        id_short=f"BatteryModule{n}AAS", id=i["aas"],
        description=f"Battery module {n} of pack SN-0042: twelve cells under a clipped lid",
        display_name={"en": f"Battery module {n}"},

        nameplate=Nameplate(
            id_short="Nameplate",
            URIOfTheProduct=URIOfTheProduct(value=i["asset"]),
            ManufacturerName=ManufacturerName(value={"en": "Demo EV maker"}),
            ManufacturerProductDesignation=ManufacturerProductDesignation(value={"en": "Battery module, 12 cells"}),
            AddressInformation=AddressInformation(
                Street=Street(value={"en": "Demo street 1"}), Zipcode=Zipcode(value={"en": "9220"}),
                CityTown=CityTown(value={"en": "Aalborg Øst"}), NationalCode=NationalCode(value={"en": "DK"})),
            OrderCodeOfManufacturer=OrderCodeOfManufacturer(value="MOD-12C"),
            SerialNumber=SerialNumber(value=f"SN-0042-{n}"),
            YearOfConstruction=YearOfConstruction(value="2019"),
            CountryOfOrigin=CountryOfOrigin(value="DE"),
        ),

        # ── Hierarchical Structures: lid, housing, 12 cells of one cell type (its AAS by asset id) ──
        hierarchical_structures=BillOfMaterial(
            id_short="HierarchicalStructures", ArcheType=ArcheType(value="OneDown"),
            EntryNode=ProductEntry(
                display_name={"en": f"Battery module {n}"}, global_asset_id=i["asset"],
                Node={
                    "Lid": ProductPart(id_short="Lid", display_name={"en": "Module lid"},
                                       Quantity=PartQuantity(value="1.0"), QuantityUnit=PartQuantityUnit(value="piece")),
                    "ModuleHousing": ProductPart(id_short="ModuleHousing", display_name={"en": "Module housing"},
                                                 Quantity=PartQuantity(value="1.0"), QuantityUnit=PartQuantityUnit(value="piece")),
                    "Cell": ProductPart(id_short="Cell", entity_type="SelfManagedEntity", global_asset_id=CELL_TYPE,
                                        display_name={"en": "Prismatic cell 60 Ah"},
                                        Quantity=PartQuantity(value="12.0"), QuantityUnit=PartQuantityUnit(value="piece")),
                },
            ),
        ),

        process_parameters=pp.ProcessParameters(
            id_short="ProcessParameters",
            Processes=pp.Processes(Process={
                "Unclipping": pp.Process(
                    id_short="Unclipping",
                    ProcessId=pp.ProcessId(value="Unclipping"), ProcessName=pp.ProcessName(value="Unclipping"),
                    ProcessDescription=pp.ProcessDescription(value={"en": "Release the lid's clips and lift it off"}),
                    PlannedProcessTime=pp.PlannedProcessTime(value="PT20S"),
                    ProductParameters=pp.ProductParameters(Parameter={
                        "ReleaseForce": pp.Parameter(id_short="ReleaseForce", semantic_id=f"{MEANS}/Force",
                                                     value="25.0", value_type="xs:double", qualifiers=unit("N")),
                    }),
                    ProcessParameters=pp.ProcessParameterGroup(), ResourceParameters=pp.ResourceParameters(),
                    ProcessBoM=pp.ProcessBoM(MaterialUse={
                        "Lid": pp.MaterialUse(
                            id_short="Lid",
                            MaterialReference=pp.MaterialReference(value=reference(
                                ("Submodel", i["bill"]), ("Entity", "EntryNode"), ("Entity", "Lid"))),
                            Role=pp.Role(value="output"), Quantity=pp.Quantity(value="1.0"), Unit=pp.Unit(value="piece")),
                    }),
                    RequiredCapability=pp.RequiredCapability(value=reference(
                        ("Submodel", i["capabilities"]), ("SubmodelElementCollection", "RequiredCapabilities"),
                        ("SubmodelElementCollection", "Unclipping"), ("Capability", "Capability"))),
                ),
                "CellTesting": pp.Process(
                    id_short="CellTesting",
                    ProcessId=pp.ProcessId(value="CellTesting"), ProcessName=pp.ProcessName(value="CellTesting"),
                    ProcessDescription=pp.ProcessDescription(value={"en": "Test the twelve cells and give the module's state of health"}),
                    PlannedProcessTime=pp.PlannedProcessTime(value="PT300S"),
                    ProductParameters=pp.ProductParameters(Parameter={
                        "DischargeCurrent": pp.Parameter(id_short="DischargeCurrent", semantic_id=f"{MEANS}/Current",
                                                         value="10.0", value_type="xs:double", qualifiers=unit("A")),
                        "NominalCapacity": pp.Parameter(id_short="NominalCapacity", semantic_id=f"{MEANS}/Capacity",
                                                        value="60.0", value_type="xs:double", qualifiers=unit("A·h")),
                    }),
                    ProcessParameters=pp.ProcessParameterGroup(), ResourceParameters=pp.ResourceParameters(),
                    ProcessBoM=pp.ProcessBoM(MaterialUse={
                        "Cell": pp.MaterialUse(
                            id_short="Cell",
                            MaterialReference=pp.MaterialReference(value=reference(
                                ("Submodel", i["bill"]), ("Entity", "EntryNode"), ("Entity", "Cell"))),
                            Role=pp.Role(value="workpiece"), Quantity=pp.Quantity(value="12.0"), Unit=pp.Unit(value="piece")),
                    }),
                    RequiredCapability=pp.RequiredCapability(value=reference(
                        ("Submodel", i["capabilities"]), ("SubmodelElementCollection", "RequiredCapabilities"),
                        ("SubmodelElementCollection", "CellTesting"), ("Capability", "Capability"))),
                ),
                "SortingForReuse": pp.Process(
                    id_short="SortingForReuse",
                    ProcessId=pp.ProcessId(value="SortingForReuse"), ProcessName=pp.ProcessName(value="SortingForReuse"),
                    ProcessDescription=pp.ProcessDescription(value={"en": "Put the module on the reuse shelf"}),
                    PlannedProcessTime=pp.PlannedProcessTime(value="PT15S"),
                    ProductParameters=pp.ProductParameters(Parameter={
                        "Destination": pp.Parameter(id_short="Destination", semantic_id=f"{MEANS}/Destination", value="reuse"),
                    }),
                    ProcessParameters=pp.ProcessParameterGroup(), ResourceParameters=pp.ResourceParameters(),
                    ProcessBoM=pp.ProcessBoM(),
                    RequiredCapability=pp.RequiredCapability(value=reference(
                        ("Submodel", i["capabilities"]), ("SubmodelElementCollection", "RequiredCapabilities"),
                        ("SubmodelElementCollection", "SortingForReuse"), ("Capability", "Capability"))),
                ),
                "SortingForRecycling": pp.Process(
                    id_short="SortingForRecycling",
                    ProcessId=pp.ProcessId(value="SortingForRecycling"), ProcessName=pp.ProcessName(value="SortingForRecycling"),
                    ProcessDescription=pp.ProcessDescription(value={"en": "Put the module in the recycling bin"}),
                    PlannedProcessTime=pp.PlannedProcessTime(value="PT15S"),
                    ProductParameters=pp.ProductParameters(Parameter={
                        "Destination": pp.Parameter(id_short="Destination", semantic_id=f"{MEANS}/Destination", value="recycling"),
                    }),
                    ProcessParameters=pp.ProcessParameterGroup(), ResourceParameters=pp.ResourceParameters(),
                    ProcessBoM=pp.ProcessBoM(),
                    RequiredCapability=pp.RequiredCapability(value=reference(
                        ("Submodel", i["capabilities"]), ("SubmodelElementCollection", "RequiredCapabilities"),
                        ("SubmodelElementCollection", "SortingForRecycling"), ("Capability", "Capability"))),
                ),
            }),
        ),

        capability_description=cd.CapabilityDescription(
            id_short="CapabilityDescription",
            CapabilitySet={"RequiredCapabilities": cd.CapabilitySet(
                id_short="RequiredCapabilities",
                CapabilityContainer={
                    "Unclipping": cd.CapabilityContainer(
                        id_short="Unclipping",
                        Capability=Capability(id_short="Capability", semantic_id=CAPABILITY,
                                              supplemental_semantic_ids=[f"{MEANS}/Unclipping"],
                                              display_name={"en": "Unclipping"}, qualifiers=required()),
                    ),
                    "CellTesting": cd.CapabilityContainer(
                        id_short="CellTesting",
                        Capability=Capability(id_short="Capability", semantic_id=CAPABILITY,
                                              supplemental_semantic_ids=[f"{MEANS}/CellTesting"],
                                              display_name={"en": "Cell testing"}, qualifiers=required()),
                        PropertySet={"PropertySet": cd.PropertySet(PropertyContainer={
                            "Current": cd.PropertyContainer(id_short="Current", PropertyProperty={
                                "Value": cd.PropertyProperty(id_short="Value", display_name={"en": "Current"},
                                                             supplemental_semantic_ids=[f"{MEANS}/Current"],
                                                             value="10.0", value_type="xs:double", qualifiers=unit("A"))}),
                        })},
                    ),
                    "SortingForReuse": cd.CapabilityContainer(
                        id_short="SortingForReuse",
                        Capability=Capability(id_short="Capability", semantic_id=CAPABILITY,
                                              supplemental_semantic_ids=[f"{MEANS}/Sorting"],
                                              display_name={"en": "Sorting"}, qualifiers=required()),
                        PropertySet={"PropertySet": cd.PropertySet(PropertyContainer={
                            "Destination": cd.PropertyContainer(id_short="Destination", PropertyProperty={
                                "Value": cd.PropertyProperty(id_short="Value", display_name={"en": "Destination"},
                                                             supplemental_semantic_ids=[f"{MEANS}/Destination"],
                                                             value="reuse")}),
                        })},
                    ),
                    "SortingForRecycling": cd.CapabilityContainer(
                        id_short="SortingForRecycling",
                        Capability=Capability(id_short="Capability", semantic_id=CAPABILITY,
                                              supplemental_semantic_ids=[f"{MEANS}/Sorting"],
                                              display_name={"en": "Sorting"}, qualifiers=required()),
                        PropertySet={"PropertySet": cd.PropertySet(PropertyContainer={
                            "Destination": cd.PropertyContainer(id_short="Destination", PropertyProperty={
                                "Value": cd.PropertyProperty(id_short="Value", display_name={"en": "Destination"},
                                                             supplemental_semantic_ids=[f"{MEANS}/Destination"],
                                                             value="recycling")}),
                        })},
                    ),
                },
            )},
        ),

        disassembly_sequence=battery_module_sequence(n),
    )


def battery_module_sequence(n: int) -> ps4.ProductionSequence:
    """Taking module ``n`` apart and grading it."""
    i = ids(n)

    def process(name: str) -> ps4.ProcessReference:
        return ps4.ProcessReference(value=reference(
            ("Submodel", i["processes"]), ("SubmodelElementCollection", "Processes"), ("SubmodelElementCollection", name)))

    def step(sequence: str, name: str) -> ModelReference:
        """A step of the partial block Teardown: an end of a ProcessOrder."""
        return reference(("Submodel", sequence), ("SubmodelElementCollection", "Steps"),
                         ("SubmodelElementCollection", "Step_0000"), ("SubmodelElementCollection", "Steps"),
                         ("SubmodelElementCollection", name))

    return ps4.ProductionSequence(
        id=i["disassembly"], id_short="ProductionSequenceDisassembly",
        display_name={"en": f"Battery module {n}: taking apart"},
        ArcheType=ps4.ArcheType(value="Disassembly"),
        Revision=ps4.Revision(value="1"),
        Name=ps4.Name(value=f"Battery module {n}, taken apart and graded"),
        Subject=ps4.Subject(value=reference(("AssetAdministrationShell", i["aas"]))),
        Steps=ps4.Steps(Step={
            "Step_0000": ps4.Step(
                id_short="Step_0000", NodeId=ps4.NodeId(value="Teardown"), Kind=ps4.Kind(value="partial"),
                Name=ps4.StepName(value="Take the module apart"), Order=ps4.Order(value="0"),
                ProcessOrders=ps4.ProcessOrders(ProcessOrder={
                    "ProcessOrder_0000": ps4.ProcessOrder(
                        id_short="ProcessOrder_0000", first=step(i["disassembly"], "Step_0000"),
                        second=step(i["disassembly"], "Step_0001"), Reason=ps4.Reason(value="the cells are under the lid")),
                    "ProcessOrder_0001": ps4.ProcessOrder(
                        id_short="ProcessOrder_0001", first=step(i["disassembly"], "Step_0001"),
                        second=step(i["disassembly"], "Step_0002"), Reason=ps4.Reason(value="grading needs the state of health")),
                }),
                Steps=ps4.Steps(Step={

                    # RemoveLid: breaks the clip joint between lid and housing.
                    "Step_0000": ps4.Step(
                        id_short="Step_0000", NodeId=ps4.NodeId(value="RemoveLid"), Kind=ps4.Kind(value="step"),
                        Name=ps4.StepName(value="Remove the lid"), Order=ps4.Order(value="0"),
                        EstimatedDuration=ps4.EstimatedDuration(value="30"),
                        ProcessReference=process("Unclipping"),
                        Joints=ps4.Joints(Joint={
                            "J_Lid": ps4.Joint(
                                id_short="J_Lid", display_name={"en": "Lid to housing, four clips"},
                                supplemental_semantic_ids=[f"{MEANS}/SnapFitJoint"],
                                first=reference(("Submodel", i["bill"]), ("Entity", "EntryNode"), ("Entity", "Lid")),
                                second=reference(("Submodel", i["bill"]), ("Entity", "EntryNode"), ("Entity", "ModuleHousing")),
                                JointType=ps4.JointType(value="Clip")),
                        })),

                    # TestCells: after the lid; declares the module's state of health.
                    "Step_0001": ps4.Step(
                        id_short="Step_0001", NodeId=ps4.NodeId(value="TestCells"), Kind=ps4.Kind(value="step"),
                        Name=ps4.StepName(value="Test the cells"), Order=ps4.Order(value="1"),
                        EstimatedDuration=ps4.EstimatedDuration(value="300"),
                        ProcessReference=process("CellTesting"),
                        Outputs=ps4.Outputs(Output={
                            "Output_0000": ps4.Output(
                                id_short="Output_0000", OutputId=ps4.OutputId(value="StateOfHealth"),
                                Name=ps4.OutputName(value="State of health"), DataType=ps4.DataType(value="number"),
                                Unit=ps4.Unit(value="%")),
                        })),

                    # The decision: reuse at 80 % or more, else recycle.
                    "Step_0002": ps4.Step(
                        id_short="Step_0002", NodeId=ps4.NodeId(value="Grade"), Kind=ps4.Kind(value="decision"),
                        Name=ps4.StepName(value="State of health at least 80 %?"), Order=ps4.Order(value="2"),
                        Condition=ps4.Condition(
                            ConditionType=ps4.ConditionType(value="comparison"),
                            Operator=ps4.Operator(value="gte"), Unit=ps4.ConditionUnit(value="%"),
                            Expected=ps4.Expected(DataType=ps4.ExpectedDataType(value="number"), Value=ps4.Value(value="80.0")),
                            Operand=ps4.Operand(OperandType=ps4.OperandType(value="output"), StepId=ps4.StepId(value="TestCells"),
                                                OutputId=ps4.OperandOutputId(value="StateOfHealth"))),
                        Branches=ps4.Branches(Branch={
                            "Branch_0000": ps4.Branch(
                                id_short="Branch_0000", BranchId=ps4.BranchId(value="Reuse"),
                                Name=ps4.BranchName(value="Yes: reuse"), Order=ps4.BranchOrder(value="0"),
                                Steps=ps4.Steps(Step={
                                    "Step_0000": ps4.Step(
                                        id_short="Step_0000", NodeId=ps4.NodeId(value="SortForReuse"),
                                        Kind=ps4.Kind(value="step"), Name=ps4.StepName(value="Sort for reuse"),
                                        Order=ps4.Order(value="0"), ProcessReference=process("SortingForReuse")),
                                })),
                            "Branch_0001": ps4.Branch(
                                id_short="Branch_0001", BranchId=ps4.BranchId(value="Recycle"),
                                Name=ps4.BranchName(value="No: recycle"), Order=ps4.BranchOrder(value="1"),
                                Steps=ps4.Steps(Step={
                                    "Step_0000": ps4.Step(
                                        id_short="Step_0000", NodeId=ps4.NodeId(value="SortForRecycling"),
                                        Kind=ps4.Kind(value="step"), Name=ps4.StepName(value="Sort for recycling"),
                                        Order=ps4.Order(value="0"), ProcessReference=process("SortingForRecycling")),
                                })),
                        })),
                })),
        }))
