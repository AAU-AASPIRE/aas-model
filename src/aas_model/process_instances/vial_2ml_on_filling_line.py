"""The 2 mL vial on the filling line, for the Production Sequence 4.0 (``vial_2ml.py``): the
reference process AAS of iec61499-mgmt-py (``cell/examples/processes/vial_2ml_on_filling_line.py``),
bound to the vial's extended bill of processes.

    Filling      -> FillingModule.Dispensing     Volume <- Filling.FillVolume (2 mL)
    Stoppering   -> StopperingModule.Stoppering
    Capping      -> CappingModule.Capping
    Unload, RejectTop, RejectSide   manual (no unloading station on the line)
    CheckWeight, InspectTop, InspectSide   not bound

The line offers four module skills (Dispensing, Stoppering, Capping, Inspection). It weighs inside
Dispensing and takes both images inside Inspection; no module offers weighing, or one camera's
inspection, as a skill of its own. So the plan does not fit, and Validation says why: the product asks
for more than the line offers. A line whose modules offer those skills, or these modules reconfigured,
would bind them.
"""
from __future__ import annotations

from aas_model.constants import BASE_URL
from aas_model.process_template import Process
from aas_model.product_template import sequence_id
from aas_model.submodel_templates.process import bindings as b, process_information as pi, validation as v
from aas_pydantic import Key, ModelReference

AAS_ID = f"{BASE_URL}/aas/Vial2mLOnFillingLineAAS"
ASSET_ID = f"{BASE_URL}/assets/Vial2mLOnFillingLine"
PRODUCT = f"{BASE_URL}/aas/Vial2mLAAS"
LINE = f"{BASE_URL}/aas/FillingLineAAS"
RECIPE = sequence_id(PRODUCT, "Assembly")       # the product's Production Sequence, archetype Assembly
PROCESSES = f"{PRODUCT}/submodels/ProcessParameters"
FILLING = f"{BASE_URL}/aas/FillingModuleAAS"
STOPPERING = f"{BASE_URL}/aas/StopperingModuleAAS"
CAPPING = f"{BASE_URL}/aas/CappingModuleAAS"
INSPECTION = f"{BASE_URL}/aas/InspectionModuleAAS"


def reference(*keys: tuple[str, str]) -> ModelReference:
    """A model reference along ``keys``: (type, value) pairs."""
    return ModelReference(key=tuple(Key(type_=kind, value=value) for kind, value in keys))


def vial_2ml_on_filling_line() -> Process:
    return Process(
        id_short="Vial2mLOnFillingLineAAS", id=AAS_ID,
        description="The process of the 2 mL vial on the filling line: its recipe bound to the line's modules",
        display_name={"en": "Vial 2 mL on the filling line"},
        specific_asset_ids={"product": f"{BASE_URL}/assets/Vial2mL", "line": f"{BASE_URL}/assets/FillingLine"},

        # ── Process Information: what is bound, and how far ─────────────────────────────────────
        process_information=pi.ProcessInformation(
            id_short="ProcessInformation",
            Product=pi.Product(value=reference(("AssetAdministrationShell", PRODUCT))),
            Line=pi.Line(value=reference(("AssetAdministrationShell", LINE))),
            Recipe=pi.Recipe(value=reference(("Submodel", RECIPE))),
            RecipeRevision=pi.RecipeRevision(value="2"),
            Status=pi.Status(value="Draft"),
        ),

        # ── Bindings: per step of the recipe, the module, its skill and its inputs ──────────────
        bindings=b.ProcessBindings(
            id_short="Bindings",
            StepBinding={
                "Filling": b.ProcessStepBinding(
                    id_short="Filling",
                    NodeId=b.NodeId(value="Filling"),
                    Step=b.BoundStep(value=reference(
                        ("Submodel", RECIPE), ("SubmodelElementCollection", "Steps"), ("SubmodelElementCollection", "Step_0000"),
                        ("SubmodelElementCollection", "Steps"), ("SubmodelElementCollection", "Step_0000"))),
                    Resource=b.Resource(value=reference(("AssetAdministrationShell", FILLING))),
                    Skill=b.BoundSkill(value=reference(
                        ("Submodel", f"{FILLING}/submodels/Skills"), ("SubmodelElementCollection", "Dispensing"))),
                    ExecutionMode=b.ExecutionMode(value="station"),
                    Bindings=b.InputBindings(Binding={
                        # Dispensing's Volume is the vial's fill volume.
                        "Binding_0000": b.InputBinding(
                            id_short="Binding_0000",
                            Name=b.Name(value="Volume"),
                            SourceElement=b.SourceElement(value=reference(
                                ("Submodel", PROCESSES), ("SubmodelElementCollection", "Processes"),
                                ("SubmodelElementCollection", "Filling"),
                                ("SubmodelElementCollection", "ProductParameters"), ("Property", "FillVolume"))),
                            InputReference=b.InputReference(value=reference(
                                ("Submodel", f"{FILLING}/submodels/Skills"), ("SubmodelElementCollection", "Dispensing"),
                                ("SubmodelElementCollection", "Start"), ("Operation", "Start"), ("Property", "Volume"))),
                        ),
                    }),
                ),
                "Stoppering": b.ProcessStepBinding(
                    id_short="Stoppering",
                    NodeId=b.NodeId(value="Stoppering"),
                    Step=b.BoundStep(value=reference(
                        ("Submodel", RECIPE), ("SubmodelElementCollection", "Steps"), ("SubmodelElementCollection", "Step_0000"),
                        ("SubmodelElementCollection", "Steps"), ("SubmodelElementCollection", "Step_0002"))),
                    Resource=b.Resource(value=reference(("AssetAdministrationShell", STOPPERING))),
                    Skill=b.BoundSkill(value=reference(
                        ("Submodel", f"{STOPPERING}/submodels/Skills"), ("SubmodelElementCollection", "Stoppering"))),
                    ExecutionMode=b.ExecutionMode(value="station"),
                ),
                "Capping": b.ProcessStepBinding(
                    id_short="Capping",
                    NodeId=b.NodeId(value="Capping"),
                    Step=b.BoundStep(value=reference(
                        ("Submodel", RECIPE), ("SubmodelElementCollection", "Steps"), ("SubmodelElementCollection", "Step_0000"),
                        ("SubmodelElementCollection", "Steps"), ("SubmodelElementCollection", "Step_0003"))),
                    Resource=b.Resource(value=reference(("AssetAdministrationShell", CAPPING))),
                    Skill=b.BoundSkill(value=reference(
                        ("Submodel", f"{CAPPING}/submodels/Skills"), ("SubmodelElementCollection", "Capping"))),
                    ExecutionMode=b.ExecutionMode(value="station"),
                ),
                # The release, by hand: the line has no unloading station.
                "Unload": b.ProcessStepBinding(
                    id_short="Unload",
                    NodeId=b.NodeId(value="Unload"),
                    Step=b.BoundStep(value=reference(("Submodel", RECIPE), ("SubmodelElementCollection", "Steps"), ("SubmodelElementCollection", "Step_0000"), ("SubmodelElementCollection", "Steps"), ("SubmodelElementCollection", "Step_0006"), ("SubmodelElementCollection", "Branches"), ("SubmodelElementCollection", "Branch_0000"), ("SubmodelElementCollection", "Steps"), ("SubmodelElementCollection", "Step_0000"), ("SubmodelElementCollection", "Branches"), ("SubmodelElementCollection", "Branch_0000"), ("SubmodelElementCollection", "Steps"), ("SubmodelElementCollection", "Step_0000"))),
                    ExecutionMode=b.ExecutionMode(value="manual"),
                ),
                "RejectSide": b.ProcessStepBinding(
                    id_short="RejectSide",
                    NodeId=b.NodeId(value="RejectSide"),
                    Step=b.BoundStep(value=reference(("Submodel", RECIPE), ("SubmodelElementCollection", "Steps"), ("SubmodelElementCollection", "Step_0000"), ("SubmodelElementCollection", "Steps"), ("SubmodelElementCollection", "Step_0006"), ("SubmodelElementCollection", "Branches"), ("SubmodelElementCollection", "Branch_0000"), ("SubmodelElementCollection", "Steps"), ("SubmodelElementCollection", "Step_0000"), ("SubmodelElementCollection", "Branches"), ("SubmodelElementCollection", "Branch_0001"), ("SubmodelElementCollection", "Steps"), ("SubmodelElementCollection", "Step_0000"))),
                    ExecutionMode=b.ExecutionMode(value="manual"),
                ),
                "RejectTop": b.ProcessStepBinding(
                    id_short="RejectTop",
                    NodeId=b.NodeId(value="RejectTop"),
                    Step=b.BoundStep(value=reference(("Submodel", RECIPE), ("SubmodelElementCollection", "Steps"), ("SubmodelElementCollection", "Step_0000"), ("SubmodelElementCollection", "Steps"), ("SubmodelElementCollection", "Step_0006"), ("SubmodelElementCollection", "Branches"), ("SubmodelElementCollection", "Branch_0001"), ("SubmodelElementCollection", "Steps"), ("SubmodelElementCollection", "Step_0000"))),
                    ExecutionMode=b.ExecutionMode(value="manual"),
                ),
            },
        ),

        # ── Validation: the plan check's result ──────────────────────────────────────────────────
        validation=v.Validation(
            id_short="Validation",
            Result=v.Result(value="DoesNotFit"),
            CheckedBy=v.CheckedBy(value="by hand, against the line's module skills (26 Nov 2026)"),
            Findings=v.Findings(value=[
                v.FindingsItem(value="CheckWeight: no module offers Weighing as a skill; the FillingModule weighs inside Dispensing"),
                v.FindingsItem(value="InspectTop: no module offers one camera's inspection; the InspectionModule takes both images inside Inspection"),
                v.FindingsItem(value="InspectSide: as InspectTop"),
            ]),
        ),
    )
