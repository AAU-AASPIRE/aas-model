# Example AASs

The filling module of the example line, its three components and the 2 mL vial, as AAS JSON (one AAS
environment per file, as BaSyx loads it). They show the execution model on real instances: each component's
capability with what it needs and changes, the offered Filling derived from them, and the vial's State
Declaration (`docs/lab-aas.md`).

Written by `python scripts/export_examples.py` from `aas_model.resource_instances.modules` and
`aas_model.product_instances`; do not edit them by hand. `tests/test_example_line.py` fails when they are not
what the script writes.
