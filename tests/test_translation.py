"""The Translations (D34) run: each script loads in a Lua 5.2 sandbox like the DMP's (no I/O), the call sends exactly
what the realizing Operation takes, the reply names only outcomes the capability declares and errors the skill can
answer with. And the mappings that sink into the state store (D36) give it the state the capabilities talk about. Needs lupa (``uv run --with lupa python -m pytest tests/test_translation.py``)."""

from __future__ import annotations

import json

import pytest
from basyx.aas import model

lupa = pytest.importorskip("lupa.lua52")

from aas_model import build_from_model  # noqa: E402
from aas_model.constants import (  # noqa: E402
    EXECUTION_ONE_OF, EXECUTION_SUBJECT_REQUIREMENT, LAB, PRODUCT_ASSET_TYPE,
)
from aas_model.product_instances import PRODUCT_FACTORIES  # noqa: E402
from aas_model.resource_instances import RESOURCE_FACTORIES  # noqa: E402
from aas_model.resource_instances.modules import MODULE_FACTORIES  # noqa: E402

UNIT = "urn:uuid:7f3a9c2e-5b1d-4e8a-9f60-2d4c8b1a0e57"
PLACE_X, PLACE_Y = 240.0, 660.0

SANDBOX = """
local json_decode, json_encode = ...
return function(code, name)
  local env = { assert = assert, error = error, ipairs = ipairs, next = next, pairs = pairs, pcall = pcall,
                select = select, tonumber = tonumber, tostring = tostring, type = type,
                math = math, string = string, table = table,
                json = { decode = json_decode, encode = json_encode } }
  local chunk, err = load(code, name, "t", env)
  if not chunk then error(err) end
  chunk()
  return env
end
"""

_lua = lupa.LuaRuntime(unpack_returned_tuples=True)
_load = _lua.execute(SANDBOX, lambda text: _table(json.loads(text)), lambda value: json.dumps(_py(value)))


def _table(value):
    if isinstance(value, dict):
        return _lua.table_from({k: _table(v) for k, v in value.items()})
    if isinstance(value, list):
        return _lua.table_from([_table(v) for v in value])
    return value


def _py(value):
    if lupa.lua_type(value) == "table":
        items = {k: _py(v) for k, v in value.items()}
        if items and list(items) == list(range(1, len(items) + 1)):
            return list(items.values())                             # a Lua sequence is an array
        return items
    return value


def _stores():
    """Each resource the example line and the stations name, in a store of its own (the module with its components)."""
    module = model.DictIdentifiableStore()
    for factory in MODULE_FACTORIES.values():
        for identifiable in build_from_model(factory()):
            module.add(identifiable)
    yield "fillingModule", module
    for name in ("dispensingStation", "stopperingStation", "planarShuttle1"):
        store = model.DictIdentifiableStore()
        for identifiable in build_from_model(RESOURCE_FACTORIES[name]()):
            store.add(identifiable)
        yield name, store


def _translated():
    """(resource, capability, its relations, the realizing Operation, the store) for every capability with a
    Translation."""
    found = []
    for name, store in _stores():
        for submodel in store:
            if not isinstance(submodel, model.Submodel) or submodel.id_short != "CapabilityDescription":
                continue
            for capability_set in submodel.submodel_element:
                for container in capability_set.value:
                    relations = container.get_referable("CapabilityRelations") if any(
                        e.id_short == "CapabilityRelations" for e in container.value) else None
                    if relations is None or not any(e.id_short == "Translation" for e in relations.value):
                        continue
                    found.append((name, container, relations, _operation(relations, store), store))
    return found


def _operation(relations, store) -> model.Operation:
    """The Operation of the one skill the capability is realized by."""
    (realized_by,) = [e for e in relations.value if isinstance(e, model.RelationshipElement)
                      and e.id_short.startswith("RealizedBy")]
    pending = [realized_by.second.resolve(store)]
    while pending:
        element = pending.pop(0)
        if isinstance(element, model.Operation):
            return element
        if isinstance(element, (model.SubmodelElementCollection, model.SubmodelElementList)):
            pending.extend(element.value)
    raise AssertionError(f"{relations.parent.id_short}: its skill has no Operation")


def _script(relations, which: str) -> str:
    return relations.get_referable(["Translation", which]).value.decode("utf-8")


def _required(meaning: str):
    """What the vial requires of its filling, with this meaning: a number, or a Range as {min, max}."""
    store = model.DictIdentifiableStore()
    for identifiable in build_from_model(PRODUCT_FACTORIES["vial2mL"]()):
        store.add(identifiable)
    description = next(s for s in store if isinstance(s, model.Submodel) and s.id_short == "CapabilityDescription")
    for entry in description.get_referable(["RequiredCapabilities", "Filling", "PropertySet"]).value:
        value = entry.get_referable("Value")
        if value.supplemental_semantic_id and value.supplemental_semantic_id[0].key[0].value == meaning:
            return {"min": float(value.min), "max": float(value.max)} if isinstance(value, model.Range) \
                else float(value.value)
    raise AssertionError(f"the vial requires nothing with meaning {meaning}")


def _subjects(relations) -> list[dict]:
    """The subjects as the behaviour tree hands them to a script: the unit, its requirements, a shuttle serving it, a
    place in the line's frame."""
    subjects = []
    for subject in relations.get_referable("Subjects").value:
        reference = subject.value
        meaning = reference.key[0].value
        entry = {"id": meaning, "state": {f"{LAB}OccupiedBy": UNIT, f"{LAB}AbsoluteX": PLACE_X,
                                         f"{LAB}AbsoluteY": PLACE_Y}}
        if isinstance(reference, model.ExternalReference) and meaning == PRODUCT_ASSET_TYPE:
            entry["id"] = UNIT
        if any(k.value == EXECUTION_SUBJECT_REQUIREMENT for r in subject.supplemental_semantic_id for k in r.key):
            entry["value"] = _required(meaning)
        subjects.append(entry)
    return subjects


def _variables(operation, *kinds) -> dict:
    return {v.id_short: v for kind in kinds for v in getattr(operation, kind)}


def _optional(variable) -> bool:
    return any(q.type == "Optional" and q.value in (True, "true") for q in variable.qualifier)


def _call(relations, subjects=None) -> dict:
    env = _load(_script(relations, "Call"), "Call")
    return _py(env.call(_table(subjects if subjects is not None else _subjects(relations)), _table({})))


def _reply(relations, outputs: dict, subjects=None) -> dict:
    env = _load(_script(relations, "Reply"), "Reply")
    return _py(env.reply(_table(outputs), _table(subjects if subjects is not None else _subjects(relations)),
                         _table({})))


def _outcomes(relations) -> set[str]:
    effects = relations.get_referable("EffectSet")
    return {outcome.id_short for section in effects.value for term in section.value
            if term.semantic_id and term.semantic_id.key[0].value == EXECUTION_ONE_OF for outcome in term.value}


def _errors(store) -> set[str]:
    return {error.id_short for submodel in store if isinstance(submodel, model.Submodel)
            and submodel.id_short == "Skills" for element in submodel.submodel_element
            if element.id_short == "Errors" for error in element.value}


TRANSLATED = _translated()


def test_the_capabilities_the_behaviour_tree_runs_have_translations():
    named = {(name, container.id_short) for name, container, *_ in TRANSLATED}
    assert {("fillingModule", "Filling"), ("fillingModule", "Occupying"), ("fillingModule", "Releasing"),
            ("dispensingStation", "Dispensing"), ("dispensingStation", "Occupying"), ("dispensingStation", "Releasing"),
            ("stopperingStation", "Occupying"), ("planarShuttle1", "MoveToPosition"),
            ("planarShuttle1", "Occupying")} <= named


@pytest.mark.parametrize("name, container, relations, operation, store", TRANSLATED,
                         ids=[f"{n}-{c.id_short}" for n, c, *_ in TRANSLATED])
def test_the_call_sends_exactly_what_the_operation_takes(name, container, relations, operation, store):
    sent = _call(relations)
    takes = _variables(operation, "input_variable", "in_output_variable")
    assert set(sent) <= set(takes), f"{container.id_short} sends what {operation.id_short} does not take"
    required = {n for n, v in takes.items() if not _optional(v)}
    assert required <= set(sent), f"{container.id_short} leaves out {required - set(sent)}"


@pytest.mark.parametrize("name, container, relations, operation, store", TRANSLATED,
                         ids=[f"{n}-{c.id_short}" for n, c, *_ in TRANSLATED])
def test_the_reply_names_only_declared_outcomes_and_errors(name, container, relations, operation, store):
    answered = _variables(operation, "output_variable", "in_output_variable")
    success = {"State": "SUCCESS", "ErrorID": 0, "Weight": 2.0, "Outcome": 0, "Uuid": UNIT[9:]}
    failure = {**success, "State": "FAILURE", "ErrorID": 3}
    outcomes = _outcomes(relations)
    ok = _reply(relations, {k: v for k, v in success.items() if k in answered})
    assert ok["ok"] is True and (ok.get("outcome") in outcomes if outcomes else "outcome" not in ok)
    if answered:                                                    # a skill that answers can fail
        failed = _reply(relations, {k: v for k, v in failure.items() if k in answered})
        assert failed["ok"] is False and failed.get("error") in _errors(store) | {None}


def test_filling_classifies_the_weight_against_what_the_product_requires():
    (relations,) = [r for n, c, r, *_ in TRANSLATED if (n, c.id_short) == ("fillingModule", "Filling")]
    assert _call(relations) == {"Volume": 2.0}                      # the vial's required FillVolume
    assert _reply(relations, {"ErrorID": 0, "Weight": 1.95}) == {"ok": True, "outcome": "InTolerance"}
    assert _reply(relations, {"ErrorID": 0, "Weight": 2.3}) == {"ok": True, "outcome": "OutOfTolerance"}
    assert _reply(relations, {"ErrorID": 0, "Weight": 1.0}) == {"ok": True, "outcome": "OutOfTolerance"}
    assert _reply(relations, {"ErrorID": 3, "Weight": 0.0}) == {"ok": False, "error": "PumpFault"}


def test_a_station_command_carries_the_units_uuid_its_queue_holds():
    (occupying,) = [r for n, c, r, *_ in TRANSLATED if (n, c.id_short) == ("dispensingStation", "Occupying")]
    assert _call(occupying) == {"Uuid": UNIT[len("urn:uuid:"):]}
    (dispensing,) = [r for n, c, r, *_ in TRANSLATED if (n, c.id_short) == ("dispensingStation", "Dispensing")]
    assert _call(dispensing) == {"Uuid": UNIT[len("urn:uuid:"):], "Volume": 2.0}


def test_a_move_goes_to_the_places_pose_for_the_unit_the_shuttle_serves():
    (move,) = [r for n, c, r, *_ in TRANSLATED if (n, c.id_short) == ("planarShuttle1", "MoveToPosition")]
    assert _call(move) == {"Uuid": UNIT[len("urn:uuid:"):], "ProductID": UNIT, "X": PLACE_X, "Y": PLACE_Y,
                           "Theta": 0.0}
    idle = _subjects(move)
    del idle[0]["state"][f"{LAB}OccupiedBy"]
    with pytest.raises(lupa.LuaError, match="serves no unit"):
        _call(move, idle)


def _mapping(store, sink_id: str):
    """The AIMC mapping of a store's resource with this SinkId."""
    for submodel in store:
        if isinstance(submodel, model.Submodel) and submodel.id_short == "AssetInterfacesMappingConfiguration":
            for mapping in submodel.get_referable("MappingConfigurations").value:
                if any(s.get_referable("SinkId").value == sink_id for s in mapping.get_referable("Sinks").value):
                    return mapping
    raise AssertionError(f"no mapping sinks {sink_id}")


def _transform(mapping, sources: dict) -> dict:
    code = mapping.get_referable("Transformation").value.decode("utf-8")
    return _py(_load(code, "Transformation").aimc_main(_table(sources)))


def test_a_station_sinks_the_head_of_its_queue_as_who_it_serves():
    """The station-state mapping writes the series row and, into the state store, the unit at the queue's head."""
    store = dict(_stores())["dispensingStation"]
    mapping = _mapping(store, "OccupiedBy")
    out = _transform(mapping, {"State": "EXECUTE", "ProcessQueue": ["7f3a9c2e", "0b1d"]})
    assert out["OccupiedBy"] == "urn:uuid:7f3a9c2e"
    assert out["Live"] == {"PackMLState": "EXECUTE", "OccupationState": '["7f3a9c2e", "0b1d"]'}
    assert "OccupiedBy" not in _transform(mapping, {"State": "IDLE", "ProcessQueue": []})    # none: free


def test_a_shuttle_sinks_its_reported_position_beside_the_series_row():
    mapping = _mapping(dict(_stores())["planarShuttle1"], "X")
    out = _transform(mapping, {"Location": {"Position": [240.0, 660.0, 0.5]}})
    assert (out["X"], out["Y"]) == (240.0, 660.0) and out["Live"]["yaw"] == 0.5


def test_the_transfer_points_position_is_composed_with_its_base():
    """Base at (240, 720) turned by 180°, the point 60 mm along the base's Y: (240, 660) in the line's frame, the
    pose MoveToPosition's call sends a shuttle to."""
    mapping = _mapping(dict(_stores())["fillingModule"], "TransferPointX")
    out = _transform(mapping, {"ModuleBase": {"X": "240.0", "Y": "720.0", "Yaw": "180.0"},
                               "TransferPoint": {"Y": "60.0"}})
    assert out["TransferPointX"] == pytest.approx(PLACE_X) and out["TransferPointY"] == pytest.approx(PLACE_Y)
