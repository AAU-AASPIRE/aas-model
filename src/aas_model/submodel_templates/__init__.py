"""
Custom aas_pydantic submodel templates — project-specific and IDTA-extended models.

These models follow the same pattern as aas_pydantic generated templates:
- Submodel/SubmodelElementCollection base classes
- Inline semantic_id, description, qualifiers on every class and leaf element
- Typed leaf elements (Property, ReferenceElement, File, etc.) with defaults

Modules:
    aid                    — DMP-extended AID (MQTT + generic WoT action layer)
    capability_description — IDTA Capability Description with each capability's Execution
    execution              — Execution: what a capability needs and changes (subjects, conditions, effects)
    state_declaration      — StateDeclaration submodel: state no data point reports, and its store
    control_component_instance — Extended CCI Skill; Operation variable roles (subject, parameter)
    variables              — Variables submodel (custom, not yet IDTA)
    parameters             — Parameters submodel (custom, not yet IDTA)

The AIMC (AssetInterfacesMappingConfiguration) is extended here (DmpAimc):
the DMP mapping extension adds the OPTIONAL ``ResponseTransformation`` blob
(the correlated-reply direction of an operation mapping, ADR-022) and the
DMP-facing names alias onto the extended classes
(``Aimc`` = ``DmpAimc``, ``AimcMappingConfiguration`` = ``DmpMappingConfiguration``).
"""

from aas_model.submodel_templates.aid import (
    DmpAssetInterfacesDescription,
    Op,
    ReadOnly,
    WriteOnly,
    Safe,
    Idempotent,
    Synchronous,
    DmpForm,
    DmpActionForm,
    DmpResponseForm,
    DmpProperty,
    DmpProperties,
    DmpAction,
    DmpActionInput,
    DmpActionOutput,
    DmpActions,
    DmpEvent,
    DmpEventSubscription,
    DmpEventData,
    DmpEventDataResponse,
    DmpEventCancellation,
    DmpEvents,
    DmpInteractionMetadata,
    DmpHttpInterface,
    DmpModbusInterface,
    DmpOpcuaInterface,
    DmpBacnetInterface,
    DmpIolinkInterface,
    MqvResponseTopic,
    MqttActionForm,
    MqttAction,
    MqttActions,
    MqttInteractionMetadata,
    MqttInterface,
    UavComponentOf,
    OpcuaAction,
    OpcuaActions,
    UavEventType,
    UavEventField,
    OpcuaEventField,
    OpcuaEventFields,
    OpcuaEventData,
    OpcuaEvent,
    OpcuaEvents,
    OpcuaInteractionMetadata,
)
from aas_model.submodel_templates.aimc import (
    DmpAimc,
    DmpMappingConfiguration,
    DmpMappingConfigurations,
    DmpResponseSinkId,
    DmpResponseSinkReference,
    DmpResponseSink,
    DmpResponseSinks,
    DmpResponseSourceId,
    DmpResponseSourceReference,
    DmpResponseSource,
    DmpResponseSources,
    DmpResponseTransformation,
    DmpEvaluation,
    DmpEvaluationMode,
    DmpSource,
    DmpSources,
)
from .control_component_instance import (
    ExecutionModel,
    ExecutionModelParameter,
    Fluent,
    Term,
    ExtendedSkill,
    ExtendedSkills,
    SkillOperation,
    SkillInterfaceRelationship,
    ResourceEndpoints,
)
from .capability_description import (
    ModuleCapabilityContainer,
    ModuleCapabilityDescription,
    ModuleCapabilitySet,
)
from .execution import Execution
from .state_declaration import StateDeclaration, StateVariable
from .control_component_instance import ParameterVariable, SubjectVariable
from .variables import Variables
from .parameters import Parameters
# The AIMC submodel is the GENERATED IDTA template + the DMP extension
# (ResponseTransformation, ADR-022). Alias the DMP-facing names onto it.
from aas_pydantic.submodel_templates.asset_interfaces_mapping_configuration import (
    Transformation,
)

Aimc = DmpAimc
AimcMappingConfiguration = DmpMappingConfiguration
AimcMappingConfigurations = DmpMappingConfigurations

__all__ = [
    # DMP AID (generated template + the extension in docs/aid-extension.md)
    "DmpAssetInterfacesDescription",
    "Op",
    "ReadOnly",
    "WriteOnly",
    "Safe",
    "Idempotent",
    "Synchronous",
    "DmpForm",
    "DmpActionForm",
    "DmpResponseForm",
    "DmpProperty",
    "DmpProperties",
    "DmpAction",
    "DmpActionInput",
    "DmpActionOutput",
    "DmpActions",
    "DmpEvent",
    "DmpEventSubscription",
    "DmpEventData",
    "DmpEventDataResponse",
    "DmpEventCancellation",
    "DmpEvents",
    "DmpInteractionMetadata",
    "MqvResponseTopic",
    "MqttActionForm",
    "MqttAction",
    "MqttActions",
    "MqttInteractionMetadata",
    "UavComponentOf",
    "OpcuaAction",
    "OpcuaActions",
    "OpcuaEvent",
    "OpcuaEvents",
    "OpcuaEventData",
    "OpcuaEventFields",
    "OpcuaEventField",
    "UavEventType",
    "UavEventField",
    # Capability Description with Execution, StateDeclaration, Operation variable roles
    "ModuleCapabilityContainer",
    "ModuleCapabilityDescription",
    "ModuleCapabilitySet",
    "Execution",
    "StateDeclaration",
    "StateVariable",
    "ParameterVariable",
    "SubjectVariable",
    # Execution model (old, on skills; superseded by Execution)
    "ExecutionModel",
    "ExecutionModelParameter",
    "Fluent",
    "Term",
    # Skills
    "ExtendedSkill",
    "ExtendedSkills",
    "SkillOperation",
    "SkillInterfaceRelationship",
    "ResourceEndpoints",
    # REST AID interface
    # Custom submodels
    "Variables",
    "Parameters",
    "Aimc",
    "AimcMappingConfiguration",
    "AimcMappingConfigurations",
    "Transformation",
    "DmpResponseSource",
    "DmpResponseSources",
    "DmpResponseSourceReference",
    "DmpResponseSourceId",
    "DmpResponseSink",
    "DmpResponseSinks",
    "DmpResponseSinkReference",
    "DmpResponseSinkId",
    "DmpResponseTransformation",
    "DmpEvaluation",
    "DmpEvaluationMode",
    "DmpSource",
    "DmpSources",
]
