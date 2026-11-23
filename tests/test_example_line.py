"""The filling module and the 2 mL vial: the execution model on real instances, built together as one line."""

from __future__ import annotations

import json
import math

import pytest
from basyx.aas import model

from aas_model import build_from_model
from aas_model.constants import (
    EXECUTION_AND, EXECUTION_CONDITION, EXECUTION_DURING, EXECUTION_EFFECT, EXECUTION_SUBJECT, LAB,
    OPERATION_VARIABLE_CAPABILITY, OPERATION_VARIABLE_GROUNDING, PRODUCT_ASSET_TYPE,
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


def _terms(container, kind: str):
    """A capability's top-level terms of its ConditionSet or EffectSet: (Pre / Invariant / ... / End, term)."""
    if not _has(container, f"CapabilityRelations/{kind}"):
        return
    for section in container.get_referable(["CapabilityRelations", kind]).value:
        for term in section.value:
            yield section.id_short, term


def _subject(store, term):
    return term.get_referable("Subject").value.resolve(store)


def _is_unit(subject) -> bool:
    """A subject that stands for a unit of a product: an external reference to the products' asset type."""
    return isinstance(subject.value, model.ExternalReference) and subject.value.key[0].value == PRODUCT_ASSET_TYPE


def _asset(store, subject):
    """The AAS a subject is (Self, a component), or None for one only known at run time."""
    return subject.value.resolve(store) if isinstance(subject.value, model.ModelReference) else None


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
    assert len(references) > 50 and not unresolved


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
        "OfferedCapabilities", "AuxiliaryCapabilities", "ModuleControl"}


def test_conditions_and_effects_are_term_trees_in_the_capability_relations():
    """Subjects, ConditionSet (Pre, Invariant, Post) and EffectSet (Start, During, End) beside 02020's relations;
    02020's ConstraintSet is left as IDTA has it, unused."""
    from aas_model.resource_instances.modules.filling_module import MODULE

    store = _store()
    description = _submodel(store, MODULE, "CapabilityDescription")
    dosing = description.get_referable(["AuxiliaryCapabilities", "Dosing"])
    relations = dosing.get_referable("CapabilityRelations")
    assert {e.id_short for e in relations.value} >= {"Subjects", "ConditionSet", "EffectSet", "RealizedBy"}
    assert not _has(relations, "ConstraintSet")
    rim = relations.get_referable(["ConditionSet", "Invariant", "Term_00"])
    assert _semantic_id(rim) == EXECUTION_CONDITION and _meaning(rim) == f"{LAB}Position"
    assert _subject(store, rim).display_name["en"] == "Needle axis"
    rim_height = rim.get_referable(["Uses", "RimHeight"])
    assert rim_height.value.resolve(store).display_name["en"] == "Container in the nest"
    assert _meaning(rim_height) == f"{LAB}RimHeight"

    during = relations.get_referable(["EffectSet", "During"])
    assert _semantic_id(during) == EXECUTION_DURING
    immersion = during.get_referable("Term_00")
    assert _semantic_id(immersion) == EXECUTION_EFFECT and _meaning(immersion) == f"{LAB}OutletImmersion"
    assert {use.id_short: _meaning(use) for use in immersion.get_referable("Uses").value} == {
        "Position": f"{LAB}Position", "NestPosition": None, "InnerBottomHeight": f"{LAB}InnerBottomHeight",
        "ContentVolume": f"{LAB}ContentVolume", "InnerDiameter": f"{LAB}InnerDiameter"}
    weighing = description.get_referable(["AuxiliaryCapabilities", "Weighing"])
    assert sorted((when, t.get_referable("Operator").value) for when, t in _terms(weighing, "ConditionSet")) == [
        ("Invariant", "unchanged"), ("Pre", "equal")]


def test_subjects_are_an_aas_or_the_semantic_id_of_what_they_stand_for():
    from aas_model.resource_instances.modules.filling_module import LINEAR_AXIS, MODULE

    store = _store()
    subjects = _submodel(store, MODULE, "CapabilityDescription").get_referable(
        ["AuxiliaryCapabilities", "Dosing", "CapabilityRelations", "Subjects"])
    assert isinstance(subjects, model.SubmodelElementList)
    assert subjects.semantic_id_list_element.key[0].value == EXECUTION_SUBJECT
    axis, unit = subjects.value
    assert [s.display_name["en"] for s in subjects.value] == ["Needle axis", "Container in the nest"]
    assert _asset(store, axis).id == LINEAR_AXIS                                       # one particular asset
    assert _is_unit(unit) and _asset(store, unit) is None                              # known only at run time
    own = _submodel(store, LINEAR_AXIS, "CapabilityDescription").get_referable(
        ["AuxiliaryCapabilities", "Positioning", "CapabilityRelations", "Subjects"]).value[0]
    assert _asset(store, own).id == LINEAR_AXIS                                        # Self: its own AAS


def test_every_skill_a_call_can_ground_carries_the_capability_and_its_grounding():
    """A skill realizing a capability with subjects takes the capability a call carries out and who its subjects are
    (Grounding, in the order of the capability's Subjects) as Operation inputs; a primitive, which its module runs,
    takes neither."""
    store, grounded, primitives = _store(), set(), set()
    for container in _module_containers(store, every=True):
        relations = container.get_referable("CapabilityRelations")
        skill = relations.get_referable("RealizedBy").second.resolve(store)
        inputs = {_semantic_id(v): v for v in skill.get_referable(["Start", "Start"]).input_variable}
        if any(r.key[0].value.endswith("/Primitive") for r in skill.supplemental_semantic_id):
            assert OPERATION_VARIABLE_GROUNDING not in inputs
            primitives.add(skill.id_short)
            continue
        assert inputs[OPERATION_VARIABLE_CAPABILITY].id_short == "Capability", container.id_short
        grounding = inputs[OPERATION_VARIABLE_GROUNDING]
        assert isinstance(grounding, model.SubmodelElementList) and not grounding.value      # filled by a call
        grounded.add(skill.id_short)
    assert grounded == {"Dispensing", "Occupy", "Release"} and primitives == {"MoveAxis", "Dispense", "Weigh"}


def test_every_term_says_in_its_display_name_what_it_states():
    store, terms = _store(), 0
    for container in _module_containers(store, every=True):
        for kind in ("ConditionSet", "EffectSet"):
            for _, term in _terms(container, kind):
                assert term.display_name and term.display_name.get("en"), (container.id_short, term.id_short)
                terms += 1
    assert terms == 22


def test_the_offered_filling_is_derived_and_bound_to_its_skill():
    from aas_model.resource_instances.modules.filling_module import MODULE

    store = _store()
    filling = _submodel(store, MODULE, "CapabilityDescription").get_referable(["OfferedCapabilities", "Filling"])
    relations = filling.get_referable("CapabilityRelations")
    assert _is_unit(relations.get_referable("Subjects").value[1])
    effects = {_meaning(term): (when, term) for when, term in _terms(filling, "EffectSet")}
    assert {when for when, _ in effects.values()} == {"End"}
    rate = effects[f"{LAB}ContentVolume"][1].get_referable("Rate").value.resolve(store)
    assert rate.value == "1.0"                                        # the step's constant flow rate
    assert sorted(when for when, _ in _terms(filling, "ConditionSet")) == ["Invariant", "Pre"]
    parts = relations.get_referable(["ComposedOfSet", "ComposedOf"])
    assert {part.second.resolve(store).parent.id_short for part in parts.value
            if isinstance(part, model.RelationshipElement)} == {"Positioning", "Dosing", "Weighing"}


def _unit_properties(store, element) -> set:
    """The meanings of what the terms and Uses below an element say of a unit."""
    found = set()
    if isinstance(element, model.SubmodelElementCollection):
        subject = next((e for e in element.value if e.id_short == "Subject"), None)
        if subject is not None and _is_unit(subject.value.resolve(store)):
            found.add(_meaning(element))
        for child in element.value:
            found |= _unit_properties(store, child)
    elif isinstance(element, model.ReferenceElement) and element.id_short != "Subject" \
            and isinstance(element.value, model.ModelReference) and _meaning(element):
        target = element.value.resolve(store)
        if _semantic_id(target) == EXECUTION_SUBJECT and _is_unit(target):
            found.add(_meaning(element))
    return found


def test_the_vial_declares_what_the_module_reads_of_its_units():
    """Every property of a unit a capability of the line names is declared by the vial."""
    from aas_model.product_instances.vial_2ml import AAS_ID

    store = _store()
    declared = {_meaning(v) for v in _submodel(store, AAS_ID, "StateDeclaration").submodel_element}
    named = set()
    for container in _module_containers(store, every=True):
        named |= _unit_properties(store, container)
    assert named and named <= declared, named - declared


# ── A module's capability specializes its components' and never widens them ─────────────────────────────────────

SPECIALIZES = ("/CapabilityGeneralizedBy/", "/CapabilityComposedOf/")   # the relations whose second is more general


def _stated(container) -> dict:
    """A capability's properties as meaning -> (lowest, highest); a list of choices is left out."""
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
    """What a capability says of each property: (ConditionSet or EffectSet, Pre / ... / End, meaning) -> its bound."""
    said = {}
    for kind in ("ConditionSet", "EffectSet"):
        for when, root in _terms(container, kind):
            for term in _top_level(root):
                said[(kind, when, _meaning(term))] = _bound(term)
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
    unit's property, a Use naming the unit, at the vial's declared value)."""
    named = {e.id_short: e for e in term.value}
    if "Value" in named:
        return float(named["Value"].value)
    if "ValueReference" in named:
        return float(named["ValueReference"].value.resolve(store).value)
    values = {}
    for use in named["Uses"].value:
        used = use.value.resolve(store)
        values[use.id_short] = unit[_meaning(use)] if isinstance(used, model.ReferenceElement) else float(used.value)
    return eval(named["Formula"].value, {"__builtins__": {}}, {"pi": math.pi, **values})


SATISFIABLE = {"equal": lambda low, high, b: low <= b <= high, "less": lambda low, high, b: low < b,
               "lessOrEqual": lambda low, high, b: low <= b, "greater": lambda low, high, b: high > b,
               "greaterOrEqual": lambda low, high, b: high >= b}


def test_the_stations_conditions_on_a_component_leave_it_room_within_what_it_offers():
    """Each condition the module sets on a component's property, at the vial's dimensions, is one the component can
    meet: the fill position and the weighing position are within the axis's travel."""
    from aas_model.product_instances.vial_2ml import AAS_ID
    from aas_model.resource_instances.modules.filling_module import MODULE

    store, checked = _store(), []
    unit = {_meaning(v): float(v.get_referable("Initial").value)
            for v in _submodel(store, AAS_ID, "StateDeclaration").submodel_element if _has(v, "Initial")}
    for container in _module_containers(store):
        for when, root in _terms(container, "ConditionSet"):
            for term in _top_level(root):
                component = _asset(store, _subject(store, term))
                operator = term.get_referable("Operator").value
                if not isinstance(component, model.AssetAdministrationShell) or component.id == MODULE \
                        or operator not in SATISFIABLE:
                    continue
                low, high = _component_offers(store, component)[_meaning(term)]
                bound = _evaluate(store, term, unit)
                assert SATISFIABLE[operator](low, high, bound), (container.id_short, when, operator, bound)
                checked.append((container.id_short, when))
    assert sorted(checked) == [("Dosing", "Invariant"), ("Dosing", "Pre"), ("Positioning", "Invariant"),
                               ("Weighing", "Pre")]


# ── The predicates fit together: move, receive, fill ────────────────────────────────────────────────────────────

def _reference_key(reference) -> str:
    """An identity for what a reference names: its keys, joined."""
    return "/".join(key.value for key in reference.key)


class _Ground:
    """Applies a capability, grounded on concrete subjects, to a symbolic state: (identity, meaning) -> value."""

    def __init__(self, store, state: dict):
        self.store, self.state = store, state

    def _identity(self, subjects, grounding: list, reference) -> str:
        """Who a term's subject reference names: the call's grounding at the subject's place."""
        return grounding[int(reference.key[-1].value)]

    @staticmethod
    def _check_grounding(subjects, grounding: list) -> None:
        """One entry per subject, in order; a subject the capability fixes is given as it states it."""
        assert len(grounding) == len(subjects.value)
        for subject, given in zip(subjects.value, grounding):
            if isinstance(subject.value, model.ModelReference):
                assert given == _reference_key(subject.value), (subject.display_name["en"], given)

    def _operand(self, subjects, grounding: list, term, parameters: dict):
        named = {e.id_short: e for e in term.value}
        if "Value" in named:
            return float(named["Value"].value)
        target = named["ValueReference"].value
        if target.key[-2].value == "Subjects":
            return self._identity(subjects, grounding, target)
        resolved = target.resolve(self.store)
        if resolved.id_short in parameters:
            return parameters[resolved.id_short]
        return float(resolved.value)

    def apply(self, container, grounding: list, parameters: dict | None = None) -> None:
        parameters = parameters or {}
        relations = container.get_referable("CapabilityRelations")
        subjects = relations.get_referable("Subjects")
        self._check_grounding(subjects, grounding)
        for when, term in _terms(container, "ConditionSet"):
            if when != "Pre" and when != "Invariant":
                continue
            key = (self._identity(subjects, grounding, term.get_referable("Subject").value), _meaning(term))
            operator, have = term.get_referable("Operator").value, self.state.get(key)
            want = self._operand(subjects, grounding, term, parameters) if operator != "unchanged" else have
            holds = {"equal": have == want, "less": have is not None and have < want,
                     "greater": have is not None and have > want, "unchanged": True}[operator]
            assert holds, f"{container.id_short}: {term.display_name['en']} ({key}: {have!r} {operator} {want!r})"
        for when, term in _terms(container, "EffectSet"):
            if when != "End":
                continue
            key = (self._identity(subjects, grounding, term.get_referable("Subject").value), _meaning(term))
            operator = term.get_referable("Operator").value
            if operator == "measured":
                self.state[key] = "known"
                continue
            value = self._operand(subjects, grounding, term, parameters)
            if operator == "assign":
                self.state[key] = value
            else:
                self.state[key] = (self.state.get(key) or 0) + (value if operator == "increase" else -value)


def test_a_shuttle_brings_a_vial_the_module_takes_it_and_fills_it():
    """The line's predicates chain: each step's preconditions are what the steps before made true, matched by the
    properties' semantic ids and the subjects' identities. MoveToPosition puts the shuttle at the filling module's
    transfer point; Receiving needs exactly that and the vial on the shuttle, and hands it to the module; Filling
    needs the vial held by the module."""
    from aas_model.resource_instances import RESOURCE_FACTORIES
    from aas_model.resource_instances.modules.filling_module import MODULE, TRANSFER_POINT
    from aas_pydantic import ModelReference

    store = _store()
    shuttle = RESOURCE_FACTORIES["planarShuttle1"]()
    for identifiable in build_from_model(shuttle):
        store.add(identifiable)
    vial, place = "urn:batch:1/unit/17", _reference_key(ModelReference(key=TRANSFER_POINT))
    module = _submodel(store, MODULE, "CapabilityDescription")
    move = _submodel(store, shuttle.id, "CapabilityDescription").get_referable(["Transport", "MoveToPosition"])
    state = {(vial, f"{LAB}HeldBy"): shuttle.id, (vial, f"{LAB}ContentVolume"): 0.0,
             (MODULE, f"{LAB}Occupancy"): 0.0}
    line = _Ground(store, state)

    # Each call's Grounding: who the capability's subjects are, in their order (fixed ones as the model states them).
    receiving = module.get_referable(["ModuleControl", "Receiving"])
    handover = [MODULE, place, shuttle.id, vial]
    with pytest.raises(AssertionError, match="Shuttle at the transfer point"):
        line.apply(receiving, handover)                                     # not there yet
    with pytest.raises(AssertionError, match="Transfer point"):
        line.apply(receiving, [MODULE, "elsewhere", shuttle.id, vial])      # a fixed subject given otherwise
    line.apply(move, [shuttle.id, place])                                   # the shuttle drives to the module
    assert state[(shuttle.id, f"{LAB}Location")] == place
    line.apply(receiving, handover)                                         # the module takes the vial
    assert state[(vial, f"{LAB}HeldBy")] == MODULE and state[(MODULE, f"{LAB}Occupancy")] == 1.0
    line.apply(module.get_referable(["OfferedCapabilities", "Filling"]), [MODULE, vial], {"Volume": 2.0})
    assert state[(vial, f"{LAB}ContentVolume")] == 2.0 and state[(vial, f"{LAB}FillWeight")] == "known"
    line.apply(module.get_referable(["ModuleControl", "Releasing"]), handover)
    assert state[(vial, f"{LAB}HeldBy")] == shuttle.id and state[(MODULE, f"{LAB}Occupancy")] == 0.0


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
