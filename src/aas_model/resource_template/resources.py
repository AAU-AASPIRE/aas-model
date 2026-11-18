"""The lab's resource types: one AAS class per kind of resource, each with the submodels that apply to it.

``Resource`` declares the typed submodels without claiming a location, interface, skill or observation. Its
subtypes add what holds for their kind: a physical resource has a Location parameter, a station speaks the
PackML contract over its protocol (``operational``) and declares its capabilities (``capability_description``):
what each means (the lab vocabulary, as a supplemental semantic id) and, where its type alone says it, what it
needs and changes (``Execution``). An
instance (``aas_model.resource_instances``) binds its own skills and observations. A full JSON export restores
through ``Resource.model_validate_json()``.
"""

from __future__ import annotations

from typing import Optional

from aas_pydantic import AAS, Capability
from aas_pydantic.submodel_templates.hierarchical_structures import HierarchicalStructures
from aas_pydantic.submodel_templates.nameplate import (
    AddressInformation, AddressInformation_t, CityTown, ManufacturerName, ManufacturerProductDesignation, Nameplate,
    NationalCode, OrderCodeOfManufacturer, Street, URIOfTheProduct, Zipcode,
)

from aas_model.constants import BASE_URL, CSSX, LAB
from aas_model.submodel_templates import Aimc, AimcMappingConfigurations
from aas_model.submodel_templates.capability_description import (
    ModuleCapabilityContainer, ModuleCapabilityDescription, ModuleCapabilitySet,
)
from aas_model.submodel_templates.execution import (
    ConditionOperator, EffectOperator, EndTerms, Execution, ExecutionConditions, ExecutionEffects, ExecutionSubject,
    PreTerms, StateCondition, StateEffect, SubjectRole, Subjects, TermSubject, TermValue,
)
from aas_model.submodel_templates.state_declaration import StateDeclaration
from aas_model.submodel_templates.aid import DmpAssetInterfacesDescription
from aas_model.submodel_templates.control_component_instance import ResourceControlComponentInstance
from aas_model.submodel_templates.hierarchical_structures import ResourceHierarchicalStructures
from aas_model.submodel_templates.parameters import Position, ResourceParameters
from aas_model.submodel_templates.variables import Variables
from aas_model.resource_template.operational import (
    MqttInterfaces, OperationalCapabilityDescription, OperationalMqttControlComponent, OperationalMqttInterfaces,
    OperationalMqttMappings, OperationalOpcuaControlComponent, OperationalOpcuaInterfaces, OperationalOpcuaMappings,
    OperationalVariables,
)
from aas_model.resource_template.references import execution_subject_ref


# ── Nameplate ────────────────────────────────────────────────────────────────────────────────────────────────────────

class ResourceNameplate(Nameplate):
    """A resource's Nameplate: the lab's address unless the instance names its manufacturer's."""
    AddressInformation: AddressInformation_t = AddressInformation(
        Street=Street(value={"en": "Fibigerstr\u00e6de 14"}),
        Zipcode=Zipcode(value={"en": "9220"}),
        CityTown=CityTown(value={"en": "Aalborg \u00d8st"}),
        NationalCode=NationalCode(value={"en": "DK"}),
    )


# ── Resource ─────────────────────────────────────────────────────────────────────────────────────────────────────────

class Resource(AAS):
    """Python-authored Resource AAS with shared, independently owned defaults.

    Pass typed submodels to the constructor. Ids, identity macros and the
    skills' invocation addresses are resolved when the AAS is built.
    Standard Pydantic JSON serialization preserves the complete authored
    structure; restoring it does not deep-merge additional resource defaults.
    Use ``aas_model.build_from_model(resource)`` to produce a BaSyx store.

    Resource supplies typed submodels, but does not claim any protocol,
    station skills, telemetry or physical location. Those are inherited by
    the resource types for which they actually apply.
    """

    model_config = {"extra": "forbid"}
    derived_from: str = f"{BASE_URL}/aas/templates/resource"

    # ── Nameplate ─────────────────────────────────────────────────────────
    nameplate: Nameplate = ResourceNameplate(
        id_short="Nameplate",
        URIOfTheProduct=URIOfTheProduct(value="https://smartproductionlab.aau.dk/product/1"),
        ManufacturerName=ManufacturerName(value={"en": "Not specified"}),
        ManufacturerProductDesignation=ManufacturerProductDesignation(value={"en": "Resource"}),
        OrderCodeOfManufacturer=OrderCodeOfManufacturer(value=""),
    )

    # ── Asset Interfaces Description ──────────────────────────────────────
    asset_interfaces_description: DmpAssetInterfacesDescription = DmpAssetInterfacesDescription(
        id_short="AssetInterfacesDescription",
    )

    # ── Control Component Instance ────────────────────────────────────────
    control_component_instance: ResourceControlComponentInstance = ResourceControlComponentInstance(
        id_short="ControlComponentInstance",
    )

    # ── Capability Description (included unless explicitly omitted) ──────────
    capability_description: Optional[ModuleCapabilityDescription] = ModuleCapabilityDescription(
        id_short="CapabilityDescription",
    )

    # ── Variables ─────────────────────────────────────────────────────────
    variables: Variables = Variables(id_short="Variables")

    # ── Parameters ────────────────────────────────────────────────────────
    parameters: ResourceParameters = ResourceParameters(
        id_short="Parameters", parameter={},
    )
    # ── Asset Interfaces Mapping Configuration ──────────────────────────────
    asset_interfaces_mapping_configuration: Aimc = Aimc(
        id_short="AssetInterfacesMappingConfiguration",
        MappingConfigurations=AimcMappingConfigurations(value=[]),
    )
    # ── Optional submodels (no defaults — stations opt in) ────────────────
    hierarchical_structures: Optional[ResourceHierarchicalStructures] = None
    # The state of this resource that effects change and no data point reports.
    state_declaration: Optional[StateDeclaration] = None


# Existing registration-service consumers import this name.
ResourceTypeAAS = Resource


# ── Physical resources ───────────────────────────────────────────────────────────────────────────────────────────────

class PhysicalResource(Resource):
    parameters: ResourceParameters = ResourceParameters(id_short="Parameters")


class OperationalResource(PhysicalResource):
    """Operational physical asset, without an assumed native protocol."""


# ── Stations ─────────────────────────────────────────────────────────────────────────────────────────────────────────

class Station(OperationalResource):
    """Physical workstation, independent of the native interface protocol."""

    asset_type: str = f"{CSSX}#Station"


class MqttOperationalStation(Station):
    """Station with the shared PackML contract over MQTT."""

    asset_interfaces_description: DmpAssetInterfacesDescription = OperationalMqttInterfaces(
        id_short="AssetInterfacesDescription",
    )
    control_component_instance: ResourceControlComponentInstance = OperationalMqttControlComponent(
        id_short="ControlComponentInstance",
    )
    asset_interfaces_mapping_configuration: Aimc = OperationalMqttMappings(
        id_short="AssetInterfacesMappingConfiguration",
    )
    variables: Variables = OperationalVariables()


class OpcuaOperationalStation(Station):
    """Station with the shared PackML contract over OPC UA."""

    asset_interfaces_description: DmpAssetInterfacesDescription = OperationalOpcuaInterfaces(
        id_short="AssetInterfacesDescription",
    )
    control_component_instance: ResourceControlComponentInstance = OperationalOpcuaControlComponent(
        id_short="ControlComponentInstance",
    )
    asset_interfaces_mapping_configuration: Aimc = OperationalOpcuaMappings(
        id_short="AssetInterfacesMappingConfiguration",
    )
    variables: Variables = OperationalVariables()


class ProcessingStation(Station):
    """A station that changes a product; concrete stations declare their skills."""

    asset_type: str = f"{CSSX}#ProcessingStation"


class HandlingStation(Station):
    """A station that loads, unloads, or otherwise handles a product."""

    asset_type: str = f"{CSSX}#HandlingStation"


class StopperingStation(ProcessingStation):
    asset_type: str = f"{CSSX}#StopperingSystem"
    capability_description: ModuleCapabilityDescription = OperationalCapabilityDescription(
        id_short="CapabilityDescription",
        CapabilitySet={
            "Processing": ModuleCapabilitySet(CapabilityContainer={
                "Stoppering": ModuleCapabilityContainer(Capability=Capability(
                    semantic_id=f"{CSSX}#Stoppering", supplemental_semantic_ids=[f"{LAB}Stoppering"],
                )),
            }),
        },
    )


class CappingStation(ProcessingStation):
    asset_type: str = f"{CSSX}#CappingSystem"
    capability_description: ModuleCapabilityDescription = OperationalCapabilityDescription(
        id_short="CapabilityDescription",
        CapabilitySet={
            "Processing": ModuleCapabilitySet(CapabilityContainer={
                "Capping": ModuleCapabilityContainer(Capability=Capability(
                    semantic_id=f"{CSSX}#Capping", supplemental_semantic_ids=[f"{LAB}Capping"],
                )),
            }),
        },
    )


class DispensingStation(ProcessingStation):
    """Fills a unit (the lab's Filling): it needs the unit empty and leaves the volume it was given in it. Which
    Operation variables carry the unit and the volume is the instance's (the Subject's Binding, the End effect)."""
    asset_type: str = f"{CSSX}#DispensingSystem"
    capability_description: ModuleCapabilityDescription = OperationalCapabilityDescription(
        id_short="CapabilityDescription",
        CapabilitySet={
            "Processing": ModuleCapabilitySet(CapabilityContainer={
                "Dispensing": ModuleCapabilityContainer(
                    Capability=Capability(
                        semantic_id=f"{CSSX}#Dispensing", supplemental_semantic_ids=[f"{LAB}Filling"],
                    ),
                    Execution=Execution(
                        Subjects=Subjects(subject={
                            "Self": ExecutionSubject(Role=SubjectRole(value="Self")),
                            "Unit": ExecutionSubject(Role=SubjectRole(value="Product")),
                        }),
                        Conditions=ExecutionConditions(Pre=PreTerms(term={
                            "Term_00": StateCondition(
                                supplemental_semantic_ids=[f"{LAB}ContentVolume"],
                                Subject=TermSubject(value=execution_subject_ref("Processing", "Dispensing", "Unit")),
                                Operator=ConditionOperator(value="equal"),
                                Value=TermValue(value="0.0", value_type="xs:double"),
                            ),
                        })),
                    ),
                ),
            }),
        },
    )


class LoadingStation(HandlingStation):
    asset_type: str = f"{CSSX}#LoadingSystem"
    capability_description: ModuleCapabilityDescription = OperationalCapabilityDescription(
        id_short="CapabilityDescription",
        CapabilitySet={
            "Handling": ModuleCapabilitySet(CapabilityContainer={
                "Loading": ModuleCapabilityContainer(Capability=Capability(
                    semantic_id=f"{CSSX}#Loading", supplemental_semantic_ids=[f"{LAB}Loading"],
                )),
            }),
        },
    )


class UnloadingStation(HandlingStation):
    asset_type: str = f"{CSSX}#UnloadingSystem"
    # Scrap has no meaning in the lab vocabulary yet.
    capability_description: ModuleCapabilityDescription = OperationalCapabilityDescription(
        id_short="CapabilityDescription",
        CapabilitySet={
            "Handling": ModuleCapabilitySet(CapabilityContainer={
                "Unloading": ModuleCapabilityContainer(Capability=Capability(
                    semantic_id=f"{CSSX}#Unloading", supplemental_semantic_ids=[f"{LAB}Unloading"],
                )),
                "Scrap": ModuleCapabilityContainer(Capability=Capability(semantic_id=f"{CSSX}#Scrap")),
            }),
        },
    )


class InspectionStation(Station):
    asset_type: str = f"{CSSX}#QualityControlSystem"
    capability_description: ModuleCapabilityDescription = OperationalCapabilityDescription(
        id_short="CapabilityDescription",
        CapabilitySet={
            "Inspection": ModuleCapabilitySet(CapabilityContainer={
                "Capture": ModuleCapabilityContainer(Capability=Capability(
                    semantic_id=f"{CSSX}#Capture", supplemental_semantic_ids=[f"{LAB}Inspection"],
                )),
            }),
        },
    )


# ── Transport ────────────────────────────────────────────────────────────────────────────────────────────────────────

class TransportResource(PhysicalResource):
    """Protocol-neutral physical transport resource."""
    asset_type: str = f"{CSSX}#TransportSystem"


class Shuttle(TransportResource):
    """Protocol-neutral shuttle; payload and product tracking are specialized."""
    asset_type: str = f"{CSSX}#Shuttle"


class PlanarShuttle(Shuttle):
    """A planar shuttle with the shared PackML contract over MQTT; the instance binds MoveToPosition.

    Native Position arrays and operation X/Y/Theta use millimetres and radians.
    """
    asset_type: str = f"{CSSX}#PlanarTableShuttle"
    parameters: ResourceParameters = ResourceParameters(
        id_short="Parameters",
        parameter={"Location": Position()},
    )
    asset_interfaces_description: DmpAssetInterfacesDescription = OperationalMqttInterfaces(
        id_short="AssetInterfacesDescription",
    )
    control_component_instance: ResourceControlComponentInstance = OperationalMqttControlComponent(
        id_short="ControlComponentInstance",
    )
    # A move takes the shuttle and the unit it carries; where it ends is known once its position is reported
    # again: the move is given a pose, not a place, so its position is measured, not assigned.
    capability_description: ModuleCapabilityDescription = OperationalCapabilityDescription(
        id_short="CapabilityDescription",
        CapabilitySet={
            "Transport": ModuleCapabilitySet(CapabilityContainer={
                "MoveToPosition": ModuleCapabilityContainer(
                    Capability=Capability(
                        semantic_id=f"{CSSX}#MoveToPosition", supplemental_semantic_ids=[f"{LAB}Transporting"],
                    ),
                    Execution=Execution(
                        Subjects=Subjects(subject={
                            "Self": ExecutionSubject(Role=SubjectRole(value="Self")),
                            "Unit": ExecutionSubject(Role=SubjectRole(value="Product")),
                        }),
                        Effects=ExecutionEffects(End=EndTerms(term={
                            "Term_00": StateEffect(
                                supplemental_semantic_ids=[f"{LAB}Position"],
                                Subject=TermSubject(value=execution_subject_ref("Transport", "MoveToPosition", "Self")),
                                Operator=EffectOperator(value="measured"),
                            ),
                        })),
                    ),
                ),
            }),
        },
    )
    asset_interfaces_mapping_configuration: Aimc = OperationalMqttMappings(
        id_short="AssetInterfacesMappingConfiguration",
    )
    variables: Variables = OperationalVariables()


# ── Software ─────────────────────────────────────────────────────────────────────────────────────────────────────────

class SoftwareResource(Resource):
    asset_type: str = f"{CSSX}#SoftwareResource"


class MqttSoftwareResource(SoftwareResource):
    """Software exposes MQTT without inheriting station-specific skills."""

    asset_interfaces_description: DmpAssetInterfacesDescription = MqttInterfaces(
        id_short="AssetInterfacesDescription",
    )


# ── Systems ──────────────────────────────────────────────────────────────────────────────────────────────────────────

class CompositeResource(Resource):
    """A composed resource explicitly declares its members in IDTA hierarchy."""

    asset_type: str = f"{CSSX}#CompositeResource"
    hierarchical_structures: HierarchicalStructures
