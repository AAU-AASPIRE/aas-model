"""The address a skill's Operation is invoked at.

A skill's Operation is delegated to the DMP by its invocationDelegation qualifier, authored as
``INVOCATION_URL_TEMPLATE``. Its ``{operation_path}`` is filled when the AAS is built (``inject_ids``), once the
Skills submodel's id is known; a concrete URL authored instead is kept.
"""

from __future__ import annotations

import base64
from urllib.parse import quote

OPERATION_PATH = "{operation_path}"


def operation_path(submodel_id: str, id_short_path: str) -> str:
    """The path an Operation is invoked at in the AAS API:
    ``/submodels/{base64url(submodel id)}/submodel-elements/{idShortPath}/invoke``.

    A submodel id is globally unique and an idShortPath unique within its submodel, so no two Operations share
    a path. The DMP serves exactly this path and rejects any other.
    """
    encoded = base64.urlsafe_b64encode(submodel_id.encode("utf-8")).decode("ascii").rstrip("=")
    return f"/submodels/{encoded}/submodel-elements/{quote(id_short_path, safe='.')}/invoke"


def resolve_invocation_addresses(aas) -> None:
    """Fill the ``{operation_path}`` of the invocationDelegation qualifier of each Operation in the Skills submodel:
    a command's (``<skill>.<command>.<operation>``) and, in a skill's short form, the skill's own
    (``<skill>.<operation>``). The Skills submodel's id must be set."""
    skills = getattr(aas, "skills", None)
    if skills is None:
        return
    for skill_key, skill in (skills.Skill or {}).items():
        # The idShortPath is made of map keys and field names, as the AAS holds it.
        operations = [(f"{skill_key}.{key}", operation) for key, operation in (skill.SkillOperation or {}).items()]
        for command in ("Start", "Stop", "Abort", "Reset"):
            held = getattr(skill, command, None)
            if held is not None:
                operations += [(f"{skill_key}.{command}.{key}", operation)
                               for key, operation in (held.SkillOperation or {}).items()]
        for id_short_path, operation in operations:
            path = operation_path(skills.id, id_short_path)
            for qualifier in operation.qualifiers:
                if qualifier.type_ == "invocationDelegation":
                    qualifier.value = qualifier.value.replace(OPERATION_PATH, path)
