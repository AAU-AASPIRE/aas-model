"""The lab's resource types: one AAS class per kind of resource, each with the submodels that apply to it.

``Resource`` declares the typed submodels without claiming a location, interface, skill or observation. Its
subtypes add what holds for their kind: a physical resource has a Location parameter, a station speaks the
PackML contract over its protocol (``operational``) and declares its capabilities (``capability_description``):
what each means (the lab vocabulary, as a supplemental semantic id) and, where its type alone says it, what it
needs and changes (its Subjects, ConditionSet and EffectSet). An
instance (``aas_model.resource_instances``) binds its own skills and observations. A full JSON export restores
through ``Resource.model_validate_json()``.
"""

from __future__ import annotations

from typing import Dict, Optional

from aas_pydantic import AAS, Capability
from pydantic import model_validator
from aas_pydantic.submodel_templates.hierarchical_structures import HierarchicalStructures
from aas_pydantic.submodel_templates.nameplate import (
    AddressInformation, AddressInformation_t, CityTown, ManufacturerName, ManufacturerProductDesignation, Nameplate,
    NationalCode, OrderCodeOfManufacturer, Street, URIOfTheProduct, Zipcode,
)

from aas_model.constants import BASE_URL, CSSX, LAB, SHUTTLE_ASSET_TYPE
from aas_model.submodel_templates import Aimc, AimcMappingConfigurations
from aas_model.submodel_templates.capability_description import (
    ModuleCapabilityContainer, ModuleCapabilityDescription, ModuleCapabilityRelations, ModuleCapabilitySet,
)
from aas_model.submodel_templates.execution import (
    ConditionOperator, ConditionSet, EffectOperator, EffectSet, EndTerms, ExecutionDuration, PlaceSubject, PreTerms,
    RequirementSubject, SelfSubject,
    StateCondition, StateEffect, Subjects, TermSubject, TermValue, TermValueReference, Translation, UnitSubject,
)
from aas_model.submodel_templates.knowledge import Knowledge, StateVariable
from aas_model.resource_template.translations import COMMAND_STATE_REPLY, LAB_PREFIX, UNIT_UUID
from aas_model.submodel_templates.aid import DmpAssetInterfacesDescription
from aas_model.submodel_templates.skills import ModuleSkills
from aas_model.submodel_templates.hierarchical_structures import ResourceHierarchicalStructures
from aas_model.submodel_templates.parameters import Position, ResourceParameters
from aas_model.submodel_templates.variables import Variables
from aas_model.resource_template.operational import (
    MqttInterfaces, OperationalCapabilityDescription, OperationalMqttInterfaces, OperationalMqttMappings,
    OperationalMqttSkills, OperationalOpcuaInterfaces, OperationalOpcuaMappings, OperationalOpcuaSkills,
    OperationalVariables,
)
from aas_model.resource_template.references import subject_ref


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

    # ── Skills (ARSO): each skill's commands, the action that carries each out, its Operation ───────
    skills: Optional[ModuleSkills] = ModuleSkills(id_short="Skills")

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

    @classmethod
    def knowledge(cls) -> Dict[str, StateVariable]:
        """The state variables a resource of this type declares in its Variables/Knowledge: none unless its type says."""
        return {}

    # The Knowledge is added unless authored, not a class default, as a station's series are (``OperationalVariables``):
    # the resource restored from JSON holds what was authored.
    @model_validator(mode="after")
    def _declares_what_is_known_of_it(self):
        variables = getattr(self, "variables", None)
        if variables is not None and variables.Knowledge is None and (declared := self.knowledge()):
            variables.Knowledge = Knowledge(variable=declared)
        return self


# Existing registration-service consumers import this name.
ResourceTypeAAS = Resource


# ── Physical resources ───────────────────────────────────────────────────────────────────────────────────────────────

class PhysicalResource(Resource):
    parameters: ResourceParameters = ResourceParameters(id_short="Parameters")


def occupied_by() -> StateVariable:
    """Who an operational device serves: the head of its process queue. Observed: the station-state mapping sinks
    it into Variables/Knowledge/OccupiedBy (D36)."""
    return StateVariable.own(f"{LAB}OccupiedBy")


class OperationalResource(PhysicalResource):
    """Operational physical asset, without an assumed native protocol. Every one has module control (Occupy,
    Release) and reports its process queue, so its Knowledge declares who it serves: the unit at the head of the
    queue."""

    @classmethod
    def knowledge(cls) -> Dict[str, StateVariable]:
        return {"OccupiedBy": occupied_by()}


# ── Stations ─────────────────────────────────────────────────────────────────────────────────────────────────────────

class Station(OperationalResource):
    """Physical workstation, independent of the native interface protocol."""

    asset_type: str = f"{CSSX}#Station"


class MqttOperationalStation(Station):
    """Station with the shared PackML contract over MQTT."""

    asset_interfaces_description: DmpAssetInterfacesDescription = OperationalMqttInterfaces(
        id_short="AssetInterfacesDescription",
    )
    skills: Optional[ModuleSkills] = OperationalMqttSkills(id_short="Skills")
    asset_interfaces_mapping_configuration: Aimc = OperationalMqttMappings(
        id_short="AssetInterfacesMappingConfiguration",
    )
    variables: Variables = OperationalVariables()


class OpcuaOperationalStation(Station):
    """Station with the shared PackML contract over OPC UA."""

    asset_interfaces_description: DmpAssetInterfacesDescription = OperationalOpcuaInterfaces(
        id_short="AssetInterfacesDescription",
    )
    skills: Optional[ModuleSkills] = OperationalOpcuaSkills(id_short="Skills")
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
    """Fills a unit (the lab's Filling): it needs the unit empty. What the unit ends holding, and how a call is built
    (the Translation), is the instance's, whose Operation it is; the volume is what the unit's product requires."""
    asset_type: str = f"{CSSX}#DispensingSystem"
    capability_description: ModuleCapabilityDescription = OperationalCapabilityDescription(
        id_short="CapabilityDescription",
        CapabilitySet={
            "Processing": ModuleCapabilitySet(CapabilityContainer={
                "Dispensing": ModuleCapabilityContainer(
                    Capability=Capability(
                        semantic_id=f"{CSSX}#Dispensing", supplemental_semantic_ids=[f"{LAB}Filling"],
                    ),
                    CapabilityRelations=ModuleCapabilityRelations(
                        Subjects=Subjects(value=[
                            SelfSubject(display_name={"en": "This station"}),
                            UnitSubject(display_name={"en": "Unit being filled"}),
                            RequirementSubject.of(f"{LAB}FillVolume", display_name={"en": "Required fill volume"}),
                        ]),
                        ConditionSet=ConditionSet(Pre=PreTerms(term={"Term_00": StateCondition(
                            display_name={"en": "Unit empty"}, supplemental_semantic_ids=[f"{LAB}ContentVolume"],
                            Subject=TermSubject(value=subject_ref("Processing", "Dispensing", 1)),
                            Operator=ConditionOperator(value="equal"),
                            Value=TermValue(value="0.0", value_type="xs:double"),
                        )})),
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
    asset_type: str = SHUTTLE_ASSET_TYPE


# MoveToPosition's call: the place's pose in the line's frame (its projected AbsoluteX/Y), on behalf of the unit the
# shuttle serves (the head of its queue, whose uuid every command it runs for the unit carries). The table's frame is
# the line's; the heading stays 0 until places state one.
MOVE_TO_PLACE_CALL = LAB_PREFIX + UNIT_UUID + """function call(subjects, properties)
  local shuttle, place = subjects[1], subjects[2]
  local unit = shuttle.state[LAB .. "OccupiedBy"]
  if unit == nil then error("the shuttle serves no unit") end
  return {
    Uuid = unit_uuid({ id = unit }), ProductID = unit,
    X = place.state[LAB .. "AbsoluteX"], Y = place.state[LAB .. "AbsoluteY"], Theta = 0.0,
  }
end
"""


class PlanarShuttle(Shuttle):
    """A planar shuttle with the shared PackML contract over MQTT; the instance binds MoveToPosition.

    Native Position arrays and operation X/Y/Theta use millimetres and radians.
    """
    asset_type: str = f"{CSSX}#PlanarTableShuttle"
    # Who the shuttle serves (the head of its process queue), and where it is: its reported position, sunk into the
    # state store by the mapping that writes its Location series (observed, mm in the table's frame), and the
    # place that position is at (Location: derived by query from the places' projected positions, never stored; D36).
    # A move's effect on Location is not written; the behaviour tree waits until the reported position confirms it.
    @classmethod
    def knowledge(cls) -> Dict[str, StateVariable]:
        return {
            "OccupiedBy": occupied_by(),
            "Location": StateVariable.own(f"{LAB}Location"),
            # Observed: the Location mapping sinks the reported position here, beside its series row.
            **{axis: StateVariable.own(f"{LAB}Absolute{axis}") for axis in ("X", "Y")},
        }
    parameters: ResourceParameters = ResourceParameters(
        id_short="Parameters",
        parameter={"Location": Position()},
    )
    asset_interfaces_description: DmpAssetInterfacesDescription = OperationalMqttInterfaces(
        id_short="AssetInterfacesDescription",
    )
    skills: Optional[ModuleSkills] = OperationalMqttSkills(id_short="Skills")
    # A move takes the shuttle to a place: the shuttle is at that place when it ends. Where a unit it carries is
    # follows from custody (the unit is held by the shuttle), so the unit takes no part. The place is a coordinate
    # of the line (a module's TransferPoint); the pose the device is sent to is that place's, in the table's frame.
    capability_description: ModuleCapabilityDescription = OperationalCapabilityDescription(
        id_short="CapabilityDescription",
        CapabilitySet={
            "Transport": ModuleCapabilitySet(CapabilityContainer={
                "MoveToPosition": ModuleCapabilityContainer(
                    Capability=Capability(
                        semantic_id=f"{CSSX}#MoveToPosition", supplemental_semantic_ids=[f"{LAB}Transporting"],
                    ),
                    CapabilityRelations=ModuleCapabilityRelations(
                        Subjects=Subjects(value=[SelfSubject(display_name={"en": "This shuttle"}),
                                                PlaceSubject(display_name={"en": "Target place"})]),
                        EffectSet=EffectSet(End=EndTerms(term={"Term_00": StateEffect(
                            display_name={"en": "Shuttle at the target place"},
                            supplemental_semantic_ids=[f"{LAB}Location"],
                            Subject=TermSubject(value=subject_ref("Transport", "MoveToPosition", 0)),
                            Operator=EffectOperator(value="assign"),
                            ValueReference=TermValueReference(value=subject_ref("Transport", "MoveToPosition", 1)),
                        )})),
                        # Nominal, until the time series says how long moves take (D11).
                        Duration=ExecutionDuration(Value=TermValue(value="3.0", value_type="xs:double")),
                        Translation=Translation.lua(MOVE_TO_PLACE_CALL, COMMAND_STATE_REPLY),
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
