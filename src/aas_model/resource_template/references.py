"""References into a resource's own submodels, one function per path, and the idShorts of its interfaces.

A reference's shape follows where its element sits in the AAS, not the element's class, so the paths are
kept here in one place. The submodel ids (``constants``) are resolved by the id injector.
"""

from __future__ import annotations

from aas_pydantic import Key, ModelReference

from aas_model.constants import (
    AID_SUBMODEL_ID, CAPABILITIES_SUBMODEL_ID, CCI_SUBMODEL_ID, VARIABLES_SUBMODEL_ID,
)

# The idShorts of an asset's one interface per protocol. No protocol is a default: every reference into the AID
# names its interface.
MQTT_INTERFACE = "interface_mqtt"
OPCUA_INTERFACE = "interface_opcua"


def _collections(*names: str) -> tuple[Key, ...]:
    return tuple(Key(type_="SubmodelElementCollection", value=name) for name in names)


def affordance_ref(interface: str, kind: str, name: str) -> ModelReference:
    """The affordance ``name`` of ``interface`` in the AID; ``kind`` is ``properties``, ``actions`` or
    ``events``."""
    return ModelReference(key=(Key(type_="Submodel", value=AID_SUBMODEL_ID),
                               *_collections(interface, "InteractionMetadata", kind, name)))


def action_member_ref(interface: str, action: str, schema: str, *members: str) -> ModelReference:
    """The ``input`` or ``output`` DataSchema of an action, or one of its object members
    (``.../output/properties/State``)."""
    keys = affordance_ref(interface, "actions", action).key + _collections(schema)
    for member in members:
        keys += _collections("properties", member)
    return ModelReference(key=keys)


def skill_ref(name: str) -> ModelReference:
    """The skill ``name`` in the ControlComponentInstance."""
    return ModelReference(key=(Key(type_="Submodel", value=CCI_SUBMODEL_ID), *_collections("Skills", name)))


def operation_ref(skill: str) -> ModelReference:
    """A skill's delegated Operation; AIMC Sources and response Sinks address its variables
    (:func:`operation_variable_ref`), not the Operation itself."""
    return ModelReference(key=skill_ref(skill).key + (Key(type_="Operation", value="operation"),))


def operation_variable_ref(skill: str, variable: str, element_type: str = "Property") -> ModelReference:
    """One variable of a skill's delegated Operation."""
    return ModelReference(key=operation_ref(skill).key + (Key(type_=element_type, value=variable),))


def variable_ref(*path: str) -> ModelReference:
    """A Property in a group of Variables, e.g. ``variable_ref("Measurements", "Image")``. The key types are what
    the Variables submodel stores: the resolver checks reference key types against the repository."""
    return ModelReference(key=(Key(type_="Submodel", value=VARIABLES_SUBMODEL_ID), *_collections(*path[:-1]),
                               Key(type_="Property", value=path[-1])))


def state_variable_ref(name: str) -> ModelReference:
    """A state variable of the resource's Knowledge (``Variables/Knowledge/<name>``): the sink of a mapping that keeps
    it in the state store (observed state, D36), as a series segment is the sink of one that keeps a time series."""
    return ModelReference(key=(Key(type_="Submodel", value=VARIABLES_SUBMODEL_ID),
                               Key(type_="SubmodelElementCollection", value="Knowledge"),
                               Key(type_="SubmodelElementCollection", value=name)))


def series_segment_ref(group: str, series: str, segment: str = "Live") -> ModelReference:
    """A TimeSeries LinkedSegment in Variables, e.g. ``.../Variables/State/Station/Segments/Live``: the target
    of a history Sink."""
    return ModelReference(key=(Key(type_="Submodel", value=VARIABLES_SUBMODEL_ID),
                               *_collections(group, series, "Segments", segment)))


def capability_ref(capability_set: str, name: str) -> ModelReference:
    """The Capability ``name`` of a CapabilitySet in the CapabilityDescription."""
    return ModelReference(key=(Key(type_="Submodel", value=CAPABILITIES_SUBMODEL_ID),
                               *_collections(capability_set, name), Key(type_="Capability", value="Capability")))


def capability_property_ref(capability_set: str, name: str, prop: str) -> ModelReference:
    """The Property ``prop`` of a capability, in its PropertyContainer of the same name
    (``.../<name>/PropertySet/<prop>/<prop>``): a named value or a characteristic a condition or effect uses."""
    return ModelReference(key=(Key(type_="Submodel", value=CAPABILITIES_SUBMODEL_ID),
                               *_collections(capability_set, name, "PropertySet", prop),
                               Key(type_="Property", value=prop)))


def subject_ref(capability_set: str, name: str, index: int) -> ModelReference:
    """A Subject of a capability, by its place in the list (``.../<name>/CapabilityRelations/Subjects/<index>``):
    what a condition or effect is about, or the value it compares with."""
    return ModelReference(key=(Key(type_="Submodel", value=CAPABILITIES_SUBMODEL_ID),
                               *_collections(capability_set, name, "CapabilityRelations"),
                               Key(type_="SubmodelElementList", value="Subjects"),
                               Key(type_="ReferenceElement", value=str(index))))
