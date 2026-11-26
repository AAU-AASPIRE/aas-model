"""The example AASs of the Production Sequence 4.0: they build, the checks of
scripts/export_precedence_examples.py find no fault, and a sequence reads back into its classes."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import export_precedence_examples as examples  # noqa: E402


@pytest.fixture(scope="module")
def cases() -> dict[str, list[dict]]:
    return {case: made() for case, made in examples.CASES.items()}


@pytest.mark.parametrize("case", sorted(examples.CASES))
def test_the_checks_find_no_fault(cases, case):
    report = examples.check(cases[case], [])
    assert [line for line in report if line.startswith(examples.FAULTS)] == []


def test_the_steps_of_the_pack_become_ready_in_turn(cases):
    report = examples.check(cases["battery"], [])
    assert ("BatteryPackAAS/ProductionSequenceDisassembly (Disassembly), ready in turn: [UnscrewCover, UnplugHV] | "
            "[RemoveBusbars, RemoveBMS] | [BatteryModule1, BatteryModule2, BatteryModule3, BatteryModule4]") in report
    assert "steps run by a process AAS: 20" in report
    # Only the stations of the disassembly cell are not modelled.
    assert report[0].endswith("DisassemblyCellAAS, HandlingStationAAS, TestStationAAS, UnscrewingStationAAS")


def test_a_fault_is_found(cases):
    import copy
    broken = copy.deepcopy(cases["pharma"])
    sequence = next(sm for sm in broken[0]["submodels"] if sm["idShort"] == "ProductionSequenceAssembly")
    # Filling after Inspection: a cycle, and an Order that does not respect the ProcessOrders.
    orders = examples.child(examples.child(examples.child(sequence, "Steps"), "Step_0000"), "ProcessOrders")
    back = copy.deepcopy(orders["value"][0])                   # Filling before Stoppering, turned round
    back["idShort"] = "ProcessOrder_9999"
    back["first"]["keys"][-1]["value"], back["second"]["keys"][-1]["value"] = "Step_0003", "Step_0000"
    orders["value"].append(back)
    found = [line.split()[0] for line in examples.check(broken, []) if line.startswith(examples.FAULTS)]
    assert "CYCLE" in found and "ORDER" in found


def test_a_call_runs_the_sequence_of_its_part(cases):
    import copy
    report = examples.check(cases["battery"], [])
    idle = next((line for line in report if line.startswith("not run by a process AAS")), "")
    assert "BatteryModule" not in idle                                  # the four modules' sequences are run
    broken = copy.deepcopy(cases["battery"])
    sequence = next(sm for sm in broken[0]["submodels"] if sm["idShort"] == "ProductionSequenceDisassembly")
    call = examples.child(examples.child(examples.child(examples.child(sequence, "Steps"), "Step_0000"), "Steps"),
                          "Step_0004")
    examples.child(call, "Part")["value"]["keys"][-1]["value"] = "Busbars"             # a part with no AAS
    found = [line for line in examples.check(broken, []) if line.startswith("CALL")]
    assert found and "BatteryModule1" in found[0]


def test_the_shell_names_its_asset_and_kind(cases):
    pack = cases["battery"][0]["assetAdministrationShells"][0]["assetInformation"]
    assert pack["globalAssetId"] == "https://smartproductionlab.aau.dk/assets/BatteryPack/SN-0042"
    assert pack["assetKind"] == "Instance"
    vial = cases["pharma"][0]["assetAdministrationShells"][0]["assetInformation"]
    assert vial["assetKind"] == "Type"


def test_a_sequence_reads_back_with_its_joints():
    from aas_pydantic import convert_model_to_aas
    from aas_pydantic.convert_aas_instance import convert_submodel_to_model_instance
    from basyx.aas import model
    from aas_model.product_instances import battery_pack
    from aas_model.submodel_templates.product import production_sequence_4 as ps4

    store = convert_model_to_aas(battery_pack.battery_pack())
    built = next(o for o in store if isinstance(o, model.Submodel) and o.id == battery_pack.DISASSEMBLY)
    back = convert_submodel_to_model_instance(built, ps4.ProductionSequence)
    remove = back.Steps.Step["Step_0000"].Steps.Step["Step_0002"]
    assert remove.NodeId.value == "RemoveBusbars"
    assert sorted(remove.Joints.Joint) == ["J_Busbar1", "J_Busbar2", "J_Busbar3", "J_Busbar4"]
    joint = remove.Joints.Joint["J_Busbar3"]
    assert isinstance(joint, ps4.Joint) and joint.JointType.value == "Bolt"
    assert joint.second.key[-1].value == "BatteryModule3"
    assert float(remove.EstimatedDuration.value) == 120
    orders = back.Steps.Step["Step_0000"].ProcessOrders.ProcessOrder
    before = sorted(o.first.key[-1].value for o in orders.values() if o.second.key[-1].value == "Step_0002")
    assert before == ["Step_0000", "Step_0001"]
    assert orders["ProcessOrder_0000"].Reason.value == "the cover is over the busbars"


def test_a_sequence_is_of_its_fields_archetype():
    from aas_model.product_instances import battery_pack
    pack = battery_pack.battery_pack()
    with pytest.raises(ValueError, match="archetype"):
        type(pack)(**{**{f: getattr(pack, f) for f in pack.model_fields_set}, "assembly_sequence": battery_pack.disassembly()})
