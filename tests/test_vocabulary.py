"""The proposed vocabulary additions (vocabulary/lab-execution.ttl) give every state property the example line uses a
cardinality and a value type (D14: a state property without a cardinality is an error)."""

from __future__ import annotations

from pathlib import Path

import pytest
from basyx.aas import model

from aas_model import build_from_model
from aas_model.constants import EXECUTION_CONDITION, EXECUTION_EFFECT, EXECUTION_FORMULA_USE, STATE_VARIABLE

rdflib = pytest.importorskip("rdflib")

VOCABULARY = Path(__file__).resolve().parents[1] / "vocabulary" / "lab-execution.ttl"
LAB = rdflib.Namespace("https://smartproductionlab.aau.dk/semantics/")


def _state_properties() -> set:
    """The meanings of the state properties the example line's terms, formulas and declarations name."""
    from aas_model.batch_instances import BATCH_FACTORIES
    from aas_model.product_instances import PRODUCT_FACTORIES
    from aas_model.resource_instances import RESOURCE_FACTORIES
    from aas_model.resource_instances.modules import MODULE_FACTORIES

    factories = [*MODULE_FACTORIES.values(), *PRODUCT_FACTORIES.values(), *BATCH_FACTORIES.values(),
                 RESOURCE_FACTORIES["planarShuttle1"], RESOURCE_FACTORIES["imaDispensing"]]
    kinds = {EXECUTION_CONDITION, EXECUTION_EFFECT, EXECUTION_FORMULA_USE, STATE_VARIABLE}
    found = set()

    def walk(element):
        if element.semantic_id and element.semantic_id.key[0].value in kinds and element.supplemental_semantic_id:
            found.add(element.supplemental_semantic_id[0].key[0].value)
        if isinstance(element, (model.SubmodelElementCollection, model.SubmodelElementList)):
            for child in element.value:
                walk(child)

    for factory in factories:
        for identifiable in build_from_model(factory()):
            if isinstance(identifiable, model.Submodel):
                for element in identifiable.submodel_element:
                    walk(element)
    return found


def test_every_state_property_the_line_uses_has_a_cardinality_and_a_value_type():
    graph = rdflib.Graph().parse(VOCABULARY)
    used = _state_properties()
    assert len(used) >= 14
    missing = sorted(p for p in used if (rdflib.URIRef(p), LAB.cardinality, None) not in graph)
    assert not missing, f"no lab:cardinality: {missing}"
    untyped = sorted(p for p in used if (rdflib.URIRef(p), LAB.valueType, None) not in graph)
    assert not untyped, f"no lab:valueType: {untyped}"
    assert {str(o) for _, _, o in graph.triples((None, LAB.cardinality, None))} <= {"single", "set"}


def test_custody_and_place_are_references_and_occupying_is_named_as_its_skill():
    graph = rdflib.Graph().parse(VOCABULARY)
    for prop in (LAB.HeldBy, LAB.Location):
        assert (prop, LAB.valueType, rdflib.Literal("reference")) in graph
    assert (LAB.Occupying, rdflib.OWL.equivalentClass, LAB.Receiving) in graph
