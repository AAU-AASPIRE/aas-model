"""
Skill Operations — the delegated Operation of a skill's command and the roles of its variables.

A skill's command (ARSO Skills, ``submodel_templates.skills``) is called through its Operation (``SkillOperation``),
delegated to the DMP by its ``invocationDelegation`` qualifier. Its variables are what the asset's action needs and
answers, nothing more: the DMP maps them to the action and back. A variable may be a parameter
(``ParameterVariable``), which may accept a reference (``AcceptsReference``), or optional (``OptionalVariable``).

What a skill's capability needs and changes, and how a call is built from its subjects, is not here: it is the
capability's conditions, effects and Translation (``capability_description``, ``execution``), which the behaviour
tree reads.

The module keeps its name from the IDTA Control Component Instance, which the lab's resources no longer use: every
resource has the ARSO Skills submodel.
"""

from __future__ import annotations

from typing import List

from aas_pydantic import Property, Operation, Qualifier

from aas_model.constants import (
    BASE_URL, INVOCATION_URL_TEMPLATE, OPERATION_VARIABLE_ACCEPTS_REFERENCE, OPERATION_VARIABLE_PARAMETER,
)


# Skill Operation (operation delegation)
SKILL_OPERATION = f"{BASE_URL}/ControlComponent/Skill/Operation/2/0"
SKILL_INVOCATION_DELEGATION = f"{BASE_URL}/ControlComponent/Skill/InvocationDelegation/1/0"


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
