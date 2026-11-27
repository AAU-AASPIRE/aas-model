#!/usr/bin/env python3
"""Write the shared execution fixtures' AAS (``<nn-name>/aas.json``) from aas-model's classes.

Each fixture is one small AAS environment (two where the fixture is about a relation between AASs: a batch and its
product type, a specialization and what it specializes), built from the same pydantic templates the example line uses
and serialized as AAS JSON with sorted keys, so that the same fixture is always the same file. ``expected.json``
beside it is written by hand: it is the canonical reading of section 15 of ``docs/execution-model.md``.
``tests/test_execution_fixtures.py`` fails when a checked-in ``aas.json`` is not what this script writes. Run from the
repository root::

    python tests/fixtures/execution/build.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Callable, ClassVar, NamedTuple

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "src"))

from aas_pydantic import Capability, Key, ModelReference  # noqa: E402
from aas_pydantic.submodel_templates.asset_interfaces_mapping_configuration import SinksItem, SourcesItem  # noqa: E402
from aas_pydantic.submodel_templates.capability_description import (  # noqa: E402
    BasicConstraint, CapabilityGeneralizedBy, ConstraintHasProperty, ConstraintPropertyRelations, ConstraintType,
    GeneralizedBySet, PropertyConditionalType, PropertyProperty,
)
from basyx.aas import model  # noqa: E402
from basyx.aas.adapter.json import json_serialization  # noqa: E402

from aas_model import build_from_model  # noqa: E402
from aas_model.batch_template import Batch  # noqa: E402
from aas_model.constants import BASE_URL, LAB, PRODUCT_ASSET_TYPE, RESOURCE_TYPE  # noqa: E402
from aas_model.resource_template.modules import ModuleSkill  # noqa: E402
from aas_model.resource_template.modules.asset import ArsoResource  # noqa: E402
from aas_model.submodel_templates import Aimc, AimcMappingConfiguration, AimcMappingConfigurations  # noqa: E402
from aas_model.submodel_templates.arso import skills as s  # noqa: E402
from aas_model.submodel_templates.batch import (  # noqa: E402
    BatchInformation, BatchProductType, BatchQuantity, Goal, GoalCondition,
)
from aas_model.submodel_templates.capability_description import (  # noqa: E402
    AUXILIARY_CAPABILITIES, MODULE_CONTROL_CAPABILITIES, OFFERED_CAPABILITIES, BasicConstraintContainer,
    ModuleCapabilityContainer, ModuleCapabilityDescription, ModuleCapabilityRelations, ModuleCapabilitySet,
    ModuleConstraintSet, RealizedBySkill, StatedProperty, StatedPropertySet,
)
from aas_model.submodel_templates.control_component_instance import ParameterVariable  # noqa: E402
from aas_model.submodel_templates.coordinates import CoordinateX, CoordinateY, Coordinates, RelativeCoordinate  # noqa: E402
from aas_model.submodel_templates.execution import (  # noqa: E402
    And, Body, CarrierSubject, ConditionOperator, ConditionSet, DuringTerms, EffectBody, EffectForAll, EffectOperator,
    EffectSet, EndTerms, ExecutionDuration, ExecutionSubject, Exists, ForAll, FormulaUse, FormulaUses, InvariantTerms,
    Not, OneOfEffects, Or, Outcome, PlaceSubject, PostTerms, PreTerms, QuantifiedVariable, Rate, RequirementSubject,
    SelfSubject, StartTerms, StateCondition, StateEffect, Subjects, TermFormula, TermSubject, TermValue,
    TermValueReference, Translation, UnitSubject, When, WhenCondition, WhenThen,
)
from aas_model.submodel_templates.knowledge import (  # noqa: E402
    Knowledge, StateVariable, StateVariableCardinality, StateVariableInitial, StateVariableValueType,
)
from aas_model.submodel_templates.skills import ModuleSkills  # noqa: E402
from aas_model.submodel_templates.variables import MeasurementsGroup, Variables  # noqa: E402

FIXTURES_BASE = f"{BASE_URL}/aas/fixtures"
SKILL = f"{BASE_URL}/skill"
SKILL_TYPE = f"{BASE_URL}/skills"
SMC, SML, SM = "SubmodelElementCollection", "SubmodelElementList", "Submodel"
OFFERED, AUXILIARY, CONTROL = OFFERED_CAPABILITIES, AUXILIARY_CAPABILITIES, MODULE_CONTROL_CAPABILITIES
REQUIRED = "RequiredCapabilities"
IDTA_CAPABILITY = "https://admin-shell.io/idta/CapabilityDescription/Capability/1/0"


def lab(name: str) -> str:
    return f"{LAB}{name}"


CV, WEIGHED, HELD_BY, POSITION = lab("ContentVolume"), lab("Weighed"), lab("HeldBy"), lab("Position")
FILL_RESULT, FILL_WEIGHT, LOCATION, OCCUPIED_BY = lab("FillResult"), lab("FillWeight"), lab("Location"), lab("OccupiedBy")
STOPPERED, CAPPED, INSPECTED = lab("Stoppered"), lab("Capped"), lab("Inspected")
IN_TOLERANCE, OUT_OF_TOLERANCE = lab("InTolerance"), lab("OutOfTolerance")
CARRYING = "urn:fixture:Carrying"


# ── The AAS of a fixture ─────────────────────────────────────────────────────────────────────────────────────

class FixtureAAS(ArsoResource):
    """An AAS with only the submodels a fixture gives it."""
    asset_type: str = f"{RESOURCE_TYPE}/Fixture"


class FixtureProduct(FixtureAAS):
    """The AAS of a product type, with only the submodels a fixture gives it."""
    ASSET_KIND: ClassVar[str] = "Type"
    asset_type: str = PRODUCT_ASSET_TYPE


def aas_id(name: str, role: str = "") -> str:
    return f"{FIXTURES_BASE}/{name}" + (f"/{role}" if role else "")


def make_aas(identifier: str, cls=FixtureAAS, **submodels):
    """The AAS of the id: its idShort is the last segment of the fixture's name and role."""
    short = identifier[len(FIXTURES_BASE) + 1:].replace("/", "_").replace("-", "_")
    return cls(id_short=short, id=identifier, **submodels)


# ── References into an AAS ───────────────────────────────────────────────────────────────────────────────────

def sm_key(aas: str, submodel: str) -> Key:
    return Key(type_=SM, value=f"{aas}/submodels/{submodel}")


def smc(name: str) -> Key:
    return Key(type_=SMC, value=name)


def element(aas: str, submodel: str, path: str, leaf: str = "Property") -> ModelReference:
    """A reference to the element at the idShort ``path`` (collections down to the last, which is a ``leaf``)."""
    *inner, last = path.split("/")
    return ModelReference(key=(sm_key(aas, submodel), *(smc(p) for p in inner), Key(type_=leaf, value=last)))


def aas_ref(aas: str) -> ModelReference:
    return ModelReference(key=(Key(type_="AssetAdministrationShell", value=aas),))


def parameter(aas: str, skill: str, variable: str) -> ModelReference:
    """An input of the Start Operation of a skill (what a call sends)."""
    return ModelReference(key=(sm_key(aas, "Skills"), smc(skill), smc("Start"), Key(type_="Operation", value="Start"),
                               Key(type_="Property", value=variable)))


class Cap:
    """One capability of a fixture: where it is, how it is referenced, and its container once built."""

    def __init__(self, aas: str, name: str, meaning: str, set_: str = AUXILIARY):
        self.aas, self.name, self.meaning, self.set = aas, name, meaning, set_
        self.container: ModuleCapabilityContainer | None = None

    @property
    def key(self) -> tuple:
        return sm_key(self.aas, "CapabilityDescription"), smc(self.set), smc(self.name)

    def subject(self, index: int) -> ModelReference:
        return ModelReference(key=(*self.key, smc("CapabilityRelations"), Key(type_=SML, value="Subjects"),
                                   Key(type_="ReferenceElement", value=str(index))))

    def prop(self, name: str) -> ModelReference:
        """The value of one of the capability's properties."""
        return ModelReference(key=(*self.key, smc("PropertySet"), smc(name), Key(type_="Property", value="Value")))

    def inside(self, path: str, leaf: str = "ReferenceElement") -> ModelReference:
        """An element of the CapabilityRelations (``ConditionSet/Pre/Term_00/Variable``)."""
        *inner, last = path.split("/")
        return ModelReference(key=(*self.key, smc("CapabilityRelations"), *(smc(p) for p in inner),
                                   Key(type_=leaf, value=last)))

    @property
    def capability_key(self) -> ModelReference:
        return ModelReference(key=(*self.key, Key(type_="Capability", value="Capability")))

    def build(self, subjects=(), *, pre=(), invariant=(), post=(), start=(), during=(), end=(), duration=None,
              properties=None, skill=None, general=None, translation=None, constraints=None,
              relations=True) -> "Cap":
        """The container: ``subjects`` and the terms of each phase (lists), ``properties`` (name -> value, meaning),
        the ``skill`` that realizes it, the capability it is ``general``ized by."""
        conditions = ConditionSet(
            Pre=PreTerms(term=terms(pre)) if pre else None,
            Invariant=InvariantTerms(term=terms(invariant)) if invariant else None,
            Post=PostTerms(term=terms(post)) if post else None) if (pre or invariant or post) else None
        effects = EffectSet(
            Start=StartTerms(term=terms(start)) if start else None,
            During=DuringTerms(term=terms(during)) if during else None,
            End=EndTerms(term=terms(end)) if end else None) if (start or during or end) else None
        description = ModuleCapabilityRelations(
            CapabilityRealizedBy={"RealizedBy": RealizedBySkill(
                first=self.capability_key,
                second=ModelReference(key=(sm_key(self.aas, "Skills"), smc(skill))))} if skill else {},
            GeneralizedBySet={"GeneralizedBySet": GeneralizedBySet(CapabilityGeneralizedBy={
                "GeneralizedBy": CapabilityGeneralizedBy(first=self.capability_key, second=general.capability_key)})}
            if general else {},
            ConstraintSet=constraints or {}, Subjects=Subjects(value=list(subjects)) if subjects else None,
            ConditionSet=conditions, EffectSet=effects, Duration=duration, Translation=translation)
        self.container = ModuleCapabilityContainer(
            Capability=Capability(semantic_id=IDTA_CAPABILITY, supplemental_semantic_ids=[self.meaning]),
            PropertySet={"PropertySet": StatedPropertySet(PropertyContainer={
                name: number_property(value, meaning) for name, (value, meaning) in properties.items()})}
            if properties else {},
            CapabilityRelations=description if relations else None)
        return self


def describe(*caps: Cap) -> ModuleCapabilityDescription:
    sets: dict[str, dict] = {}
    for cap in caps:
        sets.setdefault(cap.set, {})[cap.name] = cap.container
    return ModuleCapabilityDescription(id_short="CapabilityDescription", CapabilitySet={
        name: ModuleCapabilitySet(CapabilityContainer=containers) for name, containers in sets.items()})


def number_property(value: float, meaning: str) -> StatedProperty:
    return StatedProperty(PropertyProperty={"Value": PropertyProperty(
        value=repr(float(value)), value_type="xs:double", supplemental_semantic_ids=[meaning])})


# ── Subjects ─────────────────────────────────────────────────────────────────────────────────────────────────

def _named(text: str | None) -> dict:
    return {"display_name": {"en": text}} if text else {}


def this(text: str | None = "This module") -> SelfSubject:
    return SelfSubject(**_named(text))


def fixed(reference: ModelReference, text: str | None) -> ExecutionSubject:
    return ExecutionSubject(value=reference, **_named(text))


def unit(text: str | None = "Unit") -> UnitSubject:
    return UnitSubject(**_named(text))


def carrier(text: str) -> CarrierSubject:
    return CarrierSubject(**_named(text))


def place(text: str) -> PlaceSubject:
    return PlaceSubject(**_named(text))


def required(meaning: str, text: str) -> RequirementSubject:
    return RequirementSubject.of(meaning, **_named(text))


# ── Terms ────────────────────────────────────────────────────────────────────────────────────────────────────

def number(x: float) -> TermValue:
    return TermValue(value=repr(float(x)), value_type="xs:double")


def boolean(x: bool) -> TermValue:
    return TermValue(value="true" if x else "false", value_type="xs:boolean")


def iri(x: str) -> TermValue:
    return TermValue(value=x, value_type="xs:anyURI")


class Formula(NamedTuple):
    """An arithmetic operand: its text, and what each alias stands for (a reference, or a reference and the meaning of
    the subject's property it reads)."""
    text: str
    uses: dict


def uses(table: dict) -> FormulaUses:
    return FormulaUses(use={alias: (FormulaUse(value=ref[0], supplemental_semantic_ids=[ref[1]])
                                    if isinstance(ref, tuple) else FormulaUse(value=ref))
                            for alias, ref in table.items()})


def _operand(operand) -> dict:
    if operand is None:
        return {}
    if isinstance(operand, TermValue):
        return {"Value": operand}
    if isinstance(operand, ModelReference):
        return {"ValueReference": TermValueReference(value=operand)}
    return {"Formula": TermFormula(value=operand.text), "Uses": uses(operand.uses)}


def condition(name: str, meaning: str | None, subject: ModelReference, operator: str, operand=None) -> StateCondition:
    return StateCondition(display_name={"en": name}, supplemental_semantic_ids=[meaning] if meaning else [],
                          Subject=TermSubject(value=subject), Operator=ConditionOperator(value=operator),
                          **_operand(operand))


def effect(name: str, meaning: str | None, subject: ModelReference, operator: str, operand=None,
           rate: ModelReference | None = None) -> StateEffect:
    return StateEffect(display_name={"en": name}, supplemental_semantic_ids=[meaning] if meaning else [],
                       Subject=TermSubject(value=subject), Operator=EffectOperator(value=operator),
                       Rate=Rate(value=rate) if rate else None, **_operand(operand))


def terms(items) -> dict:
    return {f"Term_{i:02d}": item for i, item in enumerate(items)}


def conj(name: str, *items) -> And:
    return And(display_name={"en": name}, term=terms(items))


def disj(name: str, *items) -> Or:
    return Or(display_name={"en": name}, term=terms(items))


def negation(name: str, *items) -> Not:
    return Not(display_name={"en": name}, term=terms(items))


def variable(text: str, meaning: str = PRODUCT_ASSET_TYPE) -> QuantifiedVariable:
    return QuantifiedVariable.over(meaning, display_name={"en": text})


def exists(name: str, var: QuantifiedVariable, *body) -> Exists:
    return Exists(display_name={"en": name}, Variable=var, Body=Body(term=terms(body)))


def for_all(name: str, var: QuantifiedVariable, *body) -> ForAll:
    return ForAll(display_name={"en": name}, Variable=var, Body=Body(term=terms(body)))


def for_all_effects(name: str, var: QuantifiedVariable, *body) -> EffectForAll:
    return EffectForAll(display_name={"en": name}, Variable=var, Body=EffectBody(term=terms(body)))


def when(name: str, if_: list, then: list) -> When:
    return When(display_name={"en": name}, Condition=WhenCondition(term=terms(if_)), Then=WhenThen(term=terms(then)))


def one_of(name: str, meaning: str, **outcomes) -> OneOfEffects:
    """``outcomes``: idShort -> (meaning, effects)."""
    return OneOfEffects(display_name={"en": name}, supplemental_semantic_ids=[meaning], outcome={
        id_short: Outcome(supplemental_semantic_ids=[m], term=terms(effects)) for id_short, (m, effects) in outcomes.items()})


def duration(operand) -> ExecutionDuration:
    return ExecutionDuration(**_operand(operand))


# ── Skills, variables, mappings ──────────────────────────────────────────────────────────────────────────────

def skills(*named: tuple, errors: dict | None = None) -> ModuleSkills:
    """``named``: (skill, [(input, meaning)]); ``errors``: the skill errors' idShorts and descriptions."""
    return ModuleSkills(
        id_short="Skills",
        **({"Errors": s.Errors(SkillError={name: s.SkillError(value=str(i + 1), description=text)
                                           for i, (name, text) in enumerate(errors.items())})} if errors else {}),
        Skill={name: ModuleSkill(
            supplemental_semantic_ids=[f"{SKILL}/Primitive"], SemanticId=s.SemanticId(value=f"{SKILL_TYPE}/{name}"),
            Start=s.Start(semantic_id=f"{SKILL}/Start", SkillOperation={"Start": s.SkillOperation(
                id_short="Start", semantic_id=f"{SKILL}/Start", input_variable=[
                    ParameterVariable(id_short=var, value="1.0", value_type="xs:double",
                                      supplemental_semantic_ids=[meaning]) for var, meaning in inputs])}))
            for name, inputs in named})


def knowledge(*declared: str, measurements=None, **named: StateVariable) -> Variables:
    """A Variables submodel declaring state: ``declared`` are meanings of variables about the AAS itself (named after
    the meaning), ``named`` other StateVariables by idShort."""
    own = {m.rsplit("/", 1)[-1].rsplit(":", 1)[-1]: StateVariable.own(m) for m in declared}
    return Variables(id_short="Variables", Measurements=measurements, Knowledge=Knowledge(variable={**own, **named}))


def transfer_point(aas: str) -> ModelReference:
    return element(aas, "Variables", "Measurements/Coordinates/TransferPoint", SMC)


def coordinates() -> MeasurementsGroup:
    return MeasurementsGroup(value={"Coordinates": Coordinates(coordinate={"TransferPoint": RelativeCoordinate(
        id_short="TransferPoint", display_name={"en": "Transfer point"},
        supplemental_semantic_ids=[lab("TransferPoint")], X=CoordinateX(value="100.0"), Y=CoordinateY(value="60.0"))})})


def mapping(aas: str, name: str, sink: str) -> AimcMappingConfiguration:
    """A mapping of the transfer point's coordinate into the state variable ``sink`` of the Knowledge."""
    return AimcMappingConfiguration(
        id_short=name, DefaultPollingInterval="0.0",
        Sources=[SourcesItem(SourceId="TransferPoint", Source=transfer_point(aas))],
        Sinks=[SinksItem(SinkId=sink, Sink=ModelReference(key=(sm_key(aas, "Variables"), smc("Knowledge"), smc(sink))))],
        Transformation=f"function aimc_main(sources)\n  return {{ {sink} = tonumber(sources.TransferPoint.X) or 0 }}\nend\n")


def mappings(*configurations) -> Aimc:
    return Aimc(id_short="AssetInterfacesMappingConfiguration",
                MappingConfigurations=AimcMappingConfigurations(value=list(configurations)))


# ── The fixtures ─────────────────────────────────────────────────────────────────────────────────────────────

FIXTURES: dict[str, Callable[[str], list]] = {}


def fixture(name: str):
    def register(build):
        FIXTURES[name] = build
        return build
    return register


def one(name: str, cap: Cap, **submodels) -> list:
    """The fixture's single AAS: its capability and what it needs besides."""
    return [make_aas(aas_id(name), capability_description=describe(cap), **submodels)]


# Group A: atoms ----------------------------------------------------------------------------------------------

@fixture("a01-literal-number")
def a01(name):
    cap = Cap(aas_id(name), "Filling", lab("Filling"), OFFERED)
    axis, vial = cap.subject(0), cap.subject(1)
    cap.build([this("This axis"), unit("Unit being filled")], pre=[
        condition("Unit empty", CV, vial, "equal", number(0.0)),
        condition("Needle at fill depth", POSITION, axis, "greaterOrEqual", number(40.0))])
    return one(name, cap, variables=knowledge(POSITION))


@fixture("a02-literal-boolean-and-iri")
def a02(name):
    cap = Cap(aas_id(name), "Filling", lab("Filling"), OFFERED)
    vial = cap.subject(0)
    cap.build([unit("Unit being filled")], end=[
        effect("Unit weighed", WEIGHED, vial, "assign", boolean(True)),
        effect("Fill in tolerance", FILL_RESULT, vial, "assign", iri(IN_TOLERANCE))])
    return one(name, cap)


@fixture("a03-parameter-operand")
def a03(name):
    a = aas_id(name)
    cap = Cap(a, "Dosing", lab("Dosing"))
    cap.build([unit("Unit dosed into")], skill="Dispense", end=[
        effect("Unit holds the dosed volume", CV, cap.subject(0), "increase", parameter(a, "Dispense", "Volume"))])
    return one(name, cap, skills=skills(("Dispense", [("Volume", lab("Volume"))])))


@fixture("a04-capability-property-operand")
def a04(name):
    cap = Cap(aas_id(name), "Dosing", lab("Dosing"))
    cap.build([this("This axis")], properties={"FillPosition": (40.0, lab("FillPosition"))}, pre=[
        condition("Needle at fill depth", POSITION, cap.subject(0), "greaterOrEqual", cap.prop("FillPosition"))])
    return one(name, cap, variables=knowledge(POSITION))


@fixture("a05-subject-operand")
def a05(name):
    cap = Cap(aas_id(name), "Occupying", lab("Occupying"), CONTROL)
    cap.build([this("This module"), unit("Unit received")], end=[
        effect("Unit held here", HELD_BY, cap.subject(1), "assign", cap.subject(0))])
    return one(name, cap)


@fixture("a06-formula-uses")
def a06(name):
    cap = Cap(aas_id(name), "Dosing", lab("Dosing"))
    axis, container = cap.subject(0), cap.subject(1)
    cap.build([this("This axis"), unit("Container in the nest")], properties={"NestPosition": (70.0, lab("NestPosition"))},
              invariant=[condition("Needle inside the rim", POSITION, axis, "greaterOrEqual", Formula(
                  "NestPosition - RimHeight + 2 * pi",
                  {"NestPosition": cap.prop("NestPosition"), "RimHeight": (container, lab("RimHeight"))}))])
    return one(name, cap, variables=knowledge(POSITION))


@fixture("a07-set-valued")
def a07(name):
    cap = Cap(aas_id(name), "Handover", lab("Releasing"), CONTROL)
    tray, leaving, arriving = cap.subject(0), cap.subject(1), cap.subject(2)
    cap.build([this("This tray"), unit("Unit leaving"), unit("Unit arriving")],
              pre=[condition("Tray holds the unit", CARRYING, tray, "contains", leaving)],
              end=[effect("Unit leaves the tray", CARRYING, tray, "remove", leaving),
                   effect("Next unit joins", CARRYING, tray, "add", arriving)])
    carrying = StateVariable.own(CARRYING, ValueType=StateVariableValueType(value="reference"),
                                 Cardinality=StateVariableCardinality(value="set"))
    return one(name, cap, variables=knowledge(Carrying=carrying))


@fixture("a08-unchanged")
def a08(name):
    cap = Cap(aas_id(name), "Weighing", lab("Weighing"))
    cap.build([this("This axis")], invariant=[condition("Needle still", POSITION, cap.subject(0), "unchanged")])
    return one(name, cap, variables=knowledge(POSITION))


@fixture("a09-increase-decrease")
def a09(name):
    cap = Cap(aas_id(name), "Dosing", lab("Dosing"))
    target, source = cap.subject(0), cap.subject(1)
    cap.build([unit("Unit dosed into"), unit("Source container")], end=[
        effect("Unit gains 2 mL", CV, target, "increase", number(2.0)),
        effect("Source loses 2 mL", CV, source, "decrease", number(2.0))])
    return one(name, cap)


@fixture("a10-measured-and-clear")
def a10(name):
    cap = Cap(aas_id(name), "Weighing", lab("Weighing"))
    device, vial = cap.subject(0), cap.subject(1)
    cap.build([this("This device"), unit("Unit on the scale")], end=[
        effect("Unit's weight known", FILL_WEIGHT, vial, "measured"),
        effect("Free again", OCCUPIED_BY, device, "clear")])
    return one(name, cap, variables=knowledge(OCCUPIED_BY))


@fixture("a11-end-rate")
def a11(name):
    a = aas_id(name)
    cap = Cap(a, "Dosing", lab("Dosing"))
    cap.build([unit("Unit dosed into")], skill="Dispense", end=[
        effect("Unit holds the dosed volume", CV, cap.subject(0), "increase", parameter(a, "Dispense", "Volume"),
               rate=parameter(a, "Dispense", "FlowRate"))])
    return one(name, cap, skills=skills(("Dispense", [("Volume", lab("Volume")), ("FlowRate", lab("FlowRate"))])))


@fixture("a12-during")
def a12(name):
    cap = Cap(aas_id(name), "Dosing", lab("Dosing"))
    axis, container = cap.subject(0), cap.subject(1)
    cap.build([this("This axis"), unit("Container in the nest")], properties={"NestPosition": (70.0, lab("NestPosition"))},
              during=[effect("Outlet immersion", lab("OutletImmersion"), container, "assign", Formula(
                  "Position - NestPosition + InnerBottomHeight",
                  {"Position": (axis, POSITION), "NestPosition": cap.prop("NestPosition"),
                   "InnerBottomHeight": (container, lab("InnerBottomHeight"))}))])
    return one(name, cap, variables=knowledge(POSITION))


@fixture("a13-duration-value")
def a13(name):
    cap = Cap(aas_id(name), "MoveToPosition", lab("Transporting"))
    cap.build([this("This shuttle"), place("Target place")], duration=duration(number(3.0)), end=[
        effect("Shuttle at the place", LOCATION, cap.subject(0), "assign", cap.subject(1))])
    return one(name, cap, variables=knowledge(LOCATION))


@fixture("a14-duration-formula")
def a14(name):
    a = aas_id(name)
    cap = Cap(a, "Dosing", lab("Dosing"))
    cap.build([unit("Unit dosed into")], skill="Dispense", properties={"FlowRate": (1.0, lab("FlowRate"))},
              duration=duration(Formula("Volume / FlowRate", {
                  "Volume": parameter(a, "Dispense", "Volume"), "FlowRate": cap.prop("FlowRate")})),
              end=[effect("Unit holds the dosed volume", CV, cap.subject(0), "increase",
                          parameter(a, "Dispense", "Volume"))])
    return one(name, cap, skills=skills(("Dispense", [("Volume", lab("Volume"))])))


# Group B: connectives ----------------------------------------------------------------------------------------

@fixture("b01-implicit-and")
def b01(name):
    cap = Cap(aas_id(name), "Filling", lab("Filling"), OFFERED)
    vial = cap.subject(0)
    cap.build([unit("Unit being filled")], pre=[
        condition("Unit empty", CV, vial, "equal", number(0.0)),
        condition("Unit not weighed", WEIGHED, vial, "equal", boolean(False)),
        conj("Open unit", condition("Unit not stoppered", STOPPERED, vial, "equal", boolean(False)),
             condition("Unit not capped", CAPPED, vial, "equal", boolean(False)))])
    return one(name, cap)


@fixture("b02-and-or-not")
def b02(name):
    cap = Cap(aas_id(name), "Inspection", lab("Inspection"), OFFERED)
    vial = cap.subject(0)
    cap.build([unit("Unit inspected")], pre=[
        disj("Weighed or stoppered", condition("Unit weighed", WEIGHED, vial, "equal", boolean(True)),
             condition("Unit stoppered", STOPPERED, vial, "equal", boolean(True))),
        negation("Not inspected", condition("Unit inspected", INSPECTED, vial, "equal", boolean(True))),
        conj("Stoppered and not capped", condition("Unit stoppered", STOPPERED, vial, "equal", boolean(True)),
             negation("Not capped", condition("Unit capped", CAPPED, vial, "equal", boolean(True))))])
    return one(name, cap)


@fixture("b03-exists")
def b03(name):
    cap = Cap(aas_id(name), "Unloading", lab("Unloading"), OFFERED)
    tray, any_unit = cap.subject(0), cap.inside("ConditionSet/Pre/Term_00/Variable")
    cap.build([this("This tray")], pre=[exists(
        "A weighed unit is on the tray", variable("Any unit on the tray"),
        condition("Unit held here", HELD_BY, any_unit, "equal", tray),
        condition("Unit weighed", WEIGHED, any_unit, "equal", boolean(True)))])
    return one(name, cap)


@fixture("b04-forall-condition")
def b04(name):
    cap = Cap(aas_id(name), "Unloading", lab("Unloading"), OFFERED)
    every = cap.inside("ConditionSet/Pre/Term_00/Variable")
    cap.build([this("This tray")], pre=[for_all(
        "Every unit is weighed", variable("Every unit"),
        condition("Unit weighed", WEIGHED, every, "equal", boolean(True)))])
    return one(name, cap)


@fixture("b05-forall-effect")
def b05(name):
    cap = Cap(aas_id(name), "Releasing", lab("Releasing"), CONTROL)
    shuttle, every = cap.subject(1), cap.inside("EffectSet/End/Term_00/Variable")
    cap.build([this("This module"), carrier("Collecting shuttle")], end=[for_all_effects(
        "Every unit goes on the shuttle", variable("Every unit in the module"),
        effect("Unit on the shuttle", HELD_BY, every, "assign", shuttle))])
    return one(name, cap)


@fixture("b06-when")
def b06(name):
    cap = Cap(aas_id(name), "Filling", lab("Filling"), OFFERED)
    vial = cap.subject(0)
    cap.build([unit("Unit being filled")], end=[when(
        "Weighed if in tolerance", [condition("Fill in tolerance", FILL_RESULT, vial, "equal", iri(IN_TOLERANCE))],
        [effect("Unit weighed", WEIGHED, vial, "assign", boolean(True))])])
    return one(name, cap)


@fixture("b07-oneof-classification")
def b07(name):
    cap = Cap(aas_id(name), "Filling", lab("Filling"), OFFERED)
    vial = cap.subject(0)
    cap.build([unit("Unit being filled")], end=[
        effect("Unit's weight known", FILL_WEIGHT, vial, "measured"),
        one_of("Fill classified", FILL_RESULT,
               InTolerance=(IN_TOLERANCE, [effect("Fill in tolerance", FILL_RESULT, vial, "assign", iri(IN_TOLERANCE))]),
               OutOfTolerance=(OUT_OF_TOLERANCE, [
                   effect("Fill out of tolerance", FILL_RESULT, vial, "assign", iri(OUT_OF_TOLERANCE))]))])
    return one(name, cap)


# Group C: subjects, knowledge, goals, specialization ---------------------------------------------------------

@fixture("c01-subjects-every-kind")
def c01(name):
    a, axis = aas_id(name), aas_id(name, "axis")
    cap = Cap(a, "Filling", lab("Filling"), OFFERED)
    cap.build([this("This module"), fixed(aas_ref(axis), "Needle axis"), fixed(transfer_point(a), "Own transfer point"),
               unit("Unit being filled"), carrier("Delivering shuttle"), place("Target place"),
               required(lab("FillVolume"), "Required fill volume")],
              pre=[condition("Unit on the shuttle", HELD_BY, cap.subject(3), "equal", cap.subject(4))])
    return [make_aas(a, capability_description=describe(cap), variables=Variables(
        id_short="Variables", Measurements=coordinates())), make_aas(axis)]


@fixture("c02-knowledge")
def c02(name):
    a = aas_id(name)
    declared = knowledge(
        LOCATION, measurements=coordinates(),
        ContentVolume=StateVariable.own(CV, Initial=StateVariableInitial(value="0.0", value_type="xs:double")),
        TransferPointX=StateVariable.about(lab("AbsoluteX"), transfer_point(a)))
    return [make_aas(a, variables=declared,
                     asset_interfaces_mapping_configuration=mappings(mapping(a, "TransferPoint", "TransferPointX")))]


@fixture("c03-batch-goal")
def c03(name):
    product, batch = aas_id(name, "product"), aas_id(name, "batch")
    filling = Cap(product, "Filling", lab("Filling"), REQUIRED).build(
        properties={"FillVolume": (2.0, lab("FillVolume"))}, relations=False)
    the_unit = ModelReference(key=(sm_key(batch, "Goal"), Key(type_=SML, value="Subjects"),
                                   Key(type_="ReferenceElement", value="0")))
    goal = Goal(Subjects=Subjects(value=[unit("The unit")]), Condition=GoalCondition(term=terms([
        condition("Filled with the required volume", CV, the_unit, "equal", filling.prop("FillVolume")),
        condition("Weighed", WEIGHED, the_unit, "equal", boolean(True))])))
    return [
        make_aas(product, FixtureProduct, capability_description=describe(filling)),
        make_aas(batch, Batch, batch_information=BatchInformation(
            ProductType=BatchProductType(value=aas_ref(product)), Quantity=BatchQuantity(value="3")), goal=goal)]


def specialization(name: str, widen: bool = False, drop_effect: bool = False) -> list:
    """A component's Positioning, and the module's NeedlePositioning that generalizes to it: the module's subjects
    are not in the component's order (its axis is the second), and it narrows the needle's position and adds the unit's
    content. ``widen`` loosens the position bound instead; ``drop_effect`` leaves out the component's End effect."""
    component, module = aas_id(name, "component"), aas_id(name, "module")
    general = Cap(component, "Positioning", lab("Positioning"))
    general.build([this("This axis"), unit("Unit moved")],
                  pre=[condition("Axis lifted", POSITION, general.subject(0), "greaterOrEqual", number(3.0))],
                  end=[effect("Unit no longer weighed", WEIGHED, general.subject(1), "assign", boolean(False))])
    specific = Cap(module, "NeedlePositioning", lab("Positioning"))
    axis, moved = specific.subject(1), specific.subject(2)
    specific.build(
        [this("This module"), fixed(aas_ref(component), "Needle axis"), unit("Unit moved")], general=general,
        pre=[condition("Needle lifted", POSITION, axis, "greaterOrEqual", number(1.0 if widen else 5.0)),
             condition("Unit empty", CV, moved, "equal", number(0.0))],
        end=[effect("Unit no longer capped", CAPPED, moved, "assign", boolean(False)) if drop_effect else
             effect("Unit no longer weighed", WEIGHED, moved, "assign", boolean(False))])
    return [make_aas(component, capability_description=describe(general), variables=knowledge(POSITION)),
            make_aas(module, capability_description=describe(specific))]


@fixture("c04-specialization-superset")
def c04(name):
    return specialization(name)


# Group D: one invalid model per code of section 11 -------------------------------------------------------------

def dosing(name: str, build, **submodels) -> list:
    """A Dosing capability the ``build`` function fills in, given the capability."""
    cap = Cap(aas_id(name), "Dosing", lab("Dosing"))
    build(cap)
    return one(name, cap, **submodels)


@fixture("d01-structure-kind")
def d01(name):
    def build(cap):
        term = condition("Unit empty", CV, cap.subject(0), "equal", number(0.0))
        term.semantic_id = f"{BASE_URL}/execution/Maybe/1/0"
        cap.build([unit()], pre=[term])
    return dosing(name, build)


@fixture("d02-structure-meaning")
def d02(name):
    return dosing(name, lambda cap: cap.build([unit()], pre=[
        condition("Unit empty", None, cap.subject(0), "equal", number(0.0))]))


@fixture("d03-structure-operand")
def d03(name):
    return dosing(name, lambda cap: cap.build([unit()], pre=[condition("Unit empty", CV, cap.subject(0), "equal")]))


@fixture("d04-structure-rate")
def d04(name):
    return dosing(name, lambda cap: cap.build(
        [unit()], properties={"FlowRate": (1.0, lab("FlowRate"))}, start=[
            effect("Unit holds a volume", CV, cap.subject(0), "assign", number(1.0), rate=cap.prop("FlowRate"))]))


@fixture("d05-structure-not-arity")
def d05(name):
    def build(cap):
        vial = cap.subject(0)
        cap.build([unit()], pre=[negation("Neither", condition("Unit weighed", WEIGHED, vial, "equal", boolean(True)),
                                          condition("Unit capped", CAPPED, vial, "equal", boolean(True)))])
    return dosing(name, build)


@fixture("d06-structure-placement")
def d06(name):
    def build(cap):
        vial = cap.subject(0)
        cap.build([unit()], start=[one_of(
            "Fill classified", FILL_RESULT,
            InTolerance=(IN_TOLERANCE, [effect("Fill in tolerance", FILL_RESULT, vial, "assign", iri(IN_TOLERANCE))]),
            OutOfTolerance=(OUT_OF_TOLERANCE, [
                effect("Fill out of tolerance", FILL_RESULT, vial, "assign", iri(OUT_OF_TOLERANCE))]))])
    return dosing(name, build)


@fixture("d07-structure-subject-name")
def d07(name):
    return dosing(name, lambda cap: cap.build([unit(None)], pre=[condition("Unit empty", CV, cap.subject(0), "equal", number(0.0))]))


@fixture("d08-reference-unresolved")
def d08(name):
    a = aas_id(name)
    return dosing(name, lambda cap: cap.build([unit()], end=[
        effect("Unit holds the dosed volume", CV, cap.subject(0), "increase", parameter(a, "Dispense", "Volume"))]))


@fixture("d09-reference-subject")
def d09(name):
    def build(cap):
        cap.build([unit()], properties={"FillVolume": (2.0, lab("FillVolume"))},
                  pre=[condition("Unit empty", CV, cap.prop("FillVolume"), "equal", number(0.0))])
    return dosing(name, build)


@fixture("d10-reference-scope")
def d10(name):
    def build(cap):
        outside = cap.inside("ConditionSet/Pre/Term_00/Variable")
        cap.build([unit()], pre=[
            exists("A unit is weighed", variable("Any unit"),
                   condition("Unit weighed", WEIGHED, outside, "equal", boolean(True))),
            condition("Unit weighed", WEIGHED, outside, "equal", boolean(True))])
    return dosing(name, build)


@fixture("d11-operand-type")
def d11(name):
    return dosing(name, lambda cap: cap.build([unit()], pre=[
        condition("Unit weighed", WEIGHED, cap.subject(0), "equal", number(0.0))]))


@fixture("d12-operator-cardinality")
def d12(name):
    return dosing(name, lambda cap: cap.build([unit()], pre=[
        condition("Unit holds 1 mL", CV, cap.subject(0), "contains", number(1.0))]))


@fixture("d13-operator-unchanged")
def d13(name):
    return dosing(name, lambda cap: cap.build([unit()], pre=[condition("Content kept", CV, cap.subject(0), "unchanged")]))


@fixture("d14-operator-during")
def d14(name):
    return dosing(name, lambda cap: cap.build([unit()], during=[
        effect("Content grows", CV, cap.subject(0), "increase", number(1.0))]))


@fixture("d15-operator-equal-measured")
def d15(name):
    def build(cap):
        vial = cap.subject(0)
        cap.build([unit()], pre=[condition("Weight as measured", FILL_WEIGHT, vial, "equal", number(2.0))],
                  end=[effect("Unit's weight known", FILL_WEIGHT, vial, "measured")])
    return dosing(name, build)


@fixture("d16-formula-syntax")
def d16(name):
    return dosing(name, lambda cap: cap.build([unit()], pre=[
        condition("Content at least a sum", CV, cap.subject(0), "greaterOrEqual", Formula("2 +* 3", {}))]))


@fixture("d17-formula-alias")
def d17(name):
    return dosing(name, lambda cap: cap.build(
        [unit()], properties={"FillVolume": (2.0, lab("FillVolume"))}, pre=[
            condition("Content at least the volume", CV, cap.subject(0), "greaterOrEqual",
                      Formula("Volume + Other", {"Volume": cap.prop("FillVolume")}))]))


@fixture("d18-formula-unused")
def d18(name):
    return dosing(name, lambda cap: cap.build(
        [unit()], properties={"FillVolume": (2.0, lab("FillVolume"))}, pre=[
            condition("Content at least the volume", CV, cap.subject(0), "greaterOrEqual",
                      Formula("Volume", {"Volume": cap.prop("FillVolume"), "Spare": cap.prop("FillVolume")}))]))


@fixture("d19-formula-linear")
def d19(name):
    def build(cap):
        vial = cap.subject(0)
        cap.build([unit()], pre=[condition("Diameter within the product", lab("InnerDiameter"), vial, "lessOrEqual", Formula(
            "ContentVolume * FillWeight", {"ContentVolume": (vial, CV), "FillWeight": (vial, FILL_WEIGHT)}))],
                  end=[effect("Unit gains a volume", CV, vial, "increase", number(1.0)),
                       effect("Unit's weight set", FILL_WEIGHT, vial, "assign", number(2.0))])
    return dosing(name, build)


@fixture("d20-effect-conflict")
def d20(name):
    def build(cap):
        vial = cap.subject(0)
        cap.build([unit()], end=[effect("Unit weighed", WEIGHED, vial, "assign", boolean(True)),
                                 effect("Unit not weighed", WEIGHED, vial, "assign", boolean(False))])
    return dosing(name, build)


@fixture("d21-effect-target")
def d21(name):
    return dosing(name, lambda cap: cap.build([this()], end=[
        effect("Module holds a volume", CV, cap.subject(0), "assign", number(1.0))]))


@fixture("d22-declaration-vocabulary")
def d22(name):
    wrong = StateVariable.own(CV, ValueType=StateVariableValueType(value="boolean"))
    return [make_aas(aas_id(name), variables=knowledge(ContentVolume=wrong))]


@fixture("d23-declaration-kind")
def d23(name):
    a = aas_id(name)
    declared = knowledge(measurements=coordinates(), TransferPointX=StateVariable.about(lab("AbsoluteX"), transfer_point(a)))
    return [make_aas(a, variables=declared, asset_interfaces_mapping_configuration=mappings(
        mapping(a, "First", "TransferPointX"), mapping(a, "Second", "TransferPointX")))]


@fixture("d24-declaration-missing")
def d24(name):
    return dosing(name, lambda cap: cap.build([this("This axis")], pre=[
        condition("Needle at fill depth", POSITION, cap.subject(0), "greaterOrEqual", number(40.0))]))


@fixture("d25-constraint-state")
def d25(name):
    def build(cap):
        limit = ModelReference(key=(*cap.key, smc("CapabilityRelations"), smc("ConstraintSet"), smc("Limit"),
                                    Key(type_="Property", value="BasicConstraint")))
        constraints = {"ConstraintSet": ModuleConstraintSet(PropertyConstraintContainer={"Limit": BasicConstraintContainer(
            BasicConstraint=BasicConstraint(value="ContentVolume <= 10.0"),
            ConstraintType=ConstraintType(value="BasicConstraint"),
            PropertyConditionalType=PropertyConditionalType(value="Condition"),
            ConstraintPropertyRelations=ConstraintPropertyRelations(ConstraintHasProperty={
                "ConstraintHasProperty": ConstraintHasProperty(first=limit, second=cap.prop("ContentVolume"))}))})}
        cap.build([unit()], properties={"ContentVolume": (10.0, CV)}, constraints=constraints)
    return dosing(name, build)


LUA_CALL = "function call(subjects, properties)\n  return { Volume = 1.0 }\nend\n"
LUA_REPLY = "function reply(outputs, subjects, properties)\n  return { ok = true }\nend\n"
LUA_REPLY_UNKNOWN_ERROR = ("function reply(outputs, subjects, properties)\n"
                           "  if outputs.ErrorID ~= 0 then return { ok = false, error = \"Jammed\" } end\n"
                           "  return { ok = true }\nend\n")


@fixture("d26-translation-realized-by")
def d26(name):
    return dosing(name, lambda cap: cap.build([unit()], translation=Translation.lua(LUA_CALL, LUA_REPLY)))


@fixture("d27-translation-coverage")
def d27(name):
    return dosing(name, lambda cap: cap.build(
        [unit()], skill="Dispense", translation=Translation.lua(LUA_CALL, LUA_REPLY_UNKNOWN_ERROR)),
        skills=skills(("Dispense", [("Volume", lab("Volume"))]), errors={"NoContainer": "No container in the nest"}))


@fixture("d28-level-widening")
def d28(name):
    return specialization(name, widen=True)


@fixture("d29-level-incomplete")
def d29(name):
    return specialization(name, drop_effect=True)


# ── The files ────────────────────────────────────────────────────────────────────────────────────────────────

def environment(aases) -> str:
    """The AASs as one AAS environment in JSON: sorted keys, and the sets BaSyx keeps in a fixed order."""
    store = model.DictIdentifiableStore()
    for built in aases:
        for identifiable in build_from_model(built):
            store.add(identifiable)
    document = json.loads(json_serialization.object_store_to_json(store))
    for shell in document.get("assetAdministrationShells", ()):
        shell["submodels"] = sorted(shell.get("submodels", ()), key=lambda ref: ref["keys"][0]["value"])
    document["assetAdministrationShells"] = sorted(document.get("assetAdministrationShells", ()), key=lambda x: x["id"])
    document["submodels"] = sorted(document.get("submodels", ()), key=lambda x: x["id"])
    return json.dumps(document, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def documents() -> dict[str, str]:
    """Each fixture's name and its aas.json."""
    return {name: environment(build(name)) for name, build in sorted(FIXTURES.items())}


def write(output: Path) -> list[Path]:
    """Write every fixture's aas.json below ``output`` (a directory per fixture)."""
    written = []
    for name, text in documents().items():
        path = output / name / "aas.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        written.append(path)
    return written


def main() -> None:
    for path in write(HERE):
        print(path.relative_to(ROOT))


if __name__ == "__main__":
    main()
