"""The batch AAS: one batch of a product type, its units and the goal every unit is to reach."""

from __future__ import annotations

from typing import ClassVar, Optional

from aas_pydantic import AAS

from aas_model.constants import BATCH_ASSET_TYPE
from aas_model.submodel_templates.batch import BatchInformation, BatchUnits, Goal


class Batch(AAS):
    """AAS of one batch, as the MES writes it: what it makes (the product type AAS), how many, its units (IRIs, no
    AAS of their own) and the goal. The planner reads its goal and its units from it (D13); nothing else has to be
    generated for the planner to work."""
    model_config = {"extra": "forbid"}
    ASSET_KIND: ClassVar[str] = "Instance"
    asset_type: str = BATCH_ASSET_TYPE
    batch_information: BatchInformation = BatchInformation()
    batch_units: BatchUnits = BatchUnits()
    goal: Optional[Goal] = None


Batch.model_rebuild()
