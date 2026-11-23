"""A batch of 2 mL vials, as the MES would write it: three units, each to be filled with the vial's fill volume
and weighed.

The goal is what the filling line of the example can reach (a shuttle brings a vial to the filling module, which
takes it, fills and weighs it): the vial's further processes (stoppering, capping, inspection) are not yet
modelled with what they need and change, so the goal does not ask for them yet.
"""

from aas_pydantic import ExternalReference, Key, ModelReference

from aas_model.batch_template import Batch
from aas_model.constants import BASE_URL, LAB
from aas_model.product_instances.vial_2ml import AAS_ID as VIAL, REQUIRED_SET
from aas_model.submodel_templates.batch import (
    BatchInformation, BatchProductType, BatchQuantity, BatchUnit, BatchUnits, Goal, GoalCondition, Units,
)
from aas_model.submodel_templates.execution import (
    ConditionOperator, StateCondition, Subjects, TermSubject, TermValue, TermValueReference, UnitSubject,
)

AAS_ID = f"{BASE_URL}/aas/Vial2mLBatch0001AAS"
BATCH_ID = f"{BASE_URL}/batches/Vial2mL-0001"
QUANTITY = 3

GOAL = Key(type_="Submodel", value=f"{AAS_ID}/submodels/Goal")
EACH_UNIT = ModelReference(key=(GOAL, Key(type_="SubmodelElementList", value="Subjects"),
                                Key(type_="ReferenceElement", value="0")))
REQUIRED_FILL_VOLUME = ModelReference(key=(
    *REQUIRED_SET, Key(type_="SubmodelElementCollection", value="Filling"),
    Key(type_="SubmodelElementCollection", value="PropertySet"),
    Key(type_="SubmodelElementCollection", value="FillVolume"), Key(type_="Property", value="Value")))


def vial_2ml_batch() -> Batch:
    return Batch(
        id_short="Vial2mLBatch0001AAS", id=AAS_ID, display_name={"en": "Batch 0001 of 2 mL vials"},
        batch_information=BatchInformation(
            ProductType=BatchProductType(value=ModelReference(key=(
                Key(type_="AssetAdministrationShell", value=VIAL),))),
            Quantity=BatchQuantity(value=str(QUANTITY)),
        ),
        batch_units=BatchUnits(Units=Units(value=[
            BatchUnit(value=ExternalReference(key=(Key(type_="GlobalReference", value=f"{BATCH_ID}/unit/{n}"),)))
            for n in range(1, QUANTITY + 1)
        ])),
        # Every unit filled with the vial's fill volume, and weighed.
        goal=Goal(
            Subjects=Subjects(value=[UnitSubject(display_name={"en": "Each unit"})]),
            Condition=GoalCondition(term={
                "Term_00": StateCondition(
                    display_name={"en": "Filled with the fill volume"},
                    supplemental_semantic_ids=[f"{LAB}ContentVolume"], Subject=TermSubject(value=EACH_UNIT),
                    Operator=ConditionOperator(value="equal"),
                    ValueReference=TermValueReference(value=REQUIRED_FILL_VOLUME)),
                "Term_01": StateCondition(
                    display_name={"en": "Weighed"}, supplemental_semantic_ids=[f"{LAB}Weighed"],
                    Subject=TermSubject(value=EACH_UNIT), Operator=ConditionOperator(value="equal"),
                    Value=TermValue(value="true", value_type="xs:boolean")),
            }),
        ),
    )
