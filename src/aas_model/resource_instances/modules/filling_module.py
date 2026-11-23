"""The filling module of the example line and its components, with what each capability needs and changes.

The module (``cell/modules/filling.yaml`` in iec61499-mgmt-py) fills a liquid into the container under its
needle and weighs it. It is built from three components, each an AAS of its own: a linear axis that moves the
needle (MoveAxis, Home), a pump (Dispense) and a scale (Tare, Weigh). Its composite skill Dispensing runs them:
needle down to the fill position, dispense the volume, needle up, weigh.

Who says what:

- **Each component** offers its capability in its own Capability Description (``AuxiliaryCapabilities``),
  realized by its primitive, with what holds wherever it is built in (its EffectSet): the axis ends where it was
  sent, at its speed; the pump adds the volume it was given to the unit, at the flow rate; the scale makes the
  unit's weight known.
- **The module** states, per component capability, what holds in this station (its own
  ``AuxiliaryCapabilities``): each generalized by the component's (``CapabilityGeneralizedBy``, into the
  component's AAS), with the station's values (fill and nest positions, insert depth, clearance) and the
  conditions they set (its ConstraintSet): where the needle has to be, how deep it is in the liquid while dosing,
  and that nothing moves it while the scale weighs. These relate the components to one another and to the
  container in the nest, which is why they are the module's. Each is a specialization of the component's: carried
  out by the same primitive, it inherits the component's properties, conditions and effects, narrows their values
  and adds conditions, never widens or contradicts them (``tests/test_example_line.py`` checks this).
- **What the module offers**, Filling, realized by Dispensing and composed of the module's three capabilities,
  with conditions and effects **derived** from theirs and the composite's steps: the net effect, and as
  preconditions what no step provides. modplan's compose is to write it; here it is written out by hand.

The properties a condition or effect is about are in the capability's PropertySet: the station's values, and the
properties of its subjects (a unit's RimHeight, the axis's Position), each the same as its subject's
(``OfSubject``) and without a value, as the state store holds it. The subjects are the axis (its AAS) and the
container, the unit in the module, known only at run time: what it holds and how it is shaped is declared by its
product (``aas_model.product_instances.vial_2ml``, StateDeclaration). Where the needle is, is observed: the
linear axis declares its position, and the module's Variables record it.

IDTA 02020 relations between capabilities (ComposedOf, GeneralizedBy) relate elements of Capability Description
submodels (§1.8.1); nothing in it keeps them to one submodel, so the module's capabilities name the components'
across their AASs.

Values follow the module spec, where the fill and nest positions are placeholders until the station is
measured.
"""

from aas_pydantic import Capability, Key, ModelReference, Property
from aas_pydantic.submodel_templates.capability_description import (
    CapabilityComposedOf, CapabilityGeneralizedBy, ComposedOfContainer, ComposedOfSet, GeneralizedBySet,
    PropertyProperty, PropertyRange, PropertySubmodelList,
)
from aas_pydantic.submodel_templates.nameplate import ManufacturerProductDesignation
from aas_pydantic.submodel_templates.time_series import Name

from aas_model.constants import BASE_URL, LAB
from aas_model.resource_template.modules import (
    Component, LabNameplate, LocatedEntryNode, LocatedNode, LocatedStructures, Module, ModuleSkill, ModuleSkills,
)
from aas_model.submodel_templates.arso import skills as s
from aas_model.submodel_templates.capability_description import (
    HasProperty, ModuleCapabilityContainer, ModuleCapabilityDescription, ModuleCapabilityRelations,
    ModuleCapabilitySet, ModuleConstraintSet, RealizedBySkill, SameAs, StateConditionalType, StateConstraint,
    StateConstraintContainer, StatedConstraintPropertyRelations, StatedProperty, StatedPropertySet,
)
from aas_model.submodel_templates.control_component_instance import ParameterVariable, SubjectVariable
from aas_model.submodel_templates.execution import (
    ComponentSubject, ConditionOperator, EffectContainer, EffectDefinition, EffectHasProperty, EffectOperator,
    EffectPropertyRelations, EffectSet, EffectTimingType, FormulaUse, FormulaUses, ProductSubject, Rate, SelfSubject,
    StateCondition, StateEffect, Subjects, TermFormula, TermProperty, TermValue, TermValueReference,
)
from aas_model.submodel_templates.state_declaration import StateDeclaration, StateVariable, StateVariableObserved
from aas_model.submodel_templates.time_series import (
    DmpLinkedSegment, InfluxDb2Target, RecordField, TimeSeriesCollection, TimeSeriesMetadata, TimeSeriesRecord,
    TimeSeriesSegments,
)
from aas_model.submodel_templates.variables import MeasurementsGroup, Variables

SKILL = f"{BASE_URL}/skill"                 # a skill's commands and kinds (iec61499-mgmt-py, commands.ttl)
SKILL_TYPE = f"{BASE_URL}/skills"           # what a skill does (skills.ttl)
SMC = "SubmodelElementCollection"
AUXILIARY = "AuxiliaryCapabilities"         # the CapabilitySet of the capabilities no product asks for directly

MODULE = f"{BASE_URL}/aas/FillingModuleAAS"
LINEAR_AXIS = f"{BASE_URL}/aas/FillingLinearAxisAAS"
PUMP = f"{BASE_URL}/aas/FillingPumpAAS"
SCALE = f"{BASE_URL}/aas/FillingScaleAAS"

# ── What the references below name ───────────────────────────────────────────────────────────────────────────

MODULE_SKILLS = Key(type_="Submodel", value=f"{MODULE}/submodels/Skills")
MODULE_CAPABILITIES = Key(type_="Submodel", value=f"{MODULE}/submodels/CapabilityDescription")
MODULE_VARIABLES = Key(type_="Submodel", value=f"{MODULE}/submodels/Variables")
CAPABILITY = Key(type_="Capability", value="Capability")
PROPERTY_SET = Key(type_=SMC, value="PropertySet")
SUBJECTS = Key(type_=SMC, value="Subjects")
CONSTRAINT_SET = (Key(type_=SMC, value="CapabilityRelations"), Key(type_=SMC, value="ConstraintSet"))
EFFECT_SET = (Key(type_=SMC, value="CapabilityRelations"), Key(type_=SMC, value="EffectSet"))

# The components' primitives and the inputs of their Start.
MOVE_AXIS = (Key(type_="Submodel", value=f"{LINEAR_AXIS}/submodels/Skills"), Key(type_=SMC, value="MoveAxis"))
DISPENSE = (Key(type_="Submodel", value=f"{PUMP}/submodels/Skills"), Key(type_=SMC, value="Dispense"))
WEIGH = (Key(type_="Submodel", value=f"{SCALE}/submodels/Skills"), Key(type_=SMC, value="Weigh"))
HOME = (Key(type_="Submodel", value=f"{LINEAR_AXIS}/submodels/Skills"), Key(type_=SMC, value="Home"))
MOVE_AXIS_START = (*MOVE_AXIS, Key(type_=SMC, value="Start"), Key(type_="Operation", value="Start"))
DISPENSE_START = (*DISPENSE, Key(type_=SMC, value="Start"), Key(type_="Operation", value="Start"))

# The components' own capabilities, in their AASs.
AXIS_POSITIONING = (Key(type_="Submodel", value=f"{LINEAR_AXIS}/submodels/CapabilityDescription"),
                    Key(type_=SMC, value=AUXILIARY), Key(type_=SMC, value="Positioning"))
PUMP_DOSING = (Key(type_="Submodel", value=f"{PUMP}/submodels/CapabilityDescription"),
               Key(type_=SMC, value=AUXILIARY), Key(type_=SMC, value="Dosing"))
SCALE_WEIGHING = (Key(type_="Submodel", value=f"{SCALE}/submodels/CapabilityDescription"),
                  Key(type_=SMC, value=AUXILIARY), Key(type_=SMC, value="Weighing"))

# The composite, its Operation and its steps.
DISPENSING = (MODULE_SKILLS, Key(type_=SMC, value="Dispensing"))
DISPENSING_START = (*DISPENSING, Key(type_=SMC, value="Start"), Key(type_="Operation", value="Start"))
DISPENSING_STEPS = (*DISPENSING, Key(type_=SMC, value="Start"), Key(type_=SMC, value="Steps"))

# The module's capabilities: what holds of each component's in this station, and what the module offers.
POSITIONING = (MODULE_CAPABILITIES, Key(type_=SMC, value=AUXILIARY), Key(type_=SMC, value="Positioning"))
DOSING = (MODULE_CAPABILITIES, Key(type_=SMC, value=AUXILIARY), Key(type_=SMC, value="Dosing"))
WEIGHING = (MODULE_CAPABILITIES, Key(type_=SMC, value=AUXILIARY), Key(type_=SMC, value="Weighing"))
FILLING = (MODULE_CAPABILITIES, Key(type_=SMC, value="OfferedCapabilities"), Key(type_=SMC, value="Filling"))

# The axis as a part of the module, and the record of where it is.
AXIS_POSITION_FIELD = (MODULE_VARIABLES, Key(type_=SMC, value="Measurements"), Key(type_=SMC, value="LinearAxis"),
                       Key(type_=SMC, value="Metadata"), Key(type_=SMC, value="Record"),
                       Key(type_="Property", value="Position"))

def _property(capability: tuple, name: str, kind: str = "Property") -> ModelReference:
    """The value of a capability's property ``name`` (its PropertyContainer of that name); ``kind`` is the value's
    element type (a Range where the property is a range)."""
    return ModelReference(key=(*capability, PROPERTY_SET, Key(type_=SMC, value=name), Key(type_=kind, value="Value")))


def _subject(capability: tuple, name: str) -> ModelReference:
    return ModelReference(key=(*capability, SUBJECTS, Key(type_="ReferenceElement", value=name)))


def _condition(capability: tuple, name: str) -> ModelReference:
    """A condition's CustomConstraint: the first element of what relates it to its properties."""
    return ModelReference(key=(*capability, *CONSTRAINT_SET, Key(type_=SMC, value=name),
                               Key(type_=SMC, value="CustomConstraint")))


def _effect(capability: tuple, name: str) -> ModelReference:
    return ModelReference(key=(*capability, *EFFECT_SET, Key(type_=SMC, value=name), Key(type_=SMC, value="Effect")))


def _of_subject(capability: tuple, name: str, subject: str, meaning: str) -> StatedProperty:
    """A property of a subject: no value (the state store holds it), the same as that subject's ``meaning``."""
    return StatedProperty(
        PropertyProperty={"Value": PropertyProperty(value_type="xs:double", supplemental_semantic_ids=[meaning])},
        SameProperty={"OfSubject": SameAs(first=_property(capability, name), second=_subject(capability, subject))})


def _station_value(value: str, meaning: str) -> StatedProperty:
    return StatedProperty(PropertyProperty={"Value": PropertyProperty(
        value=value, value_type="xs:double", supplemental_semantic_ids=[meaning])})


def _reads(capability: tuple, condition: str, *names: str) -> StatedConstraintPropertyRelations:
    """What a condition relates to: each property it reads (02020 ConstraintHasProperty)."""
    return StatedConstraintPropertyRelations(ConstraintHasProperty={
        name: HasProperty(first=_condition(capability, condition), second=_property(capability, name))
        for name in names})


# ── The components: their primitives, their own capabilities, and the axis's own state ───────────────────────

def filling_linear_axis() -> Component:
    """The needle lift: a stepper motor with a limit switch at the top. Its position is observed: the module
    records it (``Variables/Measurements/LinearAxis``)."""
    return Component(
        id_short="FillingLinearAxisAAS", id=LINEAR_AXIS, asset_type=f"{BASE_URL}/Resource/Component/LinearAxis",
        skills=ModuleSkills(Skill={
            "Home": ModuleSkill(
                supplemental_semantic_ids=[f"{SKILL}/Primitive"],
                SemanticId=s.SemanticId(value=f"{SKILL_TYPE}/Home"),
                Start=s.Start(semantic_id=f"{SKILL}/Start", SkillOperation={"Start": s.SkillOperation(
                    id_short="Start", semantic_id=f"{SKILL}/Start")}),
                Conditions=s.Conditions_2(Postcondition=s.Postcondition(value="AtHome")),
                Completion=s.Completion(Timeout=s.Timeout(value="60s")),
            ),
            "MoveAxis": ModuleSkill(
                supplemental_semantic_ids=[f"{SKILL}/Primitive"],
                SemanticId=s.SemanticId(value=f"{SKILL_TYPE}/MoveAxis"),
                Start=s.Start(semantic_id=f"{SKILL}/Start", SkillOperation={"Start": s.SkillOperation(
                    id_short="Start", semantic_id=f"{SKILL}/Start", input_variable=[
                        ParameterVariable(id_short="Position", value="0.0", value_type="xs:double",
                                          supplemental_semantic_ids=[f"{LAB}Position"],
                                          description="Where to move to, in mm down from the limit switch"),
                    ])}),
                # The device contract, compiled into the module's program (ST over the axis's signals).
                Conditions=s.Conditions_2(
                    Precondition=s.Precondition(value="Homed"),
                    Postcondition=s.Postcondition(value="NOT Moving AND ABS(ActualPosition - Position) < 0.001"),
                ),
                Completion=s.Completion(Timeout=s.Timeout(value="30s")),
            ),
        }),
        state_declaration=StateDeclaration(id_short="StateDeclaration", variable={
            "Position": StateVariable(
                supplemental_semantic_ids=[f"{LAB}Position"],
                Observed=StateVariableObserved(value=ModelReference(key=AXIS_POSITION_FIELD)),
            ),
        }),
        # What the axis does wherever it is built in: it ends where it was sent, at its speed. Its position is the
        # capability's Position: the range it takes, and the axis's state (OfSubject Self).
        capability_description=ModuleCapabilityDescription(id_short="CapabilityDescription", CapabilitySet={
            AUXILIARY: ModuleCapabilitySet(CapabilityContainer={"Positioning": ModuleCapabilityContainer(
                Capability=Capability(supplemental_semantic_ids=[f"{LAB}Positioning"]),
                Subjects=Subjects(subject={"Self": SelfSubject()}),
                PropertySet={"PropertySet": StatedPropertySet(PropertyContainer={
                    "Position": StatedProperty(
                        PropertyRange={"Value": PropertyRange(min="0.0", max="60.0", value_type="xs:double",
                                                              supplemental_semantic_ids=[f"{LAB}Position"])},
                        SameProperty={"OfSubject": SameAs(first=_property(AXIS_POSITIONING, "Position", "Range"),
                                                          second=_subject(AXIS_POSITIONING, "Self"))}),
                    "Speed": StatedProperty(PropertyProperty={"Value": PropertyProperty(
                        value="12.5", value_type="xs:double", supplemental_semantic_ids=[f"{LAB}Speed"])}),
                })},
                CapabilityRelations=ModuleCapabilityRelations(
                    CapabilityRealizedBy={"RealizedBy": RealizedBySkill(
                        first=ModelReference(key=(*AXIS_POSITIONING, CAPABILITY)), second=ModelReference(key=MOVE_AXIS))},
                    EffectSet=EffectSet(EffectContainer={"Moved": EffectContainer(
                        EffectTimingType=EffectTimingType(value="End"),
                        Effect=EffectDefinition(term={"Term": StateEffect(
                            Property=TermProperty(value=_property(AXIS_POSITIONING, "Position", "Range")),
                            Operator=EffectOperator(value="assign"),
                            ValueReference=TermValueReference(value=ModelReference(
                                key=(*MOVE_AXIS_START, Key(type_="Property", value="Position")))),
                            Rate=Rate(value=_property(AXIS_POSITIONING, "Speed")),
                        )}),
                        EffectPropertyRelations=EffectPropertyRelations(EffectHasProperty={"Position": EffectHasProperty(
                            first=_effect(AXIS_POSITIONING, "Moved"), second=_property(AXIS_POSITIONING, "Position", "Range"))}),
                    )}),
                ),
            )}),
        }),
    )


def filling_pump() -> Component:
    """The filling pump. None is wired yet: dispensing is a time at the flow rate (After)."""
    return Component(
        id_short="FillingPumpAAS", id=PUMP, asset_type=f"{BASE_URL}/Resource/Component/FillingPump",
        skills=ModuleSkills(Skill={
            "Dispense": ModuleSkill(
                supplemental_semantic_ids=[f"{SKILL}/Primitive"],
                SemanticId=s.SemanticId(value=f"{SKILL_TYPE}/Dispense"),
                Start=s.Start(semantic_id=f"{SKILL}/Start", SkillOperation={"Start": s.SkillOperation(
                    id_short="Start", semantic_id=f"{SKILL}/Start", input_variable=[
                        ParameterVariable(id_short="Volume", value="1.0", value_type="xs:double",
                                          supplemental_semantic_ids=[f"{LAB}FillVolume"],
                                          description="Volume to dispense, mL"),
                        ParameterVariable(id_short="FlowRate", value="1.0", value_type="xs:double",
                                          supplemental_semantic_ids=[f"{LAB}FlowRate"],
                                          description="How fast the pump doses, mL/s"),
                    ])}),
                Completion=s.Completion(After=s.After(value="Volume / FlowRate")),
            ),
        }),
        # What the pump does wherever it is built in: it adds the volume it was given to the unit it doses into,
        # at the flow rate. Which unit that is, is the module's to say (the composite's Unit).
        capability_description=ModuleCapabilityDescription(id_short="CapabilityDescription", CapabilitySet={
            AUXILIARY: ModuleCapabilitySet(CapabilityContainer={"Dosing": ModuleCapabilityContainer(
                Capability=Capability(supplemental_semantic_ids=[f"{LAB}Dosing"]),
                Subjects=Subjects(subject={"Self": SelfSubject(), "Unit": ProductSubject()}),
                PropertySet={"PropertySet": StatedPropertySet(PropertyContainer={
                    "Volume": StatedProperty(PropertyRange={"Value": PropertyRange(
                        min="0.5", max="10.0", value_type="xs:double",
                        supplemental_semantic_ids=[f"{LAB}FillVolume"])}),
                    "FlowRate": StatedProperty(PropertyRange={"Value": PropertyRange(
                        min="0.1", max="5.0", value_type="xs:double", supplemental_semantic_ids=[f"{LAB}FlowRate"])}),
                    "ContentVolume": StatedProperty(
                        PropertyProperty={"Value": PropertyProperty(
                            value_type="xs:double", supplemental_semantic_ids=[f"{LAB}ContentVolume"])},
                        SameProperty={"OfSubject": SameAs(first=_property(PUMP_DOSING, "ContentVolume"),
                                                          second=_subject(PUMP_DOSING, "Unit"))}),
                })},
                CapabilityRelations=ModuleCapabilityRelations(
                    CapabilityRealizedBy={"RealizedBy": RealizedBySkill(
                        first=ModelReference(key=(*PUMP_DOSING, CAPABILITY)), second=ModelReference(key=DISPENSE))},
                    EffectSet=EffectSet(EffectContainer={"Dosed": EffectContainer(
                        EffectTimingType=EffectTimingType(value="End"),
                        Effect=EffectDefinition(term={"Term": StateEffect(
                            Property=TermProperty(value=_property(PUMP_DOSING, "ContentVolume")),
                            Operator=EffectOperator(value="increase"),
                            ValueReference=TermValueReference(value=ModelReference(
                                key=(*DISPENSE_START, Key(type_="Property", value="Volume")))),
                            Rate=Rate(value=ModelReference(key=(*DISPENSE_START, Key(type_="Property", value="FlowRate")))),
                        )}),
                        EffectPropertyRelations=EffectPropertyRelations(EffectHasProperty={
                            "ContentVolume": EffectHasProperty(first=_effect(PUMP_DOSING, "Dosed"),
                                                               second=_property(PUMP_DOSING, "ContentVolume"))}),
                    )}),
                ),
            )}),
        }),
    )


def filling_scale() -> Component:
    """The scale under the nest (simulated: the hardware has none)."""
    return Component(
        id_short="FillingScaleAAS", id=SCALE, asset_type=f"{BASE_URL}/Resource/Component/Scale",
        skills=ModuleSkills(Skill={
            "Tare": ModuleSkill(
                supplemental_semantic_ids=[f"{SKILL}/Primitive"],
                SemanticId=s.SemanticId(value=f"{SKILL_TYPE}/Tare"),
                Start=s.Start(semantic_id=f"{SKILL}/Start", SkillOperation={"Start": s.SkillOperation(
                    id_short="Start", semantic_id=f"{SKILL}/Start")}),
                Completion=s.Completion(After=s.After(value="2.0")),
            ),
            "Weigh": ModuleSkill(
                supplemental_semantic_ids=[f"{SKILL}/Primitive"],
                SemanticId=s.SemanticId(value=f"{SKILL_TYPE}/Weigh"),
                Start=s.Start(semantic_id=f"{SKILL}/Start", SkillOperation={"Start": s.SkillOperation(
                    id_short="Start", semantic_id=f"{SKILL}/Start", output_variable=[
                        Property(id_short="Weight", value_type="xs:double",
                                 supplemental_semantic_ids=[f"{LAB}Weight"], description="What it weighed, g"),
                    ])}),
                Completion=s.Completion(After=s.After(value="0.2")),
            ),
        }),
        # What the scale does wherever it is built in: the weight of the unit on it becomes known.
        capability_description=ModuleCapabilityDescription(id_short="CapabilityDescription", CapabilitySet={
            AUXILIARY: ModuleCapabilitySet(CapabilityContainer={"Weighing": ModuleCapabilityContainer(
                Capability=Capability(supplemental_semantic_ids=[f"{LAB}Weighing"]),
                Subjects=Subjects(subject={"Self": SelfSubject(), "Unit": ProductSubject()}),
                PropertySet={"PropertySet": StatedPropertySet(PropertyContainer={
                    "FillWeight": StatedProperty(
                        PropertyProperty={"Value": PropertyProperty(
                            value_type="xs:double", supplemental_semantic_ids=[f"{LAB}FillWeight"])},
                        SameProperty={"OfSubject": SameAs(first=_property(SCALE_WEIGHING, "FillWeight"),
                                                          second=_subject(SCALE_WEIGHING, "Unit"))}),
                })},
                CapabilityRelations=ModuleCapabilityRelations(
                    CapabilityRealizedBy={"RealizedBy": RealizedBySkill(
                        first=ModelReference(key=(*SCALE_WEIGHING, CAPABILITY)), second=ModelReference(key=WEIGH))},
                    EffectSet=EffectSet(EffectContainer={"Weighed": EffectContainer(
                        EffectTimingType=EffectTimingType(value="End"),
                        Effect=EffectDefinition(term={"Term": StateEffect(
                            Property=TermProperty(value=_property(SCALE_WEIGHING, "FillWeight")),
                            Operator=EffectOperator(value="measured"),
                        )}),
                        EffectPropertyRelations=EffectPropertyRelations(EffectHasProperty={
                            "FillWeight": EffectHasProperty(first=_effect(SCALE_WEIGHING, "Weighed"),
                                                            second=_property(SCALE_WEIGHING, "FillWeight"))}),
                    )}),
                ),
            )}),
        }),
    )


# ── The module ───────────────────────────────────────────────────────────────────────────────────────────────

def filling_module() -> Module:
    # ── Capability Description ──────────────────────────────────────────────────────────────────────────────
    # Per component capability, what holds of it in this station: generalized by the component's own (in its AAS,
    # with what the component does anywhere), it adds the station's values and the conditions they set. The
    # properties of the subjects its conditions read are in its PropertySet, each the same as its subject's.
    axis = ComponentSubject(value=ModelReference(key=(Key(type_="AssetAdministrationShell", value=LINEAR_AXIS),)))

    # Positioning: the needle's tip stays BottomClearance above the inner bottom of the container in the nest.
    positioning = ModuleCapabilityContainer(
        Capability=Capability(supplemental_semantic_ids=[f"{LAB}Positioning"]),
        Subjects=Subjects(subject={"LinearAxis": axis, "Unit": ProductSubject()}),
        PropertySet={"PropertySet": StatedPropertySet(PropertyContainer={
            "NestPosition": _station_value("70.0", f"{LAB}NestPosition"),
            "BottomClearance": _station_value("1.0", f"{LAB}BottomClearance"),
            "Position": _of_subject(POSITIONING, "Position", "LinearAxis", f"{LAB}Position"),
            "InnerBottomHeight": _of_subject(POSITIONING, "InnerBottomHeight", "Unit", f"{LAB}InnerBottomHeight"),
        })},
        CapabilityRelations=ModuleCapabilityRelations(
            CapabilityRealizedBy={"RealizedBy": RealizedBySkill(first=ModelReference(key=(*POSITIONING, CAPABILITY)),
                                                                second=ModelReference(key=MOVE_AXIS))},
            GeneralizedBySet={"GeneralizedBySet": GeneralizedBySet(CapabilityGeneralizedBy={
                "GeneralizedBy": CapabilityGeneralizedBy(first=ModelReference(key=(*POSITIONING, CAPABILITY)),
                                                         second=ModelReference(key=(*AXIS_POSITIONING, CAPABILITY)))})},
            ConstraintSet={"ConstraintSet": ModuleConstraintSet(PropertyConstraintContainer={
                "AboveBottom": StateConstraintContainer(
                    CustomConstraint=StateConstraint(value={"Term": StateCondition(
                        Property=TermProperty(value=_property(POSITIONING, "Position")),
                        Operator=ConditionOperator(value="lessOrEqual"),
                        Formula=TermFormula(value="NestPosition - InnerBottomHeight - BottomClearance"),
                        Uses=FormulaUses(use={name: FormulaUse(value=_property(POSITIONING, name))
                                              for name in ("NestPosition", "InnerBottomHeight", "BottomClearance")}),
                    )}),
                    PropertyConditionalType=StateConditionalType(value="Invariant"),
                    ConstraintPropertyRelations=_reads(POSITIONING, "AboveBottom", "Position", "NestPosition",
                                                       "InnerBottomHeight", "BottomClearance"),
                ),
            })},
        ),
    )

    # Dosing: the pump doses through the needle on the axis, so a dose starts with the needle at the fill
    # position or deeper, and the needle stays InsertDepth below the rim meanwhile. While it doses, how deep the
    # needle's tip is in the liquid (OutletImmersion) follows from where the axis is, the container's geometry
    # and its content.
    dosing = ModuleCapabilityContainer(
        Capability=Capability(supplemental_semantic_ids=[f"{LAB}Dosing"]),
        Subjects=Subjects(subject={"LinearAxis": axis, "Unit": ProductSubject()}),
        PropertySet={"PropertySet": StatedPropertySet(PropertyContainer={
            "FillPosition": _station_value("40.0", f"{LAB}FillPosition"),
            "NestPosition": _station_value("70.0", f"{LAB}NestPosition"),
            "InsertDepth": _station_value("5.0", f"{LAB}InsertDepth"),
            "Position": _of_subject(DOSING, "Position", "LinearAxis", f"{LAB}Position"),
            **{name: _of_subject(DOSING, name, "Unit", f"{LAB}{name}")
               for name in ("RimHeight", "InnerBottomHeight", "InnerDiameter", "ContentVolume", "OutletImmersion")},
        })},
        CapabilityRelations=ModuleCapabilityRelations(
            CapabilityRealizedBy={"RealizedBy": RealizedBySkill(first=ModelReference(key=(*DOSING, CAPABILITY)),
                                                                second=ModelReference(key=DISPENSE))},
            GeneralizedBySet={"GeneralizedBySet": GeneralizedBySet(CapabilityGeneralizedBy={
                "GeneralizedBy": CapabilityGeneralizedBy(first=ModelReference(key=(*DOSING, CAPABILITY)),
                                                         second=ModelReference(key=(*PUMP_DOSING, CAPABILITY)))})},
            ConstraintSet={"ConstraintSet": ModuleConstraintSet(PropertyConstraintContainer={
                "NeedleAtFillDepth": StateConstraintContainer(
                    CustomConstraint=StateConstraint(value={"Term": StateCondition(
                        Property=TermProperty(value=_property(DOSING, "Position")),
                        Operator=ConditionOperator(value="greaterOrEqual"),
                        ValueReference=TermValueReference(value=_property(DOSING, "FillPosition")),
                    )}),
                    PropertyConditionalType=StateConditionalType(value="Pre"),
                    ConstraintPropertyRelations=_reads(DOSING, "NeedleAtFillDepth", "Position", "FillPosition"),
                ),
                "NeedleInsideRim": StateConstraintContainer(
                    CustomConstraint=StateConstraint(value={"Term": StateCondition(
                        Property=TermProperty(value=_property(DOSING, "Position")),
                        Operator=ConditionOperator(value="greaterOrEqual"),
                        Formula=TermFormula(value="NestPosition - RimHeight + InsertDepth"),
                        Uses=FormulaUses(use={name: FormulaUse(value=_property(DOSING, name))
                                              for name in ("NestPosition", "RimHeight", "InsertDepth")}),
                    )}),
                    PropertyConditionalType=StateConditionalType(value="Invariant"),
                    ConstraintPropertyRelations=_reads(DOSING, "NeedleInsideRim", "Position", "NestPosition",
                                                       "RimHeight", "InsertDepth"),
                ),
            })},
            EffectSet=EffectSet(EffectContainer={"Immersion": EffectContainer(
                EffectTimingType=EffectTimingType(value="During"),
                Effect=EffectDefinition(term={"Term": StateEffect(
                    Property=TermProperty(value=_property(DOSING, "OutletImmersion")),
                    Operator=EffectOperator(value="assign"),
                    Formula=TermFormula(
                        value="Position - NestPosition + InnerBottomHeight"
                              " + 1000 * ContentVolume / (pi * InnerDiameter * InnerDiameter / 4)"),
                    Uses=FormulaUses(use={name: FormulaUse(value=_property(DOSING, name)) for name in (
                        "Position", "NestPosition", "InnerBottomHeight", "ContentVolume", "InnerDiameter")}),
                )}),
                EffectPropertyRelations=EffectPropertyRelations(EffectHasProperty={"OutletImmersion": EffectHasProperty(
                    first=_effect(DOSING, "Immersion"), second=_property(DOSING, "OutletImmersion"))}),
            )}),
        ),
    )

    # Weighing: the scale weighs the container under the needle with the needle out of it, and nothing may move
    # the needle meanwhile (the lock).
    weighing = ModuleCapabilityContainer(
        Capability=Capability(supplemental_semantic_ids=[f"{LAB}Weighing"]),
        Subjects=Subjects(subject={"LinearAxis": axis}),
        PropertySet={"PropertySet": StatedPropertySet(PropertyContainer={
            "Position": _of_subject(WEIGHING, "Position", "LinearAxis", f"{LAB}Position"),
        })},
        CapabilityRelations=ModuleCapabilityRelations(
            CapabilityRealizedBy={"RealizedBy": RealizedBySkill(first=ModelReference(key=(*WEIGHING, CAPABILITY)),
                                                                second=ModelReference(key=WEIGH))},
            GeneralizedBySet={"GeneralizedBySet": GeneralizedBySet(CapabilityGeneralizedBy={
                "GeneralizedBy": CapabilityGeneralizedBy(first=ModelReference(key=(*WEIGHING, CAPABILITY)),
                                                         second=ModelReference(key=(*SCALE_WEIGHING, CAPABILITY)))})},
            ConstraintSet={"ConstraintSet": ModuleConstraintSet(PropertyConstraintContainer={
                "NeedleUp": StateConstraintContainer(
                    CustomConstraint=StateConstraint(value={"Term": StateCondition(
                        Property=TermProperty(value=_property(WEIGHING, "Position")),
                        Operator=ConditionOperator(value="equal"),
                        Value=TermValue(value="0.0", value_type="xs:double"),
                    )}),
                    PropertyConditionalType=StateConditionalType(value="Pre"),
                    ConstraintPropertyRelations=_reads(WEIGHING, "NeedleUp", "Position"),
                ),
                "NeedleStill": StateConstraintContainer(
                    CustomConstraint=StateConstraint(value={"Term": StateCondition(
                        Property=TermProperty(value=_property(WEIGHING, "Position")),
                        Operator=ConditionOperator(value="unchanged"),
                    )}),
                    PropertyConditionalType=StateConditionalType(value="Invariant"),
                    ConstraintPropertyRelations=_reads(WEIGHING, "NeedleStill", "Position"),
                ),
            })},
        ),
    )

    # What the module offers: Filling, realized by Dispensing and composed of the three capabilities above. What
    # it needs and changes is derived from theirs (and so from the components' they specialize) and from the steps:
    # what they add up to for the unit, the components' state hidden (every cycle starts and ends at rest): the
    # unit empty and in the module's custody, then holding the volume it was given, dosed at the station's flow
    # rate (the step's constant), and its weight known. Written by hand until modplan's compose derives it; the
    # validator re-derives it from the parts (ComposedOf) and the steps (RealizedBy) and compares.
    filling = ModuleCapabilityContainer(
        Capability=Capability(supplemental_semantic_ids=[f"{LAB}Filling"]),
        Subjects=Subjects(subject={
            "Self": SelfSubject(),
            "Unit": ProductSubject(value=ModelReference(key=(*DISPENSING_START, Key(type_="Property", value="Unit")))),
        }),
        PropertySet={"PropertySet": StatedPropertySet(PropertyContainer={
            "FillVolume": StatedProperty(PropertyRange={"Value": PropertyRange(
                min="0.5", max="10.0", value_type="xs:double", supplemental_semantic_ids=[f"{LAB}FillVolume"])}),
            "ContainerType": StatedProperty(PropertySubmodelList={"Value": PropertySubmodelList(
                supplemental_semantic_ids=[f"{LAB}ContainerType"], type_value_list_element="Property",
                value_type_list_element="xs:string",
                value=[Property(value=kind) for kind in ("vial", "syringe", "cartridge")])}),
            "GraspDiameter": StatedProperty(PropertyRange={"Value": PropertyRange(
                min="6.0", max="30.0", value_type="xs:double", supplemental_semantic_ids=[f"{LAB}GraspDiameter"])}),
            "AbsoluteFillError": StatedProperty(PropertyProperty={"Value": PropertyProperty(
                value="0.05", value_type="xs:double", supplemental_semantic_ids=[f"{LAB}AbsoluteFillError"])}),
            **{name: _of_subject(FILLING, name, "Unit", f"{LAB}{name}")
               for name in ("ContentVolume", "HeldBy", "FillWeight")},
        })},
        CapabilityRelations=ModuleCapabilityRelations(
            CapabilityRealizedBy={"RealizedBy": RealizedBySkill(
                first=ModelReference(key=(*FILLING, CAPABILITY)),
                second=ModelReference(key=DISPENSING))},
            ComposedOfSet=ComposedOfSet(ComposedOfContainer={"ComposedOf": ComposedOfContainer(CapabilityComposedOf={
                part: CapabilityComposedOf(first=ModelReference(key=(*FILLING, CAPABILITY)),
                                           second=ModelReference(key=(*path, CAPABILITY)))
                for part, path in (("Positioning", POSITIONING), ("Dosing", DOSING), ("Weighing", WEIGHING))
            })}),
            ConstraintSet={"ConstraintSet": ModuleConstraintSet(PropertyConstraintContainer={
                "UnitEmpty": StateConstraintContainer(
                    CustomConstraint=StateConstraint(value={"Term": StateCondition(
                        Property=TermProperty(value=_property(FILLING, "ContentVolume")),
                        Operator=ConditionOperator(value="equal"),
                        Value=TermValue(value="0.0", value_type="xs:double"),
                    )}),
                    PropertyConditionalType=StateConditionalType(value="Pre"),
                    ConstraintPropertyRelations=_reads(FILLING, "UnitEmpty", "ContentVolume"),
                ),
                "HeldHere": StateConstraintContainer(
                    CustomConstraint=StateConstraint(value={"Term": StateCondition(
                        Property=TermProperty(value=_property(FILLING, "HeldBy")),
                        Operator=ConditionOperator(value="equal"),
                        ValueReference=TermValueReference(value=_subject(FILLING, "Self")),
                    )}),
                    PropertyConditionalType=StateConditionalType(value="Invariant"),
                    ConstraintPropertyRelations=_reads(FILLING, "HeldHere", "HeldBy"),
                ),
            })},
            EffectSet=EffectSet(EffectContainer={
                "Filled": EffectContainer(
                    EffectTimingType=EffectTimingType(value="End"),
                    Effect=EffectDefinition(term={"Term": StateEffect(
                        Property=TermProperty(value=_property(FILLING, "ContentVolume")),
                        Operator=EffectOperator(value="increase"),
                        ValueReference=TermValueReference(value=ModelReference(
                            key=(*DISPENSING_START, Key(type_="Property", value="Volume")))),
                        Rate=Rate(value=ModelReference(key=(*DISPENSING_STEPS, Key(type_=SMC, value="Step_0001"),
                            Key(type_=SMC, value="Bindings"), Key(type_=SMC, value="Binding_0001"),
                            Key(type_="Property", value="Value")))),
                    )}),
                    EffectPropertyRelations=EffectPropertyRelations(EffectHasProperty={"ContentVolume": EffectHasProperty(
                        first=_effect(FILLING, "Filled"), second=_property(FILLING, "ContentVolume"))}),
                ),
                "Weighed": EffectContainer(
                    EffectTimingType=EffectTimingType(value="End"),
                    Effect=EffectDefinition(term={"Term": StateEffect(
                        Property=TermProperty(value=_property(FILLING, "FillWeight")),
                        Operator=EffectOperator(value="measured"),
                    )}),
                    EffectPropertyRelations=EffectPropertyRelations(EffectHasProperty={"FillWeight": EffectHasProperty(
                        first=_effect(FILLING, "Weighed"), second=_property(FILLING, "FillWeight"))}),
                ),
            }),
        ),
    )

    return Module(
        id_short="FillingModuleAAS", id=MODULE,
        nameplate=LabNameplate(
            ManufacturerProductDesignation=ManufacturerProductDesignation(value={"en": "Filling module"}),
        ),
        hierarchical_structures=LocatedStructures(EntryNode=LocatedEntryNode(Node={
            "LinearAxis": LocatedNode(global_asset_id=LINEAR_AXIS),
            "Pump": LocatedNode(global_asset_id=PUMP),
            "Scale": LocatedNode(global_asset_id=SCALE),
        })),

        # ── Skills: the composite the module offers ──────────────────────────────────────────────────────────
        # Needle down to the fill position, dispense the volume at the station's flow rate, needle up (by
        # homing, so every cycle starts from the switch), weigh. The unit is not sent to the module: the DMP
        # grounds the effects of Filling on it.
        skills=ModuleSkills(Skill={"Dispensing": ModuleSkill(
            supplemental_semantic_ids=[f"{SKILL}/Composite"],
            SemanticId=s.SemanticId(value=f"{SKILL_TYPE}/Dispensing"),
            Start=s.Start(
                semantic_id=f"{SKILL}/Start",
                SkillOperation={"Start": s.SkillOperation(
                    id_short="Start", semantic_id=f"{SKILL}/Start", input_variable=[
                        ParameterVariable(id_short="Volume", value="1.0", value_type="xs:double",
                                          supplemental_semantic_ids=[f"{LAB}FillVolume"],
                                          description="Fill volume, mL"),
                        SubjectVariable(id_short="Unit", description="The unit being filled, as an IRI"),
                    ])},
                Steps=s.Steps(SkillStep={
                    "Step_0000": s.SkillStep(
                        NodeId=s.NodeId(value="NeedleDown"), Kind=s.Kind(value="step"), Name=s.Name(value="MoveAxis"),
                        Order=s.Order(value="0"),
                        Skill=s.Skill_production_sequence(value=ModelReference(key=MOVE_AXIS)),
                        Bindings=s.Bindings(StepBinding={"Binding_0000": s.StepBinding(
                            Name=s.Name(value="Position"), Value=s.Value(value="40.0"))})),
                    "Step_0001": s.SkillStep(
                        NodeId=s.NodeId(value="Dispense"), Kind=s.Kind(value="step"), Name=s.Name(value="Dispense"),
                        Order=s.Order(value="1"),
                        Skill=s.Skill_production_sequence(value=ModelReference(key=DISPENSE)),
                        Bindings=s.Bindings(StepBinding={
                            "Binding_0000": s.StepBinding(
                                Name=s.Name(value="Volume"),
                                SourceElement=s.SourceElement(value=ModelReference(
                                    key=(*DISPENSING_START, Key(type_="Property", value="Volume"))))),
                            "Binding_0001": s.StepBinding(Name=s.Name(value="FlowRate"), Value=s.Value(value="1.0")),
                        })),
                    "Step_0002": s.SkillStep(
                        NodeId=s.NodeId(value="NeedleUp"), Kind=s.Kind(value="step"), Name=s.Name(value="Home"),
                        Order=s.Order(value="2"),
                        Skill=s.Skill_production_sequence(value=ModelReference(key=HOME))),
                    "Step_0003": s.SkillStep(
                        NodeId=s.NodeId(value="Weigh"), Kind=s.Kind(value="step"), Name=s.Name(value="Weigh"),
                        Order=s.Order(value="3"),
                        Skill=s.Skill_production_sequence(value=ModelReference(key=WEIGH))),
                }),
            ),
        )}),

        # ── Variables: where the needle is, and what the scale weighs ────────────────────────────────────────
        variables=Variables(id_short="Variables", Measurements=MeasurementsGroup(value={
            "LinearAxis": TimeSeriesCollection(
                Metadata=TimeSeriesMetadata(Name=Name(value={"en": "Needle position"}), Record=TimeSeriesRecord(
                    field={"Position": RecordField(value_type="xs:double", supplemental_semantic_ids=[f"{LAB}Position"],
                                                   description="mm down from the limit switch")})),
                Segments=TimeSeriesSegments(LinkedSegment={
                    "Live": DmpLinkedSegment(InfluxDb2Target=InfluxDb2Target(Measurement="filling_axis"))}),
            ),
            "Scale": TimeSeriesCollection(
                Metadata=TimeSeriesMetadata(Name=Name(value={"en": "Weight"}), Record=TimeSeriesRecord(
                    field={"Weight": RecordField(value_type="xs:double", supplemental_semantic_ids=[f"{LAB}Weight"],
                                                 description="g")})),
                Segments=TimeSeriesSegments(LinkedSegment={
                    "Live": DmpLinkedSegment(InfluxDb2Target=InfluxDb2Target(Measurement="filling_weight"))}),
            ),
        })),

        capability_description=ModuleCapabilityDescription(id_short="CapabilityDescription", CapabilitySet={
            "OfferedCapabilities": ModuleCapabilitySet(CapabilityContainer={"Filling": filling}),
            AUXILIARY: ModuleCapabilitySet(CapabilityContainer={
                "Positioning": positioning, "Dosing": dosing, "Weighing": weighing}),
        }),
    )
