"""AAU filling line instance."""

from aas_model.constants import BASE_URL, SYSTEM_TYPE
from aas_pydantic.submodel_templates.hierarchical_structures import EntryNode, Node
from aas_model.resource_template.modules import lab_nameplate
from aas_model.resource_template.resources import CompositeResource
from aas_model.submodel_templates.hierarchical_structures import ResourceHierarchicalStructures


def aau_filling_line() -> CompositeResource:
    identity = "aauFillingLineAAS"
    resource_id = f"{BASE_URL}/aas/{identity}"
    children = (
        "StopperingStationAAS", "CappingStationAAS",
        "DispensingStationAAS", "LoadingStationAAS",
        "UnloadingStationAAS", "InspectionStationAAS", "planarTableAAS",
    )
    return CompositeResource(
        id_short=identity,
        id=resource_id,
        asset_type=f"{SYSTEM_TYPE}/FillingLine",
        nameplate=lab_nameplate("The AP2030 filling line"),
        hierarchical_structures=ResourceHierarchicalStructures(
            ArcheType="OneDown",
            EntryNode=EntryNode(
                global_asset_id=resource_id,
                Node={child: Node(global_asset_id=f"{BASE_URL}/aas/{child}") for child in children},
            ),
        ),
    )
