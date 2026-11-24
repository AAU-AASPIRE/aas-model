"""The filling module of the example line and its components, with what each capability needs and changes.

The module (``cell/modules/filling.yaml`` in iec61499-mgmt-py) fills a liquid into the container under its
needle and weighs it. It is built from three components, each an AAS of its own: a linear axis that moves the
needle (MoveAxis, Home), a pump (Dispense) and a scale (Tare, Weigh). Its composite skill Dispensing runs them:
needle down to the fill position, dispense the volume, needle up, weigh.

Who says what:

- **Each component** offers its capability in its own Capability Description (``AuxiliaryCapabilities``),
  realized by its primitive, with what holds wherever it is built in: the axis ends where it was
  sent, at its speed; the pump adds the volume it was given to the unit, at the flow rate; the scale makes the
  unit's weight known.
- **The module** states, per component capability, what holds in this station (its own
  ``AuxiliaryCapabilities``): each generalized by the component's (``CapabilityGeneralizedBy``, into the
  component's AAS), with the station's values (fill and nest positions, insert depth, clearance) and the
  conditions they set: where the needle has to be, how deep it is in the liquid while dosing,
  and that nothing moves it while the scale weighs. These relate the components to one another and to the
  container in the nest, which is why they are the module's. Each is a specialization of the component's: carried
  out by the same primitive, it inherits the component's properties, conditions and effects, narrows their values
  and adds conditions, never widens or contradicts them (``tests/test_example_line.py`` checks this).
- **Module control**: the module takes the unit off a shuttle at its transfer point (Occupying, realized by Occupy)
  and puts it back on one (Releasing, by Release). Custody (HeldBy) moves between the shuttle and the module, so a
  shuttle's move to the transfer point, Occupying and Filling chain: each one's preconditions are what the one
  before made true.
- **What the module offers**, Filling, realized by Dispensing and composed of the module's three capabilities,
  with conditions and effects **derived** from theirs and the composite's steps: the net effect, and as
  preconditions what no step provides. modplan's compose is to write it; here it is written out by hand.

Who takes part, what must hold of them and what changes sit in each capability's CapabilityRelations
(Subjects, ConditionSet, EffectSet). The subjects are the axis (its AAS) and the container, the unit in the
module, known only at run time: what it holds and how it is shaped is declared by its product
(``aas_model.product_instances.vial_2ml``, StateDeclaration). Where the needle is, is observed: the linear axis
declares its position, and the module's Variables record it.

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
    ModuleCapabilityContainer, ModuleCapabilityDescription, ModuleCapabilityRelations, ModuleCapabilitySet,
    RealizedBySkill, StatedProperty, StatedPropertySet,
)
from aas_model.submodel_templates.control_component_instance import AcceptsReference, ParameterVariable
from aas_model.submodel_templates.execution import (
    CarrierSubject, ConditionOperator, ConditionSet, DuringTerms, EffectOperator, EffectSet, EndTerms,
    ExecutionDuration, ExecutionSubject,
    FormulaUse,
    FormulaUses, InvariantTerms, OneOfEffects, Outcome, PreTerms, Rate, RequirementSubject, SelfSubject,
    StateCondition, StateEffect, Subjects, TermFormula, TermSubject, TermValue, TermValueReference, Translation,
    UnitSubject,
)
from aas_model.resource_template.translations import COMPLETED_REPLY, NO_INPUTS_CALL
from aas_model.submodel_templates import Aimc, AimcMappingConfiguration, AimcMappingConfigurations
from aas_pydantic.submodel_templates.asset_interfaces_mapping_configuration import SinksItem, SourcesItem
from aas_model.submodel_templates.state_declaration import (
    StateDeclaration, StateVariable, StateVariableSubject,
)
from aas_model.submodel_templates.time_series import (
    DmpLinkedSegment, InfluxDb2Target, RecordField, TimeSeriesCollection, TimeSeriesMetadata, TimeSeriesRecord,
    TimeSeriesSegments,
)
from aas_model.submodel_templates.coordinates import (
    CoordinateRelativeTo, Coordinates, CoordinateX, CoordinateY, CoordinateYaw, RelativeCoordinate,
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
SUBJECTS = (Key(type_=SMC, value="CapabilityRelations"), Key(type_="SubmodelElementList", value="Subjects"))

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

# The module's control skills (take a unit off a shuttle, put it back), and their capabilities.
OCCUPY = (MODULE_SKILLS, Key(type_=SMC, value="Occupy"))
RELEASE = (MODULE_SKILLS, Key(type_=SMC, value="Release"))
MODULE_CONTROL = "ModuleControl"
OCCUPYING = (MODULE_CAPABILITIES, Key(type_=SMC, value=MODULE_CONTROL), Key(type_=SMC, value="Occupying"))
RELEASING = (MODULE_CAPABILITIES, Key(type_=SMC, value=MODULE_CONTROL), Key(type_=SMC, value="Releasing"))

# The composite, its Operation and its steps.
DISPENSING = (MODULE_SKILLS, Key(type_=SMC, value="Dispensing"))
DISPENSING_START = (*DISPENSING, Key(type_=SMC, value="Start"), Key(type_="Operation", value="Start"))
DISPENSING_STEPS = (*DISPENSING, Key(type_=SMC, value="Start"), Key(type_=SMC, value="Steps"))

# The module's capabilities: what holds of each component's in this station, and what the module offers.
POSITIONING = (MODULE_CAPABILITIES, Key(type_=SMC, value=AUXILIARY), Key(type_=SMC, value="Positioning"))
DOSING = (MODULE_CAPABILITIES, Key(type_=SMC, value=AUXILIARY), Key(type_=SMC, value="Dosing"))
WEIGHING = (MODULE_CAPABILITIES, Key(type_=SMC, value=AUXILIARY), Key(type_=SMC, value="Weighing"))
FILLING = (MODULE_CAPABILITIES, Key(type_=SMC, value="OfferedCapabilities"), Key(type_=SMC, value="Filling"))

# The errors the module's answer can carry (its ErrorID): each is an outcome a FOND plan branches on, beside success
# (D23). Codes as the module's program reports them; Filling's reply names them.
ERRORS = (
    ("NoContainer", "1", "No container in the nest"),
    ("AxisFault", "2", "The needle axis did not reach its position"),
    ("PumpFault", "3", "The pump did not deliver the volume"),
    ("ScaleUnstable", "4", "The scale did not settle"),
)

# Filling's Translation: the module is sent the volume the unit's product requires; its answer is a failure where it
# reports an error, and otherwise the unit's weight classified against the weight the product requires.
FILLING_CALL = """function call(subjects, properties)
  return { Volume = subjects[3].value }
end
"""
FILLING_REPLY = "local ERRORS = { " + ", ".join(f'[{code}] = "{name}"' for name, code, _ in ERRORS) + """ }
function reply(outputs, subjects, properties)
  if outputs.ErrorID ~= 0 then return { ok = false, error = ERRORS[outputs.ErrorID] } end
  local required = subjects[4].value
  if outputs.Weight >= required.min and outputs.Weight <= required.max then
    return { ok = true, outcome = "InTolerance" }
  end
  return { ok = true, outcome = "OutOfTolerance" }
end
"""

# The axis as a part of the module, and the record of where it is.
# The module's state, and the Lua that composes its transfer point into the line's frame (the base's pose, then the
# point relative to it; yaw in degrees).
MODULE_STATE = Key(type_="Submodel", value=f"{MODULE}/submodels/StateDeclaration")
TRANSFER_POINT_TRANSFORMATION = """function aimc_main(sources)
  local base, point = sources.ModuleBase, sources.TransferPoint
  local yaw = math.rad(tonumber(base.Yaw) or 0)
  local x, y = tonumber(point.X) or 0, tonumber(point.Y) or 0
  return {
    TransferPointX = (tonumber(base.X) or 0) + x * math.cos(yaw) - y * math.sin(yaw),
    TransferPointY = (tonumber(base.Y) or 0) + x * math.sin(yaw) + y * math.cos(yaw),
  }
end
"""

# The module's coordinates: its base, and the transfer point a shuttle is sent to.
COORDINATES = (MODULE_VARIABLES, Key(type_=SMC, value="Measurements"), Key(type_=SMC, value="Coordinates"))
MODULE_BASE = (*COORDINATES, Key(type_=SMC, value="ModuleBase"))
TRANSFER_POINT = (*COORDINATES, Key(type_=SMC, value="TransferPoint"))
AXIS_POSITION_FIELD = (MODULE_VARIABLES, Key(type_=SMC, value="Measurements"), Key(type_=SMC, value="LinearAxis"),
                       Key(type_=SMC, value="Metadata"), Key(type_=SMC, value="Record"),
                       Key(type_="Property", value="Position"))

def _property(capability: tuple, name: str, kind: str = "Property") -> ModelReference:
    """The value of a capability's property ``name`` (its PropertyContainer of that name); ``kind`` is the value's
    element type (a Range where the property is a range)."""
    return ModelReference(key=(*capability, PROPERTY_SET, Key(type_=SMC, value=name), Key(type_=kind, value="Value")))


def _subject(capability: tuple, index: int) -> ModelReference:
    """A capability's subject, by its place in Subjects."""
    return ModelReference(key=(*capability, *SUBJECTS, Key(type_="ReferenceElement", value=str(index))))


def _station_value(value: str, meaning: str) -> StatedProperty:
    return StatedProperty(PropertyProperty={"Value": PropertyProperty(
        value=value, value_type="xs:double", supplemental_semantic_ids=[meaning])})


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
            # Observed once the module's interface is mapped: the mapping that writes the module's LinearAxis
            # series (AXIS_POSITION_FIELD) sinks the position here too.
            "Position": StateVariable(supplemental_semantic_ids=[f"{LAB}Position"]),
        }),
        # What the axis does wherever it is built in: it ends where it was sent, at its speed.
        capability_description=ModuleCapabilityDescription(id_short="CapabilityDescription", CapabilitySet={
            AUXILIARY: ModuleCapabilitySet(CapabilityContainer={"Positioning": ModuleCapabilityContainer(
                Capability=Capability(supplemental_semantic_ids=[f"{LAB}Positioning"]),
                PropertySet={"PropertySet": StatedPropertySet(PropertyContainer={
                    "Position": StatedProperty(PropertyRange={"Value": PropertyRange(
                        min="0.0", max="60.0", value_type="xs:double", supplemental_semantic_ids=[f"{LAB}Position"])}),
                    "Speed": StatedProperty(PropertyProperty={"Value": PropertyProperty(
                        value="12.5", value_type="xs:double", supplemental_semantic_ids=[f"{LAB}Speed"])}),
                })},
                CapabilityRelations=ModuleCapabilityRelations(
                    CapabilityRealizedBy={"RealizedBy": RealizedBySkill(
                        first=ModelReference(key=(*AXIS_POSITIONING, CAPABILITY)),
                        second=ModelReference(key=MOVE_AXIS))},
                    Subjects=Subjects(value=[SelfSubject(display_name={"en": "This axis"})]),
                    EffectSet=EffectSet(End=EndTerms(term={"Term_00": StateEffect(
                        display_name={"en": "Axis ends at the target"}, supplemental_semantic_ids=[f"{LAB}Position"],
                        Subject=TermSubject(value=_subject(AXIS_POSITIONING, 0)),
                        Operator=EffectOperator(value="assign"),
                        ValueReference=TermValueReference(value=ModelReference(
                            key=(*MOVE_AXIS_START, Key(type_="Property", value="Position")))),
                        Rate=Rate(value=_property(AXIS_POSITIONING, "Speed")),
                    )})),
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
                PropertySet={"PropertySet": StatedPropertySet(PropertyContainer={
                    "Volume": StatedProperty(PropertyRange={"Value": PropertyRange(
                        min="0.5", max="10.0", value_type="xs:double",
                        supplemental_semantic_ids=[f"{LAB}FillVolume"])}),
                    "FlowRate": StatedProperty(PropertyRange={"Value": PropertyRange(
                        min="0.1", max="5.0", value_type="xs:double", supplemental_semantic_ids=[f"{LAB}FlowRate"])}),
                })},
                CapabilityRelations=ModuleCapabilityRelations(
                    CapabilityRealizedBy={"RealizedBy": RealizedBySkill(
                        first=ModelReference(key=(*PUMP_DOSING, CAPABILITY)), second=ModelReference(key=DISPENSE))},
                    Subjects=Subjects(value=[SelfSubject(display_name={"en": "This pump"}),
                                             UnitSubject(display_name={"en": "Unit dosed into"})]),
                    EffectSet=EffectSet(End=EndTerms(term={"Term_00": StateEffect(
                        display_name={"en": "Unit holds the dosed volume"},
                        supplemental_semantic_ids=[f"{LAB}ContentVolume"],
                        Subject=TermSubject(value=_subject(PUMP_DOSING, 1)),
                        Operator=EffectOperator(value="increase"),
                        ValueReference=TermValueReference(value=ModelReference(
                            key=(*DISPENSE_START, Key(type_="Property", value="Volume")))),
                        Rate=Rate(value=ModelReference(key=(*DISPENSE_START, Key(type_="Property", value="FlowRate")))),
                    ), "Term_01": StateEffect(
                        display_name={"en": "Unit no longer weighed"}, supplemental_semantic_ids=[f"{LAB}Weighed"],
                        Subject=TermSubject(value=_subject(PUMP_DOSING, 1)),
                        Operator=EffectOperator(value="assign"),
                        Value=TermValue(value="false", value_type="xs:boolean"),
                    )})),
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
                CapabilityRelations=ModuleCapabilityRelations(
                    CapabilityRealizedBy={"RealizedBy": RealizedBySkill(
                        first=ModelReference(key=(*SCALE_WEIGHING, CAPABILITY)), second=ModelReference(key=WEIGH))},
                    Subjects=Subjects(value=[SelfSubject(display_name={"en": "This scale"}),
                                             UnitSubject(display_name={"en": "Unit on the scale"})]),
                    EffectSet=EffectSet(End=EndTerms(term={
                        "Term_00": StateEffect(
                            display_name={"en": "Unit weighed"}, supplemental_semantic_ids=[f"{LAB}Weighed"],
                            Subject=TermSubject(value=_subject(SCALE_WEIGHING, 1)),
                            Operator=EffectOperator(value="assign"),
                            Value=TermValue(value="true", value_type="xs:boolean")),
                        "Term_01": StateEffect(
                            display_name={"en": "Unit's weight known"}, supplemental_semantic_ids=[f"{LAB}FillWeight"],
                            Subject=TermSubject(value=_subject(SCALE_WEIGHING, 1)),
                            Operator=EffectOperator(value="measured")),
                    })),
                    # The weighing itself: the skill's open-loop time (Completion After).
                    Duration=ExecutionDuration(Value=TermValue(value="0.2", value_type="xs:double")),
                ),
            )}),
        }),
    )


# ── The module ───────────────────────────────────────────────────────────────────────────────────────────────

def filling_module() -> Module:
    # ── Capability Description ──────────────────────────────────────────────────────────────────────────────
    # Per component capability, what holds of it in this station: generalized by the component's own (in its AAS,
    # with what the component does anywhere), it adds the station's values and the conditions they set. A
    # property of a subject in a formula is a Use naming the subject, its meaning the property's.
    axis = ExecutionSubject(display_name={"en": "Needle axis"},
                            value=ModelReference(key=(Key(type_="AssetAdministrationShell", value=LINEAR_AXIS),)))
    container = UnitSubject(display_name={"en": "Container in the nest"})

    # Positioning: the needle's tip stays BottomClearance above the inner bottom of the container in the nest.
    positioning = ModuleCapabilityContainer(
        Capability=Capability(supplemental_semantic_ids=[f"{LAB}Positioning"]),
        PropertySet={"PropertySet": StatedPropertySet(PropertyContainer={
            "NestPosition": _station_value("70.0", f"{LAB}NestPosition"),
            "BottomClearance": _station_value("1.0", f"{LAB}BottomClearance"),
        })},
        CapabilityRelations=ModuleCapabilityRelations(
            CapabilityRealizedBy={"RealizedBy": RealizedBySkill(first=ModelReference(key=(*POSITIONING, CAPABILITY)),
                                                                second=ModelReference(key=MOVE_AXIS))},
            GeneralizedBySet={"GeneralizedBySet": GeneralizedBySet(CapabilityGeneralizedBy={
                "GeneralizedBy": CapabilityGeneralizedBy(first=ModelReference(key=(*POSITIONING, CAPABILITY)),
                                                         second=ModelReference(key=(*AXIS_POSITIONING, CAPABILITY)))})},
            Subjects=Subjects(value=[axis, container]),
            ConditionSet=ConditionSet(Invariant=InvariantTerms(term={"Term_00": StateCondition(
                display_name={"en": "Needle above the bottom"}, supplemental_semantic_ids=[f"{LAB}Position"],
                Subject=TermSubject(value=_subject(POSITIONING, 0)),
                Operator=ConditionOperator(value="lessOrEqual"),
                Formula=TermFormula(value="NestPosition - InnerBottomHeight - BottomClearance"),
                Uses=FormulaUses(use={
                    "NestPosition": FormulaUse(value=_property(POSITIONING, "NestPosition")),
                    "InnerBottomHeight": FormulaUse(value=_subject(POSITIONING, 1),
                                                    supplemental_semantic_ids=[f"{LAB}InnerBottomHeight"]),
                    "BottomClearance": FormulaUse(value=_property(POSITIONING, "BottomClearance")),
                }),
            )})),
        ),
    )

    # Dosing: the pump doses through the needle on the axis, so a dose starts with the needle at the fill
    # position or deeper, and the needle stays InsertDepth below the rim meanwhile. While it doses, how deep the
    # needle's tip is in the liquid (OutletImmersion) follows from where the axis is, the container's geometry
    # and its content.
    dose_axis, dose_unit = _subject(DOSING, 0), _subject(DOSING, 1)
    nest = FormulaUse(value=_property(DOSING, "NestPosition"))
    dosing = ModuleCapabilityContainer(
        Capability=Capability(supplemental_semantic_ids=[f"{LAB}Dosing"]),
        PropertySet={"PropertySet": StatedPropertySet(PropertyContainer={
            "FillPosition": _station_value("40.0", f"{LAB}FillPosition"),
            "NestPosition": _station_value("70.0", f"{LAB}NestPosition"),
            "InsertDepth": _station_value("5.0", f"{LAB}InsertDepth"),
        })},
        CapabilityRelations=ModuleCapabilityRelations(
            CapabilityRealizedBy={"RealizedBy": RealizedBySkill(first=ModelReference(key=(*DOSING, CAPABILITY)),
                                                                second=ModelReference(key=DISPENSE))},
            GeneralizedBySet={"GeneralizedBySet": GeneralizedBySet(CapabilityGeneralizedBy={
                "GeneralizedBy": CapabilityGeneralizedBy(first=ModelReference(key=(*DOSING, CAPABILITY)),
                                                         second=ModelReference(key=(*PUMP_DOSING, CAPABILITY)))})},
            Subjects=Subjects(value=[axis, container]),
            ConditionSet=ConditionSet(
                Pre=PreTerms(term={"Term_00": StateCondition(
                    display_name={"en": "Needle at fill depth"}, supplemental_semantic_ids=[f"{LAB}Position"],
                    Subject=TermSubject(value=dose_axis),
                    Operator=ConditionOperator(value="greaterOrEqual"),
                    ValueReference=TermValueReference(value=_property(DOSING, "FillPosition")),
                )}),
                Invariant=InvariantTerms(term={"Term_00": StateCondition(
                    display_name={"en": "Needle inside the rim"}, supplemental_semantic_ids=[f"{LAB}Position"],
                    Subject=TermSubject(value=dose_axis),
                    Operator=ConditionOperator(value="greaterOrEqual"),
                    Formula=TermFormula(value="NestPosition - RimHeight + InsertDepth"),
                    Uses=FormulaUses(use={
                        "NestPosition": nest,
                        "RimHeight": FormulaUse(value=dose_unit, supplemental_semantic_ids=[f"{LAB}RimHeight"]),
                        "InsertDepth": FormulaUse(value=_property(DOSING, "InsertDepth")),
                    }),
                )}),
            ),
            EffectSet=EffectSet(During=DuringTerms(term={"Term_00": StateEffect(
                display_name={"en": "Outlet immersion"}, supplemental_semantic_ids=[f"{LAB}OutletImmersion"],
                Subject=TermSubject(value=dose_unit),
                Operator=EffectOperator(value="assign"),
                Formula=TermFormula(
                    value="Position - NestPosition + InnerBottomHeight"
                          " + 1000 * ContentVolume / (pi * InnerDiameter * InnerDiameter / 4)"),
                Uses=FormulaUses(use={
                    "Position": FormulaUse(value=dose_axis, supplemental_semantic_ids=[f"{LAB}Position"]),
                    "NestPosition": nest,
                    **{name: FormulaUse(value=dose_unit, supplemental_semantic_ids=[f"{LAB}{name}"])
                       for name in ("InnerBottomHeight", "ContentVolume", "InnerDiameter")},
                }),
            )})),
        ),
    )

    # Weighing: the scale weighs the container under the needle with the needle out of it, and nothing may move
    # the needle meanwhile (the lock).
    weigh_axis = _subject(WEIGHING, 0)
    weighing = ModuleCapabilityContainer(
        Capability=Capability(supplemental_semantic_ids=[f"{LAB}Weighing"]),
        CapabilityRelations=ModuleCapabilityRelations(
            CapabilityRealizedBy={"RealizedBy": RealizedBySkill(first=ModelReference(key=(*WEIGHING, CAPABILITY)),
                                                                second=ModelReference(key=WEIGH))},
            GeneralizedBySet={"GeneralizedBySet": GeneralizedBySet(CapabilityGeneralizedBy={
                "GeneralizedBy": CapabilityGeneralizedBy(first=ModelReference(key=(*WEIGHING, CAPABILITY)),
                                                         second=ModelReference(key=(*SCALE_WEIGHING, CAPABILITY)))})},
            Subjects=Subjects(value=[axis]),
            ConditionSet=ConditionSet(
                Pre=PreTerms(term={"Term_00": StateCondition(
                    display_name={"en": "Needle up"},
                    supplemental_semantic_ids=[f"{LAB}Position"], Subject=TermSubject(value=weigh_axis),
                    Operator=ConditionOperator(value="equal"), Value=TermValue(value="0.0", value_type="xs:double"),
                )}),
                Invariant=InvariantTerms(term={"Term_00": StateCondition(
                    display_name={"en": "Needle still"},
                    supplemental_semantic_ids=[f"{LAB}Position"], Subject=TermSubject(value=weigh_axis),
                    Operator=ConditionOperator(value="unchanged"),
                )}),
            ),
        ),
    )

    # What the module offers: Filling, realized by Dispensing and composed of the three capabilities above. What
    # it needs and changes is derived from theirs (and so from the components' they specialize) and from the steps:
    # what they add up to for the unit, the components' state hidden (every cycle starts and ends at rest): the
    # unit empty and in the module's custody, then holding the volume it was given, dosed at the station's flow
    # rate (the step's constant), and its weight known, which classifies the fill against what the product requires
    # (the outcomes: in or out of tolerance, the Translation's reply says which). Written by hand until modplan's
    # compose derives it; the validator re-derives it from the parts (ComposedOf) and the steps (RealizedBy) and
    # compares. The volume and the weight the product requires are subjects, bound when the behaviour tree is built.
    fill_unit = _subject(FILLING, 1)
    filling = ModuleCapabilityContainer(
        Capability=Capability(supplemental_semantic_ids=[f"{LAB}Filling"]),
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
            Subjects=Subjects(value=[
                SelfSubject(display_name={"en": "This module"}),
                UnitSubject(display_name={"en": "Unit being filled"}),
                RequirementSubject.of(f"{LAB}FillVolume", display_name={"en": "Required fill volume"}),
                RequirementSubject.of(f"{LAB}FillWeight", display_name={"en": "Required fill weight"}),
            ]),
            ConditionSet=ConditionSet(
                Pre=PreTerms(term={"Term_00": StateCondition(
                    display_name={"en": "Unit empty"},
                    supplemental_semantic_ids=[f"{LAB}ContentVolume"], Subject=TermSubject(value=fill_unit),
                    Operator=ConditionOperator(value="equal"), Value=TermValue(value="0.0", value_type="xs:double"),
                )}),
                Invariant=InvariantTerms(term={"Term_00": StateCondition(
                    display_name={"en": "Unit held here"},
                    supplemental_semantic_ids=[f"{LAB}HeldBy"], Subject=TermSubject(value=fill_unit),
                    Operator=ConditionOperator(value="equal"),
                    ValueReference=TermValueReference(value=_subject(FILLING, 0)),
                )}),
            ),
            EffectSet=EffectSet(End=EndTerms(term={
                "Term_00": StateEffect(
                    display_name={"en": "Unit holds the fill volume"},
                    supplemental_semantic_ids=[f"{LAB}ContentVolume"], Subject=TermSubject(value=fill_unit),
                    Operator=EffectOperator(value="increase"),
                    ValueReference=TermValueReference(value=ModelReference(
                        key=(*DISPENSING_START, Key(type_="Property", value="Volume")))),
                    Rate=Rate(value=ModelReference(key=(*DISPENSING_STEPS, Key(type_=SMC, value="Step_0001"),
                        Key(type_=SMC, value="Bindings"), Key(type_=SMC, value="Binding_0001"),
                        Key(type_="Property", value="Value")))),
                ),
                "Term_02": StateEffect(
                    display_name={"en": "Unit weighed"}, supplemental_semantic_ids=[f"{LAB}Weighed"],
                    Subject=TermSubject(value=fill_unit), Operator=EffectOperator(value="assign"),
                    Value=TermValue(value="true", value_type="xs:boolean"),
                ),
                "Term_01": StateEffect(
                    display_name={"en": "Unit's weight known"},
                    supplemental_semantic_ids=[f"{LAB}FillWeight"], Subject=TermSubject(value=fill_unit),
                    Operator=EffectOperator(value="measured"),
                ),
                "Term_03": OneOfEffects(display_name={"en": "Fill classified"}, outcome={
                    result: Outcome(supplemental_semantic_ids=[f"{LAB}{result}"], term={"Term_00": StateEffect(
                        display_name={"en": text}, supplemental_semantic_ids=[f"{LAB}FillResult"],
                        Subject=TermSubject(value=fill_unit), Operator=EffectOperator(value="assign"),
                        Value=TermValue(value=f"{LAB}{result}", value_type="xs:anyURI"))})
                    for result, text in (("InTolerance", "Fill in tolerance"), ("OutOfTolerance", "Fill out of tolerance"))
                }),
            })),
            # The steps one after the other: the needle down to the fill position and up again at the axis's speed,
            # the dose at the station's flow rate, the weighing.
            Duration=ExecutionDuration(
                Formula=TermFormula(value="2 * Position / Speed + Volume / FlowRate + Weighing"),
                Uses=FormulaUses(use={
                    "Position": FormulaUse(value=ModelReference(key=(
                        *DISPENSING_STEPS, Key(type_=SMC, value="Step_0000"), Key(type_=SMC, value="Bindings"),
                        Key(type_=SMC, value="Binding_0000"), Key(type_="Property", value="Value")))),
                    "Speed": FormulaUse(value=_property(AXIS_POSITIONING, "Speed")),
                    "Volume": FormulaUse(value=ModelReference(
                        key=(*DISPENSING_START, Key(type_="Property", value="Volume")))),
                    "FlowRate": FormulaUse(value=ModelReference(key=(
                        *DISPENSING_STEPS, Key(type_=SMC, value="Step_0001"), Key(type_=SMC, value="Bindings"),
                        Key(type_=SMC, value="Binding_0001"), Key(type_="Property", value="Value")))),
                    "Weighing": FormulaUse(value=ModelReference(key=(
                        *SCALE_WEIGHING, Key(type_=SMC, value="CapabilityRelations"),
                        Key(type_=SMC, value="Duration"), Key(type_="Property", value="Value")))),
                }),
            ),
            Translation=Translation.lua(FILLING_CALL, FILLING_REPLY),
        ),
    )

    # Module control: the module takes the unit off the shuttle at its transfer point (Occupying), and puts it back
    # on one (Releasing). Custody moves between the shuttle and the module; the module serves one unit at a time. The
    # transfer point is the module's own coordinate, so its subject is fixed; who the shuttle and the unit are, the
    # behaviour tree binds as the planner chose. The module's Occupy and Release take and answer nothing.
    transfer_point = ExecutionSubject(display_name={"en": "Transfer point"},
                                      value=ModelReference(key=TRANSFER_POINT))

    def handover(capability: tuple, skill: tuple, carrier: str, unit: str, pre: dict, end: dict,
                 meaning: str) -> ModuleCapabilityContainer:
        return ModuleCapabilityContainer(
            Capability=Capability(supplemental_semantic_ids=[meaning]),
            CapabilityRelations=ModuleCapabilityRelations(
                CapabilityRealizedBy={"RealizedBy": RealizedBySkill(first=ModelReference(key=(*capability, CAPABILITY)),
                                                                    second=ModelReference(key=skill))},
                Subjects=Subjects(value=[SelfSubject(display_name={"en": "This module"}), transfer_point,
                                         CarrierSubject(display_name={"en": carrier}),
                                         UnitSubject(display_name={"en": unit})]),
                ConditionSet=ConditionSet(Pre=PreTerms(term=pre)),
                EffectSet=EffectSet(End=EndTerms(term=end)),
                Duration=ExecutionDuration(Value=TermValue(value="2.0", value_type="xs:double")),   # nominal, s
                Translation=Translation.lua(NO_INPUTS_CALL, COMPLETED_REPLY),
            ),
        )

    def at_transfer_point(capability: tuple) -> StateCondition:
        return StateCondition(
            display_name={"en": "Shuttle at the transfer point"}, supplemental_semantic_ids=[f"{LAB}Location"],
            Subject=TermSubject(value=_subject(capability, 2)), Operator=ConditionOperator(value="equal"),
            ValueReference=TermValueReference(value=_subject(capability, 1)))

    occupying = handover(
        OCCUPYING, OCCUPY, "Delivering shuttle", "Unit received", meaning=f"{LAB}Occupying",
        pre={
            "Term_00": at_transfer_point(OCCUPYING),
            "Term_01": StateCondition(
                display_name={"en": "Unit on the shuttle"}, supplemental_semantic_ids=[f"{LAB}HeldBy"],
                Subject=TermSubject(value=_subject(OCCUPYING, 3)), Operator=ConditionOperator(value="equal"),
                ValueReference=TermValueReference(value=_subject(OCCUPYING, 2))),
        },
        end={
            "Term_00": StateEffect(
                display_name={"en": "Unit held here"}, supplemental_semantic_ids=[f"{LAB}HeldBy"],
                Subject=TermSubject(value=_subject(OCCUPYING, 3)), Operator=EffectOperator(value="assign"),
                ValueReference=TermValueReference(value=_subject(OCCUPYING, 0))),
            "Term_01": StateEffect(
                display_name={"en": "Serves the unit"}, supplemental_semantic_ids=[f"{LAB}OccupiedBy"],
                Subject=TermSubject(value=_subject(OCCUPYING, 0)), Operator=EffectOperator(value="assign"),
                ValueReference=TermValueReference(value=_subject(OCCUPYING, 3))),
        },
    )
    releasing = handover(
        RELEASING, RELEASE, "Collecting shuttle", "Unit released", meaning=f"{LAB}Releasing",
        pre={
            "Term_00": at_transfer_point(RELEASING),
            "Term_01": StateCondition(
                display_name={"en": "Unit held here"}, supplemental_semantic_ids=[f"{LAB}HeldBy"],
                Subject=TermSubject(value=_subject(RELEASING, 3)), Operator=ConditionOperator(value="equal"),
                ValueReference=TermValueReference(value=_subject(RELEASING, 0))),
            "Term_02": StateCondition(
                display_name={"en": "Serves the unit"}, supplemental_semantic_ids=[f"{LAB}OccupiedBy"],
                Subject=TermSubject(value=_subject(RELEASING, 0)), Operator=ConditionOperator(value="equal"),
                ValueReference=TermValueReference(value=_subject(RELEASING, 3))),
        },
        end={
            "Term_00": StateEffect(
                display_name={"en": "Unit on the shuttle"}, supplemental_semantic_ids=[f"{LAB}HeldBy"],
                Subject=TermSubject(value=_subject(RELEASING, 3)), Operator=EffectOperator(value="assign"),
                ValueReference=TermValueReference(value=_subject(RELEASING, 2))),
            "Term_01": StateEffect(
                display_name={"en": "Free again"}, supplemental_semantic_ids=[f"{LAB}OccupiedBy"],
                Subject=TermSubject(value=_subject(RELEASING, 0)), Operator=EffectOperator(value="clear")),
        },
    )

    return Module(
        id_short="FillingModuleAAS", id=MODULE,
        nameplate=LabNameplate(
            ManufacturerProductDesignation=ManufacturerProductDesignation(value={"en": "Filling module"}),
        ),
        # The module's state: who it serves, and where its transfer point is in the line's frame (observed: the
        # TransferPoint mapping below sinks it, so a query can tell whether a shuttle is at it; D36). The module reports no process queue, so who it serves is asserted by the
        # tree that occupies it until it does (plan, open question 24).
        state_declaration=StateDeclaration(id_short="StateDeclaration", variable={
            "OccupiedBy": StateVariable(supplemental_semantic_ids=[f"{LAB}OccupiedBy"]),
            **{f"TransferPoint{axis}": StateVariable(
                supplemental_semantic_ids=[f"{LAB}Absolute{axis}"],
                Subject=StateVariableSubject(value=ModelReference(key=TRANSFER_POINT)),
            ) for axis in ("X", "Y")},
        }),
        # The transfer point's position in the line's frame, into the state store: the coordinate and the base it is
        # relative to are the mapping's sources (static elements, read again when one changes), composed in its Lua.
        asset_interfaces_mapping_configuration=Aimc(
            id_short="AssetInterfacesMappingConfiguration", MappingConfigurations=AimcMappingConfigurations(value=[
                AimcMappingConfiguration(
                    id_short="TransferPoint", DefaultPollingInterval="0.0",
                    Sources=[SourcesItem(SourceId="TransferPoint", Source=ModelReference(key=TRANSFER_POINT)),
                             SourcesItem(SourceId="ModuleBase", Source=ModelReference(key=MODULE_BASE))],
                    Sinks=[SinksItem(SinkId=f"TransferPoint{axis}", Sink=ModelReference(key=(
                        MODULE_STATE, Key(type_=SMC, value=f"TransferPoint{axis}")))) for axis in ("X", "Y")],
                    Transformation=TRANSFER_POINT_TRANSFORMATION,
                ),
            ])),
        hierarchical_structures=LocatedStructures(EntryNode=LocatedEntryNode(Node={
            "LinearAxis": LocatedNode(global_asset_id=LINEAR_AXIS),
            "Pump": LocatedNode(global_asset_id=PUMP),
            "Scale": LocatedNode(global_asset_id=SCALE),
        })),

        # ── Skills: the composite the module offers ──────────────────────────────────────────────────────────
        # Needle down to the fill position, dispense the volume at the station's flow rate, needle up (by
        # homing, so every cycle starts from the switch), weigh. The unit is not sent to the module: the behaviour
        # tree applies the effects of Filling to it. The errors its answer can carry are ERRORS.
        skills=ModuleSkills(Errors=s.Errors(SkillError={
            name: s.SkillError(value=code, description=text) for name, code, text in ERRORS}), Skill={
            **{name: ModuleSkill(
                supplemental_semantic_ids=[f"{SKILL}/ModuleControl"],
                SemanticId=s.SemanticId(value=f"{SKILL_TYPE}/{name}"),
                Start=s.Start(semantic_id=f"{SKILL}/Start", SkillOperation={"Start": s.SkillOperation(
                    id_short="Start", semantic_id=f"{SKILL}/Start")}),
            ) for name in ("Occupy", "Release")},
            "Dispensing": ModuleSkill(
            supplemental_semantic_ids=[f"{SKILL}/Composite"],
            SemanticId=s.SemanticId(value=f"{SKILL_TYPE}/Dispensing"),
            Start=s.Start(
                semantic_id=f"{SKILL}/Start",
                SkillOperation={"Start": s.SkillOperation(
                    id_short="Start", semantic_id=f"{SKILL}/Start", input_variable=[
                        ParameterVariable(id_short="Volume", value="1.0", value_type="xs:double",
                                          supplemental_semantic_ids=[f"{LAB}FillVolume"],
                                          qualifiers=[AcceptsReference()], description="Fill volume, mL"),
                    ], output_variable=[
                        # The module's answer: its error code (0, or one of its Errors) and what the unit weighed,
                        # which Filling's reply classifies (D23, D34).
                        Property(id_short="ErrorID", value_type="xs:int",
                                 description="0, or the code of one of the module's Errors"),
                        Property(id_short="Weight", value_type="xs:double", supplemental_semantic_ids=[f"{LAB}Weight"],
                                 description="What the unit weighed after filling, g"),
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
            # Where the module and its transfer point are. The base is to be relative to the planar table's base once
            # the table declares one (the line's root); the values are placeholders until the station is measured.
            # The TransferPoint is the place a shuttle is sent to (the Target place of its MoveToPosition).
            "Coordinates": Coordinates(coordinate={
                "ModuleBase": RelativeCoordinate(
                    id_short="ModuleBase", supplemental_semantic_ids=[f"{LAB}ModuleBase"],
                    X=CoordinateX(value="240.0"), Y=CoordinateY(value="720.0"), Yaw=CoordinateYaw(value="180.0")),
                "TransferPoint": RelativeCoordinate(
                    id_short="TransferPoint", display_name={"en": "Filling module transfer point"},
                    supplemental_semantic_ids=[f"{LAB}TransferPoint"],
                    RelativeTo=CoordinateRelativeTo(value=ModelReference(key=MODULE_BASE)),
                    Y=CoordinateY(value="60.0")),
            }),
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
            MODULE_CONTROL: ModuleCapabilitySet(CapabilityContainer={"Occupying": occupying, "Releasing": releasing}),
        }),
    )
