"""The filling module and the 2 mL vial: the execution model on real instances, built together as one line."""

from __future__ import annotations

import json

import pytest
from basyx.aas import model

from aas_model import build_from_model
from aas_model.constants import EXECUTION_DURING, EXECUTION_EFFECT, LAB
from aas_model.product_instances import PRODUCT_FACTORIES
from aas_model.resource_instances.modules import MODULE_FACTORIES

FACTORIES = {**MODULE_FACTORIES, **PRODUCT_FACTORIES}


def _store() -> model.DictIdentifiableStore:
    """Every AAS of the example built into one store, so references across them resolve."""
    store = model.DictIdentifiableStore()
    for factory in FACTORIES.values():
        for identifiable in build_from_model(factory()):
            store.add(identifiable)
    return store


def _references(element):
    if isinstance(element, model.ReferenceElement) and isinstance(element.value, model.ModelReference):
        yield element
    if isinstance(element, model.SubmodelElementCollection):
        for child in element.value:
            yield from _references(child)


def _submodel(store, aas_id: str, id_short: str) -> model.Submodel:
    return store.get_item(f"{aas_id}/submodels/{id_short}")


@pytest.mark.parametrize("name", sorted(FACTORIES))
def test_each_instance_reads_back_from_its_json(name):
    made = FACTORIES[name]()
    again = type(made).model_validate_json(made.model_dump_json())
    assert json.loads(again.model_dump_json()) == json.loads(made.model_dump_json())


def test_every_reference_of_the_modules_capabilities_resolves_in_the_line():
    from aas_model.resource_instances.modules.filling_module import MODULE

    store = _store()
    description = _submodel(store, MODULE, "CapabilityDescription")
    references = [ref for capability_set in description.submodel_element for container in capability_set.value
                  for ref in _references(container)]
    unresolved = [ref for ref in references if ref.value.resolve(store) is None]
    assert len(references) > 30 and not unresolved


def test_the_components_capabilities_say_what_the_filling_module_does():
    from aas_model.resource_instances.modules.filling_module import MODULE

    description = _submodel(_store(), MODULE, "CapabilityDescription")
    dosing = description.get_referable(["Pump", "Dosing", "Execution"])
    assert dosing.get_referable(["Effects", "During"]).semantic_id.key[0].value == EXECUTION_DURING
    during = dosing.get_referable(["Effects", "During", "Term_00"])
    assert during.semantic_id.key[0].value == EXECUTION_EFFECT
    assert during.supplemental_semantic_id[0].key[0].value == f"{LAB}OutletImmersion"
    uses = {use.id_short: [r.key[0].value for r in use.supplemental_semantic_id] for use in during.get_referable("Uses")}
    assert uses == {"Position": [f"{LAB}Position"], "NestPosition": [], "InnerBottomHeight": [f"{LAB}InnerBottomHeight"],
                    "ContentVolume": [f"{LAB}ContentVolume"], "InnerDiameter": [f"{LAB}InnerDiameter"]}
    lock = description.get_referable(["Scale", "Weighing", "Execution", "Conditions", "Invariant", "Term_00"])
    assert lock.get_referable("Operator").value == "unchanged"


def test_the_offered_filling_is_derived_and_bound_to_its_skill():
    from aas_model.resource_instances.modules.filling_module import MODULE

    store = _store()
    filling = _submodel(store, MODULE, "CapabilityDescription").get_referable(
        ["OfferedCapabilities", "Filling", "Execution"])
    unit = filling.get_referable(["Subjects", "Unit", "Binding"]).value.resolve(store)
    assert unit.id_short == "Unit" and unit.semantic_id.key[0].value.endswith("/OperationVariable/Subject/1/0")
    end = filling.get_referable(["Effects", "End"])
    assert {term.semantic_id.key[0].value for term in end} == {EXECUTION_EFFECT}
    rate = end.get_referable(["Term_00", "Rate"]).value.resolve(store)
    assert rate.value == "1.0"                                        # the step's constant flow rate
    derived = filling.get_referable(["Provenance"])
    assert {d.id_short for d in derived.value if d.id_short != "Fingerprint"} == {
        "Positioning", "Dosing", "Weighing", "Steps"}


def test_the_vial_declares_what_the_module_reads_of_its_units():
    """Every property of the Unit the module's formulas and terms name is declared by the vial."""
    from aas_model.product_instances.vial_2ml import AAS_ID
    from aas_model.resource_instances.modules import filling_module

    declared = {variable.supplemental_semantic_ids[0] for variable in
                PRODUCT_FACTORIES["vial2mL"]().state_declaration.variable.values()}
    named = set()
    module = filling_module()
    for capability_set in module.capability_description.CapabilitySet.values():
        for container in capability_set.CapabilityContainer.values():
            dumped = json.loads(container.Execution.model_dump_json()) if container.Execution else {}
            named |= _unit_properties(dumped)
    assert named and named <= declared, named - declared
    store = _store()
    assert _submodel(store, AAS_ID, "StateDeclaration") is not None


def _unit_properties(node) -> set:
    """The meanings of what a term (its Subject) or a Use (its value) says about the subject named Unit."""
    found = set()
    if isinstance(node, dict):
        reference = (node.get("Subject") or {}).get("value") if "Subject" in node else node.get("value")
        keys = reference.get("key") if isinstance(reference, dict) else None
        if keys and keys[-1]["value"] == "Unit":
            found |= set(node.get("supplemental_semantic_ids") or ())
        for child in node.values():
            found |= _unit_properties(child)
    elif isinstance(node, list):
        for child in node:
            found |= _unit_properties(child)
    return found
