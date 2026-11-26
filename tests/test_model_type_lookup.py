"""How a dump's modelType finds its class again: by qualified name, and an older bare name only where it is
unambiguous (aas_pydantic.aas_model._class_named)."""

from __future__ import annotations

import importlib
import json
import pkgutil

import pytest

import aas_model
from aas_pydantic import DynamicSubmodelElementCollection, Property, SubmodelElement
from aas_pydantic.aas_model import (
    AmbiguousModelTypeError, _ELEMENT_CLASS_REGISTRY, _ELEMENT_CLASSES_BY_NAME, coerce_submodel_element,
)
from aas_pydantic.submodel_templates.hierarchical_structures import SameAs as HierarchySameAs
from aas_model.submodel_templates.capability_description import SameAs as CapabilitySameAs
from aas_model.submodel_templates.execution import EndTerms, StateEffect

for _module in pkgutil.walk_packages(aas_model.__path__, "aas_model."):
    importlib.import_module(_module.name)


def _round_trip(element: SubmodelElement) -> SubmodelElement:
    """Through a container whose field names no class: only the dump's modelType tells."""
    holder = DynamicSubmodelElementCollection(id_short="Holder", value={element.id_short: element})
    return DynamicSubmodelElementCollection.model_validate_json(holder.model_dump_json()).value[element.id_short]


def _constructible():
    """Every class whose default instance reads back as itself directly: the lookup is what is tested, not
    the class (one with required children, or a default its own validator refuses, is left out)."""
    for name, cls in sorted(_ELEMENT_CLASS_REGISTRY.items()):
        try:
            element = cls(id_short="Element")
            cls.model_validate_json(element.model_dump_json())
        except Exception:
            continue
        yield name, element


def test_dumps_name_their_class_qualified():
    end = EndTerms(term={"Term_00": StateEffect()})
    dumped = json.loads(end.model_dump_json())
    assert dumped["term"]["Term_00"]["modelType"] == "aas_model.submodel_templates.execution:StateEffect"


def test_every_class_comes_back_as_itself_from_a_generic_container():
    checked = 0
    for name, element in _constructible():
        assert type(_round_trip(element)) is type(element), name
        checked += 1
    assert checked > 300


def test_classes_sharing_a_bare_name_come_back_apart():
    shared = [classes for classes in _ELEMENT_CLASSES_BY_NAME.values() if len(set(classes)) > 1]
    assert shared                              # the package does repeat names (SameAs, Start, Type, ...)
    for cls in (HierarchySameAs, CapabilitySameAs):
        assert type(_round_trip(cls(id_short="SameAs"))) is cls


def test_an_older_dump_with_a_unique_bare_name_still_loads():
    dumped = {**StateEffect().model_dump(), "modelType": "StateEffect"}
    assert type(coerce_submodel_element(dumped)) is StateEffect


def test_an_older_dump_with_a_shared_bare_name_is_told_apart_by_its_semantic_id():
    dumped = {**CapabilitySameAs(id_short="SameAs").model_dump(), "modelType": "SameAs"}
    assert type(coerce_submodel_element(dumped)) is CapabilitySameAs


def test_an_older_dump_that_stays_ambiguous_is_an_error_not_a_guess():
    dumped = {**CapabilitySameAs(id_short="SameAs").model_dump(), "modelType": "SameAs", "semantic_id": ""}
    with pytest.raises(AmbiguousModelTypeError):
        coerce_submodel_element(dumped)


def test_aas_json_metamodel_types_still_resolve():
    assert type(coerce_submodel_element({"modelType": "Property", "id_short": "P", "value": "1"})) is Property
