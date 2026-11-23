"""The filling module and the 2 mL vial: the execution model on real instances, built together as one line."""

from __future__ import annotations

import json
import math

import pytest
from basyx.aas import model

from aas_model import build_from_model
from aas_model.constants import (
    EXECUTION_AND, EXECUTION_CONDITION, EXECUTION_DURING, EXECUTION_EFFECT, LAB,
)
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


def test_every_reference_of_the_capabilities_resolves_in_the_line():
    """The module's and the components' capabilities, which name each other across their AASs."""
    from aas_model.resource_instances.modules.filling_module import LINEAR_AXIS, MODULE, PUMP, SCALE

    store = _store()
    references = [ref for aas_id in (MODULE, LINEAR_AXIS, PUMP, SCALE)
                  for capability_set in _submodel(store, aas_id, "CapabilityDescription").submodel_element
                  for container in capability_set.value for ref in _references(container)]
    unresolved = [ref for ref in references if ref.value.resolve(store) is None]
    assert len(references) > 40 and not unresolved


def test_each_component_offers_its_capability_and_the_module_specializes_it():
    from aas_model.resource_instances.modules.filling_module import LINEAR_AXIS, MODULE, PUMP, SCALE

    store = _store()
    for aas_id, name in ((LINEAR_AXIS, "Positioning"), (PUMP, "Dosing"), (SCALE, "Weighing")):
        own = _submodel(store, aas_id, "CapabilityDescription").get_referable(["AuxiliaryCapabilities", name])
        realized = own.get_referable(["CapabilityRelations", "RealizedBy"]).second.resolve(store)
        assert realized.id_short in ("MoveAxis", "Dispense", "Weigh")
        here = _submodel(store, MODULE, "CapabilityDescription").get_referable(["AuxiliaryCapabilities", name])
        general = here.get_referable(["CapabilityRelations", "GeneralizedBySet", "GeneralizedBy"]).second
        assert general.resolve(store) is own.get_referable("Capability")
    assert {s.id_short for s in _submodel(store, MODULE, "CapabilityDescription").submodel_element} == {
        "OfferedCapabilities", "AuxiliaryCapabilities"}


def test_the_components_capabilities_say_what_the_filling_module_does():
    from aas_model.resource_instances.modules.filling_module import MODULE

    description = _submodel(_store(), MODULE, "CapabilityDescription")
    dosing = description.get_referable(["AuxiliaryCapabilities", "Dosing", "Execution"])
    assert dosing.get_referable(["Effects", "During"]).semantic_id.key[0].value == EXECUTION_DURING
    during = dosing.get_referable(["Effects", "During", "Term_00"])
    assert during.semantic_id.key[0].value == EXECUTION_EFFECT
    assert during.supplemental_semantic_id[0].key[0].value == f"{LAB}OutletImmersion"
    uses = {use.id_short: [r.key[0].value for r in use.supplemental_semantic_id] for use in during.get_referable("Uses")}
    assert uses == {"Position": [f"{LAB}Position"], "NestPosition": [], "InnerBottomHeight": [f"{LAB}InnerBottomHeight"],
                    "ContentVolume": [f"{LAB}ContentVolume"], "InnerDiameter": [f"{LAB}InnerDiameter"]}
    lock = description.get_referable(["AuxiliaryCapabilities", "Weighing", "Execution", "Conditions", "Invariant",
                                      "Term_00"])
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
        "Positioning", "Dosing", "Weighing", "AxisPositioning", "PumpDosing", "ScaleWeighing", "Steps"}


def test_the_vial_declares_what_the_module_reads_of_its_units():
    """Every property of the Unit the module's formulas and terms name is declared by the vial."""
    from aas_model.product_instances.vial_2ml import AAS_ID

    declared = {variable.supplemental_semantic_ids[0] for variable in
                PRODUCT_FACTORIES["vial2mL"]().state_declaration.variable.values()}
    named = set()
    descriptions = [made.capability_description for made in (factory() for factory in MODULE_FACTORIES.values())]
    for capability_set in (s for description in descriptions for s in description.CapabilitySet.values()):
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


# ── A module's capability specializes its components' and never widens them ─────────────────────────────────────

SPECIALIZES = ("/CapabilityGeneralizedBy/", "/CapabilityComposedOf/")   # the relations whose second is more general


def _semantic_id(element) -> str:
    return element.semantic_id.key[0].value if element.semantic_id else ""


def _meaning(element) -> str | None:
    return element.supplemental_semantic_id[0].key[0].value if element.supplemental_semantic_id else None


def _stated(container) -> dict:
    """A capability container's properties as meaning -> (lowest, highest); a list of choices is left out."""
    found = {}
    properties = container.get_referable("PropertySet") if "PropertySet" in {e.id_short for e in container.value} \
        else ()
    for property_container in properties:
        value = property_container.get_referable("Value")
        if isinstance(value, model.Range):
            found[_meaning(value)] = (float(value.min), float(value.max))
        elif isinstance(value, model.Property):
            found[_meaning(value)] = (float(value.value), float(value.value))
    return found


def _more_general(store, container) -> list:
    """The capability containers a container specializes or is composed of, all the way up."""
    found, relations = [], container.get_referable("CapabilityRelations")
    stack = list(relations.value)
    while stack:
        element = stack.pop()
        if isinstance(element, model.SubmodelElementCollection):
            stack.extend(element.value)
        elif isinstance(element, model.RelationshipElement) and any(s in _semantic_id(element) for s in SPECIALIZES):
            general = element.second.resolve(store).parent
            found += [general, *_more_general(store, general)]
    return found


def _module_containers(store):
    from aas_model.resource_instances.modules.filling_module import MODULE

    return [container for capability_set in _submodel(store, MODULE, "CapabilityDescription").submodel_element
            for container in capability_set.value]


def test_the_module_states_its_capabilities_within_what_their_components_offer():
    """A value the module states for a property is one the capability it specializes, or is made of, allows."""
    store, compared = _store(), []
    for container in _module_containers(store):
        for general in _more_general(store, container):
            offered = _stated(general)
            for meaning, (low, high) in _stated(container).items():
                if meaning in offered:
                    compared.append((container.id_short, meaning))
                    assert offered[meaning][0] <= low and high <= offered[meaning][1], (container.id_short, meaning)
    assert (("Filling", f"{LAB}FillVolume")) in compared


def _terms(execution, section: str):
    """The top-level terms of a section (through And), each with its meaning and what it bounds."""
    stack = list(execution.get_referable(section.split("/")).value) if _has(execution, section) else []
    while stack:
        term = stack.pop()
        if _semantic_id(term) == EXECUTION_AND:
            stack.extend(term.value)
        elif _semantic_id(term) in (EXECUTION_CONDITION, EXECUTION_EFFECT):
            yield term


def _has(element, path: str) -> bool:
    try:
        element.get_referable(path.split("/"))
        return True
    except KeyError:
        return False


def _bound(term) -> tuple:
    """What a term holds of its subject: its operator and value, reference or formula."""
    named = {e.id_short: e for e in term.value}
    target = named.get("Value") or named.get("Formula") or named.get("ValueReference")
    return named["Operator"].value, target.value if isinstance(target, model.Property) else str(target.value) \
        if target else None


def test_the_module_adds_to_its_components_executions_and_never_restates_them_otherwise():
    """What the component's Execution says of a property holds in the module as it is: restated, it is the same."""
    store, specialized = _store(), 0
    for container in _module_containers(store):
        relations = container.get_referable("CapabilityRelations")
        if not _has(relations, "GeneralizedBySet"):
            continue
        general = relations.get_referable(["GeneralizedBySet", "GeneralizedBy"]).second.resolve(store).parent
        realized = [c.get_referable(["CapabilityRelations", "RealizedBy"]).second.resolve(store)
                    for c in (container, general)]
        assert realized[0] is realized[1], container.id_short      # carried out by the same primitive
        specialized += 1
        for section in ("Conditions/Pre", "Conditions/Invariant", "Conditions/Post", "Effects/Start",
                        "Effects/During", "Effects/End"):
            own = {_meaning(t): _bound(t) for t in _terms(general.get_referable("Execution"), section)}
            for term in _terms(container.get_referable("Execution"), section):
                if _meaning(term) in own:
                    assert _bound(term) == own[_meaning(term)], (container.id_short, section, _meaning(term))
    assert specialized == 3


def _component_offers(store, entity) -> dict:
    """What the component an entity of the module's structure is offers, over all its capabilities."""
    shell = next(i for i in store if isinstance(i, model.AssetAdministrationShell)
                 and i.asset_information.global_asset_id == entity.global_asset_id)
    offered = {}
    for capability_set in _submodel(store, shell.id, "CapabilityDescription").submodel_element:
        for container in capability_set.value:
            offered |= _stated(container)
    return offered


def _evaluate(store, term, unit: dict) -> float:
    """A condition's bound as a number: its value, the property it references, or its formula over its Uses."""
    named = {e.id_short: e for e in term.value}
    if "Value" in named:
        return float(named["Value"].value)
    if "ValueReference" in named:
        return float(named["ValueReference"].value.resolve(store).value)
    values = {}
    for use in named["Uses"].value:
        used = use.value.resolve(store)
        values[use.id_short] = float(used.value) if isinstance(used, model.Property) else unit[_meaning(use)]
    return eval(named["Formula"].value, {"__builtins__": {}}, {"pi": math.pi, **values})


SATISFIABLE = {"equal": lambda low, high, b: low <= b <= high, "less": lambda low, high, b: low < b,
               "lessOrEqual": lambda low, high, b: low <= b, "greater": lambda low, high, b: high > b,
               "greaterOrEqual": lambda low, high, b: high >= b}


def test_the_stations_conditions_on_a_component_leave_it_room_within_what_it_offers():
    """Each condition the module sets on a component's property, at the vial's dimensions, is one the component can
    meet: the fill position and the weighing position are within the axis's travel."""
    from aas_model.product_instances.vial_2ml import AAS_ID

    store, checked = _store(), []
    unit = {_meaning(v): float(v.get_referable("Initial").value)
            for v in _submodel(store, AAS_ID, "StateDeclaration").submodel_element if _has(v, "Initial")}
    for container in _module_containers(store):
        if not _has(container, "Execution"):
            continue
        for section in ("Conditions/Pre", "Conditions/Invariant"):
            for term in _terms(container.get_referable("Execution"), section):
                subject = term.get_referable("Subject").value.resolve(store)
                operator = term.get_referable("Operator").value
                if subject.get_referable("Role").value != "Component" or operator not in SATISFIABLE:
                    continue
                offered = _component_offers(store, subject.get_referable("Binding").value.resolve(store))
                low, high = offered[_meaning(term)]
                bound = _evaluate(store, term, unit)
                assert SATISFIABLE[operator](low, high, bound), (container.id_short, section, operator, bound)
                checked.append((container.id_short, section))
    assert sorted(checked) == [("Dosing", "Conditions/Invariant"), ("Dosing", "Conditions/Pre"),
                               ("Positioning", "Conditions/Invariant"), ("Weighing", "Conditions/Pre")]


def test_the_checked_in_example_files_are_what_the_export_writes():
    import importlib.util
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location("export_examples", root / "scripts" / "export_examples.py")
    export = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(export)
    stale = [name for name, text in export.documents().items()
             if not (root / "examples" / "aas" / name).exists()
             or (root / "examples" / "aas" / name).read_text(encoding="utf-8") != text]
    assert not stale, f"run: python scripts/export_examples.py ({', '.join(stale)})"
