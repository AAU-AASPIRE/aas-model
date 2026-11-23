"""
The batch's submodels (D10, D13): what is made, the units it consists of, and the goal every unit is to reach.

A custom (non-IDTA) set of submodels, as the MES writes them::

    BatchInformation          ProductType (the product type AAS), Quantity (how many units)
    BatchUnits
    └── Units                 SML: one reference per unit, its IRI (<batch id>/unit/<n>); a unit has no AAS
    Goal
    ├── Subjects              SML, as a capability's: who the goal is about; a UnitSubject is each unit
    └── Condition             terms, all of which are to hold at the end (an implicit And), as a ConditionSet's

The goal holds for every unit of the batch: a subject that stands for a unit (``UnitSubject``) ranges over the
batch's units, so a planner states it once per unit. Batches are homogeneous: every unit has the same goal. The
goal's values may be the product's (a ValueReference to its required FillVolume), so a batch of another product
type states the same goal with its own values.
"""

from __future__ import annotations

from typing import ClassVar, Dict, List, TypeAlias

from aas_pydantic import Property, ReferenceElement, Submodel, SubmodelElementCollection, SubmodelElementList

from aas_model.constants import (
    BATCH_PRODUCT_TYPE, BATCH_QUANTITY, BATCH_UNIT, BATCH_UNIT_LIST, GOAL_CONDITION, SM_BATCH_INFORMATION,
    SM_BATCH_UNITS, SM_GOAL,
)
from aas_model.submodel_templates.execution import ConditionTerm, Subjects


# ── BatchInformation ─────────────────────────────────────────────────────────

class BatchProductType(ReferenceElement):
    id_short: str = "ProductType"
    semantic_id: str = BATCH_PRODUCT_TYPE
    description: str = "The product type AAS the batch makes units of."

BatchProductType_t: TypeAlias = BatchProductType  # a field may share the class's id_short


class BatchQuantity(Property):
    id_short: str = "Quantity"
    semantic_id: str = BATCH_QUANTITY
    description: str = "How many units the batch is to make."
    value_type: str = "xs:int"

BatchQuantity_t: TypeAlias = BatchQuantity  # a field may share the class's id_short


class BatchInformation(Submodel):
    id_short: str = "BatchInformation"
    semantic_id: str = SM_BATCH_INFORMATION
    description: str = "What the batch makes and how many."
    ProductType: BatchProductType_t = BatchProductType()
    Quantity: BatchQuantity_t = BatchQuantity()


# ── BatchUnits ───────────────────────────────────────────────────────────────

class BatchUnit(ReferenceElement):
    """One unit: its IRI, as an external reference. Effects ground on it and the state store holds its values."""
    semantic_id: str = BATCH_UNIT


class Units(SubmodelElementList):
    id_short: str = "Units"
    semantic_id: str = BATCH_UNIT_LIST
    description: str = "The batch's units, one IRI each, in the order the MES lists them."
    type_value_list_element: str = "ReferenceElement"
    semantic_id_list_element: str = BATCH_UNIT
    item_type: ClassVar = BatchUnit
    value: List[BatchUnit] = []

Units_t: TypeAlias = Units  # a field may share the class's id_short


class BatchUnits(Submodel):
    id_short: str = "BatchUnits"
    semantic_id: str = SM_BATCH_UNITS
    description: str = "The units of the batch, as the MES lists them, appended as units enter the line."
    Units: Units_t = Units()


# ── Goal ─────────────────────────────────────────────────────────────────────

class GoalCondition(SubmodelElementCollection):
    id_short: str = "Condition"
    semantic_id: str = GOAL_CONDITION
    description: str = "What is to hold of every unit at the end: all of its terms."
    term: Dict[str, ConditionTerm] = {}

GoalCondition_t: TypeAlias = GoalCondition  # a field may share the class's id_short
Subjects_t: TypeAlias = Subjects  # the field shares the class's id_short


class Goal(Submodel):
    id_short: str = "Goal"
    semantic_id: str = SM_GOAL
    description: str = "What every unit of the batch is to reach."
    Subjects: Subjects_t = Subjects()
    Condition: GoalCondition_t = GoalCondition()


for _model in (GoalCondition, Goal):
    _model.model_rebuild()
