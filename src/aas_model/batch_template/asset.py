"""The batch AAS: one batch of a product type, how many units it makes, and the goal every unit is to reach."""

from __future__ import annotations

from typing import ClassVar, Optional

from aas_pydantic import AAS

from aas_model.constants import BATCH_ASSET_TYPE
from aas_model.submodel_templates.batch import BatchInformation, Goal


class Batch(AAS):
    """AAS of one batch, as the MES writes it: what it makes (the product type AAS), how many, and the goal. Units
    are listed nowhere in the AAS: each BT instance mints the IRI of the one unit it makes and admits it (D10, D35).
    The planner reads the goal from it (D13); nothing else has to be generated for the planner to work."""
    model_config = {"extra": "forbid"}
    ASSET_KIND: ClassVar[str] = "Instance"
    asset_type: str = BATCH_ASSET_TYPE
    batch_information: BatchInformation = BatchInformation()
    goal: Optional[Goal] = None


Batch.model_rebuild()
