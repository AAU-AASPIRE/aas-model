"""The stoppering station: the PackML contract and its
Stoppering skill, all over MQTT."""

from aas_pydantic import Property
from aas_model.constants import BASE_URL, BROKER, SITE
from aas_pydantic.submodel_templates.nameplate import ManufacturerProductDesignation
from aas_model.resource_template.modules import LabNameplate
from aas_pydantic.submodel_templates.hierarchical_structures import EntryNode, Node
from aas_model.resource_template.operational import (
    COMMAND_RESPONSE_SCHEMA, COMMAND_RESPONSE_SCHEMA_URL, COMMAND_SCHEMA, COMMAND_SCHEMA_URL,
    OperationalMqttSkills, OperationalMqttInterfaces, OperationalMqttMappings, OperationalVariables,
)
from aas_model.resource_template.resources import StopperingStation
from aas_model.resource_template.references import (
    MQTT_INTERFACE, action_member_ref, affordance_ref, capability_ref, operation_variable_ref, skill_ref,
)
from aas_model.submodel_templates.control_component_instance import (
    SkillOperation, OptionalVariable,
)
from aas_model.submodel_templates.skills import PRIMITIVE, command_skill
from aas_pydantic.submodel_templates.asset_interfaces_mapping_configuration import SourcesItem, SinksItem
from aas_model.submodel_templates import AimcMappingConfiguration, DmpResponseSink, DmpResponseSource
from aas_model.submodel_templates.capability_description import OFFERED_CAPABILITIES, ModuleCapabilityRelations, RealizedBySkill
from aas_model.submodel_templates.aid import DmpActionInput, DmpActionOutput, MqttAction, MqttActionForm
from aas_model.json_schema_aid import datapoint_from_schema
from aas_model.submodel_templates.hierarchical_structures import ResourceHierarchicalStructures


def syntegon_stoppering() -> StopperingStation:
    identity = "syntegonStopperingSystemAAS"
    parent = "aauFillingLineAAS"
    resource_id = f"{BASE_URL}/aas/{identity}"
    resource = StopperingStation(
        id_short=identity,
        id=resource_id,
        nameplate=LabNameplate(
            ManufacturerProductDesignation=ManufacturerProductDesignation(value={"en": "Stoppering station"})),
        hierarchical_structures=ResourceHierarchicalStructures(
            ArcheType="OneUp",
            EntryNode=EntryNode(
                global_asset_id=resource_id, Node={parent: Node(global_asset_id=f"{BASE_URL}/aas/{parent}")}
            ),
        ),
        asset_interfaces_description=OperationalMqttInterfaces(id_short="AssetInterfacesDescription"),
        skills=OperationalMqttSkills(id_short="Skills"),
        asset_interfaces_mapping_configuration=OperationalMqttMappings(
            id_short="AssetInterfacesMappingConfiguration",
        ),
        variables=OperationalVariables(),
    )
    mqtt = resource.asset_interfaces_description.InterfaceTemplateForMQTT[MQTT_INTERFACE]
    mqtt.title.value = "Stoppering station"
    mqtt.EndpointMetadata.base.value = f"{BROKER}/{SITE}/Stoppering/"
    resource.parameters.parameter["Location"].x.parameter.value = 480.0

    # Stoppering: CMD/Stoppering answered on DATA/Stoppering (command / commandResponse).
    name = "Stoppering"
    mqtt.InteractionMetadata.actions.property_name[name] = MqttAction(
        title=name,
        synchronous="false",
        input=datapoint_from_schema(COMMAND_SCHEMA, cls=DmpActionInput, schema_url=COMMAND_SCHEMA_URL),
        output=datapoint_from_schema(
            COMMAND_RESPONSE_SCHEMA, cls=DmpActionOutput, schema_url=COMMAND_RESPONSE_SCHEMA_URL
        ),
        forms=MqttActionForm(href=f"CMD/{name}", mqv_qos="2", mqv_responseTopic=f"DATA/{name}"),
    )
    resource.skills.Skill[name] = command_skill(
        name, PRIMITIVE, affordance_ref(MQTT_INTERFACE, "actions", name), SkillOperation(
            in_output_variable=[Property(id_short="Uuid", description="The UUID of the command")],
            output_variable=[
                Property(id_short="State", description="The state of the command being executed"),
                Property(id_short="Outcome", value="0", value_type="xs:integer", qualifiers=[OptionalVariable()]),
            ],
        ),
    )
    resource.asset_interfaces_mapping_configuration.MappingConfigurations.value.append(
        AimcMappingConfiguration(
            id_short=name, DefaultPollingInterval="0.0",
            Sources=[SourcesItem(SourceId="Uuid", Source=operation_variable_ref(name, "Uuid"))],
            Sinks=[SinksItem(SinkId=name, Sink=action_member_ref(MQTT_INTERFACE, name, "input"))],
            Transformation=f"function aimc_main(sources) return {{ {name} = {{ Uuid = sources.Uuid }} }} end",
            # The correlated MQTT reply is the whole commandResponse.
            ResponseSources=[
                DmpResponseSource(SourceId="Reply", Source=action_member_ref(MQTT_INTERFACE, name, "output")),
            ],
            ResponseTransformation=(
                "function aimc_main(sources) local reply = sources.Reply "
                "return { Uuid = reply.Uuid, State = reply.State, Outcome = reply.Outcome } end"
            ),
            ResponseSinks=[DmpResponseSink(SinkId=member, Sink=operation_variable_ref(name, member))
                           for member in ("Uuid", "State", "Outcome")],
        ),
    )
    container = resource.capability_description.CapabilitySet[OFFERED_CAPABILITIES].CapabilityContainer[name]
    container.CapabilityRelations = ModuleCapabilityRelations(CapabilityRealizedBy={
        f"RealizedBy_{name}": RealizedBySkill(first=capability_ref(OFFERED_CAPABILITIES, name), second=skill_ref(name)),
    })
    return resource
