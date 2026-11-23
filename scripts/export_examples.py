#!/usr/bin/env python3
"""Write the example AASs as AAS JSON into ``examples/aas/``: the filling module, its components, the 2 mL vial and a
batch of it.

One file per AAS (``<idShort>.json``), an AAS environment with the shell and its submodels, as BaSyx loads it.
``tests/test_example_line.py`` fails when the checked-in files are not what this script writes. Run from the
repository root::

    python scripts/export_examples.py
"""

from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "src"))

from basyx.aas.adapter.json import json_serialization  # noqa: E402

from aas_model import build_from_model  # noqa: E402
from aas_model.batch_instances import BATCH_FACTORIES  # noqa: E402
from aas_model.product_instances import PRODUCT_FACTORIES  # noqa: E402
from aas_model.resource_instances.modules import MODULE_FACTORIES  # noqa: E402

OUTPUT = os.path.join(_ROOT, "examples", "aas")
FACTORIES = {**MODULE_FACTORIES, **PRODUCT_FACTORIES, **BATCH_FACTORIES}


def documents() -> dict[str, str]:
    """Each example AAS's file name and its AAS JSON (sorted keys, so a change shows as a small diff)."""
    found = {}
    for factory in FACTORIES.values():
        made = factory()
        document = json.loads(json_serialization.object_store_to_json(build_from_model(made)))
        # BaSyx keeps a shell's submodel references, and the store its identifiables, as sets: put them in a fixed
        # order, so that the same AAS is always the same file.
        for shell in document.get("assetAdministrationShells", ()):
            shell["submodels"] = sorted(shell.get("submodels", ()), key=lambda ref: ref["keys"][0]["value"])
        document["submodels"] = sorted(document.get("submodels", ()), key=lambda submodel: submodel["id"])
        found[f"{made.id_short}.json"] = json.dumps(document, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    return found


def main() -> None:
    os.makedirs(OUTPUT, exist_ok=True)
    for name, text in documents().items():
        with open(os.path.join(OUTPUT, name), "w", encoding="utf-8") as out:
            out.write(text)
        print(os.path.relpath(os.path.join(OUTPUT, name), _ROOT))


if __name__ == "__main__":
    main()
