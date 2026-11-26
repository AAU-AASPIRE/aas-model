#!/usr/bin/env python3
"""Build the example AASs of the Production Sequence 4.0 (proposed,
``docs/lab-submodels/ProductionSequence4.md``) and check them. Run from the aas-model root::

    PYTHONPATH=src python scripts/export_precedence_examples.py --out <folder> [--against <folder>]

Two cases, each written to ``<folder>/<case>/<idShort>.json`` and, all of them in one file, to
``<folder>/<case>/<case>-environment.json`` (to load into an AAS server at once):

- battery: the pack (``aas_model.product_instances.battery_pack``), its four modules
  (``battery_module``), the cell type (``battery_cell``) and the process AAS in the simulated
  disassembly cell (``aas_model.process_instances.battery_pack_on_disassembly_cell``);
- pharma: the 2 mL vial (``vial_2ml``), its flip-off seal and the seal's aluminium part, and the
  process AAS on the filling line (``vial_2ml_on_filling_line``).

What is checked, and printed:
- every reference in these AASs: found, found in ``--against`` (a folder of AAS JSON environments,
  e.g. a copy of the lab's server with the filling line), or into an AAS not modelled (the battery
  cell's stations);
- every partial block: its ProcessOrders join only steps of the block, no cycle, Order respects them;
- every joint: first and second are entities of the bill of material of the AAS holding the step,
  each joint is defined once in its AAS, a joint referred to from another archetype exists;
- every call: its Part is an entity of the bill of material whose asset id has an AAS here with a
  sequence of the same ArcheType (the sequence the call runs);
- every step of a recipe (and of the sequences it calls) has a binding in the process AAS.

Nothing is sent to a server.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from basyx.aas import model as basyx
from basyx.aas.adapter.json import AASToJsonEncoder

from aas_pydantic import convert_model_to_aas
from aas_pydantic.convert_util import strip_temp_id_short_attributes

from aas_model.id_injector import inject_ids
from aas_model.process_instances import battery_pack_on_disassembly_cell, vial_2ml_on_filling_line
from aas_model.product_instances import (
    aluminium_seal, battery_cell, battery_module, battery_pack, flip_off_seal, vial_2ml,
)

SEQUENCE = "https://smartproductionlab.aau.dk/SubmodelTemplate/ProductionSequence/4/0"
# A Product without a bill of material or processes of its own (a part) gets empty defaults.
DEFAULTS = {"HierarchicalStructures": "hierarchical_structures", "ProcessParameters": "process_parameters"}
IEC61360 = "https://admin-shell.io/DataSpecificationTemplates/DataSpecificationIEC61360/3/0"
BOOLEAN_QUALIFIERS = ("CapabilityRoleQualifier/Required", "CapabilityRoleQualifier/Offered",
                      "CapabilityRoleQualifier/NotAssigned", "Derived")


def with_units(element) -> None:
    """Every element with a ``Unit`` qualifier also states its unit the standard way, in an IEC 61360
    data specification, first among its data specifications (where the BaSyx web UI's capability
    matching looks), as iec61499-mgmt-py's ``modreg`` writes the lab's AASs."""
    if isinstance(element, list):
        for item in element:
            with_units(item)
        return
    if not isinstance(element, dict):
        return
    unit = next((q.get("value") for q in element.get("qualifiers") or [] if q.get("type") == "Unit"), None)
    if unit and element.get("modelType") not in (None, "Submodel", "AssetAdministrationShell"):
        names = element.get("displayName") or [{"language": "en", "text": element.get("idShort", "")}]
        element["embeddedDataSpecifications"] = [{
            "dataSpecification": {"type": "ExternalReference", "keys": [{"type": "GlobalReference", "value": IEC61360}]},
            "dataSpecificationContent": {"modelType": "DataSpecificationIec61360", "preferredName": names, "unit": unit},
        }, *(element.get("embeddedDataSpecifications") or [])]
    for value in element.values():
        if isinstance(value, (list, dict)):
            with_units(value)


def typed_qualifiers(element) -> None:
    """The capability role qualifiers are booleans (IDTA 02020). The model keeps them as strings, as
    BaSyx refuses "true" for an xs:boolean it is handed uncast; the JSON says xs:boolean."""
    if isinstance(element, list):
        for item in element:
            typed_qualifiers(item)
    elif isinstance(element, dict):
        for qualifier in element.get("qualifiers") or []:
            if qualifier.get("type") in BOOLEAN_QUALIFIERS:
                qualifier["valueType"] = "xs:boolean"
        for value in element.values():
            if isinstance(value, (list, dict)):
                typed_qualifiers(value)


def environment(asset, asset_id: str, kind: str = "Type") -> dict:
    """The AAS environment of an instance: its submodels with ids ``{aas id}/submodels/{idShort}``
    (the Production Sequences keep theirs), the asset's own id, and ``kind`` Instance for an AAS of
    one item (the pack and its modules, which come back used). A default submodel the instance does
    not set is left out. Units and the capability role qualifiers are written as the lab's other AASs
    are (``with_units``, ``typed_qualifiers``)."""
    asset = asset.model_copy(deep=True)
    inject_ids(asset)
    store = convert_model_to_aas(asset)
    strip_temp_id_short_attributes(store)
    found = {"assetAdministrationShells": [o for o in store if isinstance(o, basyx.AssetAdministrationShell)],
             "submodels": [o for o in store if isinstance(o, basyx.Submodel)]}
    env = json.loads(json.dumps(found, cls=AASToJsonEncoder))
    with_units(env["submodels"])
    typed_qualifiers(env["submodels"])
    dropped = {sm["id"] for sm in env["submodels"]
               if sm["idShort"] in DEFAULTS and DEFAULTS[sm["idShort"]] not in asset.model_fields_set}
    env["submodels"] = [sm for sm in env["submodels"] if sm["id"] not in dropped]
    shell = env["assetAdministrationShells"][0]
    shell["submodels"] = sorted((r for r in shell.get("submodels", []) if r["keys"][0]["value"] not in dropped),
                                key=lambda r: r["keys"][0]["value"])
    shell["assetInformation"]["globalAssetId"] = asset_id
    shell["assetInformation"]["assetKind"] = kind
    env["conceptDescriptions"] = []
    return env


def battery() -> list[dict]:
    envs = [environment(battery_pack.battery_pack(), battery_pack.ASSET_ID, battery_pack.ASSET_KIND)]
    for n in (1, 2, 3, 4):
        envs.append(environment(battery_module.battery_module(n), battery_module.ids(n)["asset"],
                                battery_module.ASSET_KIND))
    envs.append(environment(battery_cell.battery_cell(), battery_cell.ASSET_ID))
    envs.append(environment(battery_pack_on_disassembly_cell.battery_pack_on_disassembly_cell(),
                            battery_pack_on_disassembly_cell.ASSET_ID))
    return envs


def pharma() -> list[dict]:
    return [
        environment(vial_2ml.vial_2ml(), vial_2ml.ASSET_ID),
        environment(flip_off_seal.flip_off_seal(), flip_off_seal.ASSET_ID),
        environment(aluminium_seal.aluminium_seal(), aluminium_seal.ASSET_ID),
        environment(vial_2ml_on_filling_line.vial_2ml_on_filling_line(), vial_2ml_on_filling_line.ASSET_ID),
    ]


CASES = {"battery": battery, "pharma": pharma}


# ---- the checks --------------------------------------------------------------------------------------
# A line of the report that starts with one of these is a fault.
FAULTS = ("BROKEN", "UNBOUND", "TWICE", "JOINT", "AFTER", "CYCLE", "ORDER", "CALL")


def semantic(element: dict) -> str:
    return ((element.get("semanticId") or {}).get("keys") or [{}])[0].get("value", "")


def child(element: dict, id_short: str) -> dict | None:
    for c in element.get("value") or element.get("submodelElements") or element.get("statements") or []:
        if isinstance(c, dict) and c.get("idShort") == id_short:
            return c
    return None


def value(element: dict, id_short: str) -> str:
    found = child(element, id_short)
    return str(found.get("value")) if found else ""


class Index:
    """The shells and submodels of some environments, and what a model reference points at."""

    def __init__(self, envs: list[dict]):
        self.shells = {s["id"]: s for e in envs for s in e["assetAdministrationShells"]}
        self.submodels = {s["id"]: s for e in envs for s in e["submodels"]}

    def resolve(self, ref: dict) -> dict | None:
        keys = ref.get("keys") or []
        if not keys:
            return None
        if keys[0]["type"] == "AssetAdministrationShell":
            return self.shells.get(keys[0]["value"])
        at = self.submodels.get(keys[0]["value"])
        for key in keys[1:]:
            if at is None:
                return None
            items = at.get("value") or at.get("submodelElements") or at.get("statements") or []
            if at.get("modelType") == "SubmodelElementList" and key["value"].isdigit():
                k = int(key["value"])
                at = items[k] if k < len(items) else None
            elif at.get("modelType") == "Operation":
                at = next((v["value"] for side in ("inputVariables", "outputVariables", "inoutputVariables")
                           for v in at.get(side) or [] if v["value"].get("idShort") == key["value"]), None)
            else:
                at = next((c for c in items if isinstance(c, dict) and c.get("idShort") == key["value"]), None)
        return at


def references(element, path=""):
    """Every model reference in an element, with where it is."""
    if isinstance(element, dict):
        if element.get("type") == "ModelReference" and "keys" in element:
            yield path, element
            return
        for k, v in element.items():
            if k in ("semanticId", "supplementalSemanticIds"):
                continue
            yield from references(v, f"{path}/{element.get('idShort', k)}" if k in ("value", "submodelElements") else path)
    elif isinstance(element, list):
        for v in element:
            yield from references(v, path)


def check(envs: list[dict], against: list[dict]) -> list[str]:
    """The report on one case: a line per finding (a fault starts with one of ``FAULTS``)."""
    mine, line = Index(envs), Index(against + envs)      # these AASs over the copies
    lines, missing = [], set()
    n = 0
    for env in envs:
        for sm in env["submodels"]:
            for where, ref in references(sm):
                n += 1
                if mine.resolve(ref) is not None or line.resolve(ref) is not None:
                    continue
                first = ref["keys"][0]["value"]
                owner = first.split("/submodels/")[0]
                if first not in line.submodels and first not in line.shells and owner not in line.shells:
                    missing.add(owner)
                else:
                    lines.append(f"BROKEN {sm['idShort']}{where}: {[k['value'] for k in ref['keys']]}")
    lines.insert(0, f"references: {n}, of which into AASs not modelled: "
                    + (", ".join(sorted(m.rsplit('/', 1)[-1] for m in missing)) or "none"))

    bound = set()
    for env in envs:
        for sm in env["submodels"]:
            if sm.get("idShort") == "Bindings":
                for b in sm.get("submodelElements", []):
                    step = child(b, "Step")
                    if step:
                        bound.add(json.dumps([k["value"] for k in step["value"]["keys"]]))
    # A call names a part of the bill of material; the sequence it runs is the one of the same ArcheType in
    # the AAS of the part's asset id.
    by_asset = {e["assetAdministrationShells"][0]["assetInformation"].get("globalAssetId"): e for e in envs}

    def calls(sequence: dict):
        """The sequences ``sequence`` calls (their ids), and a line for each call it cannot follow."""
        found, faults = [], []

        def walk(steps):
            for s in (steps or {}).get("value", []):
                if s.get("modelType") != "SubmodelElementCollection":
                    continue
                if value(s, "Kind") == "call":
                    part = child(s, "Part")
                    entity = mine.resolve(part["value"]) if part else None
                    env = by_asset.get((entity or {}).get("globalAssetId"))
                    target = next((sm for sm in (env or {}).get("submodels", []) if semantic(sm) == SEQUENCE
                                   and value(sm, "ArcheType") == value(sequence, "ArcheType")), None)
                    if target is None:
                        faults.append(f"CALL {value(s, 'NodeId')} in {sequence['idShort']}: no part, no AAS for its "
                                      f"asset id, or no {value(sequence, 'ArcheType')} sequence there")
                    else:
                        found.append(target["id"])
                walk(child(s, "Steps"))
                for br in (child(s, "Branches") or {}).get("value", []):
                    walk(child(br, "Steps"))
        walk(child(sequence, "Steps"))
        return found, faults

    for env in envs:
        for sm in env["submodels"]:
            if semantic(sm) == SEQUENCE:
                lines.extend(calls(sm)[1])
    # The sequences a process AAS runs: its Recipe, and what the Recipe calls.
    run, todo = set(), [child(sm, "Recipe")["value"]["keys"][0]["value"] for env in envs for sm in env["submodels"]
                        if sm.get("idShort") == "ProcessInformation"]
    while todo:
        sid = todo.pop()
        if sid in run or sid not in mine.submodels:
            continue
        run.add(sid)
        todo.extend(calls(mine.submodels[sid])[0])
    idle = [sm["idShort"] + " of " + env["assetAdministrationShells"][0]["idShort"] for env in envs
            for sm in env["submodels"] if semantic(sm) == SEQUENCE and sm["id"] not in run]
    if idle:
        lines.append("not run by a process AAS here, so not checked for bindings: " + ", ".join(idle))
    steps_total = 0
    for env in envs:
        shell = env["assetAdministrationShells"][0]
        bill = next((s for s in env["submodels"] if s["idShort"] == "HierarchicalStructures"), None)
        entities = set()
        if bill:
            entry = child(bill, "EntryNode")
            entities = {s["idShort"] for s in (entry or {}).get("statements", []) if s.get("modelType") == "Entity"}
        defined = set()
        for sm in env["submodels"]:
            if semantic(sm) != SEQUENCE:
                continue
            arche = value(sm, "ArcheType")

            def walk(steps: dict, prefix: list[str]):
                """``steps``: a Steps collection; ``prefix``: the keys to it, from the submodel's id."""
                nonlocal steps_total
                items = [s for s in steps.get("value", []) if s.get("modelType") == "SubmodelElementCollection"]
                for s in items:
                    kind, keys = value(s, "Kind"), prefix + [s["idShort"]]
                    if kind == "step" and sm["id"] in run:
                        steps_total += 1
                        if json.dumps(keys) not in bound:
                            lines.append(f"UNBOUND {shell['idShort']}/{sm['idShort']}: {value(s, 'NodeId')}")
                    for j in (child(s, "Joints") or {}).get("value", []):
                        if j["modelType"] == "AnnotatedRelationshipElement":
                            if j["idShort"] in defined:
                                lines.append(f"TWICE joint {j['idShort']} in {shell['idShort']}")
                            defined.add(j["idShort"])
                            for side in ("first", "second"):
                                target = j[side]["keys"]
                                if not (target[0]["value"] == (bill or {}).get("id") and target[-1]["value"] in entities):
                                    lines.append(f"JOINT {j['idShort']}.{side} is not a part of {shell['idShort']}")
                        elif j["modelType"] == "ReferenceElement":
                            found = mine.resolve(j["value"])
                            if found is None or found.get("modelType") != "AnnotatedRelationshipElement":
                                lines.append(f"JOINT reference {j['idShort']} not found")
                    if kind == "partial":
                        inner = child(s, "Steps")
                        sib = {c["idShort"]: c for c in inner.get("value", [])}
                        after = {name: [] for name in sib}          # a step: the steps before it
                        for o in (child(s, "ProcessOrders") or {}).get("value", []):
                            ends = [[x["value"] for x in o[side]["keys"]] for side in ("first", "second")]
                            if any(k[:-1] != keys + ["Steps"] or k[-1] not in sib for k in ends):
                                lines.append(f"AFTER {o['idShort']} joins a step outside its block")
                            else:
                                after[ends[1][-1]].append(ends[0][-1])
                        layers, done = [], set()
                        while len(done) < len(sib):
                            ready = [x for x in sib if x not in done and set(after[x]) <= done]
                            if not ready:
                                lines.append(f"CYCLE among {sorted(set(sib) - done)}")
                                break
                            layers.append(", ".join(value(sib[x], "NodeId") for x in ready))
                            done |= set(ready)
                        for x, before in after.items():
                            for y in before:
                                if int(value(sib[y], "Order")) >= int(value(sib[x], "Order")):
                                    lines.append(f"ORDER {value(sib[x], 'NodeId')} is not after {value(sib[y], 'NodeId')}")
                        lines.append(f"{shell['idShort']}/{sm['idShort']} ({arche}), ready in turn: "
                                     + " | ".join(f"[{layer}]" for layer in layers))
                        walk(inner, keys + ["Steps"])
                    for br in (child(s, "Branches") or {}).get("value", []):
                        walk(child(br, "Steps"), keys + ["Branches", br["idShort"], "Steps"])
            walk(child(sm, "Steps"), [sm["id"], "Steps"])
    lines.append(f"steps run by a process AAS: {steps_total}")
    return lines


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--against", type=Path, help="a folder of AAS JSON environments the references may point into")
    args = ap.parse_args(argv)
    against = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(args.against.glob("*.json"))] if args.against else []
    faults = 0
    for case, made in CASES.items():
        envs = made()
        folder = args.out / case
        folder.mkdir(parents=True, exist_ok=True)
        for env in envs:
            name = env["assetAdministrationShells"][0]["idShort"]
            (folder / f"{name}.json").write_text(json.dumps(env, indent=2, ensure_ascii=False), encoding="utf-8")
        whole = {"assetAdministrationShells": [s for e in envs for s in e["assetAdministrationShells"]],
                 "submodels": [s for e in envs for s in e["submodels"]], "conceptDescriptions": []}
        (folder / f"{case}-environment.json").write_text(json.dumps(whole, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"{case}: {len(envs)} AASs, {len(whole['submodels'])} submodels -> {folder}")
        for line in check(envs, against):
            faults += line.startswith(FAULTS)
            print(f"  {line}")
    return 1 if faults else 0


if __name__ == "__main__":
    raise SystemExit(main())
