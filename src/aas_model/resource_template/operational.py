"""Typed defaults for the shared operational-device contract.

Every operational device of the lab has a PackML state machine and the
skills Halt, Occupy and Release. The contract is the same over each
protocol; only its native affordances differ:

- MQTT: ``CMD/<Skill>`` requests answered on ``DATA/<Skill>`` (MQTT 5
  request/reply) and the retained ``DATA/State`` (State + ProcessQueue).
- OPC UA: the Methods ``ns=2;s=Station.<Skill>`` of the ``ns=2;s=Station``
  Object and its variables ``Station.State`` and ``Station.ProcessQueue``.

Halt only invokes (``CMD/Halt`` is not answered, ``Station.Halt`` has no
OutputArguments). Occupy and Release answer with the commandResponse; their
mappings name it as ResponseSource and the Operation as ResponseSink.

Module control: Occupy and Release are also capabilities of the device
(``CapabilityDescription/ModuleControl``, the lab's Receiving and Releasing),
with what they need and change: occupying needs room (Occupancy below the
Capacity) and takes one place, releasing gives it back.

State: ``Variables/State/Station`` records the PackML state and the process
queue over time (measurement ``station_state``); the AAS holds the series, not
the current value.
``Variables/Log/<skill>`` records every Occupy and Release call (measurement
``operation_<skill>``: outcome, duration and the Operation's variables, also
for failed calls); the skill's response mapping writes it. Halt answers
nothing, so it has no log.

The protocol-specific types in ``resources`` (MqttOperationalStation,
OpcuaOperationalStation, PlanarShuttle) default to these classes; an instance
of a protocol-neutral station type picks them for the protocol its asset
speaks. Pydantic deep-copies defaults per constructed model.
"""

from typing import Dict

from aas_pydantic import Capability, Property
from aas_pydantic.submodel_templates.capability_description import PropertyProperty
from aas_model.submodel_templates.capability_description import (
    HasProperty, ModuleCapabilityContainer, ModuleCapabilityDescription, ModuleCapabilityRelations,
    ModuleCapabilitySet, ModuleConstraintSet, RealizedBySkill, SameAs, StateConditionalType, StateConstraint,
    StateConstraintContainer, StatedConstraintPropertyRelations, StatedProperty, StatedPropertySet,
)
from aas_pydantic.submodel_templates.asset_interfaces_description import (
    Base, ContentType, EndpointMetadata, Title, securityDefinitions, security_t,
)
from aas_pydantic.submodel_templates.asset_interfaces_mapping_configuration import SinksItem, SourcesItem

from aas_model.constants import BROKER, LAB, SCHEMA_BASE, SITE, STATE_OCCUPIED, STATE_OPERATIONAL
from aas_model.submodel_templates import (
    Aimc, AimcMappingConfiguration, AimcMappingConfigurations, DmpResponseSink, DmpResponseSource,
)
from aas_model.submodel_templates.aid import (
    DmpActionInput, DmpActionOutput, DmpAssetInterfacesDescription, DmpForm, DmpOpcuaInterface, DmpProperties,
    MqttAction, MqttActionForm, MqttActions, MqttForm, MqttInteractionMetadata, MqttInterface, OpcuaAction,
    OpcuaActionForm, OpcuaActions, OpcuaInteractionMetadata,
)
from aas_model.submodel_templates.control_component_instance import (
    ExtendedSkill, ExtendedSkills, ResourceControlComponentInstance, ResourceEndpoints, SkillInterfaceRelationship,
    SkillOperation,
)
from aas_model.submodel_templates.variables import LogGroup, StateGroup, Variables
from aas_model.submodel_templates.execution import (
    ConditionOperator, EffectContainer, EffectDefinition, EffectHasProperty, EffectOperator, EffectPropertyRelations,
    EffectSet, EffectTimingType, SelfSubject, StateCondition, StateEffect, Subjects, TermProperty, TermValue,
    TermValueReference,
)
from aas_pydantic.submodel_templates.time_series import Name
from aas_model.submodel_templates.time_series import (
    DmpLinkedSegment, InfluxDb2Target, RecordField, RecordReference, TimeSeriesCollection, TimeSeriesMetadata,
    TimeSeriesRecord, TimeSeriesSegments,
)
from aas_model.resource_template.references import (
    MQTT_INTERFACE, OPCUA_INTERFACE, action_member_ref, affordance_ref, capability_property_ref, capability_ref,
    condition_ref, effect_ref, operation_ref, operation_variable_ref, series_segment_ref, skill_ref, subject_ref,
)
from aas_model.json_schema_aid import datapoint_from_schema, load_schema
from aas_pydantic.aas_model import AasIdString
from pydantic import model_validator


PACKML_SKILLS = ("Halt", "Occupy", "Release")

# Halt only invokes: the station takes the command and answers nothing. Its
# Operation has no outputs, its action no output schema (and over MQTT no
# response topic) and its mapping no response.
INVOKE_ONLY_SKILLS = ("Halt",)

# The skills whose calls are logged: those that answer.
LOGGED_SKILLS = tuple(name for name in PACKML_SKILLS if name not in INVOKE_ONLY_SKILLS)

# The CapabilitySet of the capabilities the PackML contract gives every operational device.
MODULE_CONTROL = "ModuleControl"

# The OPC UA Object owning the PackML Methods and variables.
OPCUA_STATION = "ns=2;s=Station"

# A command's request and response (the input and output of every Halt / Occupy / Release / process action), and
# a station's state. Each URL rides as a supplemental semantic id on the DataSchema built from it.
COMMAND_SCHEMA_URL = f"{SCHEMA_BASE}/command.schema.json"
COMMAND_RESPONSE_SCHEMA_URL = f"{SCHEMA_BASE}/commandResponse.schema.json"
STATION_STATE_SCHEMA_URL = f"{SCHEMA_BASE}/stationState.schema.json"
COMMAND_SCHEMA = load_schema(COMMAND_SCHEMA_URL)
COMMAND_RESPONSE_SCHEMA = load_schema(COMMAND_RESPONSE_SCHEMA_URL)
STATION_STATE_SCHEMA = load_schema(STATION_STATE_SCHEMA_URL)


def station_state(occupation: bool = True) -> StateGroup:
    """``Variables/State/Station``: the PackML state over time and, for a device that is occupied, its process
    queue (measurement ``station_state``)."""
    field = {"PackMLState": RecordField(value_type="xs:string", supplemental_semantic_ids=[STATE_OPERATIONAL])}
    if occupation:
        field["OccupationState"] = RecordField(value_type="xs:string", supplemental_semantic_ids=[STATE_OCCUPIED],
                                               description="The process queue as JSON array text")
    return StateGroup(value={"Station": TimeSeriesCollection(
        Metadata=TimeSeriesMetadata(Name=Name(value={"en": "Station state"}), Record=TimeSeriesRecord(field=field)),
        Segments=TimeSeriesSegments(LinkedSegment={
            "Live": DmpLinkedSegment(InfluxDb2Target=InfluxDb2Target(Measurement="station_state")),
        }),
    )})


class OperationalVariables(Variables):
    """A station's Variables: the history of its PackML state and the logs of the skills that answer.

    The series are added unless authored, not class defaults: a class default is recorded in the AAS, and the
    resource restored from JSON holds a plain Variables without it."""
    id_short: AasIdString = "Variables"

    @model_validator(mode="after")
    def _series_follow_from_the_station(self):
        if self.State is None:
            self.State = station_state()
        # A call's outcome and duration next to the Operation itself, referenced: its input, InOut and output
        # variables are fields (Operation.Uuid) with their valueTypes and follow its definition.
        if self.Log is None:
            self.Log = LogGroup(value={name: TimeSeriesCollection(
                Metadata=TimeSeriesMetadata(Name=Name(value={"en": f"{name} calls"}), Record=TimeSeriesRecord(field={
                    "Outcome": RecordField(value_type="xs:string", description="How the invocation ended"),
                    "DurationMs": RecordField(value_type="xs:long",
                                              description="Time from accepting the call to its answer"),
                    "Operation": RecordReference(value=operation_ref(name),
                                                 description="The invoked Operation's variables"),
                })),
                Segments=TimeSeriesSegments(LinkedSegment={
                    "Live": DmpLinkedSegment(InfluxDb2Target=InfluxDb2Target(Measurement=f"operation_{name.lower()}")),
                }),
            ) for name in LOGGED_SKILLS})
        return self


# ── Capabilities: what Occupy and Release need and change ───────────────────

class ModuleControlCapabilities(ModuleCapabilitySet):
    """Occupying (Occupy, the lab's Receiving) and Releasing (Release, Releasing). The Capacity is the device's:
    an instance that holds more than one product at a time sets it. Occupancy is the device's state: how many
    products it holds now (no value: the state store keeps it)."""
    CapabilityContainer: Dict[str, ModuleCapabilityContainer] = {
        "Occupying": ModuleCapabilityContainer(
            Capability=Capability(supplemental_semantic_ids=[f"{LAB}Receiving"]),
            Subjects=Subjects(subject={"Self": SelfSubject()}),
            PropertySet={"PropertySet": StatedPropertySet(PropertyContainer={
                "Capacity": StatedProperty(PropertyProperty={"Capacity": PropertyProperty(
                    value="1", value_type="xs:int", supplemental_semantic_ids=[f"{LAB}Capacity"],
                    description="How many products the device holds at a time.",
                )}),
                "Occupancy": StatedProperty(
                    PropertyProperty={"Occupancy": PropertyProperty(
                        value_type="xs:int", supplemental_semantic_ids=[f"{LAB}Occupancy"],
                        description="How many products the device holds now.",
                    )},
                    SameProperty={"OfSubject": SameAs(
                        first=capability_property_ref(MODULE_CONTROL, "Occupying", "Occupancy"),
                        second=subject_ref(MODULE_CONTROL, "Occupying", "Self"),
                    )},
                ),
            })},
            CapabilityRelations=ModuleCapabilityRelations(
                CapabilityRealizedBy={"RealizedBy_Occupy": RealizedBySkill(
                    first=capability_ref(MODULE_CONTROL, "Occupying"), second=skill_ref("Occupy"),
                )},
                ConstraintSet={"ConstraintSet": ModuleConstraintSet(PropertyConstraintContainer={
                    "HasRoom": StateConstraintContainer(
                        CustomConstraint=StateConstraint(value={"Term": StateCondition(
                            Property=TermProperty(
                                value=capability_property_ref(MODULE_CONTROL, "Occupying", "Occupancy")),
                            Operator=ConditionOperator(value="less"),
                            ValueReference=TermValueReference(
                                value=capability_property_ref(MODULE_CONTROL, "Occupying", "Capacity")),
                        )}),
                        PropertyConditionalType=StateConditionalType(value="Pre"),
                        ConstraintPropertyRelations=StatedConstraintPropertyRelations(ConstraintHasProperty={
                            prop: HasProperty(first=condition_ref(MODULE_CONTROL, "Occupying", "HasRoom"),
                                              second=capability_property_ref(MODULE_CONTROL, "Occupying", prop))
                            for prop in ("Occupancy", "Capacity")
                        }),
                    ),
                })},
                EffectSet=EffectSet(EffectContainer={"TakesPlace": EffectContainer(
                    EffectTimingType=EffectTimingType(value="End"),
                    Effect=EffectDefinition(term={"Term": StateEffect(
                        Property=TermProperty(value=capability_property_ref(MODULE_CONTROL, "Occupying", "Occupancy")),
                        Operator=EffectOperator(value="increase"),
                        Value=TermValue(value="1", value_type="xs:int"),
                    )}),
                    EffectPropertyRelations=EffectPropertyRelations(EffectHasProperty={"Occupancy": EffectHasProperty(
                        first=effect_ref(MODULE_CONTROL, "Occupying", "TakesPlace"),
                        second=capability_property_ref(MODULE_CONTROL, "Occupying", "Occupancy"),
                    )}),
                )}),
            ),
        ),
        "Releasing": ModuleCapabilityContainer(
            Capability=Capability(supplemental_semantic_ids=[f"{LAB}Releasing"]),
            Subjects=Subjects(subject={"Self": SelfSubject()}),
            PropertySet={"PropertySet": StatedPropertySet(PropertyContainer={
                "Occupancy": StatedProperty(
                    PropertyProperty={"Occupancy": PropertyProperty(
                        value_type="xs:int", supplemental_semantic_ids=[f"{LAB}Occupancy"],
                        description="How many products the device holds now.",
                    )},
                    SameProperty={"OfSubject": SameAs(
                        first=capability_property_ref(MODULE_CONTROL, "Releasing", "Occupancy"),
                        second=subject_ref(MODULE_CONTROL, "Releasing", "Self"),
                    )},
                ),
            })},
            CapabilityRelations=ModuleCapabilityRelations(
                CapabilityRealizedBy={"RealizedBy_Release": RealizedBySkill(
                    first=capability_ref(MODULE_CONTROL, "Releasing"), second=skill_ref("Release"),
                )},
                ConstraintSet={"ConstraintSet": ModuleConstraintSet(PropertyConstraintContainer={
                    "HoldsOne": StateConstraintContainer(
                        CustomConstraint=StateConstraint(value={"Term": StateCondition(
                            Property=TermProperty(
                                value=capability_property_ref(MODULE_CONTROL, "Releasing", "Occupancy")),
                            Operator=ConditionOperator(value="greater"),
                            Value=TermValue(value="0", value_type="xs:int"),
                        )}),
                        PropertyConditionalType=StateConditionalType(value="Pre"),
                        ConstraintPropertyRelations=StatedConstraintPropertyRelations(ConstraintHasProperty={
                            "Occupancy": HasProperty(
                                first=condition_ref(MODULE_CONTROL, "Releasing", "HoldsOne"),
                                second=capability_property_ref(MODULE_CONTROL, "Releasing", "Occupancy")),
                        }),
                    ),
                })},
                EffectSet=EffectSet(EffectContainer={"GivesPlace": EffectContainer(
                    EffectTimingType=EffectTimingType(value="End"),
                    Effect=EffectDefinition(term={"Term": StateEffect(
                        Property=TermProperty(value=capability_property_ref(MODULE_CONTROL, "Releasing", "Occupancy")),
                        Operator=EffectOperator(value="decrease"),
                        Value=TermValue(value="1", value_type="xs:int"),
                    )}),
                    EffectPropertyRelations=EffectPropertyRelations(EffectHasProperty={"Occupancy": EffectHasProperty(
                        first=effect_ref(MODULE_CONTROL, "Releasing", "GivesPlace"),
                        second=capability_property_ref(MODULE_CONTROL, "Releasing", "Occupancy"),
                    )}),
                )}),
            ),
        ),
    }


class OperationalCapabilityDescription(ModuleCapabilityDescription):
    """An operational device's capabilities: its own, and the module control every one of them has.

    Module control is added unless authored, not a class default, as the series of ``OperationalVariables``."""
    id_short: AasIdString = "CapabilityDescription"

    @model_validator(mode="after")
    def _module_control_follows_from_the_contract(self):
        if MODULE_CONTROL not in self.CapabilitySet:
            self.CapabilitySet[MODULE_CONTROL] = ModuleControlCapabilities(id_short=MODULE_CONTROL)
        return self


# ── Control component: the PackML skills, bound to one interface ─────────────

class OperationalMqttControlComponent(ResourceControlComponentInstance):
    # Halt carries the command's Uuid; Occupy and Release return it with the command's State.
    Skills: ExtendedSkills = ExtendedSkills(Skill={
        **{name: ExtendedSkill(
            interface_reference=affordance_ref(MQTT_INTERFACE, "actions", name),
            operation=SkillOperation(
                input_variable=[Property(id_short="Uuid", description="The UUID of the command")],
            ),
        ) for name in INVOKE_ONLY_SKILLS},
        **{name: ExtendedSkill(
            interface_reference=affordance_ref(MQTT_INTERFACE, "actions", name),
            operation=SkillOperation(
                in_output_variable=[Property(id_short="Uuid", description="The UUID of the command")],
                output_variable=[Property(id_short="State", description="The state of the command being executed")],
            ),
        ) for name in LOGGED_SKILLS},
    })
    Endpoints: ResourceEndpoints = ResourceEndpoints(Endpoint={
        name: SkillInterfaceRelationship(first=skill_ref(name), second=affordance_ref(MQTT_INTERFACE, "actions", name))
        for name in PACKML_SKILLS
    })


class OperationalOpcuaControlComponent(ResourceControlComponentInstance):
    # Halt carries the command's Uuid; Occupy and Release return it with the command's State.
    Skills: ExtendedSkills = ExtendedSkills(Skill={
        **{name: ExtendedSkill(
            interface_reference=affordance_ref(OPCUA_INTERFACE, "actions", name),
            operation=SkillOperation(
                input_variable=[Property(id_short="Uuid", description="The UUID of the command")],
            ),
        ) for name in INVOKE_ONLY_SKILLS},
        **{name: ExtendedSkill(
            interface_reference=affordance_ref(OPCUA_INTERFACE, "actions", name),
            operation=SkillOperation(
                in_output_variable=[Property(id_short="Uuid", description="The UUID of the command")],
                output_variable=[Property(id_short="State", description="The state of the command being executed")],
            ),
        ) for name in LOGGED_SKILLS},
    })
    Endpoints: ResourceEndpoints = ResourceEndpoints(Endpoint={
        name: SkillInterfaceRelationship(first=skill_ref(name), second=affordance_ref(OPCUA_INTERFACE, "actions", name))
        for name in PACKML_SKILLS
    })


# ── Asset interfaces ─────────────────────────────────────────────────────────

class MqttInterfaces(DmpAssetInterfacesDescription):
    """An MQTT interface without implied skills or station telemetry."""

    InterfaceTemplateForMQTT: dict[str, MqttInterface] = {
        MQTT_INTERFACE: MqttInterface(
            id_short=MQTT_INTERFACE,
            EndpointMetadata=EndpointMetadata(
                base=Base(value=f"{BROKER}/{SITE}/{{station_name}}/"),
                contentType=ContentType(value="application/json"),
                security=security_t(), securityDefinitions=securityDefinitions(),
            ),
            InteractionMetadata=MqttInteractionMetadata(
                actions=MqttActions(), properties=DmpProperties(),
            ),
        ),
    }


class OperationalMqttInterfaces(MqttInterfaces):
    """Shared Halt/Occupy/Release and StationState MQTT affordances."""

    InterfaceTemplateForMQTT: dict[str, MqttInterface] = {
        MQTT_INTERFACE: MqttInterface(
            id_short=MQTT_INTERFACE,
            EndpointMetadata=MqttInterfaces(id_short="AssetInterfacesDescription").InterfaceTemplateForMQTT[
                MQTT_INTERFACE
            ].EndpointMetadata,
            InteractionMetadata=MqttInteractionMetadata(
                # CMD/<skill>, answered on DATA/<skill> by MQTT 5 request/reply (Halt is not answered).
                actions=MqttActions(property_name={
                    name: MqttAction(
                        title=name, synchronous="true",
                        input=datapoint_from_schema(COMMAND_SCHEMA, cls=DmpActionInput, schema_url=COMMAND_SCHEMA_URL),
                        output=None if name in INVOKE_ONLY_SKILLS else datapoint_from_schema(
                            COMMAND_RESPONSE_SCHEMA, cls=DmpActionOutput, schema_url=COMMAND_RESPONSE_SCHEMA_URL),
                        forms=MqttActionForm(href=f"CMD/{name}", mqv_qos="2",
                                             mqv_responseTopic=None if name in INVOKE_ONLY_SKILLS else f"DATA/{name}"),
                    ) for name in PACKML_SKILLS
                }),
                properties=DmpProperties(property_name={
                    "StationState": datapoint_from_schema(
                        STATION_STATE_SCHEMA, key="StationState", schema_url=STATION_STATE_SCHEMA_URL,
                        title=Title(value="StationState"), observable="true", readOnly="true",
                        forms=MqttForm(href="DATA/State", mqv_retain="true", mqv_qos="0"),
                    ),
                }),
            ),
        ),
    }


class OpcuaInterfaces(DmpAssetInterfacesDescription):
    """An OPC UA interface without implied skills or station telemetry."""

    InterfaceTemplateForOPCUA: dict[str, DmpOpcuaInterface] = {
        OPCUA_INTERFACE: DmpOpcuaInterface(
            id_short=OPCUA_INTERFACE,
            EndpointMetadata=EndpointMetadata(
                base=Base(value="opc.tcp://{station_name}:4840/"),
                # OPC 10101: the binding's default UA serialization
                contentType=ContentType(value="application/octet-stream"),
                security=security_t(), securityDefinitions=securityDefinitions(),
            ),
            InteractionMetadata=OpcuaInteractionMetadata(
                actions=OpcuaActions(), properties=DmpProperties(),
            ),
        ),
    }


class OperationalOpcuaInterfaces(OpcuaInterfaces):
    """Shared Halt/Occupy/Release Methods and the PackML state variables."""

    InterfaceTemplateForOPCUA: dict[str, DmpOpcuaInterface] = {
        OPCUA_INTERFACE: DmpOpcuaInterface(
            id_short=OPCUA_INTERFACE,
            EndpointMetadata=OpcuaInterfaces(id_short="AssetInterfacesDescription").InterfaceTemplateForOPCUA[
                OPCUA_INTERFACE
            ].EndpointMetadata,
            InteractionMetadata=OpcuaInteractionMetadata(
                # The Methods Station.<skill> of the Object Station; Halt has no OutputArguments.
                actions=OpcuaActions(property_name={
                    name: OpcuaAction(
                        title=name, uav_componentOf=OPCUA_STATION, synchronous="true",
                        input=datapoint_from_schema(COMMAND_SCHEMA, cls=DmpActionInput, schema_url=COMMAND_SCHEMA_URL),
                        output=None if name in INVOKE_ONLY_SKILLS else datapoint_from_schema(
                            COMMAND_RESPONSE_SCHEMA, cls=DmpActionOutput, schema_url=COMMAND_RESPONSE_SCHEMA_URL),
                        forms=OpcuaActionForm(href=f"/?id={OPCUA_STATION}.{name}"),
                    ) for name in PACKML_SKILLS
                }),
                properties=DmpProperties(property_name={
                    name: datapoint_from_schema(
                        STATION_STATE_SCHEMA["properties"][name], key=name,
                        title=Title(value=name), observable="true", readOnly="true",
                        forms=DmpForm(href=f"/?id={OPCUA_STATION}.{name}"),
                    ) for name in ("State", "ProcessQueue")
                }),
            ),
        ),
    }


# ── Mappings: observe the PackML state, invoke the skills ───────────────────

# An answered call: the reply's Uuid and State into the Operation and, also for a failed call, one row into
# Variables/Log/<skill> (outcome, duration and the Operation's variables).
_LOGGED_REPLY_TRANSFORMATION = """function aimc_main(sources, requestSources)
    local reply = sources.Reply or {}
    local log = { Outcome = meta.invocation.outcome, DurationMs = meta.invocation.durationMs,
        Operation = { Uuid = requestSources.Uuid, State = reply.State } }
    if meta.invocation.outcome ~= "Succeeded" then return { Log = log } end
    return { Uuid = reply.Uuid, State = reply.State, Log = log }
end
"""


# One row into Variables/State/Station. The occupation queue is written as JSON array text: the field is a
# string, and an empty Lua table would not encode as an array.
_STATE_TRANSFORMATION = """function aimc_main(sources)
    local queue = {queue} or {{}}
    return {{ Live = {{
        PackMLState = {state},
        OccupationState = (#queue == 0) and "[]" or json.encode(queue),
    }} }}
end
"""


class OperationalMqttMappings(Aimc):
    MappingConfigurations: AimcMappingConfigurations = AimcMappingConfigurations(value=[
        AimcMappingConfiguration(
            id_short="StationState", DefaultPollingInterval="0.0",
            Sources=[SourcesItem(SourceId="StationState",
                                 Source=affordance_ref(MQTT_INTERFACE, "properties", "StationState"))],
            Sinks=[SinksItem(SinkId="Live", Sink=series_segment_ref("State", "Station"))],
            Transformation=_STATE_TRANSFORMATION.format(
                queue="sources.StationState.ProcessQueue", state="sources.StationState.State"),
        ),
        # Each skill: the Operation's Uuid into its action's command; Occupy and Release also answer.
        *[AimcMappingConfiguration(
            id_short=name, DefaultPollingInterval="0.0",
            Sources=[SourcesItem(SourceId="Uuid", Source=operation_variable_ref(name, "Uuid"))],
            Sinks=[SinksItem(SinkId=name, Sink=action_member_ref(MQTT_INTERFACE, name, "input"))],
            Transformation=f"function aimc_main(sources) return {{ {name} = {{ Uuid = sources.Uuid }} }} end",
        ) for name in INVOKE_ONLY_SKILLS],
        *[AimcMappingConfiguration(
            id_short=name, DefaultPollingInterval="0.0",
            Sources=[SourcesItem(SourceId="Uuid", Source=operation_variable_ref(name, "Uuid"))],
            Sinks=[SinksItem(SinkId=name, Sink=action_member_ref(MQTT_INTERFACE, name, "input"))],
            Transformation=f"function aimc_main(sources) return {{ {name} = {{ Uuid = sources.Uuid }} }} end",
            ResponseSources=[
                DmpResponseSource(SourceId="Reply", Source=action_member_ref(MQTT_INTERFACE, name, "output")),
            ],
            ResponseTransformation=_LOGGED_REPLY_TRANSFORMATION,
            ResponseSinks=[
                DmpResponseSink(SinkId="Uuid", Sink=operation_variable_ref(name, "Uuid")),
                DmpResponseSink(SinkId="State", Sink=operation_variable_ref(name, "State")),
                DmpResponseSink(SinkId="Log", Sink=series_segment_ref("Log", name)),
            ],
        ) for name in LOGGED_SKILLS],
    ])


class OperationalOpcuaMappings(Aimc):
    MappingConfigurations: AimcMappingConfigurations = AimcMappingConfigurations(value=[
        AimcMappingConfiguration(
            id_short="StationState", DefaultPollingInterval="0.0",
            Sources=[SourcesItem(SourceId=name, Source=affordance_ref(OPCUA_INTERFACE, "properties", name))
                     for name in ("State", "ProcessQueue")],
            Sinks=[SinksItem(SinkId="Live", Sink=series_segment_ref("State", "Station"))],
            Transformation=_STATE_TRANSFORMATION.format(queue="sources.ProcessQueue", state="sources.State"),
        ),
        # Each skill: the Operation's Uuid into its action's command; Occupy and Release also answer.
        *[AimcMappingConfiguration(
            id_short=name, DefaultPollingInterval="0.0",
            Sources=[SourcesItem(SourceId="Uuid", Source=operation_variable_ref(name, "Uuid"))],
            Sinks=[SinksItem(SinkId=name, Sink=action_member_ref(OPCUA_INTERFACE, name, "input"))],
            Transformation=f"function aimc_main(sources) return {{ {name} = {{ Uuid = sources.Uuid }} }} end",
        ) for name in INVOKE_ONLY_SKILLS],
        *[AimcMappingConfiguration(
            id_short=name, DefaultPollingInterval="0.0",
            Sources=[SourcesItem(SourceId="Uuid", Source=operation_variable_ref(name, "Uuid"))],
            Sinks=[SinksItem(SinkId=name, Sink=action_member_ref(OPCUA_INTERFACE, name, "input"))],
            Transformation=f"function aimc_main(sources) return {{ {name} = {{ Uuid = sources.Uuid }} }} end",
            ResponseSources=[
                DmpResponseSource(SourceId="Reply", Source=action_member_ref(OPCUA_INTERFACE, name, "output")),
            ],
            ResponseTransformation=_LOGGED_REPLY_TRANSFORMATION,
            ResponseSinks=[
                DmpResponseSink(SinkId="Uuid", Sink=operation_variable_ref(name, "Uuid")),
                DmpResponseSink(SinkId="State", Sink=operation_variable_ref(name, "State")),
                DmpResponseSink(SinkId="Log", Sink=series_segment_ref("Log", name)),
            ],
        ) for name in LOGGED_SKILLS],
    ])
