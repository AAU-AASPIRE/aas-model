"""The filling module and the 2 mL vial: the execution model on real instances, built together as one line."""

from __future__ import annotations

import json
import math

import pytest
from basyx.aas import model

from aas_model import build_from_model
from aas_model.constants import (
    EXECUTION_AND, EXECUTION_CONDITION, EXECUTION_EFFECT, EXECUTION_STATE_CONSTRAINT, EXECUTION_SUBJECT_COMPONENT,
    EXECUTION_SUBJECT_PRODUCT, LAB,
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
    """Every model reference below an element: ReferenceElement values and both ends of a relationship."""
    if isinstance(element, model.ReferenceElement) and isinstance(element.value, model.ModelReference):
        yield element.value
    if isinstance(element, model.RelationshipElement):
        yield from (end for end in (element.first, element.second) if isinstance(end, model.ModelReference))
    if isinstance(element, (model.SubmodelElementCollection, model.SubmodelElementList)):
        for child in element.value:
            yield from _references(child)


def _submodel(store, aas_id: str, id_short: str) -> model.Submodel:
    return store.get_item(f"{aas_id}/submodels/{id_short}")


def _semantic_id(element) -> str:
    return element.semantic_id.key[0].value if element.semantic_id else ""


def _meaning(element) -> str | None:
    return element.supplemental_semantic_id[0].key[0].value if element.supplemental_semantic_id else None


def _has(element, path: str) -> bool:
    try:
        element.get_referable(path.split("/"))
        return True
    except KeyError:
        return False


def _conditions(container):
    """A capability's state conditions: (when it holds, its term), each a CustomConstraint marked as one."""
    if not _has(container, "CapabilityRelations/ConstraintSet"):
        return
    for constraint in container.get_referable(["CapabilityRelations", "ConstraintSet"]).value:
        custom = next((e for e in constraint.value if e.id_short == "CustomConstraint"), None)
        if custom is not None and _meaning(custom) == EXECUTION_STATE_CONSTRAINT:
            yield constraint.get_referable("PropertyConditionalType").value, next(iter(custom.value))


def _effects(container):
    """A capability's effects: (when it applies, its term)."""
    if not _has(container, "CapabilityRelations/EffectSet"):
        return
    for effect in container.get_referable(["CapabilityRelations", "EffectSet"]).value:
        yield effect.get_referable("EffectTimingType").value, next(iter(effect.get_referable("Effect").value))


def _about(store, term):
    """The PropertySet entry's value a term is about."""
    return term.get_referable("Property").value.resolve(store)


def _subject_of(store, value):
    """The subject a property of the capability is of (its SameProperty OfSubject), or None for its own."""
    container = value.parent
    relation = next((e for e in container.value if e.id_short == "OfSubject"), None)
    return relation.second.resolve(store) if relation is not None else None


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
    unresolved = [ref for ref in references if ref.resolve(store) is None]
    assert len(references) > 100 and not unresolved


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


def test_conditions_are_02020_constraints_and_effects_sit_beside_them():
    """A condition is a PropertyConstraintContainer (CustomConstraint, its ConditionalType, ConstraintHasProperty to
    every property it reads); an effect an EffectContainer in the EffectSet next to the ConstraintSet."""
    from aas_model.resource_instances.modules.filling_module import MODULE

    store = _store()
    description = _submodel(store, MODULE, "CapabilityDescription")
    dosing = description.get_referable(["AuxiliaryCapabilities", "Dosing"])
    rim = dosing.get_referable(["CapabilityRelations", "ConstraintSet", "NeedleInsideRim"])
    assert _semantic_id(rim).endswith("/CapabilityDescription/PropertyConstraintContainer/1/0")
    assert rim.get_referable("ConstraintType").value == "CustomConstraint"
    assert rim.get_referable("PropertyConditionalType").value == "Invariant"
    term = rim.get_referable(["CustomConstraint", "Term"])
    assert _semantic_id(term) == EXECUTION_CONDITION
    read = {relation.second.resolve(store).parent.id_short
            for relation in rim.get_referable("ConstraintPropertyRelations").value}
    uses = {use.value.resolve(store).parent.id_short for use in term.get_referable("Uses").value}
    assert read == uses | {_about(store, term).parent.id_short} == {"Position", "NestPosition", "RimHeight",
                                                                     "InsertDepth"}
    rim_height = term.get_referable(["Uses", "RimHeight"]).value.resolve(store)
    assert _meaning(rim_height) == f"{LAB}RimHeight" and _subject_of(store, rim_height).id_short == "Unit"

    (timing, effect), = _effects(dosing)
    assert timing == "During" and _semantic_id(effect) == EXECUTION_EFFECT
    assert _meaning(_about(store, effect)) == f"{LAB}OutletImmersion"
    assert {use.id_short: _meaning(use.value.resolve(store)) for use in effect.get_referable("Uses").value} == {
        "Position": f"{LAB}Position", "NestPosition": f"{LAB}NestPosition",
        "InnerBottomHeight": f"{LAB}InnerBottomHeight", "ContentVolume": f"{LAB}ContentVolume",
        "InnerDiameter": f"{LAB}InnerDiameter"}
    weighing = description.get_referable(["AuxiliaryCapabilities", "Weighing"])
    assert sorted((when, t.get_referable("Operator").value) for when, t in _conditions(weighing)) == [
        ("Invariant", "unchanged"), ("Pre", "equal")]


def test_subjects_are_references_named_for_the_domain_with_their_role_as_semantic_id():
    from aas_model.resource_instances.modules.filling_module import LINEAR_AXIS, MODULE

    store = _store()
    subjects = _submodel(store, MODULE, "CapabilityDescription").get_referable(
        ["AuxiliaryCapabilities", "Dosing", "Subjects"])
    axis, unit = subjects.get_referable("LinearAxis"), subjects.get_referable("Unit")
    assert isinstance(axis, model.ReferenceElement) and _semantic_id(axis) == EXECUTION_SUBJECT_COMPONENT
    assert axis.value.resolve(store).id == LINEAR_AXIS
    assert _semantic_id(unit) == EXECUTION_SUBJECT_PRODUCT and unit.value is None       # nothing binds it here
    own = _submodel(store, LINEAR_AXIS, "CapabilityDescription").get_referable(
        ["AuxiliaryCapabilities", "Positioning", "Subjects", "Self"])
    assert own.value.resolve(store).id == LINEAR_AXIS                                  # Self: its own AAS


def test_the_offered_filling_is_derived_and_bound_to_its_skill():
    from aas_model.resource_instances.modules.filling_module import MODULE

    store = _store()
    filling = _submodel(store, MODULE, "CapabilityDescription").get_referable(["OfferedCapabilities", "Filling"])
    unit = filling.get_referable(["Subjects", "Unit"]).value.resolve(store)
    assert unit.id_short == "Unit" and unit.semantic_id.key[0].value.endswith("/OperationVariable/Subject/1/0")
    effects = dict((_meaning(_about(store, term)), (when, term)) for when, term in _effects(filling))
    assert {when for when, _ in effects.values()} == {"End"}
    rate = effects[f"{LAB}ContentVolume"][1].get_referable("Rate").value.resolve(store)
    assert rate.value == "1.0"                                        # the step's constant flow rate
    assert sorted(when for when, _ in _conditions(filling)) == ["Invariant", "Pre"]
    parts = filling.get_referable(["CapabilityRelations", "ComposedOfSet", "ComposedOf"])
    assert {part.second.resolve(store).parent.id_short for part in parts.value
            if isinstance(part, model.RelationshipElement)} == {"Positioning", "Dosing", "Weighing"}


def test_the_vial_declares_what_the_module_reads_of_its_units():
    """Every property of a unit a capability of the line states is declared by the vial."""
    from aas_model.product_instances.vial_2ml import AAS_ID

    store = _store()
    declared = {_meaning(v) for v in _submodel(store, AAS_ID, "StateDeclaration").submodel_element}
    named = set()
    for container in _module_containers(store, every=True):
        for entry in (container.get_referable("PropertySet").value if _has(container, "PropertySet") else ()):
            value = entry.get_referable("Value")
            subject = _subject_of(store, value)
            if subject is not None and _semantic_id(subject) == EXECUTION_SUBJECT_PRODUCT:
                named.add(_meaning(value))
    assert named and named <= declared, named - declared


# ── A module's capability specializes its components' and never widens them ─────────────────────────────────────

SPECIALIZES = ("/CapabilityGeneralizedBy/", "/CapabilityComposedOf/")   # the relations whose second is more general


def _stated(container) -> dict:
    """A capability's properties that have a value, as meaning -> (lowest, highest); a list of choices, and the
    properties of its subjects (state, no value), are left out."""
    found = {}
    for property_container in (container.get_referable("PropertySet").value if _has(container, "PropertySet")
                               else ()):
        value = property_container.get_referable("Value")
        if isinstance(value, model.Range):
            found[_meaning(value)] = (float(value.min), float(value.max))
        elif isinstance(value, model.Property) and value.value is not None:
            found[_meaning(value)] = (float(value.value), float(value.value))
    return found


def _more_general(store, container) -> list:
    """The capability containers a container specializes or is composed of, all the way up."""
    found, stack = [], list(container.get_referable("CapabilityRelations").value)
    while stack:
        element = stack.pop()
        if isinstance(element, model.SubmodelElementCollection):
            stack.extend(element.value)
        elif isinstance(element, model.RelationshipElement) and any(s in _semantic_id(element) for s in SPECIALIZES):
            general = element.second.resolve(store).parent
            found += [general, *_more_general(store, general)]
    return found


def _module_containers(store, every: bool = False):
    """The module's capability containers (with ``every``, the components' too)."""
    from aas_model.resource_instances.modules.filling_module import LINEAR_AXIS, MODULE, PUMP, SCALE

    return [container for aas_id in ((MODULE, LINEAR_AXIS, PUMP, SCALE) if every else (MODULE,))
            for capability_set in _submodel(store, aas_id, "CapabilityDescription").submodel_element
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
    assert ("Filling", f"{LAB}FillVolume") in compared


def _top_level(term):
    """A term, or the terms of an And, all the way down."""
    if _semantic_id(term) == EXECUTION_AND:
        for child in term.value:
            yield from _top_level(child)
    elif _semantic_id(term) in (EXECUTION_CONDITION, EXECUTION_EFFECT):
        yield term


def _said(store, container) -> dict:
    """What a capability says of each property of a subject: (condition or effect, when, meaning) -> its bound."""
    said = {}
    for kind, terms in (("condition", _conditions(container)), ("effect", _effects(container))):
        for when, root in terms:
            for term in _top_level(root):
                said[(kind, when, _meaning(_about(store, term)))] = _bound(term)
    return said


def _bound(term) -> tuple:
    """What a term holds: its operator and value, formula or reference."""
    named = {e.id_short: e for e in term.value}
    target = named.get("Value") or named.get("Formula") or named.get("ValueReference")
    return named["Operator"].value, target.value if isinstance(target, model.Property) else str(target.value) \
        if target else None


def test_the_module_adds_to_its_components_conditions_and_effects_and_never_restates_them_otherwise():
    """What the component's capability says of a property holds in the module as it is: restated, it is the same."""
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
        own = _said(store, general)
        for key, bound in _said(store, container).items():
            if key in own:
                assert bound == own[key], (container.id_short, key)
    assert specialized == 3


def _component_offers(store, aas) -> dict:
    """What a component offers, over all its capabilities."""
    offered = {}
    for capability_set in _submodel(store, aas.id, "CapabilityDescription").submodel_element:
        for container in capability_set.value:
            offered |= _stated(container)
    return offered


def _evaluate(store, term, unit: dict) -> float:
    """A condition's bound as a number: its value, the property it references, or its formula over its Uses (a
    unit's property at the vial's declared value)."""
    named = {e.id_short: e for e in term.value}
    if "Value" in named:
        return float(named["Value"].value)
    if "ValueReference" in named:
        return float(named["ValueReference"].value.resolve(store).value)
    values = {}
    for use in named["Uses"].value:
        used = use.value.resolve(store)
        values[use.id_short] = unit[_meaning(used)] if _subject_of(store, used) is not None else float(used.value)
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
        for when, root in _conditions(container):
            for term in _top_level(root):
                about = _about(store, term)
                subject = _subject_of(store, about)
                operator = term.get_referable("Operator").value
                if subject is None or _semantic_id(subject) != EXECUTION_SUBJECT_COMPONENT \
                        or operator not in SATISFIABLE:
                    continue
                low, high = _component_offers(store, subject.value.resolve(store))[_meaning(about)]
                bound = _evaluate(store, term, unit)
                assert SATISFIABLE[operator](low, high, bound), (container.id_short, when, operator, bound)
                checked.append((container.id_short, when))
    assert sorted(checked) == [("Dosing", "Invariant"), ("Dosing", "Pre"), ("Positioning", "Invariant"),
                               ("Weighing", "Pre")]


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
