"""
Knowledge — the SMC of an asset's Variables that declares its state as the knowledge graph keeps it.

A custom (non-IDTA) collection beside the time series of ``Variables`` (``variables.py``), and kept like one: a
time series (``TimeSeriesCollection``) states the fields of its records and the InfluxDB they are written to, the
Knowledge states the statements kept about the asset (each a state variable: a predicate of the lab vocabulary about a
subject) and the state store they are written to. A mapping sinks into a variable as it sinks into a series segment.

The state variables a capability's conditions and effects name are declared once, in the Knowledge of their
subject's AAS: what the asset reports (a station's occupation, a shuttle's position), and what only effects change (a
unit's content, who holds it). A product type has a Variables submodel for its Knowledge alone.

A variable is one of three kinds (plan, D36):

- **asserted**: only effects change it; the behaviour tree writes it when it applies the effects of an action it ran.
  Asserted state is about the unit (its content, who holds it); a tree writes asserted state about a shared resource
  only while it holds that resource's occupation;
- **observed**, a *linked projection*: a mapping of the AAS's AIMC sinks into it, as a mapping sinks into a time
  series segment. The state store is one more sink: the mapping's Lua returns the variable's value under the sink's
  SinkId, beside what it returns for its other sinks (a station's process queue into the series row, and the unit at
  its head into OccupiedBy), and its Sources are the elements the value is linked to (a data point, or static
  elements: a Coordinate and the coordinates up its ``RelativeTo`` chain, composed into the line's frame). Each run
  sets every variable the mapping sinks into; one it returns no value for has none. An effect on an observed
  variable is not written: the tree waits until the store shows it;
- **derived**: its meaning says so (``lab:derived`` in the vocabulary: a carrier's ``lab:Location`` is the place
  whose projected pose is within tolerance of its own). It is never stored: queries compute it; an effect on it is
  what the tree waits for, as for an observed one.

Which kind a variable is, is stated where it is decided: no mapping sinks into an asserted one, exactly one into an
observed one, and its meaning marks a derived one. A resource's variable names its ``Subject`` explicitly: its own AAS,
or an element of it (a coordinate: a place); a product type declares the state of its units, and its variables name
none. Whether a state variable has one value or a set, and what kind of value, is its meaning's (the lab vocabulary's
lab:cardinality and lab:valueType; vocabulary/lab-execution.ttl), written onto the variable so that no consumer
reads the vocabulary at run time.

A subject's IRI in the state store: an AAS is its id; an element is ``<submodel id>#<idShortPath>`` (list items by
``[index]``); a unit is the ``urn:uuid:`` IRI its tree minted.

Structure::

    Variables
    └── Knowledge
        ├── <variable>           StateVariable: what it means (supplemental semantic id, the lab vocabulary)
        │   ├── Subject          who it is about: the resource's own AAS, or an element of it (a coordinate: a place);
        │   │                    none on a product type, whose variables are about each unit
        │   ├── ValueType        the meaning's lab:valueType (number, boolean, string, reference), from the vocabulary
        │   ├── Cardinality      the meaning's lab:cardinality (single, set), from the vocabulary
        │   └── Initial          the value a new subject starts with (for a unit, written when its tree admits it, D35)
        └── Target               SparqlTarget: the state store the values are written to

Two writers, never of the same variable: the DMP's mappings write observed variables, the behaviour tree applies
effects to asserted ones, in the Target.
"""

from __future__ import annotations

from typing import Dict, Optional, TypeAlias

from aas_pydantic import Key, ModelReference, Property, ReferenceElement, SubmodelElementCollection
from aas_pydantic.aas_model import AasIdString
from pydantic import model_validator

from aas_model.constants import (
    STATE_SPARQL_TARGET, STATE_SPARQL_TARGET_ENDPOINT, STATE_SPARQL_TARGET_GRAPH,
    STATE_STORE_GRAPH, STATE_STORE_ORIGIN, STATE_VARIABLE, STATE_VARIABLE_CARDINALITY, STATE_VARIABLE_INITIAL,
    STATE_VARIABLE_SUBJECT, STATE_VARIABLE_VALUE_TYPE, VARIABLES_KNOWLEDGE,
)
from aas_model.state_vocabulary import STATE_PROPERTIES


class StateVariableInitial(Property):
    id_short: str = "Initial"
    semantic_id: str = STATE_VARIABLE_INITIAL
    description: str = "The value a new subject starts with; without it the variable starts unknown."

StateVariableInitial_t: TypeAlias = StateVariableInitial  # a field may share the class's id_short


class StateVariableSubject(ReferenceElement):
    id_short: str = "Subject"
    semantic_id: str = STATE_VARIABLE_SUBJECT
    description: str = ("Who the variable is about: the resource's own AAS, or an element of it (a place). A product "
                        "type's variables are about each of its units and have none.")

StateVariableSubject_t: TypeAlias = StateVariableSubject  # a field may share the class's id_short


class StateVariableValueType(Property):
    """The meaning's value type in the vocabulary (lab:valueType): number, boolean, string or reference."""
    id_short: str = "ValueType"
    semantic_id: str = STATE_VARIABLE_VALUE_TYPE
    value_type: str = "xs:string"

StateVariableValueType_t: TypeAlias = StateVariableValueType  # a field may share the class's id_short


class StateVariableCardinality(Property):
    """The meaning's cardinality in the vocabulary (lab:cardinality): single or set."""
    id_short: str = "Cardinality"
    semantic_id: str = STATE_VARIABLE_CARDINALITY
    value_type: str = "xs:string"

StateVariableCardinality_t: TypeAlias = StateVariableCardinality  # a field may share the class's id_short


class StateVariable(SubmodelElementCollection):
    """One state variable of the subject. What it means rides as a supplemental semantic id; its value type and
    cardinality are the meaning's in the vocabulary, written here from it (``state_vocabulary``)."""
    semantic_id: str = STATE_VARIABLE
    Subject: Optional[StateVariableSubject_t] = None
    ValueType: Optional[StateVariableValueType_t] = None
    Cardinality: Optional[StateVariableCardinality_t] = None
    Initial: Optional[StateVariableInitial_t] = None

    @model_validator(mode="after")
    def _typed_as_its_meaning(self):
        meaning = self.supplemental_semantic_ids[0] if self.supplemental_semantic_ids else None
        if meaning in STATE_PROPERTIES:
            value_type, cardinality = STATE_PROPERTIES[meaning]
            if self.ValueType is None:
                self.ValueType = StateVariableValueType(value=value_type)
            if self.Cardinality is None:
                self.Cardinality = StateVariableCardinality(value=cardinality)
        return self

    @classmethod
    def own(cls, meaning: str, **kwargs) -> "StateVariable":
        """A variable about the resource whose AAS declares it."""
        return cls(supplemental_semantic_ids=[meaning], Subject=StateVariableSubject(
            value=ModelReference(key=(Key(type_="AssetAdministrationShell", value="{aas_id}"),))), **kwargs)

    @classmethod
    def about(cls, meaning: str, element: ModelReference, **kwargs) -> "StateVariable":
        """A variable about an element of the resource's AAS (a place: a coordinate)."""
        return cls(supplemental_semantic_ids=[meaning], Subject=StateVariableSubject(value=element), **kwargs)


class SparqlEndpoint(Property):
    id_short: str = "Endpoint"
    semantic_id: str = STATE_SPARQL_TARGET_ENDPOINT
    value: str = STATE_STORE_ORIGIN

SparqlEndpoint_t: TypeAlias = SparqlEndpoint  # a field may share the class's id_short


class SparqlGraph(Property):
    id_short: str = "Graph"
    semantic_id: str = STATE_SPARQL_TARGET_GRAPH
    value: str = STATE_STORE_GRAPH

SparqlGraph_t: TypeAlias = SparqlGraph  # a field may share the class's id_short


class SparqlTarget(SubmodelElementCollection):
    """The state store the values go to: a SPARQL 1.1 endpoint and the named graph of the current state."""
    id_short: str = "Target"
    semantic_id: str = STATE_SPARQL_TARGET
    Endpoint: SparqlEndpoint_t = SparqlEndpoint()
    Graph: SparqlGraph_t = SparqlGraph()

SparqlTarget_t: TypeAlias = SparqlTarget  # a field may share the class's id_short


class Knowledge(SubmodelElementCollection):
    """The state variables of this asset (or, on a product type, of each of its units) and the store they are kept in."""
    id_short: AasIdString = "Knowledge"
    semantic_id: str = VARIABLES_KNOWLEDGE
    description: str = "The state kept about this asset in the knowledge graph: its variables, and the store they are kept in."

    variable: Dict[str, StateVariable] = {}
    Target: SparqlTarget_t = SparqlTarget()


StateVariable.model_rebuild()
SparqlTarget.model_rebuild()
Knowledge_t: TypeAlias = Knowledge  # a field may share the class's id_short

Knowledge.model_rebuild()
