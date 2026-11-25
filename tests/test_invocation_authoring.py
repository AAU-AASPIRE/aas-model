import base64

import pytest
from pydantic import ValidationError

from aas_model import Resource, build_from_model, inject_ids
from aas_model.invocation_authoring import OPERATION_PATH, operation_path
from aas_model.resource_template import MQTT_INTERFACE, MqttOperationalStation as Station, affordance_ref
from aas_model.submodel_templates.control_component_instance import SkillOperation
from aas_model.submodel_templates.skills import PRIMITIVE, command_skill
from aas_model.submodel_templates import AimcMappingConfiguration


def _delegation(skill):
    return next(q for q in skill.Start.SkillOperation["Start"].qualifiers if q.type_ == "invocationDelegation").value


def _built_delegation(asset, skill_name):
    """The invocationDelegation of a skill's Operation in the AAS built from ``asset``, and its submodel's id."""
    skills = {o.id_short: o for o in build_from_model(asset)}["Skills"]
    operation = skills.get_referable([skill_name, "Start", "Start"])
    return next(q for q in operation.qualifier if q.type == "invocationDelegation").value, skills.id


def _b64(identifier: str) -> str:
    return base64.urlsafe_b64encode(identifier.encode()).decode().rstrip("=")


def test_an_operation_is_invoked_at_its_aas_api_path():
    assert operation_path("urn:x/sm", "Halt.Start.Start") == \
        f"/submodels/{_b64('urn:x/sm')}/submodel-elements/Halt.Start.Start/invoke"
    assert operation_path("urn:x/sm", "List[0].operation").endswith("/List%5B0%5D.operation/invoke")


def test_default_skills_are_delegated_to_the_path_of_their_built_operation():
    asset = Station(id_short="LineA")
    for skill_name, skill in asset.skills.Skill.items():
        # The authored model keeps the template; the built AAS carries the path.
        assert OPERATION_PATH in _delegation(skill)
        delegation, submodel_id = _built_delegation(asset, skill_name)
        assert delegation == \
            f"http://dmp:8080/submodels/{_b64(submodel_id)}/submodel-elements/{skill_name}.Start.Start/invoke"


def test_an_authored_aas_id_is_the_base_of_the_submodel_id():
    asset = Station(id_short="LineA", id="urn:plant:line-a")
    delegation, _ = _built_delegation(asset, "Halt")
    assert _b64("urn:plant:line-a/submodels/Skills") in delegation


def test_skills_added_later_are_delegated_when_built():
    asset = Station(id_short="LineA")
    asset.skills.Skill["Weigh"] = command_skill(
        "Weigh", PRIMITIVE, affordance_ref(MQTT_INTERFACE, "actions", "Weigh"), SkillOperation())
    delegation, _ = _built_delegation(asset, "Weigh")
    assert delegation.endswith("/submodel-elements/Weigh.Start.Start/invoke")


def test_resource_authoring_does_not_accept_per_resource_origin():
    with pytest.raises(ValidationError, match="extra_forbidden"):
        Resource(id_short="Station", delegation_base="http://old:8080")


def test_building_preserves_concrete_authored_invocation_urls():
    asset = Station(id_short="Station")
    qualifier = asset.skills.Skill["Halt"].Start.SkillOperation["Start"].qualifiers[0]
    qualifier.value = "http://dmp-station:8080/custom/Halt"
    inject_ids(asset)

    assert qualifier.value == "http://dmp-station:8080/custom/Halt"


@pytest.mark.parametrize("url", [
    "http://dmp-station:8080/custom/Halt",
    "https://example.test/custom/invocation",
])
def test_pydantic_dict_and_json_import_preserve_authored_invocation_urls(url):
    asset = Station(id_short="Station")
    asset.skills.Skill["Halt"].Start.SkillOperation["Start"].qualifiers[0].value = url

    from_dict = Resource.model_validate(asset.model_dump(mode="json"))
    from_json = Resource.model_validate_json(asset.model_dump_json())

    for restored in (from_dict, from_json):
        assert restored.skills.Skill["Halt"].Start.SkillOperation["Start"].qualifiers[0].value == url


def test_an_invocation_timeout_is_a_positive_duration_of_at_most_fifteen_minutes():
    mapping = AimcMappingConfiguration(Sources=[], Sinks=[], InvocationTimeout="PT2M")
    assert mapping.InvocationTimeout.value == "PT2M"
    assert mapping.InvocationTimeout.semantic_id == "https://smartproductionlab.aau.dk/aimc/InvocationTimeout/1/0"
    for invalid in ("PT0S", "PT16M", "PT1.5S", "30", "P1D"):
        with pytest.raises(ValidationError):
            AimcMappingConfiguration(Sources=[], Sinks=[], InvocationTimeout=invalid)
