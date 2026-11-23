"""
Shared constants for the templates package.

All project-specific semantic IDs are defined here.
IDTA-defined semantic IDs (admin-shell.io/idta/...) stay in their generated templates.
Third-party semantic IDs (w3.org, schema.org, purl.org, etc.) stay inline in their modules.
"""

# ═══════════════════════════════════════════════════════════════════════════════
# Base URLs
# ═══════════════════════════════════════════════════════════════════════════════

BASE_URL = "https://smartproductionlab.aau.dk"
SCHEMA_BASE = "https://aausmartproductionlab.github.io/AP2030-UNS/MQTTSchemas"

# ═══════════════════════════════════════════════════════════════════════════════
# Infrastructure defaults
# ═══════════════════════════════════════════════════════════════════════════════

BROKER = "mqtt://192.168.0.104:1883"
SITE = "NN/Nybrovej/InnoLab"

# Shared invocation service origin. Resource-specific identity belongs in
# authored URL path segments, never in a per-resource host/config setting.
INVOCATION_ORIGIN = "http://dmp:8080"
# An Operation's invocationDelegation URL: the origin and the path the Operation is invoked at in the AAS API,
# filled in once the Operation's submodel id and idShortPath are known (invocation_authoring).
INVOCATION_URL_TEMPLATE = f"{INVOCATION_ORIGIN}{{operation_path}}"

# ═══════════════════════════════════════════════════════════════════════════════
# Ontology
# ═══════════════════════════════════════════════════════════════════════════════

CSSX = "http://www.w3id.org/aau-ra/cssx"

# The concepts of an operational device's state: its PackML state and its occupation (the process queue).
STATE_OPERATIONAL = "https://w3id.org/2026/apex/semantic/state/operational"
STATE_OCCUPIED = "https://w3id.org/2026/apex/semantic/state/occupied"

# The lab vocabulary (iec61499-mgmt-py, ontology/Vocabulary): what capabilities, properties and skill types mean.
# Elements carry these as supplemental semantic ids; their semantic id names the AAS structure.
LAB = f"{BASE_URL}/semantics/"

# ═══════════════════════════════════════════════════════════════════════════════
# Execution semantics — what a capability needs and changes (plans/kg-planning-execution-PLAN.md, 4.2)
# ═══════════════════════════════════════════════════════════════════════════════
# Conditions are IDTA 02020 PropertyConstraintContainers whose CustomConstraint holds a term tree (the
# ConditionalType says Pre, Invariant, Post); effects are EffectContainers in an EffectSet beside the ConstraintSet.
# A term's kind is its semantic id; the property it is about is an entry of the capability's PropertySet.

EXECUTION_SUBJECTS = f"{BASE_URL}/execution/Subjects/1/0"
EXECUTION_SUBJECT_SELF = f"{BASE_URL}/execution/Subject/Self/1/0"
EXECUTION_SUBJECT_COMPONENT = f"{BASE_URL}/execution/Subject/Component/1/0"
EXECUTION_SUBJECT_PRODUCT = f"{BASE_URL}/execution/Subject/Product/1/0"
EXECUTION_SUBJECT_CARRIER = f"{BASE_URL}/execution/Subject/Carrier/1/0"
EXECUTION_SUBJECT_VARIABLE = f"{BASE_URL}/execution/Subject/Variable/1/0"
EXECUTION_STATE_CONSTRAINT = f"{BASE_URL}/execution/StateConstraint/1/0"
EXECUTION_EFFECT_SET = f"{BASE_URL}/execution/EffectSet/1/0"
EXECUTION_EFFECT_CONTAINER = f"{BASE_URL}/execution/EffectContainer/1/0"
EXECUTION_EFFECT_TIMING = f"{BASE_URL}/execution/EffectTimingType/1/0"
EXECUTION_EFFECT_DEFINITION = f"{BASE_URL}/execution/EffectContainer/Effect/1/0"
EXECUTION_EFFECT_PROPERTY_RELATIONS = f"{BASE_URL}/execution/EffectPropertyRelations/1/0"
EXECUTION_EFFECT_HAS_PROPERTY = f"{BASE_URL}/execution/EffectHasProperty/1/0"
EXECUTION_CONDITION = f"{BASE_URL}/execution/Condition/1/0"
EXECUTION_EFFECT = f"{BASE_URL}/execution/Effect/1/0"
EXECUTION_TERM_PROPERTY = f"{BASE_URL}/execution/Term/Property/1/0"
EXECUTION_CONDITION_OPERATOR = f"{BASE_URL}/execution/Condition/Operator/1/0"
EXECUTION_EFFECT_OPERATOR = f"{BASE_URL}/execution/Effect/Operator/1/0"
EXECUTION_TERM_VALUE = f"{BASE_URL}/execution/Term/Value/1/0"
EXECUTION_TERM_VALUE_REFERENCE = f"{BASE_URL}/execution/Term/ValueReference/1/0"
EXECUTION_TERM_FORMULA = f"{BASE_URL}/execution/Term/Formula/1/0"
EXECUTION_FORMULA_USES = f"{BASE_URL}/execution/Term/Uses/1/0"
EXECUTION_FORMULA_USE = f"{BASE_URL}/execution/Term/Use/1/0"
EXECUTION_RATE = f"{BASE_URL}/execution/Effect/Rate/1/0"
EXECUTION_AND = f"{BASE_URL}/execution/And/1/0"
EXECUTION_OR = f"{BASE_URL}/execution/Or/1/0"
EXECUTION_NOT = f"{BASE_URL}/execution/Not/1/0"
EXECUTION_EXISTS = f"{BASE_URL}/execution/Exists/1/0"
EXECUTION_FOR_ALL = f"{BASE_URL}/execution/ForAll/1/0"
EXECUTION_QUANTIFIED_VARIABLE = f"{BASE_URL}/execution/Variable/1/0"
EXECUTION_BODY = f"{BASE_URL}/execution/Body/1/0"
EXECUTION_WHEN = f"{BASE_URL}/execution/When/1/0"
EXECUTION_WHEN_CONDITION = f"{BASE_URL}/execution/When/Condition/1/0"
EXECUTION_WHEN_THEN = f"{BASE_URL}/execution/When/Then/1/0"
EXECUTION_ONE_OF = f"{BASE_URL}/execution/OneOf/1/0"
EXECUTION_OUTCOME = f"{BASE_URL}/execution/OneOf/Outcome/1/0"

# The role of an Operation variable (D27): a subject only known at run time, used to ground effects, or a
# parameter the payload is built from.
OPERATION_VARIABLE_SUBJECT = f"{BASE_URL}/aas/OperationVariable/Subject/1/0"
OPERATION_VARIABLE_PARAMETER = f"{BASE_URL}/aas/OperationVariable/Parameter/1/0"

# The StateDeclaration submodel: the state variables of a subject that are not observed, and where they are kept.
SM_STATE_DECLARATION = f"{BASE_URL}/submodels/StateDeclaration/1/0"
STATE_VARIABLE = f"{BASE_URL}/state/StateVariable/1/0"
STATE_VARIABLE_INITIAL = f"{BASE_URL}/state/StateVariable/Initial/1/0"
STATE_VARIABLE_OBSERVED = f"{BASE_URL}/state/StateVariable/Observed/1/0"
STATE_SPARQL_TARGET = f"{BASE_URL}/state/SparqlTarget/1/0"
STATE_SPARQL_TARGET_ENDPOINT = f"{BASE_URL}/state/SparqlTarget/Endpoint/1/0"
STATE_SPARQL_TARGET_GRAPH = f"{BASE_URL}/state/SparqlTarget/Graph/1/0"

# The state store every StateDeclaration of this workspace points at (plans/kg-planning-execution-PLAN.md, 4.1).
STATE_STORE_ORIGIN = "http://state-store:7878"
STATE_STORE_GRAPH = f"{BASE_URL}/state"

# ═══════════════════════════════════════════════════════════════════════════════
# Submodel ids
# ═══════════════════════════════════════════════════════════════════════════════
# The id injector gives each submodel of a resource the id ``{aas_id}/submodels/<idShort>``; references into a
# resource's own submodels are authored against these and resolved with it.

AID_SUBMODEL_ID = "{aas_id}/submodels/AssetInterfacesDescription"
CCI_SUBMODEL_ID = "{aas_id}/submodels/ControlComponentInstance"
CONTROL_COMPONENT_TYPE_SUBMODEL_ID = "{aas_id}/submodels/ControlComponentType"
VARIABLES_SUBMODEL_ID = "{aas_id}/submodels/Variables"
CAPABILITIES_SUBMODEL_ID = "{aas_id}/submodels/CapabilityDescription"
HIERARCHICAL_STRUCTURES_SUBMODEL_ID = "{aas_id}/submodels/HierarchicalStructures"

# ═══════════════════════════════════════════════════════════════════════════════
# AID extension (docs/aid-extension.md) — WoT TD terms AID 1.2 does not carry.
# IRIs are those of the TD 1.1 JSON-LD context (td:, hctl:, jsonschema:).
# ═══════════════════════════════════════════════════════════════════════════════

WOT_TD = "https://www.w3.org/2019/wot/td#"
WOT_HCTL = "https://www.w3.org/2019/wot/hypermedia#"
WOT_JSONSCHEMA = "https://www.w3.org/2019/wot/json-schema#"

# Affordance members. AID gives a property member its own id
# (``…/1/0/PropertyDefinition``) and the TD class to the container; actions
# and events follow the same pattern with ids in this project's namespace.
AID_ACTION_DEFINITION = f"{BASE_URL}/aid/ActionDefinition/1/0"
AID_EVENT_DEFINITION = f"{BASE_URL}/aid/EventDefinition/1/0"
AID_WOT_NAME = f"{WOT_TD}name"

# ActionAffordance
AID_ACTION_INPUT = f"{WOT_TD}hasInputSchema"
AID_ACTION_OUTPUT = f"{WOT_TD}hasOutputSchema"
AID_WOT_SAFE = f"{WOT_TD}isSafe"
AID_WOT_IDEMPOTENT = f"{WOT_TD}isIdempotent"
AID_SYNCHRONOUS = f"{WOT_TD}isSynchronous"

# EventAffordance
AID_EVENT_SUBSCRIPTION = f"{WOT_TD}hasSubscriptionSchema"
AID_EVENT_DATA = f"{WOT_TD}hasNotificationSchema"
AID_EVENT_DATA_RESPONSE = f"{WOT_TD}hasNotificationResponseSchema"
AID_EVENT_CANCELLATION = f"{WOT_TD}hasCancellationSchema"

# DataSchema terms AID marks EXTERNAL (TD 1.1 context, jsonschema: prefix).
# readOnly/writeOnly apply to any data schema, not only to properties.
AID_WOT_READ_ONLY = f"{WOT_JSONSCHEMA}readOnly"
AID_WOT_WRITE_ONLY = f"{WOT_JSONSCHEMA}writeOnly"
AID_WOT_DATA_SCHEMA = f"{WOT_JSONSCHEMA}DataSchema"
AID_WOT_REQUIRED = f"{WOT_JSONSCHEMA}required"
AID_WOT_ONE_OF = f"{WOT_JSONSCHEMA}oneOf"
AID_WOT_ITEMS = f"{WOT_JSONSCHEMA}items"
AID_WOT_EXCLUSIVE_MINIMUM = f"{WOT_JSONSCHEMA}exclusiveMinimum"
AID_WOT_EXCLUSIVE_MAXIMUM = f"{WOT_JSONSCHEMA}exclusiveMaximum"
AID_WOT_MULTIPLE_OF = f"{WOT_JSONSCHEMA}multipleOf"
AID_WOT_PATTERN = f"{WOT_JSONSCHEMA}pattern"
AID_WOT_FORMAT = f"{WOT_JSONSCHEMA}format"
AID_WOT_CONTENT_ENCODING = f"{WOT_JSONSCHEMA}contentEncoding"
AID_WOT_CONTENT_MEDIA_TYPE = f"{WOT_JSONSCHEMA}contentMediaType"

# Form
AID_WOT_OPERATION_TYPE = f"{WOT_HCTL}hasOperationType"
AID_WOT_RESPONSE_FORM = f"{WOT_HCTL}returns"
AID_WOT_ADDITIONAL_RESPONSES = f"{WOT_HCTL}additionalReturns"
AID_WOT_ADDITIONAL_RESPONSE = f"{WOT_HCTL}AdditionalExpectedResponse"
AID_WOT_RESPONSE_SUCCESS = f"{WOT_HCTL}isSuccess"
AID_WOT_RESPONSE_SCHEMA = f"{WOT_HCTL}hasAdditionalOutputSchema"

# MQTT 5 request/reply. The WoT MQTT binding has no request/reply; the request
# carries this topic as its Response Topic and the reply echoes the request's
# Correlation Data.
AID_MQTT_RESPONSE_TOPIC = f"{BASE_URL}/aid/MqttResponseTopic/1/0"

# OPC UA. OPC 10101 v1.00 defines uav:componentOf but no event vocabulary, so
# the event terms live in this project's namespace: the EventType a
# subscription is filtered to (where clause, OfType) and, per data-schema
# property, the field's browse path relative to the event (select clause).
AID_OPCUA_COMPONENT_OF = "http://opcfoundation.org/UA/WoT-Binding/componentOf"
AID_OPCUA_EVENT_TYPE = f"{BASE_URL}/aid/OpcuaEventType/1/0"
AID_OPCUA_EVENT_FIELD = f"{BASE_URL}/aid/OpcuaEventField/1/0"

# ═══════════════════════════════════════════════════════════════════════════════
# AIMC — DMP extensions of the IDTA MappingConfiguration
# ═══════════════════════════════════════════════════════════════════════════════
# IDTA AIMC 2.0 defines Sources, Sinks, Transformation and DefaultPollingInterval.
# Everything an operation mapping adds lives in this project's namespace, so a
# standard AIMC consumer can tell the additions apart. Per invocation:
# command (IDTA Sources/Transformation/Sinks) → response (Response*).

# Response: members of the action's output, the Lua that builds the caller's
# reply, and the elements it writes.
AIMC_RESPONSE_SOURCES = f"{BASE_URL}/aimc/ResponseSources/1/0"
AIMC_RESPONSE_SOURCE = f"{BASE_URL}/aimc/ResponseSource/1/0"
AIMC_RESPONSE_SOURCE_REFERENCE = f"{BASE_URL}/aimc/ResponseSource/Source/1/0"
AIMC_RESPONSE_SOURCE_ID = f"{BASE_URL}/aimc/ResponseSource/SourceId/1/0"
AIMC_RESPONSE_TRANSFORMATION = f"{BASE_URL}/aimc/ResponseTransformation/1/0"
AIMC_RESPONSE_SINKS = f"{BASE_URL}/aimc/ResponseSinks/1/0"
AIMC_RESPONSE_SINK = f"{BASE_URL}/aimc/ResponseSink/1/0"
AIMC_RESPONSE_SINK_REFERENCE = f"{BASE_URL}/aimc/ResponseSink/Sink/1/0"
AIMC_RESPONSE_SINK_ID = f"{BASE_URL}/aimc/ResponseSink/SinkId/1/0"

# Which source updates execute an ordinary mapping.
# A Source's Evaluation: whether it triggers its mapping and how its value is obtained.
AIMC_EVALUATION = f"{BASE_URL}/aimc/Evaluation/1/0"
AIMC_EVALUATION_MODE = f"{BASE_URL}/aimc/Evaluation/Mode/1/0"

# How long a mapping an Operation triggers waits for the device's terminal reply.
AIMC_INVOCATION_TIMEOUT = f"{BASE_URL}/aimc/InvocationTimeout/1/0"

# ═══════════════════════════════════════════════════════════════════════════════
# TimeSeries — DMP profile of IDTA 02008 (TimeSeries SMCs in Variables)
# ═══════════════════════════════════════════════════════════════════════════════
# A TimeSeries SMC is shaped exactly like the IDTA submodel; only the SMC
# itself and the DMP additions (the LinkedSegment's write target, Record fields,
# groups and references) carry ids in this project's namespace.

# The InfluxDB 2 instance every LinkedSegment of this workspace points at.
INFLUX_ORIGIN = "http://influxdb:8086"
INFLUX_ORG = "ap2030"
INFLUX_BUCKET = "ap2030"

TS_COLLECTION = f"{BASE_URL}/variables/TimeSeries/1/0"
TS_RECORD_FIELD = f"{BASE_URL}/timeseries/RecordField/1/0"
TS_RECORD_GROUP = f"{BASE_URL}/timeseries/RecordGroup/1/0"
TS_RECORD_REFERENCE = f"{BASE_URL}/timeseries/RecordReference/1/0"
TS_RECORD_RANGE = f"{BASE_URL}/timeseries/RecordRange/1/0"
TS_RECORD_FILE = f"{BASE_URL}/timeseries/RecordFile/1/0"
TS_RECORD_TEXT = f"{BASE_URL}/timeseries/RecordText/1/0"
TS_INFLUX_TARGET = f"{BASE_URL}/timeseries/InfluxDb2Target/1/0"
TS_INFLUX_TARGET_BUCKET = f"{BASE_URL}/timeseries/InfluxDb2Target/Bucket/1/0"
TS_INFLUX_TARGET_MEASUREMENT = f"{BASE_URL}/timeseries/InfluxDb2Target/Measurement/1/0"
TS_INFLUX_TARGET_TAGS = f"{BASE_URL}/timeseries/InfluxDb2Target/Tags/1/0"
TS_INFLUX_TARGET_TAG = f"{BASE_URL}/timeseries/InfluxDb2Target/Tag/1/0"
TS_INFLUX_TARGET_WRITE_MODE = f"{BASE_URL}/timeseries/InfluxDb2Target/WriteMode/1/0"
