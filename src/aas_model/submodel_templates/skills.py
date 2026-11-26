"""The Skills submodel (ARSO) as every resource of the lab uses it: a skill under a name of its own, its commands and
their Operations.

The classes of ARSO's Skills are generated (``submodel_templates.arso.skills``). Declared here is what they leave
open: ``ModuleSkill``, a skill under a class name of its own (an element is read back as the class its dump names), and
``command_skill``, a skill of one command (Start) that a device carries out on one action of its interface: a station's
PackML commands (Occupy, Release, Halt) and its process skill (Loading, Dispensing, ...).

A command's Operation is delegated to the DMP (its ``invocationDelegation`` qualifier, filled in when the AAS is built,
``invocation_authoring``); its variables are what the device's action takes and answers. Its ``InterfaceReference``
names that action; the AIMC mapping that has the Operation as its Source binds the call to it.
"""

from __future__ import annotations

from typing import Dict

from aas_pydantic import ModelReference

from aas_model.constants import BASE_URL
from aas_model.submodel_templates.arso import skills as arso

SKILL = f"{BASE_URL}/skill"                 # a skill's commands and kinds (iec61499-mgmt-py, commands.ttl)
SKILL_TYPE = f"{BASE_URL}/skills"           # what a skill does (skills.ttl)

# The kinds of skill, as a supplemental semantic id: one the device carries out as a whole (Primitive), one whose
# steps run others (Composite), and the device's own commands (ModuleControl: Occupy, Release, Halt, ...).
PRIMITIVE = f"{SKILL}/Primitive"
COMPOSITE = f"{SKILL}/Composite"
MODULE_CONTROL = f"{SKILL}/ModuleControl"


class ModuleSkill(arso.Skill):
    """A skill as its commands (Start, Stop, Abort, Reset), each with the interface action that calls
    it, its Operation and, for a composite, its steps."""


class ModuleSkills(arso.Skills):
    """The Skills submodel: the skills and the errors they report."""
    Skill: Dict[str, ModuleSkill] = {}
    Errors: arso.Errors = arso.Errors()


def command_skill(name: str, kind: str, action: ModelReference, operation: arso.SkillOperation) -> ModuleSkill:
    """A skill of one command, Start: the device's action ``action`` (an AID action) carries it out, called through
    ``operation`` (named Start here, its variables the action's). ``kind`` is PRIMITIVE, COMPOSITE or
    MODULE_CONTROL; what the skill does is ``SKILL_TYPE/<name>``."""
    operation.id_short = "Start"
    operation.semantic_id = f"{SKILL}/Start"
    return ModuleSkill(
        supplemental_semantic_ids=[kind],
        SemanticId=arso.SemanticId(value=f"{SKILL_TYPE}/{name}"),
        Start=arso.Start(semantic_id=f"{SKILL}/Start", InterfaceReference=arso.InterfaceReference(value=action),
                         SkillOperation={"Start": operation}),
    )


ModuleSkill.model_rebuild()
ModuleSkills.model_rebuild()
