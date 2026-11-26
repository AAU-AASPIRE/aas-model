# Example AASs

The filling module of the example line, its three components, the 2 mL vial and a batch of it, as AAS JSON (one
AAS environment per file, as BaSyx loads it). They show the execution model on real instances: each component's
capability with what it needs and changes, the module's specializations and module control (Occupying, Releasing),
the offered Filling derived from them, the vial's State Declaration and the batch's product type, quantity and goal (no unit list: D10, D35)
(`docs/lab-aas.md`).

Written by `python scripts/export_examples.py` from `aas_model.resource_instances.modules`,
`aas_model.product_instances` and `aas_model.batch_instances`; do not edit them by hand.
`tests/test_example_line.py` fails when they are not what the script writes.
