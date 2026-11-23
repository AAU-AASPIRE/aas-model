"""The execution semantics of capabilities: conditions as IDTA 02020 constraints, effects in an EffectSet beside
them, subjects as references; their structure, references and how they serialize."""

from __future__ import annotations

import json

import pytest
from basyx.aas import model

from aas_model import build_from_model
from aas_model.constants import (
    EXECUTION_AND, EXECUTION_CONDITION, EXECUTION_EFFECT, EXECUTION_FOR_ALL, EXECUTION_ONE_OF, EXECUTION_OR,
    EXECUTION_STATE_CONSTRAINT, EXECUTION_SUBJECT_PRODUCT, EXECUTION_WHEN, LAB, OPERATION_VARIABLE_PARAMETER,
    OPERATION_VARIABLE_SUBJECT,
)
from aas_model.resource_instances import RESOURCE_FACTORIES
from aas_model.resource_template.operational import MODULE_CONTROL, OperationalCapabilityDescription
from aas_model.submodel_templates.capability_description import (
    ModuleCapabilityDescription, StateConditionalType, StateConstraint, StateConstraintContainer,
    StatedConstraintPropertyRelations,
)
from aas_model.submodel_templates.control_component_instance import OPERATION_VARIABLE_OPTIONAL
from aas_model.submodel_templates.execution import (
    And, Body, ConditionOperator, EffectContainer, EffectDefinition, EffectOperator, EffectPropertyRelations,
    EffectSet, EffectTimingType, ForAll, OneOfEffects, Or, Outcome, QuantifiedVariable, StateCondition, StateEffect,
    TermValue, When, WhenCondition, WhenThen,
)

OPERATIONAL = ("syntegonStoppering", "cytivaCapping", "imaDispensing", "imaLoadingSystem", "optimaUnloading",
               "omronCamera", "planarShuttle1", "planarShuttle2", "planarShuttle3")


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
    assert containers["Occupying"].Capability.supplemental_semantic_ids == [f"{LAB}Receiving"]
    assert containers["Releasing"].Capability.supplemental_semantic_ids == [f"{LAB}Releasing"]
    skills = resource.control_component_instance.Skills.Skill
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


def test_module_control_states_its_condition_as_a_02020_constraint_and_its_effect_beside_it():
    store = build_from_model(RESOURCE_FACTORIES["imaDispensing"]())
    occupying = _capability_description(store).get_referable([MODULE_CONTROL, "Occupying"])
    room = occupying.get_referable(["CapabilityRelations", "ConstraintSet", "HasRoom"])
    assert room.get_referable("PropertyConditionalType").value == "Pre"
    custom = room.get_referable("CustomConstraint")
    assert custom.supplemental_semantic_id[0].key[0].value == EXECUTION_STATE_CONSTRAINT
    term = custom.get_referable("Term")
    occupancy = term.get_referable("Property").value.resolve(store)
    assert occupancy.supplemental_semantic_id[0].key[0].value == f"{LAB}Occupancy" and occupancy.value is None
    assert occupancy.parent.get_referable("OfSubject").second.resolve(store).id_short == "Self"
    assert {r.second.resolve(store).parent.id_short for r in room.get_referable("ConstraintPropertyRelations").value} \
        == {"Occupancy", "Capacity"}
    effect = occupying.get_referable(["CapabilityRelations", "EffectSet", "TakesPlace"])
    assert effect.get_referable("EffectTimingType").value == "End"
    assert effect.get_referable(["Effect", "Term", "Operator"]).value == "increase"


def test_dispensing_binds_the_unit_and_the_volume_of_its_operation():
    resource = RESOURCE_FACTORIES["imaDispensing"]()
    container = resource.capability_description.CapabilitySet["Processing"].CapabilityContainer["Dispensing"]
    unit = container.Subjects.subject["Unit"]
    assert unit.semantic_id == EXECUTION_SUBJECT_PRODUCT
    assert [key.value for key in unit.value.key[-2:]] == ["operation", "Unit"]
    empty = container.CapabilityRelations.ConstraintSet["ConstraintSet"].PropertyConstraintContainer["UnitEmpty"]
    assert empty.PropertyConditionalType.value == "Pre"
    (pre,) = empty.CustomConstraint.value.values()
    assert isinstance(pre, StateCondition) and (pre.Operator.value, pre.Value.value) == ("equal", "0.0")
    assert pre.Property.value.key[-2].value == "ContentVolume"
    filled = container.CapabilityRelations.EffectSet.EffectContainer["Filled"]
    (end,) = filled.Effect.term.values()
    assert filled.EffectTimingType.value == "End" and isinstance(end, StateEffect) and end.Operator.value == "increase"
    assert [key.value for key in end.ValueReference.value.key[-2:]] == ["operation", "Volume"]
    assert container.CapabilityRelations.CapabilityRealizedBy             # the instance added its skill

    variables = {v.id_short: v for v in resource.control_component_instance.Skills.Skill["Dispensing"].operation
                 .input_variable}
    assert variables["Unit"].semantic_id == OPERATION_VARIABLE_SUBJECT
    assert any(q.semantic_id == OPERATION_VARIABLE_OPTIONAL for q in variables["Unit"].qualifiers)
    assert variables["Volume"].semantic_id == OPERATION_VARIABLE_PARAMETER
    assert variables["Volume"].supplemental_semantic_ids == [f"{LAB}Volume"]


def test_shuttle_takes_the_unit_it_carries_and_measures_where_it_ends():
    resource = RESOURCE_FACTORIES["planarShuttle1"]()
    container = resource.capability_description.CapabilitySet["Transport"].CapabilityContainer["MoveToPosition"]
    assert container.Capability.supplemental_semantic_ids == [f"{LAB}Transporting"]
    assert [key.value for key in container.Subjects.subject["Unit"].value.key[-2:]] == ["operation", "ProductID"]
    (end,) = container.CapabilityRelations.EffectSet.EffectContainer["PositionKnown"].Effect.term.values()
    assert end.Operator.value == "measured" and end.Property.value.key[-2].value == "Position"


def test_term_kinds_survive_json_and_are_told_apart_by_semantic_id_in_aas():
    condition = StateCondition(Operator=ConditionOperator(value="equal"), Value=TermValue(value="0", value_type="xs:int"))
    effect = StateEffect(Operator=EffectOperator(value="assign"), Value=TermValue(value="1", value_type="xs:int"))
    tree = StateConstraintContainer(
        CustomConstraint=StateConstraint(value={"Term": And(term={
            "Term_00": condition, "Term_01": Or(term={"Term_00": condition}),
            "Term_02": ForAll(Variable=QuantifiedVariable(), Body=Body(term={"Term_00": condition})),
        })}),
        PropertyConditionalType=StateConditionalType(value="PreInvariant"),
        ConstraintPropertyRelations=StatedConstraintPropertyRelations(),
    )
    effects = EffectSet(EffectContainer={
        "Conditional": EffectContainer(
            EffectTimingType=EffectTimingType(value="End"),
            Effect=EffectDefinition(term={"Term": When(Condition=WhenCondition(term={"Term_00": condition}),
                                                       Then=WhenThen(term={"Term_00": effect}))}),
            EffectPropertyRelations=EffectPropertyRelations()),
        "Outcomes": EffectContainer(
            EffectTimingType=EffectTimingType(value="End"),
            Effect=EffectDefinition(term={"Term": OneOfEffects(outcome={"In": Outcome(term={"Term_00": effect}),
                                                                        "Out": Outcome()})}),
            EffectPropertyRelations=EffectPropertyRelations()),
    })
    for made in (tree, effects):
        restored = type(made).model_validate_json(made.model_dump_json())
        assert json.loads(restored.model_dump_json()) == json.loads(made.model_dump_json())
    restored = StateConstraintContainer.model_validate_json(tree.model_dump_json())
    root = restored.CustomConstraint.value["Term"]
    assert (type(root), type(root.term["Term_01"]), type(root.term["Term_02"])) == (And, Or, ForAll)

    resource = RESOURCE_FACTORIES["imaDispensing"]()
    relations = resource.capability_description.CapabilitySet["Processing"].CapabilityContainer[
        "Dispensing"].CapabilityRelations
    relations.ConstraintSet["ConstraintSet"].PropertyConstraintContainer["Tree"] = tree
    relations.EffectSet = effects
    built = _capability_description(build_from_model(resource)).get_referable(
        ["Processing", "Dispensing", "CapabilityRelations"])
    ids = {path: built.get_referable(path.split("/")).semantic_id.key[0].value for path in (
        "ConstraintSet/Tree/CustomConstraint/Term", "ConstraintSet/Tree/CustomConstraint/Term/Term_00",
        "ConstraintSet/Tree/CustomConstraint/Term/Term_01", "ConstraintSet/Tree/CustomConstraint/Term/Term_02",
        "EffectSet/Conditional/Effect/Term", "EffectSet/Conditional/Effect/Term/Then/Term_00",
        "EffectSet/Outcomes/Effect/Term")}
    assert ids == {
        "ConstraintSet/Tree/CustomConstraint/Term": EXECUTION_AND,
        "ConstraintSet/Tree/CustomConstraint/Term/Term_00": EXECUTION_CONDITION,
        "ConstraintSet/Tree/CustomConstraint/Term/Term_01": EXECUTION_OR,
        "ConstraintSet/Tree/CustomConstraint/Term/Term_02": EXECUTION_FOR_ALL,
        "EffectSet/Conditional/Effect/Term": EXECUTION_WHEN,
        "EffectSet/Conditional/Effect/Term/Then/Term_00": EXECUTION_EFFECT,
        "EffectSet/Outcomes/Effect/Term": EXECUTION_ONE_OF,
    }


def test_operators_and_timings_are_restricted_to_their_kind():
    with pytest.raises(ValueError):
        ConditionOperator(value="assign")
    with pytest.raises(ValueError):
        EffectOperator(value="equal")
    with pytest.raises(ValueError):
        StateConditionalType(value="Start")
    with pytest.raises(ValueError):
        EffectTimingType(value="Pre")


def test_a_product_declares_the_state_of_its_units():
    from aas_model.product_template import Product
    from aas_model.submodel_templates.state_declaration import (
        StateDeclaration, StateVariable, StateVariableInitial,
    )

    product = Product(id_short="DemoVialAAS", state_declaration=StateDeclaration(
        id_short="StateDeclaration",
        variable={"ContentVolume": StateVariable(
            supplemental_semantic_ids=[f"{LAB}ContentVolume"],
            Initial=StateVariableInitial(value="0.0", value_type="xs:double"))},
    ))
    restored = Product.model_validate_json(product.model_dump_json())
    assert restored.state_declaration.variable["ContentVolume"].Initial.value == "0.0"
    store = build_from_model(restored)
    declared = next(s for s in store if isinstance(s, model.Submodel) and s.id_short == "StateDeclaration")
    assert declared.id.endswith("/submodels/StateDeclaration")
    assert {e.id_short for e in declared.submodel_element} == {"ContentVolume", "Target"}
