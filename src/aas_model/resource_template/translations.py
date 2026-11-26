"""The Lua of the capabilities' Translations (``execution.Translation``, plan D34) that recur across resources.

Each script is a pure function in the lab's Lua profile (Lua 5.2, the DMP's sandbox): no I/O; the behaviour tree
fills its arguments (``execution`` says how) and applies the effects of the outcome the reply names. Nothing here
writes state.

A unit's IRI is ``urn:uuid:<uuid>`` (D35). A station queues the commands of the unit it serves by that uuid: Occupy
puts it in the process queue and answers SUCCESS once it is at the head, every command the station then runs for the
unit carries it, Release takes it out. So the uuid is both the unit's name and its claim on the station.
"""

from aas_model.constants import LAB

# The uuid of a unit's IRI, for the station's command Uuid.
UNIT_UUID = """local function unit_uuid(subject)
  local uuid = string.match(subject.id, "^urn:uuid:(.+)$")
  if uuid == nil then error("not a unit IRI: " .. tostring(subject.id)) end
  return uuid
end
"""


def command_for_unit(unit: int) -> str:
    """Call: a PackML command on behalf of the unit at subject ``unit`` (0-based, as the terms count): its Uuid."""
    return UNIT_UUID + f"""function call(subjects, properties)
  return {{ Uuid = unit_uuid(subjects[{unit + 1}]) }}
end
"""


# Reply: a PackML command's terminal State; SUCCESS or not, with no error code to name a cause.
COMMAND_STATE_REPLY = """function reply(outputs, subjects, properties)
  return { ok = outputs.State == "SUCCESS" }
end
"""

# Call and reply of a skill that takes nothing and answers nothing but its completion.
NO_INPUTS_CALL = """function call(subjects, properties)
  return {}
end
"""
COMPLETED_REPLY = """function reply(outputs, subjects, properties)
  return { ok = true }
end
"""

LAB_PREFIX = f'local LAB = "{LAB}"\n'
