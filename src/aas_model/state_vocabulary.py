"""What the lab vocabulary says of each state property: its value type and cardinality (plan D14).

The lab vocabulary (AAU-AASPIRE/ontologies, ``Vocabulary/capabilities.ttl``, 0.11) is where they are defined; this table is
what aas-model writes into every StateVariable from it (D32: an AAS is generated complete, so its consumers, the DMP
among them, read one element and infer nothing from the vocabulary at run time). ``tests/test_vocabulary.py`` checks
that the two agree.

Value types: ``number``, ``boolean``, ``string``, ``reference`` (an IRI: an AAS, an element of one, a unit).
Cardinality: ``single`` (one value; an effect assigns it) or ``set`` (effects add and remove values).
"""

from aas_model.constants import LAB

STATE_PROPERTIES: dict[str, tuple[str, str]] = {
    f"{LAB}{name}": (value_type, cardinality) for name, value_type, cardinality in (
        ("Location", "reference", "single"),
        ("AbsoluteX", "number", "single"),
        ("AbsoluteY", "number", "single"),
        ("FillResult", "reference", "single"),
        ("HeldBy", "reference", "single"),
        ("OccupiedBy", "reference", "single"),
        ("Position", "number", "single"),
        ("ContentVolume", "number", "single"),
        ("OutletImmersion", "number", "single"),
        ("FillWeight", "number", "single"),
        ("Weighed", "boolean", "single"),
        ("Stoppered", "boolean", "single"),
        ("Capped", "boolean", "single"),
        ("Inspected", "boolean", "single"),
        ("InnerDiameter", "number", "single"),
        ("InnerBottomHeight", "number", "single"),
        ("RimHeight", "number", "single"),
    )
}
