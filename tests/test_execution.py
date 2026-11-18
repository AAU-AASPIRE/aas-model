"""The execution semantics of capabilities: their structure, references and how they serialize."""

from __future__ import annotations

import json

import pytest
from basyx.aas import model

from aas_model import build_from_model
from aas_model.constants import (
    EXECUTION, EXECUTION_AND, EXECUTION_CONDITION, EXECUTION_EFFECT, EXECUTION_FOR_ALL, EXECUTION_ONE_OF, EXECUTION_OR,
    EXECUTION_WHEN, LAB, OPERATION_VARIABLE_PARAMETER, OPERATION_VARIABLE_SUBJECT,
)
from aas_model.resource_instances import RESOURCE_FACTORIES
from aas_model.resource_template.operational import MODULE_CONTROL, OperationalCapabilityDescription
from aas_model.submodel_templates.capability_description import ModuleCapabilityDescription
from aas_model.submodel_templates.control_component_instance import OPERATION_VARIABLE_OPTIONAL
from aas_model.submodel_templates.execution import (
    And, Body, ConditionOperator, EffectOperator, EndTerms, Execution, ExecutionConditions, ExecutionEffects,
    ExecutionSubject, ForAll, OneOfEffects, Or, Outcome, PreTerms, StateCondition, StateEffect, SubjectRole,
    TermValue, When, WhenCondition, WhenThen,
)

OPERATIONAL = ("syntegonStoppering", "cytivaCapping", "imaDispensing", "imaLoadingSystem", "optimaUnloading",
               "omronCamera", "planarShuttle1", "planarShuttle2", "planarShuttle3")


def _capability_description(store):
    return next(s for s in store if isinstance(s, model.Submodel) and s.id_short == "CapabilityDescription")


def _references(element):
    """Every ModelReference below an element (ReferenceElement values)."""
    if isinstance(element, model.ReferenceElement) and isinstance(element.value, model.ModelReference):
        yield element.id_short, element.value
    if isinstance(element, model.SubmodelElementCollection):
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
def test_every_execution_reference_resolves_in_the_built_resource(name):
    store = build_from_model(RESOURCE_FACTORIES[name]())
    description = _capability_description(store)
    found = 0
    for capability_set in description.submodel_element:
        for container in capability_set.value:
            execution = next((e for e in container.value if e.id_short == "Execution"), None)
            if execution is None:
                continue
            assert execution.semantic_id.key[0].value == EXECUTION
            for id_short, reference in _references(execution):
                assert reference.resolve(store) is not None, f"{container.id_short}: {id_short} does not resolve"
                found += 1
    assert found


def test_dispensing_binds_the_unit_and_the_volume_of_its_operation():
    resource = RESOURCE_FACTORIES["imaDispensing"]()
    execution = resource.capability_description.CapabilitySet["Processing"].CapabilityContainer["Dispensing"].Execution
    unit = execution.Subjects.subject["Unit"]
    assert unit.Role.value == "Product"
    assert [key.value for key in unit.Binding.value.key[-2:]] == ["operation", "Unit"]
    (pre,) = execution.Conditions.Pre.term.values()
    assert isinstance(pre, StateCondition) and pre.supplemental_semantic_ids == [f"{LAB}ContentVolume"]
    assert (pre.Operator.value, pre.Value.value) == ("equal", "0.0")
    (end,) = execution.Effects.End.term.values()
    assert isinstance(end, StateEffect) and end.Operator.value == "increase"
    assert [key.value for key in end.ValueReference.value.key[-2:]] == ["operation", "Volume"]

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
    unit = container.Execution.Subjects.subject["Unit"]
    assert [key.value for key in unit.Binding.value.key[-2:]] == ["operation", "ProductID"]
    (end,) = container.Execution.Effects.End.term.values()
    assert end.Operator.value == "measured" and end.supplemental_semantic_ids == [f"{LAB}Position"]


def test_term_kinds_survive_json_and_are_told_apart_by_semantic_id_in_aas():
    condition = StateCondition(Operator=ConditionOperator(value="equal"), Value=TermValue(value="0", value_type="xs:int"))
    effect = StateEffect(Operator=EffectOperator(value="assign"), Value=TermValue(value="1", value_type="xs:int"))
    execution = Execution(
        Conditions=ExecutionConditions(Pre=PreTerms(term={
            "Term_00": And(term={"Term_00": condition, "Term_01": Or(term={"Term_00": condition})}),
            "Term_01": ForAll(Variable=ExecutionSubject(Role=SubjectRole(value="Variable")),
                              Body=Body(term={"Term_00": condition})),
        })),
        Effects=ExecutionEffects(End=EndTerms(term={
            "Term_00": When(Condition=WhenCondition(term={"Term_00": condition}),
                            Then=WhenThen(term={"Term_00": effect})),
            "Term_01": OneOfEffects(outcome={"In": Outcome(term={"Term_00": effect}), "Out": Outcome()}),
        })),
    )
    restored = Execution.model_validate_json(execution.model_dump_json())
    assert json.loads(restored.model_dump_json()) == json.loads(execution.model_dump_json())
    pre = restored.Conditions.Pre.term
    assert (type(pre["Term_00"]), type(pre["Term_00"].term["Term_01"]), type(pre["Term_01"])) == (And, Or, ForAll)
    end = restored.Effects.End.term
    assert (type(end["Term_00"]), type(end["Term_01"])) == (When, OneOfEffects)

    resource = RESOURCE_FACTORIES["imaDispensing"]()
    resource.capability_description.CapabilitySet["Processing"].CapabilityContainer["Dispensing"].Execution = execution
    description = _capability_description(build_from_model(resource))
    built = description.get_referable(["Processing", "Dispensing", "Execution"])
    ids = {
        path: built.get_referable(path.split("/")).semantic_id.key[0].value
        for path in ("Conditions/Pre/Term_00", "Conditions/Pre/Term_00/Term_01", "Conditions/Pre/Term_01",
                     "Conditions/Pre/Term_00/Term_00", "Effects/End/Term_00", "Effects/End/Term_01",
                     "Effects/End/Term_00/Then/Term_00")
    }
    assert ids == {
        "Conditions/Pre/Term_00": EXECUTION_AND, "Conditions/Pre/Term_00/Term_01": EXECUTION_OR,
        "Conditions/Pre/Term_01": EXECUTION_FOR_ALL, "Conditions/Pre/Term_00/Term_00": EXECUTION_CONDITION,
        "Effects/End/Term_00": EXECUTION_WHEN, "Effects/End/Term_01": EXECUTION_ONE_OF,
        "Effects/End/Term_00/Then/Term_00": EXECUTION_EFFECT,
    }


def test_operators_are_restricted_to_their_kind():
    with pytest.raises(ValueError):
        ConditionOperator(value="assign")
    with pytest.raises(ValueError):
        EffectOperator(value="equal")


def test_a_module_capability_holds_its_execution_bound_to_its_skills_operation():
    from aas_pydantic import Capability, Key, ModelReference
    from aas_model.resource_template.modules import Module, ModuleSkill
    from aas_model.submodel_templates.arso import skills as s
    from aas_model.submodel_templates.capability_description import (
        ModuleCapabilityContainer, ModuleCapabilityDescription, ModuleCapabilitySet,
    )
    from aas_model.submodel_templates.control_component_instance import ParameterVariable, SubjectVariable
    from aas_model.submodel_templates.execution import (
        Subjects, SubjectBinding, TermSubject, TermValueReference,
    )

    aas_id = "https://smartproductionlab.aau.dk/aas/DemoFillingModuleAAS"
    skills_sm, capabilities_sm = f"{aas_id}/submodels/Skills", f"{aas_id}/submodels/CapabilityDescription"
    start = [Key(type_="Submodel", value=skills_sm), Key(type_="SubmodelElementCollection", value="Dispensing"),
             Key(type_="SubmodelElementCollection", value="Start"), Key(type_="Operation", value="Start")]
    execution = [Key(type_="Submodel", value=capabilities_sm),
                 Key(type_="SubmodelElementCollection", value="OfferedCapabilities"),
                 Key(type_="SubmodelElementCollection", value="Filling"),
                 Key(type_="SubmodelElementCollection", value="Execution"),
                 Key(type_="SubmodelElementCollection", value="Subjects"),
                 Key(type_="SubmodelElementCollection", value="Unit")]
    module = Module(id_short="DemoFillingModuleAAS", id=aas_id)
    module.skills.Skill["Dispensing"] = ModuleSkill(Start=s.Start(SkillOperation={"Start": s.SkillOperation(
        id_short="Start", input_variable=[
            ParameterVariable(id_short="Volume", value_type="xs:double", supplemental_semantic_ids=[f"{LAB}Volume"]),
            SubjectVariable(id_short="Unit"),
        ])}))
    module.capability_description = ModuleCapabilityDescription(CapabilitySet={
        "OfferedCapabilities": ModuleCapabilitySet(CapabilityContainer={"Filling": ModuleCapabilityContainer(
            Capability=Capability(supplemental_semantic_ids=[f"{LAB}Filling"]),
            Execution=Execution(
                Subjects=Subjects(subject={"Unit": ExecutionSubject(
                    Role=SubjectRole(value="Product"),
                    Binding=SubjectBinding(value=ModelReference(key=(*start, Key(type_="Property", value="Unit")))),
                )}),
                Effects=ExecutionEffects(End=EndTerms(term={"Term_00": StateEffect(
                    supplemental_semantic_ids=[f"{LAB}ContentVolume"],
                    Subject=TermSubject(value=ModelReference(key=tuple(execution))),
                    Operator=EffectOperator(value="increase"),
                    ValueReference=TermValueReference(value=ModelReference(
                        key=(*start, Key(type_="Property", value="Volume")))),
                )})),
            ),
        )}),
    })
    restored = Module.model_validate_json(module.model_dump_json())
    assert json.loads(restored.model_dump_json()) == json.loads(module.model_dump_json())
    store = build_from_model(restored)
    description = _capability_description(store)
    references = dict(_references(description.get_referable(["OfferedCapabilities", "Filling", "Execution"])))
    assert set(references) == {"Binding", "Subject", "ValueReference"}
    assert all(reference.resolve(store) is not None for reference in references.values())


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
