"""The execution semantics of capabilities: Subjects, ConditionSet and EffectSet in the CapabilityRelations; their
structure, references and how they serialize."""

from __future__ import annotations

import json

import pytest
from basyx.aas import model

from aas_model import build_from_model
from aas_model.constants import (
    EXECUTION_AND, EXECUTION_CONDITION, EXECUTION_EFFECT, EXECUTION_FOR_ALL, EXECUTION_ONE_OF, EXECUTION_OR,
    EXECUTION_SUBJECT_REQUIREMENT, EXECUTION_WHEN, LAB, OPERATION_VARIABLE_ACCEPTS_REFERENCE,
    OPERATION_VARIABLE_PARAMETER, PRODUCT_ASSET_TYPE,
)
from aas_model.resource_instances import RESOURCE_FACTORIES
from aas_model.resource_template.operational import MODULE_CONTROL, OperationalCapabilityDescription
from aas_model.submodel_templates.capability_description import ModuleCapabilityDescription
from aas_model.submodel_templates.execution import (
    And, Body, ConditionOperator, ConditionSet, EffectOperator, EffectSet, EndTerms, ForAll, OneOfEffects, Or,
    Outcome, PreTerms, QuantifiedVariable, StateCondition, StateEffect, TermValue, When, WhenCondition, WhenThen,
)

OPERATIONAL = ("stopperingStation", "cappingStation", "dispensingStation", "loadingStation", "unloadingStation",
               "inspectionStation", "planarShuttle1", "planarShuttle2", "planarShuttle3")


def _capability_description(store):
    return next(s for s in store if isinstance(s, model.Submodel) and s.id_short == "CapabilityDescription")


def _references(element):
    """Every model reference below an element: ReferenceElement values and both ends of a relationship."""
    if isinstance(element, model.ReferenceElement) and isinstance(element.value, model.ModelReference):
        yield element.id_short, element.value
    if isinstance(element, model.RelationshipElement):
        for end in (element.first, element.second):
            if isinstance(end, model.ModelReference):
                yield element.id_short, end
    if isinstance(element, (model.SubmodelElementCollection, model.SubmodelElementList)):
        for child in element.value:
            yield from _references(child)


@pytest.mark.parametrize("name", OPERATIONAL)
def test_every_operational_device_has_module_control_realized_by_its_packml_skills(name):
    resource = RESOURCE_FACTORIES[name]()
    containers = resource.capability_description.CapabilitySet[MODULE_CONTROL].CapabilityContainer
    assert set(containers) == {"Occupying", "Releasing"}
    assert containers["Occupying"].Capability.supplemental_semantic_ids == [f"{LAB}Occupying"]
    assert containers["Releasing"].Capability.supplemental_semantic_ids == [f"{LAB}Releasing"]
    skills = resource.skills.Skill
    for container, skill in (("Occupying", "Occupy"), ("Releasing", "Release")):
        (realized,) = containers[container].CapabilityRelations.CapabilityRealizedBy.values()
        assert realized.second.key[-1].value == skill and skill in skills


def test_module_control_is_added_unless_authored_and_survives_json():
    description = OperationalCapabilityDescription()
    assert MODULE_CONTROL in description.CapabilitySet
    restored = ModuleCapabilityDescription.model_validate_json(description.model_dump_json())
    assert restored.model_dump(mode="json") == description.model_dump(mode="json")


@pytest.mark.parametrize("name", OPERATIONAL)
def test_every_reference_of_a_capability_resolves_in_the_built_resource(name):
    """Subjects, the properties of subjects, conditions and effects, and what relates them, all resolve."""
    store = build_from_model(RESOURCE_FACTORIES[name]())
    found = 0
    for capability_set in _capability_description(store).submodel_element:
        for container in capability_set.value:
            for id_short, reference in _references(container):
                assert reference.resolve(store) is not None, f"{container.id_short}: {id_short} does not resolve"
                found += 1
    assert found


def test_module_control_states_what_it_needs_and_changes_in_its_relations():
    store = build_from_model(RESOURCE_FACTORIES["dispensingStation"]())
    relations = _capability_description(store).get_referable([MODULE_CONTROL, "Occupying", "CapabilityRelations"])
    pre = {t.display_name["en"]: t for t in relations.get_referable(["ConditionSet", "Pre"]).value}
    assert set(pre) == {"Shuttle at the transfer point", "Unit on the shuttle"}         # the queue arbitrates
    end = {t.display_name["en"]: t for t in relations.get_referable(["EffectSet", "End"]).value}
    assert end["Unit held here"].get_referable("Operator").value == "assign"
    served = end["Serves the unit"]                                                     # observed: the tree waits
    assert served.supplemental_semantic_id[0].key[0].value == f"{LAB}OccupiedBy"
    assert served.get_referable("Subject").value.resolve(store).display_name["en"] == "This device"
    assert served.get_referable("ValueReference").value.resolve(store).display_name["en"] == "Unit received"
    releasing = _capability_description(store).get_referable([MODULE_CONTROL, "Releasing", "CapabilityRelations"])
    pre = {t.display_name["en"] for t in releasing.get_referable(["ConditionSet", "Pre"]).value}
    assert "Serves the unit" in pre
    end = {t.display_name["en"]: t for t in releasing.get_referable(["EffectSet", "End"]).value}
    assert end["Free again"].get_referable("Operator").value == "clear"
    # The skill's Operation is the device's command and nothing more; the Translation builds it from the subjects.
    occupy = RESOURCE_FACTORIES["dispensingStation"]().skills.Skill["Occupy"].Start.SkillOperation["Start"]
    assert not occupy.input_variable and [v.id_short for v in occupy.in_output_variable] == ["Uuid"]
    assert [v.id_short for v in occupy.output_variable] == ["State"]
    translation = relations.get_referable("Translation")
    assert b"function call(" in translation.get_referable("Call").value
    assert b"function reply(" in translation.get_referable("Reply").value


def test_dispensing_binds_the_unit_and_the_volume_of_its_operation():
    resource = RESOURCE_FACTORIES["dispensingStation"]()
    relations = resource.capability_description.CapabilitySet["OfferedCapabilities"].CapabilityContainer[
        "Dispensing"].CapabilityRelations
    unit = relations.Subjects.value[1]
    assert unit.value.type_ == "ExternalReference" and unit.value.key[0].value == PRODUCT_ASSET_TYPE
    (pre,) = relations.ConditionSet.Pre.term.values()
    assert isinstance(pre, StateCondition) and pre.supplemental_semantic_ids == [f"{LAB}ContentVolume"]
    assert (pre.Operator.value, pre.Value.value) == ("equal", "0.0")
    (end,) = relations.EffectSet.End.term.values()
    assert isinstance(end, StateEffect) and end.Operator.value == "increase"
    assert [key.value for key in end.ValueReference.value.key[-2:]] == ["Start", "Volume"]
    assert relations.CapabilityRealizedBy                              # the instance added its skill

    required = relations.Subjects.value[2]                                # the volume the product requires
    assert EXECUTION_SUBJECT_REQUIREMENT in required.supplemental_semantic_ids
    assert required.value.type_ == "ExternalReference" and required.value.key[0].value == f"{LAB}FillVolume"
    assert relations.Translation is not None                              # the call: unit's uuid, that volume

    operation = resource.skills.Skill["Dispensing"].Start.SkillOperation["Start"]
    variables = {v.id_short: v for v in operation.input_variable}
    assert set(variables) == {"Volume"}                                   # the device's, nothing else
    assert variables["Volume"].semantic_id == OPERATION_VARIABLE_PARAMETER
    assert variables["Volume"].supplemental_semantic_ids == [f"{LAB}Volume"]
    assert any(q.semantic_id == OPERATION_VARIABLE_ACCEPTS_REFERENCE for q in variables["Volume"].qualifiers)


def test_a_shuttle_move_takes_the_shuttle_to_a_place_the_call_names():
    """MoveToPosition's subjects are the shuttle and the target place; it ends with the shuttle at that place. The
    place is the call's: the Translation sends the device the place's pose, and nothing else of the call."""
    from aas_model.submodel_templates.coordinates import VAR_COORDINATE

    resource = RESOURCE_FACTORIES["planarShuttle1"]()
    container = resource.capability_description.CapabilitySet["AuxiliaryCapabilities"].CapabilityContainer["MoveToPosition"]
    assert container.Capability.supplemental_semantic_ids == [f"{LAB}Transporting"]
    relations = container.CapabilityRelations
    shuttle, place = relations.Subjects.value
    assert [s.display_name["en"] for s in (shuttle, place)] == ["This shuttle", "Target place"]
    assert place.value.type_ == "ExternalReference" and place.value.key[0].value == f"{LAB}TransferPoint"
    (end,) = relations.EffectSet.End.term.values()
    assert (end.Operator.value, end.supplemental_semantic_ids) == ("assign", [f"{LAB}Location"])
    assert [k.value for k in end.Subject.value.key[-2:]] == ["Subjects", "0"]
    assert [k.value for k in end.ValueReference.value.key[-2:]] == ["Subjects", "1"]

    operation = resource.skills.Skill["MoveToPosition"].Start.SkillOperation["Start"]
    assert [v.id_short for v in operation.input_variable] == ["X", "Y", "Theta"]
    assert relations.Translation is not None


def test_the_filling_modules_transfer_point_is_a_place_a_shuttle_can_be_sent_to():
    """What a planner grounds the Target place with: a coordinate of the line, here the filling module's
    TransferPoint, relative to the module's base."""
    from aas_model.resource_instances.modules import MODULE_FACTORIES
    from aas_model.resource_instances.modules.filling_module import TRANSFER_POINT
    from aas_model.submodel_templates.coordinates import VAR_COORDINATE
    from aas_pydantic import ModelReference
    from aas_pydantic.convert_pydantic_model import _make_basyx_reference

    store = model.DictIdentifiableStore()
    for factory in (MODULE_FACTORIES["fillingModule"], RESOURCE_FACTORIES["planarShuttle1"]):
        for identifiable in build_from_model(factory()):
            store.add(identifiable)
    point = _make_basyx_reference(ModelReference(key=TRANSFER_POINT)).resolve(store)
    assert point.semantic_id.key[0].value == VAR_COORDINATE
    assert point.supplemental_semantic_id[0].key[0].value == f"{LAB}TransferPoint"   # what a place subject is
    assert point.get_referable("RelativeTo").value.resolve(store).id_short == "ModuleBase"


def test_term_kinds_nest_survive_json_and_are_told_apart_by_semantic_id_in_aas():
    condition = StateCondition(Operator=ConditionOperator(value="equal"), Value=TermValue(value="0", value_type="xs:int"))
    effect = StateEffect(Operator=EffectOperator(value="assign"), Value=TermValue(value="1", value_type="xs:int"))
    conditions = ConditionSet(Pre=PreTerms(term={
        "Term_00": And(term={"Term_00": condition, "Term_01": Or(term={"Term_00": condition})}),
        "Term_01": ForAll(Variable=QuantifiedVariable.over(PRODUCT_ASSET_TYPE, display_name={"en": "Any unit"}),
                          Body=Body(term={"Term_00": condition})),
    }))
    effects = EffectSet(End=EndTerms(term={
        "Term_00": When(Condition=WhenCondition(term={"Term_00": condition}), Then=WhenThen(term={"Term_00": effect})),
        "Term_01": OneOfEffects(outcome={"In": Outcome(term={"Term_00": effect}), "Out": Outcome()}),
    }))
    for made in (conditions, effects):
        restored = type(made).model_validate_json(made.model_dump_json())
        assert json.loads(restored.model_dump_json()) == json.loads(made.model_dump_json())
    pre = ConditionSet.model_validate_json(conditions.model_dump_json()).Pre.term
    assert (type(pre["Term_00"]), type(pre["Term_00"].term["Term_01"]), type(pre["Term_01"])) == (And, Or, ForAll)
    variable = pre["Term_01"].Variable                      # the quantifier declares what it ranges over
    assert variable.value.type_ == "ExternalReference" and variable.value.key[0].value == PRODUCT_ASSET_TYPE
    assert variable.display_name == {"en": "Any unit"}
    end = EffectSet.model_validate_json(effects.model_dump_json()).End.term
    assert (type(end["Term_00"]), type(end["Term_01"])) == (When, OneOfEffects)

    resource = RESOURCE_FACTORIES["dispensingStation"]()
    relations = resource.capability_description.CapabilitySet["OfferedCapabilities"].CapabilityContainer[
        "Dispensing"].CapabilityRelations
    relations.ConditionSet, relations.EffectSet = conditions, effects
    built = _capability_description(build_from_model(resource)).get_referable(
        ["OfferedCapabilities", "Dispensing", "CapabilityRelations"])
    ids = {path: built.get_referable(path.split("/")).semantic_id.key[0].value for path in (
        "ConditionSet/Pre/Term_00", "ConditionSet/Pre/Term_00/Term_01", "ConditionSet/Pre/Term_01",
        "ConditionSet/Pre/Term_00/Term_00", "EffectSet/End/Term_00", "EffectSet/End/Term_01",
        "EffectSet/End/Term_00/Then/Term_00")}
    assert ids == {
        "ConditionSet/Pre/Term_00": EXECUTION_AND, "ConditionSet/Pre/Term_00/Term_01": EXECUTION_OR,
        "ConditionSet/Pre/Term_01": EXECUTION_FOR_ALL, "ConditionSet/Pre/Term_00/Term_00": EXECUTION_CONDITION,
        "EffectSet/End/Term_00": EXECUTION_WHEN, "EffectSet/End/Term_01": EXECUTION_ONE_OF,
        "EffectSet/End/Term_00/Then/Term_00": EXECUTION_EFFECT,
    }


def test_operators_are_restricted_to_their_kind():
    with pytest.raises(ValueError):
        ConditionOperator(value="assign")
    with pytest.raises(ValueError):
        EffectOperator(value="equal")


def test_a_product_declares_the_state_of_its_units():
    from aas_model.product_template import Product
    from aas_model.submodel_templates.knowledge import Knowledge, StateVariable, StateVariableInitial
    from aas_model.submodel_templates.variables import Variables

    product = Product(id_short="DemoVialAAS", variables=Variables(id_short="Variables", Knowledge=Knowledge(
        variable={"ContentVolume": StateVariable(
            supplemental_semantic_ids=[f"{LAB}ContentVolume"],
            Initial=StateVariableInitial(value="0.0", value_type="xs:double"))},
    )))
    restored = Product.model_validate_json(product.model_dump_json())
    assert restored.variables.Knowledge.variable["ContentVolume"].Initial.value == "0.0"
    store = build_from_model(restored)
    variables = next(s for s in store if isinstance(s, model.Submodel) and s.id_short == "Variables")
    assert variables.id.endswith("/submodels/Variables")
    assert [e.id_short for e in variables.submodel_element] == ["Knowledge"]       # a product type's Variables
    assert {e.id_short for e in variables.get_referable("Knowledge").value} == {"ContentVolume", "Target"}
