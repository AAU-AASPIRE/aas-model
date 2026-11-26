"""
The batch's submodels (D10, D13, D35): what is made, how many, and the goal every unit is to reach.

A custom (non-IDTA) set of submodels, as the MES writes them::

    BatchInformation          ProductType (the product type AAS), Quantity (how many units)
    Goal
    ├── Subjects              SML, as a capability's: who the goal is about; a UnitSubject is the unit
    └── Condition             terms, all of which are to hold at the end (an implicit And), as a ConditionSet's

Units are not listed: products are modelled at batch level only. A behaviour tree describes the flow of one unit
(D31); each of its instances mints the IRI of the unit it makes (``urn:uuid:<uuid>``, so that the uuid alone, which
the stations queue, names it) and admits it (D35): it writes the unit's initial state and its batch, until Quantity
units are admitted. The goal is stated once and holds for every unit: a subject
that stands for a unit (``UnitSubject``) is the one unit an instance makes. Batches are homogeneous. The goal's
values may be the product's (a ValueReference to its required FillVolume), so a batch of another product type
states the same goal with its own values.
"""

from __future__ import annotations

from typing import Dict, TypeAlias

from aas_pydantic import Property, ReferenceElement, Submodel, SubmodelElementCollection

from aas_model.constants import (
    BATCH_PRODUCT_TYPE, BATCH_QUANTITY, GOAL_CONDITION, SM_BATCH_INFORMATION, SM_GOAL,
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
