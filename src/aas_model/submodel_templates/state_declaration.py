"""
StateDeclaration submodel — the state of a subject that no data point observes, and where it is kept.

A custom (non-IDTA) submodel. The state variables a capability's conditions and effects name are declared once, on
the AAS of their subject, as a time series is: observed resource state is a series of Variables; state only effects
change (a station's occupancy where it reports none, a unit's content) is declared here. A product type declares the
state of its units; a resource declares its own. Whether a state variable has one value or a set, and what kind of
value, is its meaning's (the lab vocabulary's lab:cardinality and lab:valueType; vocabulary/lab-execution.ttl).

Structure::

    StateDeclaration
    ├── <variable>               StateVariable: what it means (supplemental semantic id, the lab vocabulary)
    │   ├── Initial              the value a new subject starts with (a unit entering its batch)
    │   └── Observed             the data point it is, where a sensor reports it after all
    └── Target                   SparqlTarget: the state store the DMP writes the values to

The DMP is the only writer: it applies effects to these variables and writes them to the Target. Whether a
property holds one value or a set of them is said by the vocabulary (``owl:FunctionalProperty``), not here.
"""

from __future__ import annotations

from typing import ClassVar, Dict, Optional, TypeAlias

from aas_pydantic import Property, ReferenceElement, Submodel, SubmodelElementCollection

from aas_model.constants import (
    SM_STATE_DECLARATION, STATE_SPARQL_TARGET, STATE_SPARQL_TARGET_ENDPOINT, STATE_SPARQL_TARGET_GRAPH,
    STATE_STORE_GRAPH, STATE_STORE_ORIGIN, STATE_VARIABLE, STATE_VARIABLE_INITIAL, STATE_VARIABLE_OBSERVED,
)


class StateVariableInitial(Property):
    id_short: str = "Initial"
    semantic_id: str = STATE_VARIABLE_INITIAL
    description: str = "The value a new subject starts with; without it the variable starts unknown."

StateVariableInitial_t: TypeAlias = StateVariableInitial  # a field may share the class's id_short


class StateVariableObserved(ReferenceElement):
    id_short: str = "Observed"
    semantic_id: str = STATE_VARIABLE_OBSERVED
    description: str = "The data point that reports this variable (a Record field of a Variables series)."

StateVariableObserved_t: TypeAlias = StateVariableObserved  # a field may share the class's id_short


class StateVariable(SubmodelElementCollection):
    """One state variable of the subject. What it means rides as a supplemental semantic id."""
    semantic_id: str = STATE_VARIABLE
    Initial: Optional[StateVariableInitial_t] = None
    Observed: Optional[StateVariableObserved_t] = None


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
    description: str = "The state variables of this subject that effects change, and the store they are kept in."
    VERSION: ClassVar[str] = "1"
    REVISION: ClassVar[str] = "0"

    variable: Dict[str, StateVariable] = {}
    Target: SparqlTarget_t = SparqlTarget()


StateVariable.model_rebuild()
SparqlTarget.model_rebuild()
StateDeclaration.model_rebuild()
