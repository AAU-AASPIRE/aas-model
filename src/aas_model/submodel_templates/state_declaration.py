"""
StateDeclaration submodel — the state variables of a subject, of what kind they are, and where they are kept.

A custom (non-IDTA) submodel. The state variables a capability's conditions and effects name are declared once, on
the AAS of their subject: what the asset reports (a station's occupation, a shuttle's position), and what only
effects change (a unit's content, who holds it).

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
observed one, and its meaning marks a derived one. A variable is about the AAS it is declared on, unless ``Subject``
names an element of it (a coordinate: a place). A product type declares the state of its units; a resource declares
its own. Whether a state variable has one value or a set, and what kind of value, is its meaning's (the lab
vocabulary's lab:cardinality and lab:valueType; vocabulary/lab-execution.ttl).

Structure::

    StateDeclaration
    ├── <variable>               StateVariable: what it means (supplemental semantic id, the lab vocabulary)
    │   ├── Subject              the element it is about, where not this AAS (a coordinate: a place)
    │   └── Initial              the value a new subject starts with (for a unit, written when its tree admits it, D35)
    └── Target                   SparqlTarget: the state store the values are written to

Two writers, never of the same variable: the DMP's mappings write observed variables, the behaviour tree applies
effects to asserted ones, in the Target.
"""

from __future__ import annotations

from typing import ClassVar, Dict, Optional, TypeAlias

from aas_pydantic import Property, ReferenceElement, Submodel, SubmodelElementCollection

from aas_model.constants import (
    SM_STATE_DECLARATION, STATE_SPARQL_TARGET, STATE_SPARQL_TARGET_ENDPOINT, STATE_SPARQL_TARGET_GRAPH,
    STATE_STORE_GRAPH, STATE_STORE_ORIGIN, STATE_VARIABLE, STATE_VARIABLE_INITIAL, STATE_VARIABLE_SUBJECT,
)


class StateVariableInitial(Property):
    id_short: str = "Initial"
    semantic_id: str = STATE_VARIABLE_INITIAL
    description: str = "The value a new subject starts with; without it the variable starts unknown."

StateVariableInitial_t: TypeAlias = StateVariableInitial  # a field may share the class's id_short


class StateVariableSubject(ReferenceElement):
    id_short: str = "Subject"
    semantic_id: str = STATE_VARIABLE_SUBJECT
    description: str = "The element this variable is about, where it is not the AAS it is declared on (a place)."

StateVariableSubject_t: TypeAlias = StateVariableSubject  # a field may share the class's id_short


class StateVariable(SubmodelElementCollection):
    """One state variable of the subject. What it means rides as a supplemental semantic id."""
    semantic_id: str = STATE_VARIABLE
    Subject: Optional[StateVariableSubject_t] = None
    Initial: Optional[StateVariableInitial_t] = None


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


class StateDeclaration(Submodel):
    semantic_id: str = SM_STATE_DECLARATION
    description: str = "The state variables of this subject, of which kind each is, and the store they are kept in."
    VERSION: ClassVar[str] = "1"
    REVISION: ClassVar[str] = "0"

    variable: Dict[str, StateVariable] = {}
    Target: SparqlTarget_t = SparqlTarget()


StateVariable.model_rebuild()
SparqlTarget.model_rebuild()
StateDeclaration.model_rebuild()
