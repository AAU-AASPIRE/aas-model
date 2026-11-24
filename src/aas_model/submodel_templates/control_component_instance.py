"""
Extended Skills — the IDTA Control Component Instance's Skill with its native interface and Operation.

The IDTA ControlComponentInstance template defines a Skill SMC with basic
fields (disabled, modes, parameters, errors, uses). This module extends it
with:
- interface_reference: ReferenceElement pointing to the AID action
- operation: the AAS Operation clients invoke, delegated to the DMP, and the roles of its variables
  (``ParameterVariable``, which may accept a reference, ``AcceptsReference``). Its variables are what the asset's
  action needs and answers, nothing more: the DMP maps them to the action and back.

What a skill's capability needs and changes, and how a call is built from its subjects, is not here: it is the
capability's conditions, effects and Translation (``capability_description``, ``execution``), which the behaviour
tree reads.

Named-field style: containers hold their children as DIRECT named fields
(no ``value``/``submodel_element`` wrapper); dynamic name-keyed maps are
``Dict[str, X]`` fields.
"""

from __future__ import annotations

from typing import ClassVar, Dict, List, Optional

from aas_pydantic import (
    Key, ModelReference,
    Property, ReferenceElement, Operation, RelationshipElement, Qualifier, SubmodelElementList,
)

from aas_pydantic.submodel_templates.control_component_instance import (
    Skill as _BaseSkill,
    Skills as _BaseSkills,
    Disabled, Modes, Parameters, Errors, Uses,
    Disabled_t, Modes_t, Parameters_t, Errors_t, Uses_t,
    Endpoints as _BaseEndpoints,
    ControlComponentInstance, Type_instance,
)

from aas_model.constants import (
    BASE_URL, CONTROL_COMPONENT_TYPE_SUBMODEL_ID, INVOCATION_URL_TEMPLATE, OPERATION_VARIABLE_ACCEPTS_REFERENCE,
    OPERATION_VARIABLE_PARAMETER,
)


EXTENDED_SKILLS = f"{BASE_URL}/ControlComponent/Skills/2/0"
EXTENDED_SKILL = f"{BASE_URL}/ControlComponent/Skill/2/0"
EXTENDED_SKILL_INTERFACE_REF = f"{BASE_URL}/ControlComponent/Skill/1/0"

# Skill Operation (operation delegation) + endpoint relationships
SKILL_OPERATION = f"{BASE_URL}/ControlComponent/Skill/Operation/2/0"
SKILL_INVOCATION_DELEGATION = f"{BASE_URL}/ControlComponent/Skill/InvocationDelegation/1/0"
SKILL_INTERFACE_RELATIONSHIP = f"{BASE_URL}/ControlComponent/Skill/NativeInterface/1/0"


# The value of an Operation variable may be absent at invocation (aas-camel-dmp SPEC §7):
# an optional input or InOut may be left out by the caller, an optional output or InOut
# by the reply. Without it a variable is required. (SMT/Cardinality says how many elements
# a template instance holds, not which values a call carries.)
OPERATION_VARIABLE_OPTIONAL = f"{BASE_URL}/aas/OperationVariable/Optional/1/0"


class OptionalVariable(Qualifier):
    """Marks an Operation variable (or a member of a collection variable) optional."""
    type_: str = "Optional"
    value: str = "true"
    value_type: str = "xs:boolean"
    kind: str = "ConceptQualifier"
    semantic_id: str = OPERATION_VARIABLE_OPTIONAL


class AcceptsReference(Qualifier):
    """Marks a parameter that may be sent as a reference instead of a value (D27): a ReferenceElement under the
    parameter's own idShort, to the element whose current value it is. The DMP resolves it at the call through its
    integrations and checks the target's meaning against the parameter's; a reference in a slot without this
    qualifier is rejected. Accepting a reference does not require one: the capability's Call script chooses."""
    type_: str = "AcceptsReference"
    value: str = "true"
    value_type: str = "xs:boolean"
    kind: str = "ConceptQualifier"
    semantic_id: str = OPERATION_VARIABLE_ACCEPTS_REFERENCE


class ParameterVariable(Property):
    """An Operation variable the payload is built from; what it means rides as a supplemental semantic id (the
    lab vocabulary), its unit is the meaning's. Sent as a value, or as a reference where it carries
    ``AcceptsReference``."""
    semantic_id: str = OPERATION_VARIABLE_PARAMETER


class InvocationDelegation(Qualifier):
    """The URL BaSyx delegates an Operation's invocation to: the DMP's AAS API invoke path of the Operation,
    filled from the template when the AAS is built (``invocation_authoring.resolve_invocation_addresses``)."""
    type_: str = "invocationDelegation"
    value: str = INVOCATION_URL_TEMPLATE
    kind: str = "ConceptQualifier"


class SkillOperation(Operation):
    """The skill's AAS Operation — the executable entry point for clients.

    Invoking it is delegated to the DMP via the
    ``invocationDelegation`` qualifier (which carries the generated REST
    endpoint). The input/inoutput/output variables mirror the native
    action's command / commandResponse payloads (e.g. ``Uuid``, ``State``,
    ``Outcome``) so the operation can also be rendered and invoked manually
    from the AAS Web GUI.

    A variable is any SubmodelElement, as in the AAS metamodel
    (``OperationVariable.value``): a Property for a scalar, a
    SubmodelElementCollection (subclass) for an object, a SubmodelElementList
    for an array. The DMP delegates Operations whose
    variables are Properties, collections and lists of them; other element
    types block the mapping there. A variable (or a collection member) is
    required unless it carries the :class:`OptionalVariable` qualifier.
    """
    semantic_id: str = SKILL_OPERATION
    description: str = "Operation to invoke this skill (delegated via operation delegation)."
    qualifiers: List[Qualifier] = [InvocationDelegation()]


class SkillInterfaceRelationship(RelationshipElement):
    """Annotated relationship: THIS skill has THIS native interface in the AID.

    ``first`` references the skill SMC (``ControlComponentInstance/skills/<skill>``),
    ``second`` references its native action in the AID
    (``AssetInterfacesDescription/<interface>/InteractionMetadata/actions/<skill>``).
    Replaces the generic Endpoint ``interface_reference``/``endpoint_reference``
    ReferenceElements for the per-skill native-interface linkage.
    """
    semantic_id: str = SKILL_INTERFACE_RELATIONSHIP
    description: str = "This skill has this native interface in the AID submodel."


class ResourceEndpoints(_BaseEndpoints):
    """Endpoints container holding one annotated native-interface relationship
    per skill (keyed by skill name) instead of generic Endpoint SMCs."""
    Endpoint: Dict[str, SkillInterfaceRelationship] = {}


class ExtendedSkill(_BaseSkill):
    """Skill children + the interface-reference + operation extensions, as
    DIRECT named fields.  The IDTA template marks ``Disabled``/``Modes``/
    ``Parameters``/``Errors``/``Uses`` as mandatory (One) — provided here so
    the extended skill constructs; stations override ``Modes`` etc. via
    config.

    ``interface_reference`` points at the skill's NATIVE interface (the AID
    action it maps to, on whichever interface the asset offers it);
    ``operation`` is the AAS Operation exposed to clients and delegated to
    the DMP."""
    semantic_id: str = EXTENDED_SKILL
    Disabled: Disabled_t = Disabled()
    Modes: Modes_t = Modes()
    Parameters: Parameters_t = Parameters()
    Errors: Errors_t = Errors()
    Uses: Uses_t = Uses()
    interface_reference: ReferenceElement = ReferenceElement(
        semantic_id=EXTENDED_SKILL_INTERFACE_REF,
        description="Reference to the AID action that natively implements this skill.",
    )
    operation: Optional[SkillOperation] = None


class ExtendedSkills(_BaseSkills):
    """Dynamic map of extended skills offered by the component instance
    (name → ExtendedSkill)."""
    semantic_id: str = EXTENDED_SKILLS
    Skill: Dict[str, ExtendedSkill] = {}


# Ensure forward references are resolved (Pydantic v2)
ExtendedSkill.model_rebuild()
ExtendedSkills.model_rebuild()


class ResourceControlComponentInstance(ControlComponentInstance):
    """CCI variant that uses ExtendedSkills + the per-skill endpoint
    relationships and default-constructs its mandatory children."""
    Endpoints: ResourceEndpoints = ResourceEndpoints()
    Skills: ExtendedSkills = ExtendedSkills()
    Type: Type_instance = Type_instance(
        value=ModelReference(
            key=(Key(type_="Submodel", value=CONTROL_COMPONENT_TYPE_SUBMODEL_ID),)
        )
    )
