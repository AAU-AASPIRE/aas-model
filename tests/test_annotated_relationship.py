"""AnnotatedRelationshipElement: a relationship whose annotations are named fields, built into BaSyx
and read back, and generated from a template."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, Optional, TypeAlias

from basyx.aas import model

from aas_pydantic import AnnotatedRelationshipElement, Key, ModelReference, Property, Submodel
from aas_pydantic.convert_aas_instance import convert_submodel_to_model_instance, get_submodel_element_value
from aas_pydantic.convert_pydantic_model import convert_model_to_submodel

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import idta_generate  # noqa: E402


class Kind(Property):
    id_short: str = "Kind"
    semantic_id: str = "urn:test:Kind"


class Standard(Property):
    id_short: str = "Standard"
    semantic_id: str = "urn:test:Standard"


Kind_t: TypeAlias = Kind
Standard_t: TypeAlias = Standard


class Joint(AnnotatedRelationshipElement):
    semantic_id: str = "urn:test:Joint"
    Kind: Kind_t
    Standard: Optional[Standard_t] = None


Joint_t: TypeAlias = Joint


class Joints(Submodel):
    semantic_id: str = "urn:test:Joints"
    Joint: Dict[str, Joint_t] = {}


def part(name: str) -> ModelReference:
    return ModelReference(key=(Key(type_="Submodel", value="urn:test:bom"), Key(type_="Entity", value=name)))


def joints() -> Joints:
    joint = Joint(id_short="J_Cover", first=part("Cover"), second=part("Housing"),
                  Kind=Kind(value="Screw"), Standard=Standard(value="DIN 8593-3"),
                  supplemental_semantic_ids=["urn:test:ScrewedJoint"])
    return Joints(id="urn:test:joints", id_short="Joints", Joint={"J_Cover": joint})


def test_the_annotations_are_built_as_annotations():
    built = convert_model_to_submodel(joints())
    joint = next(iter(built.submodel_element))
    assert isinstance(joint, model.AnnotatedRelationshipElement)
    assert {a.id_short: a.value for a in joint.annotation} == {"Kind": "Screw", "Standard": "DIN 8593-3"}
    assert joint.second.key[-1].value == "Housing"
    assert joint.supplemental_semantic_id[0].key[0].value == "urn:test:ScrewedJoint"


def test_the_annotations_are_read_back_into_their_fields():
    back = convert_submodel_to_model_instance(convert_model_to_submodel(joints()), Joints)
    assert back.model_dump() == joints().model_dump()
    assert isinstance(back.Joint["J_Cover"].Standard, Standard)


def test_an_annotation_without_a_field_is_kept():
    joint = next(iter(convert_model_to_submodel(joints()).submodel_element))
    built = model.AnnotatedRelationshipElement(
        id_short="J", first=joint.first, second=joint.second,
        annotation=[model.Property(id_short="Torque", value_type=model.datatypes.Double, value=2.5)])
    read = get_submodel_element_value(built)
    assert type(read) is AnnotatedRelationshipElement and read.annotations["Torque"].value == "2.5"


def test_a_template_relationship_is_generated_with_its_annotations(tmp_path):
    def element(model_type, id_short, cardinality="One", **more):
        return {"modelType": model_type, "idShort": id_short, **more,
                "semanticId": {"type": "ExternalReference", "keys": [{"type": "GlobalReference", "value": f"urn:test:{id_short}"}]},
                "qualifiers": [{"type": "SMT/Cardinality", "valueType": "xs:string", "value": cardinality}]}
    empty = {"type": "ModelReference", "keys": [{"type": "GlobalReference", "value": "EMPTY"}]}
    template = {"submodels": [{"modelType": "Submodel", "idShort": "Joints", "id": "urn:test:joints", "kind": "Template",
                               "semanticId": {"type": "ExternalReference", "keys": [{"type": "GlobalReference", "value": "urn:test:Joints"}]},
                               "submodelElements": [element("AnnotatedRelationshipElement", "Joint__00__", "ZeroToMany",
                                                            first=empty, second=empty, annotations=[
                                                                element("Property", "Kind", valueType="xs:string"),
                                                                element("Property", "Standard", "ZeroToOne", valueType="xs:string")])]}]}
    source = tmp_path / "Joints.json"
    source.write_text(json.dumps(template), encoding="utf-8")
    idta_generate.gen_template(str(source), str(tmp_path))
    generated = (tmp_path / "joints.py").read_text(encoding="utf-8")
    assert "class Joint(AnnotatedRelationshipElement):" in generated
    assert "    Kind: Kind_t" in generated and "    Standard: Optional[Standard_t] = None" in generated
    assert "    Joint: Dict[str, Joint_t] = {}" in generated
