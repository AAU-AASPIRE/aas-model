"""The filling module and the 2 mL vial: the execution model on real instances, built together as one line."""

from __future__ import annotations

import json
import math

import pytest
from basyx.aas import model

from aas_model import build_from_model
from aas_model.constants import (
    EXECUTION_AND, EXECUTION_CONDITION, EXECUTION_DURING, EXECUTION_EFFECT, EXECUTION_ONE_OF, EXECUTION_SUBJECT, LAB,
    PRODUCT_ASSET_TYPE, STATE_VARIABLE,
)
from aas_model.batch_instances import BATCH_FACTORIES
from aas_model.product_instances import PRODUCT_FACTORIES
from aas_model.resource_instances.modules import MODULE_FACTORIES

FACTORIES = {**MODULE_FACTORIES, **PRODUCT_FACTORIES, **BATCH_FACTORIES}


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


def test_every_capability_the_tree_runs_translates_its_call_and_the_skill_is_the_devices_alone():
    """A capability realized by a skill the behaviour tree invokes carries a Translation (Call and Reply, D34), and that
    skill's Operation holds only what the device's action takes and answers; a capability realized by a primitive,
    which its module runs, has none. Each capability is realized by exactly one skill."""
    store, translated, primitives = _store(), set(), set()
    for container in _module_containers(store, every=True):
        relations = container.get_referable("CapabilityRelations")
        (realized_by,) = [e for e in relations.value if isinstance(e, model.RelationshipElement)
                          and e.id_short.startswith("RealizedBy")]
        skill = realized_by.second.resolve(store)
        operation = skill.get_referable(["Start", "Start"])
        assert not any(isinstance(v, model.SubmodelElementCollection) for v in operation.input_variable)
        if any(r.key[0].value.endswith("/Primitive") for r in skill.supplemental_semantic_id):
            assert not _has(container, "CapabilityRelations/Translation"), container.id_short
            primitives.add(skill.id_short)
            continue
        translation = relations.get_referable("Translation")
        assert b"function call(" in translation.get_referable("Call").value, container.id_short
        assert b"function reply(" in translation.get_referable("Reply").value, container.id_short
        translated.add(skill.id_short)
    assert translated == {"Dispensing", "Occupy", "Release"} and primitives == {"MoveAxis", "Dispense", "Weigh"}


def _state_sinks(store, aas: str) -> dict:
    """Which mapping of an AAS's AIMC sinks into each of its state variables (by idShort): its observed state."""
    sunk: dict = {}
    aimc = _submodel(store, aas, "AssetInterfacesMappingConfiguration")
    for mapping in aimc.get_referable("MappingConfigurations").value:
        for sink in mapping.get_referable("Sinks").value:
            target = sink.get_referable("Sink").value.resolve(store)
            if _semantic_id(target) == STATE_VARIABLE:
                assert target.id_short not in sunk, f"{target.id_short}: sunk by two mappings"
                sunk[target.id_short] = mapping
    return sunk


def test_places_and_shuttles_project_their_positions_and_location_is_derived():
    """Linked projections (D36): the state store is one more sink of a mapping. The filling module's TransferPoint
    mapping composes the coordinate with the base it is relative to into the transfer point's position; the shuttle's
    Location mapping sinks its reported position beside the series row, its station-state mapping who it serves. The
    shuttle's Location is derived from the positions by query, never sunk."""
    from aas_model.resource_instances import RESOURCE_FACTORIES
    from aas_model.resource_instances.modules.filling_module import MODULE

    store = _store()
    shuttle = RESOURCE_FACTORIES["planarShuttle1"]()
    for identifiable in build_from_model(shuttle):
        store.add(identifiable)

    def variables(aas: str) -> dict:
        return {_meaning(v): v for v in _submodel(store, aas, "StateDeclaration").submodel_element}

    place, sunk = variables(MODULE), _state_sinks(store, MODULE)
    for axis in ("X", "Y"):
        projected = place[f"{LAB}Absolute{axis}"]
        mapping = sunk[projected.id_short]
        sources = {s.get_referable("SourceId").value: s.get_referable("Source").value.resolve(store)
                   for s in mapping.get_referable("Sources").value}
        assert {_meaning(c) for c in sources.values()} == {f"{LAB}TransferPoint", f"{LAB}ModuleBase"}
        assert projected.get_referable("Subject").value.resolve(store) is sources["TransferPoint"]  # the place
    own, sunk = variables(shuttle.id), _state_sinks(store, shuttle.id)
    def sink_ids(mapping) -> set:
        return {s.get_referable("SinkId").value for s in mapping.get_referable("Sinks").value}

    assert sunk["X"] is sunk["Y"] and sink_ids(sunk["X"]) == {"Live", "X", "Y"}    # beside the series row
    assert sink_ids(sunk["OccupiedBy"]) == {"Live", "OccupiedBy"}                  # the queue's head, beside the row
    location = own[f"{LAB}Location"]
    assert location.id_short not in sunk and not any(e.id_short == "Initial" for e in location.value)  # derived


def test_every_term_says_in_its_display_name_what_it_states():
    store, terms = _store(), 0
    for container in _module_containers(store, every=True):
        for kind in ("ConditionSet", "EffectSet"):
            for _, term in _terms(container, kind):
                assert term.display_name and term.display_name.get("en"), (container.id_short, term.id_short)
                terms += 1
    assert terms == 26


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

    @staticmethod
    def _literal(prop):
        if isinstance(prop.value, bool):
            return prop.value
        try:
            return float(prop.value)
        except ValueError:
            return str(prop.value)                                          # a URI: lab:InTolerance

    def holds(self, goal, grounding: list) -> bool:
        """Whether a goal's condition holds for the subjects it is grounded on."""
        subjects = goal.get_referable("Subjects")
        for term in goal.get_referable("Condition").value:
            key = (self._identity(subjects, grounding, term.get_referable("Subject").value), _meaning(term))
            if self.state.get(key) != self._operand(subjects, grounding, term, {}):
                return False
        return True

    def _operand(self, subjects, grounding: list, term, parameters: dict):
        named = {e.id_short: e for e in term.value}
        if "Value" in named:
            return self._literal(named["Value"])
        target = named["ValueReference"].value
        if target.key[-2].value == "Subjects":
            return self._identity(subjects, grounding, target)
        resolved = target.resolve(self.store)
        if resolved.id_short in parameters:
            return parameters[resolved.id_short]
        return self._literal(resolved)

    def apply(self, container, grounding: list, parameters: dict | None = None, outcome: str | None = None) -> None:
        """Checks Pre and Invariant, then applies the End effects, those of ``outcome`` where they hold a OneOf (what
        the Translation's reply chose). Observed variables (OccupiedBy) are applied here as the DMP's mapping's next
        observation would show them."""
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
            effects = list(term.get_referable(outcome).value) if _semantic_id(term) == EXECUTION_ONE_OF else [term]
            for effect in effects:
                self._effect(subjects, grounding, effect, parameters)

    def _effect(self, subjects, grounding: list, term, parameters: dict) -> None:
        key = (self._identity(subjects, grounding, term.get_referable("Subject").value), _meaning(term))
        operator = term.get_referable("Operator").value
        if operator == "measured":
            self.state[key] = "known"
            return
        if operator == "clear":
            self.state.pop(key, None)
            return
        value = self._operand(subjects, grounding, term, parameters)
        if operator == "assign":
            self.state[key] = value
        else:
            self.state[key] = (self.state.get(key) or 0) + (value if operator == "increase" else -value)


def test_a_shuttle_brings_a_vial_the_module_takes_it_and_fills_it():
    """The line's predicates chain: each step's preconditions are what the steps before made true, matched by the
    properties' semantic ids and the subjects' identities. MoveToPosition puts the shuttle at the filling module's
    transfer point; Occupying needs exactly that and the vial on the shuttle, and hands it to the module; Filling
    needs the vial held by the module."""
    from aas_model.resource_instances import RESOURCE_FACTORIES
    from aas_model.batch_instances.vial_2ml_batch import AAS_ID as BATCH
    from aas_model.resource_instances.modules.filling_module import MODULE, TRANSFER_POINT
    from aas_pydantic import ModelReference

    store = _store()
    shuttle = RESOURCE_FACTORIES["planarShuttle1"]()
    for identifiable in build_from_model(shuttle):
        store.add(identifiable)
    vial, place = "urn:uuid:7f3a9c2e-5b1d-4e8a-9f60-2d4c8b1a0e57", _reference_key(ModelReference(key=TRANSFER_POINT))
    state_initial = {(vial, f"{LAB}Weighed"): False}
    module = _submodel(store, MODULE, "CapabilityDescription")
    move = _submodel(store, shuttle.id, "CapabilityDescription").get_referable(["Transport", "MoveToPosition"])
    state = {(vial, f"{LAB}HeldBy"): shuttle.id, (vial, f"{LAB}ContentVolume"): 0.0, **state_initial}
    line = _Ground(store, state)

    # Each call's Grounding: who the capability's subjects are, in their order (fixed ones as the model states them).
    occupying = module.get_referable(["ModuleControl", "Occupying"])
    handover = [MODULE, place, shuttle.id, vial]
    with pytest.raises(AssertionError, match="Shuttle at the transfer point"):
        line.apply(occupying, handover)                                     # not there yet
    with pytest.raises(AssertionError, match="Transfer point"):
        line.apply(occupying, [MODULE, "elsewhere", shuttle.id, vial])      # a fixed subject given otherwise
    line.apply(move, [shuttle.id, place])                                   # the shuttle drives to the module
    assert state[(shuttle.id, f"{LAB}Location")] == place
    line.apply(occupying, handover)                                         # the module takes the vial
    assert state[(vial, f"{LAB}HeldBy")] == MODULE and state[(MODULE, f"{LAB}OccupiedBy")] == vial
    # Filling's subjects include what the vial requires (bound when the tree is built); the reply chose the outcome.
    filling = [MODULE, vial, "vial:RequiredFillVolume", "vial:RequiredFillWeight"]
    line.apply(module.get_referable(["OfferedCapabilities", "Filling"]), filling, {"Volume": 2.0}, "InTolerance")
    assert state[(vial, f"{LAB}ContentVolume")] == 2.0 and state[(vial, f"{LAB}FillWeight")] == "known"
    assert state[(vial, f"{LAB}FillResult")] == f"{LAB}InTolerance"
    line.apply(module.get_referable(["ModuleControl", "Releasing"]), handover)
    assert state[(vial, f"{LAB}HeldBy")] == shuttle.id and (MODULE, f"{LAB}OccupiedBy") not in state
    # The batch's goal, applied to this unit, now holds; for a unit that was not filled, it does not.
    goal = _submodel(store, BATCH, "Goal")
    assert line.holds(goal, [vial]) and not line.holds(goal, ["urn:uuid:00000000-0000-4000-8000-000000000018"])


def test_the_batch_names_its_product_how_many_and_the_goal_each_unit_is_to_reach():
    """Products are modelled at batch level only (D10): the batch lists no units; each BT instance mints the IRI of
    the unit it makes (D35)."""
    from aas_model.batch_instances.vial_2ml_batch import AAS_ID as BATCH
    from aas_model.product_instances.vial_2ml import AAS_ID as VIAL

    store = _store()
    information = _submodel(store, BATCH, "BatchInformation")
    assert information.get_referable("ProductType").value.resolve(store).id == VIAL
    assert int(information.get_referable("Quantity").value) == 3
    submodels = {s.id_short for s in store if isinstance(s, model.Submodel) and s.id.startswith(BATCH)}
    assert submodels == {"BatchInformation", "Goal"}

    goal = _submodel(store, BATCH, "Goal")
    (each,) = goal.get_referable("Subjects").value
    assert _is_unit(each) and each.display_name["en"] == "The unit"
    terms = list(goal.get_referable("Condition").value)
    assert {_meaning(t) for t in terms} == {f"{LAB}ContentVolume", f"{LAB}Weighed"}
    assert all(t.get_referable("Subject").value.resolve(store) is each for t in terms)
    fill_volume = goal.get_referable(["Condition", "Term_00", "ValueReference"]).value.resolve(store)
    assert fill_volume.value == 2.0 and _meaning(fill_volume) == f"{LAB}FillVolume"   # the vial's required volume
    declared = {_meaning(v) for v in _submodel(store, VIAL, "StateDeclaration").submodel_element}
    assert {_meaning(t) for t in terms} <= declared


def test_every_capability_of_the_line_says_how_long_it_takes():
    """A planner of durative actions needs a duration for each: a Duration, or the Rate of an End effect (an axis at
    its speed, a dose at its flow rate); a module's specialization takes its component's. Filling's is the sum of its
    steps: 2 x 40 mm at 12.5 mm/s, 2 mL at 1 mL/s, and the weighing's 0.2 s."""
    from aas_model.resource_instances import RESOURCE_FACTORIES

    store = _store()
    for identifiable in build_from_model(RESOURCE_FACTORIES["planarShuttle1"]()):
        store.add(identifiable)
    shuttle_move = _submodel(store, RESOURCE_FACTORIES["planarShuttle1"]().id, "CapabilityDescription").get_referable(
        ["Transport", "MoveToPosition"])
    timed = {}
    for container in (*_module_containers(store, every=True), shuttle_move):
        relations = container.get_referable("CapabilityRelations")
        if _has(relations, "Duration"):
            timed[container.id_short] = "Duration"
        elif any(_has(term, "Rate") for when, term in _terms(container, "EffectSet") if when == "End"):
            timed[container.id_short] = "Rate"
        elif _has(relations, "GeneralizedBySet"):
            timed[container.id_short] = "specializes"
    assert set(timed) == {c.id_short for c in (*_module_containers(store, every=True), shuttle_move)}
    assert timed["Positioning"] in ("Rate", "specializes") and timed["MoveToPosition"] == "Duration"

    from aas_model.resource_instances.modules.filling_module import MODULE
    duration = _submodel(store, MODULE, "CapabilityDescription").get_referable(
        ["OfferedCapabilities", "Filling", "CapabilityRelations", "Duration"])
    values = {use.id_short: float(use.value.resolve(store).value) for use in duration.get_referable("Uses").value}
    values["Volume"] = 2.0                                            # the call's parameter
    assert values["Position"] == 40.0 and values["Speed"] == 12.5 and values["Weighing"] == 0.2
    assert eval(duration.get_referable("Formula").value, {"__builtins__": {}}, values) == pytest.approx(8.6)


def test_a_fond_planner_finds_the_outcomes_a_filling_can_have():
    """Non-determinism is stated in the AASs (D23): failure outcomes from the errors the module's skills can answer
    with, and the in/out-of-tolerance split of a measured result, Filling's OneOf, recorded in a FillResult the product
    declares. Which outcome happened, the Translation's reply says, from the measured result and the product's
    requirement on it, a subject of Filling."""
    from aas_model.product_instances.vial_2ml import AAS_ID as VIAL
    from aas_model.resource_instances.modules.filling_module import MODULE

    store = _store()
    errors = _submodel(store, MODULE, "Skills").get_referable("Errors")
    codes = {error.id_short: error.value for error in errors.value}
    assert len(codes) == 4 and len(set(codes.values())) == 4                  # one outcome each, told apart

    filling = _submodel(store, MODULE, "CapabilityDescription").get_referable(["OfferedCapabilities", "Filling"])
    measured = {_meaning(t) for when, t in _terms(filling, "EffectSet") if _semantic_id(t) == EXECUTION_EFFECT
                and t.get_referable("Operator").value == "measured" and _is_unit(_subject(store, t))}
    assert measured == {f"{LAB}FillWeight"}
    (one_of,) = [t for _, t in _terms(filling, "EffectSet") if _semantic_id(t) == EXECUTION_ONE_OF]
    results = {o.id_short: o.get_referable("Term_00").get_referable("Value").value for o in one_of.value}
    assert results == {"InTolerance": f"{LAB}InTolerance", "OutOfTolerance": f"{LAB}OutOfTolerance"}
    subjects = filling.get_referable(["CapabilityRelations", "Subjects"]).value
    assert {s.value.key[0].value for s in subjects[2:]} == {f"{LAB}FillVolume", f"{LAB}FillWeight"}
    required = _submodel(store, VIAL, "CapabilityDescription").get_referable(["RequiredCapabilities", "Filling"])
    assert _meaning(required.get_referable("Capability")) == _meaning(filling.get_referable("Capability"))
    bounds = {_meaning(entry.get_referable("Value")): entry.get_referable("Value")
              for entry in required.get_referable("PropertySet").value}
    for meaning in measured:                                                  # each measured result has bounds
        assert isinstance(bounds[meaning], model.Range) and bounds[meaning].min < bounds[meaning].max
    declared = {_meaning(v) for v in _submodel(store, VIAL, "StateDeclaration").submodel_element}
    assert f"{LAB}FillResult" in declared


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
