"""AAU filling line instance."""

from aas_model.constants import BASE_URL, CSSX
from aas_pydantic.submodel_templates.hierarchical_structures import EntryNode, Node
from aas_pydantic.submodel_templates.nameplate import ManufacturerProductDesignation
from aas_model.resource_template.modules import LabNameplate
from aas_model.resource_template.resources import CompositeResource
from aas_model.submodel_templates.hierarchical_structures import ResourceHierarchicalStructures


def aau_filling_line() -> CompositeResource:
    identity = "aauFillingLineAAS"
    resource_id = f"{BASE_URL}/aas/{identity}"
    children = (
        "syntegonStopperingSystemAAS", "cytivaCappingSystemAAS",
        "imaDispensingSystemAAS", "imaLoadingSystemAAS",
        "optimaUnloadingSystemAAS", "omronCameraSystemAAS", "planarTableAAS",
    )
    return CompositeResource(
        id_short=identity,
        id=resource_id,
        asset_type=f"{CSSX}#FillingLine",
        nameplate=LabNameplate(
            ManufacturerProductDesignation=ManufacturerProductDesignation(value={"en": "Filling line"})),
        hierarchical_structures=ResourceHierarchicalStructures(
            ArcheType="OneDown",
            EntryNode=EntryNode(
                global_asset_id=resource_id,
                Node={child: Node(global_asset_id=f"{BASE_URL}/aas/{child}") for child in children},
            ),
        ),
    )
