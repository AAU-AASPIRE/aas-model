"""The shared execution fixtures (``tests/fixtures/execution/``, section 15 of ``docs/execution-model.md``): every one has
the AAS ``build.py`` writes and the reading (or the findings) written by hand, and the reading is well-formed. The reader
and validator that the fixtures test come later; nothing here reads an AAS but BaSyx."""

from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

import pytest
from basyx.aas import model
from basyx.aas.adapter.json import read_aas_json_file

FIXTURES = Path(__file__).parent / "fixtures" / "execution"
SPEC = Path(__file__).resolve().parents[1] / "docs" / "execution-model.md"
NAMES = sorted(p.name for p in FIXTURES.iterdir() if p.is_dir() and p.name != "__pycache__")
LAB, FIXTURE_NS = "https://smartproductionlab.aau.dk/semantics/", "urn:fixture:"


def _build_module():
    spec = importlib.util.spec_from_file_location("execution_fixtures_build", FIXTURES / "build.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _spec_section(heading: str) -> str:
    text = SPEC.read_text(encoding="utf-8")
    start = text.index(heading)
    end = text.find("\n## ", start + 1)
    return text[start:end if end > 0 else None]


def _finding_codes() -> dict[str, str]:
    """Section 11's table: each code and its severity (the first word of its column)."""
    rows = re.findall(r"^\| `([a-z]+\.[a-z-]+)` \| (error|warning)", _spec_section("## 11. Validation rules"), re.M)
    return dict(rows)


def _features() -> set[str]:
    """Section 12's first table: the features, in its first column."""
    table = _spec_section("## 12. Features and consumer profiles").split("| Consumer |")[0]
    return {name for row in re.findall(r"^\|([^|]+)\|", table, re.M) for name in re.findall(r"`([a-z-]+)`", row)}


def _load(name: str, file: str):
    return json.loads((FIXTURES / name / file).read_text(encoding="utf-8"))


# ── aas.json ─────────────────────────────────────────────────────────────────────────────────────────────────

def test_the_build_script_writes_every_checked_in_aas_json_again(tmp_path):
    build = _build_module()
    written = build.write(tmp_path)
    assert sorted(p.parent.name for p in written) == [n for n in NAMES], "a fixture without a builder, or the reverse"
    for path in written:
        assert path.read_text(encoding="utf-8") == (FIXTURES / path.parent.name / "aas.json").read_text(encoding="utf-8"), (
            f"{path.parent.name}/aas.json is not what build.py writes: run python tests/fixtures/execution/build.py")


@pytest.mark.parametrize("name", NAMES)
def test_every_aas_json_reads_back_with_the_basyx_deserializer(name):
    with (FIXTURES / name / "aas.json").open(encoding="utf-8") as f:
        store = read_aas_json_file(f, failsafe=False)
    shells = [o for o in store if isinstance(o, model.AssetAdministrationShell)]
    assert shells and all(s.id.startswith(f"https://smartproductionlab.aau.dk/aas/fixtures/{name}") for s in shells)
    for shell in shells:
        for reference in shell.submodel:
            assert reference.resolve(store) is not None


# ── the files each fixture holds ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("name", NAMES)
def test_every_fixture_has_its_aas_and_its_expected_reading(name):
    assert (FIXTURES / name / "aas.json").is_file() and (FIXTURES / name / "expected.json").is_file()
    assert re.fullmatch(r"[a-d]\d\d-[a-z0-9-]+", name)


def test_the_groups_are_there():
    groups = {name[0] for name in NAMES}
    assert groups == {"a", "b", "c", "d"}
    assert sum(name.startswith("d") for name in NAMES) == len(_finding_codes()) - 1       # all but level.derived


def test_the_codes_and_features_are_read_from_the_specification():
    assert len(_finding_codes()) == 30 and _finding_codes()["level.incomplete"] == "warning"
    assert len(_features()) == 12 and "non-deterministic" in _features()


@pytest.mark.parametrize("name", [n for n in NAMES if n.startswith("d")])
def test_an_invalid_fixture_states_exactly_one_finding_named_after_its_code(name):
    expected = _load(name, "expected.json")
    assert set(expected) == {"findings"} and len(expected["findings"]) == 1
    (finding,) = expected["findings"]
    assert name.split("-", 1)[1] == finding["code"].replace(".", "-")
    assert _finding_codes()[finding["code"]] == finding["severity"]


@pytest.mark.parametrize("name", NAMES)
def test_a_fixture_with_its_own_vocabulary_has_it_in_the_fixture_namespace(name):
    uses_fixture_terms = FIXTURE_NS.replace("urn:", "") in (FIXTURES / name / "expected.json").read_text(encoding="utf-8")
    vocabulary = FIXTURES / name / "vocabulary.ttl"
    assert vocabulary.is_file() == uses_fixture_terms
    if vocabulary.is_file():
        rdflib = pytest.importorskip("rdflib")
        graph = rdflib.Graph().parse(vocabulary)
        lab = rdflib.Namespace(LAB)
        subjects = {s for s in graph.subjects(lab.cardinality, None)}
        assert subjects and all(str(s).startswith(FIXTURE_NS) for s in subjects)
        assert all((s, lab.valueType, None) in graph for s in subjects)


# ── expected.json: the canonical reading of section 15 ──────────────────────────────────────────────────────

CONDITION_OPERATORS = {"equal", "notEqual", "less", "lessOrEqual", "greater", "greaterOrEqual", "unchanged", "contains",
                       "notContains"}
EFFECT_OPERATORS = {"assign", "increase", "decrease", "measured", "clear", "add", "remove"}
NO_OPERAND = {"unchanged", "measured", "clear"}
KINDS = {"observed", "asserted", "derived"}
CAPABILITY_KEYS = {"aas", "meaning", "subjects", "pre", "invariant", "post", "start", "during", "end", "duration",
                   "features"}
KNOWLEDGE_KEYS = {"aas", "subject", "property", "valueType", "cardinality", "initial", "kind"}
OPERATORS_OF_AST = {"+", "-", "*", "/"}


class Malformed(AssertionError):
    pass


def _check(condition: bool, message: str):
    if not condition:
        raise Malformed(message)


def _iri(value, where: str):
    _check(isinstance(value, str) and value, f"{where}: an IRI is a non-empty string")
    _check(not value.startswith((LAB, FIXTURE_NS)), f"{where}: write {value} with its prefix (lab:, fixture:)")


def _one_key(value, allowed: set, where: str) -> tuple:
    _check(isinstance(value, dict) and len(value) == 1 and set(value) <= allowed,
           f"{where}: one of {sorted(allowed)}, not {value!r}")
    return next(iter(value.items()))


def _ast(value, aliases: set, where: str):
    key, body = _one_key(value, {"number", "pi", "alias", "neg"} | OPERATORS_OF_AST, where)
    if key == "number":
        _check(isinstance(body, float), f"{where}: a number is a float")
    elif key == "pi":
        _check(body is True, f"{where}: pi is true")
    elif key == "alias":
        _check(isinstance(body, str), f"{where}: an alias is a name")
        aliases.add(body)
    elif key == "neg":
        _ast(body, aliases, where)
    else:
        _check(isinstance(body, list) and len(body) == 2, f"{where}: {key} has two operands")
        for part in body:
            _ast(part, aliases, where)


def _operand(value, where: str, subjects: int, variables: set, uses: bool = False):
    key, body = _one_key(value, {"number", "boolean", "string", "iri", "subject", "variable", "parameter", "element",
                                 "state", "formula", "uses"}, where) if "formula" not in value else ("formula", None)
    if key == "formula":
        _check(set(value) == {"formula", "uses"}, f"{where}: a formula has its uses")
        aliases: set = set()
        _ast(value["formula"], aliases, where)
        _check(isinstance(value["uses"], dict) and set(value["uses"]) == aliases,
               f"{where}: uses {sorted(value['uses'])} are not the aliases {sorted(aliases)}")
        for alias, use in value["uses"].items():
            _check("formula" not in use, f"{where}: a use is no formula")
            _operand(use, f"{where}/{alias}", subjects, variables, uses=True)
        return
    {"number": lambda: _check(isinstance(body, float), f"{where}: a number is a float"),
     "boolean": lambda: _check(isinstance(body, bool), f"{where}: a boolean"),
     "string": lambda: _check(isinstance(body, str), f"{where}: a string"),
     "iri": lambda: _iri(body, where),
     "subject": lambda: _check(isinstance(body, int) and not isinstance(body, bool) and 0 <= body < subjects,
                               f"{where}: subject {body!r} is not one of the {subjects} subjects"),
     "variable": lambda: _check(body in variables, f"{where}: variable {body!r} is not in scope"),
     "parameter": lambda: _check(isinstance(body, dict) and set(body) == {"operation", "variable"}
                                 and all(isinstance(x, str) for x in body.values()), f"{where}: a parameter"),
     "element": lambda: _check(isinstance(body, str) and body, f"{where}: an element path"),
     "state": lambda: (_check(uses, f"{where}: a state operand is for Uses only"),
                       _check(isinstance(body, dict) and set(body) == {"subject", "property"}
                              and isinstance(body["subject"], int) and 0 <= body["subject"] < subjects,
                              f"{where}: a state operand"), _iri(body["property"], where)),
     "uses": lambda: _check(False, f"{where}: uses belong to a formula")}[key]()


def _reference(value, where: str, subjects: int, variables: set):
    key, body = _one_key(value, {"subject", "variable"}, where)
    if key == "subject":
        _check(isinstance(body, int) and 0 <= body < subjects, f"{where}: no such subject {body!r}")
    else:
        _check(body in variables, f"{where}: variable {body!r} is not in scope")


class _Terms:
    """Checks the terms of one capability (or goal): subjects in range, variables numbered in document order."""

    def __init__(self, subjects: int):
        self.subjects, self.declared = subjects, 0

    def terms(self, values, kind: str, where: str, variables: frozenset = frozenset()):
        _check(isinstance(values, list), f"{where}: a list of terms")
        for i, value in enumerate(values):
            self.term(value, kind, f"{where}[{i}]", variables)

    def term(self, value, kind: str, where: str, variables: frozenset):
        names = {"condition", "and", "or", "not", "exists", "forall"} if kind == "condition" else {
            "effect", "and", "forall", "when", "oneOf"}
        key, body = _one_key(value, names, where)
        if key in ("condition", "effect"):
            self.atom(key, body, where, variables)
        elif key in ("and", "or"):
            self.terms(body, kind, where, variables)
            _check(key == "and" or len(body) >= 2, f"{where}: an or has two terms or more")
        elif key == "not":
            self.term(body, kind, where, variables)
        elif key in ("exists", "forall"):
            _check(isinstance(body, dict) and set(body) == {"variable", "body"}, f"{where}: a quantifier")
            var = body["variable"]
            _check(isinstance(var, dict) and set(var) == {"id", "name", "standsFor"}, f"{where}: a variable")
            _check(var["id"] == f"v{self.declared}", f"{where}: variables are numbered v0, v1 ... in document order")
            self.declared += 1
            _check(isinstance(var["name"], str) and var["name"], f"{where}: a variable has its name")
            _iri(var["standsFor"], where)
            self.terms(body["body"], kind, where, variables | {var["id"]})
        elif key == "when":
            _check(isinstance(body, dict) and set(body) == {"if", "then"}, f"{where}: a when")
            self.terms(body["if"], "condition", f"{where}/if", variables)
            self.terms(body["then"], "effect", f"{where}/then", variables)
        else:
            _check(isinstance(body, dict) and set(body) == {"meaning", "outcomes"}, f"{where}: a oneOf")
            _iri(body["meaning"], where)
            _check(len(body["outcomes"]) >= 2, f"{where}: a oneOf has two outcomes or more")
            for outcome in body["outcomes"]:
                _check(set(outcome) == {"id", "meaning", "effects"}, f"{where}: an outcome")
                _iri(outcome["meaning"], where)
                self.terms(outcome["effects"], "effect", f"{where}/{outcome['id']}", variables)

    def atom(self, kind: str, body, where: str, variables: frozenset):
        allowed = {"subject", "property", "op", "operand"} | ({"rate"} if kind == "effect" else set())
        _check(isinstance(body, dict) and {"subject", "property", "op"} <= set(body) <= allowed, f"{where}: an atom")
        _reference(body["subject"], where, self.subjects, variables)
        _iri(body["property"], where)
        operators = CONDITION_OPERATORS if kind == "condition" else EFFECT_OPERATORS
        _check(body["op"] in operators, f"{where}: {body['op']!r} is not an operator of a {kind}")
        _check(("operand" in body) == (body["op"] not in NO_OPERAND), f"{where}: an operand exactly where the operator has one")
        if "operand" in body:
            _operand(body["operand"], where, self.subjects, variables)
        if "rate" in body:
            _operand(body["rate"], where, self.subjects, variables)


def _subjects(values, where: str):
    _check(isinstance(values, list), f"{where}: a list of subjects")
    for subject in values:
        _check(isinstance(subject.get("name"), str) and subject["name"], f"{where}: a subject has its name")
        _check(set(subject) in ({"name", "fixed"}, {"name", "standsFor"}, {"name", "requirement"}), f"{where}: {subject}")
        _iri(subject.get("fixed") or subject.get("standsFor") or subject.get("requirement"), where)


def _finding(finding, where: str, codes: dict):
    _check(set(finding) == {"code", "severity", "path"}, f"{where}: a finding")
    _check(finding["code"] in codes, f"{where}: {finding['code']!r} is no code of section 11")
    _check(finding["severity"] in ("error", "warning"), f"{where}: a severity")
    _check(isinstance(finding["path"], str) and finding["path"], f"{where}: a path")


def check_reading(reading: dict, valid: bool):
    """Raise Malformed unless ``reading`` is a reading as section 15 states it; ``valid``: a fixture of groups A to C,
    which states every part of it (an invalid one may leave the rest out)."""
    top = {"capabilities", "goal", "knowledge", "findings"}
    _check(set(reading) <= top and (not valid or set(reading) == top), f"top-level keys {sorted(reading)}")
    codes, features = _finding_codes(), _features()
    findings = reading.get("findings", [])
    _check(not valid or findings == [], "a valid fixture has no findings")
    for i, finding in enumerate(findings):
        _finding(finding, f"findings[{i}]", codes)
    _check(findings == sorted(findings, key=lambda f: (f["path"], f["code"])), "findings are sorted by path, then code")
    for path, capability in reading.get("capabilities", {}).items():
        where = f"capabilities/{path}"
        _check(re.fullmatch(r"CapabilityDescription(/[A-Za-z0-9_]+)+", path), f"{where}: an idShort path")
        _check(set(capability) == CAPABILITY_KEYS, f"{where}: keys {sorted(capability)}")
        _iri(capability["meaning"], where)
        _subjects(capability["subjects"], where)
        terms = _Terms(len(capability["subjects"]))
        for phase in ("pre", "invariant", "post"):
            terms.terms(capability[phase], "condition", f"{where}/{phase}")
        for phase in ("start", "during", "end"):
            terms.terms(capability[phase], "effect", f"{where}/{phase}")
        if capability["duration"] is not None:
            _operand(capability["duration"], f"{where}/duration", len(capability["subjects"]), set())
        _check(capability["features"] == sorted(set(capability["features"])) and set(capability["features"]) <= features,
               f"{where}: features are sorted names of section 12")
    goal = reading.get("goal")
    if goal is not None:
        _check(set(goal) == {"aas", "subjects", "condition"}, "goal: keys")
        _subjects(goal["subjects"], "goal")
        _Terms(len(goal["subjects"])).terms(goal["condition"], "condition", "goal/condition")
    knowledge = reading.get("knowledge", [])
    for entry in knowledge:
        _check(set(entry) == KNOWLEDGE_KEYS, f"knowledge: keys {sorted(entry)}")
        _check(entry["kind"] in KINDS and entry["valueType"] in {"number", "boolean", "string", "reference"}
               and entry["cardinality"] in {"single", "set"}, f"knowledge: {entry}")
        _iri(entry["property"], "knowledge")
        if entry["initial"] is not None:
            _operand(entry["initial"], "knowledge/initial", 0, set())
    _check(knowledge == sorted(knowledge, key=lambda e: (e["aas"], e["subject"] or "", e["property"])),
           "knowledge is sorted by aas, subject, property")


@pytest.mark.parametrize("name", NAMES)
def test_every_expected_json_is_well_formed(name):
    check_reading(_load(name, "expected.json"), valid=not name.startswith("d"))


def test_the_checker_refuses_what_section_15_does_not_allow():
    reading = _load("a01-literal-number", "expected.json")
    check_reading(reading, valid=True)
    for damage in (
        lambda r: r["capabilities"][next(iter(r["capabilities"]))]["pre"][0]["condition"].update(op="assign"),
        lambda r: r["capabilities"][next(iter(r["capabilities"]))]["pre"][0]["condition"].pop("operand"),
        lambda r: r["capabilities"][next(iter(r["capabilities"]))].update(features=["numerical"]),
        lambda r: r["capabilities"][next(iter(r["capabilities"]))]["pre"][0]["condition"].update(subject={"subject": 7}),
        lambda r: r.update(findings=[{"code": "made.up", "severity": "error", "path": "x"}]),
        lambda r: r.pop("knowledge"),
    ):
        broken = json.loads(json.dumps(reading))
        damage(broken)
        with pytest.raises(Malformed):
            check_reading(broken, valid=True)
