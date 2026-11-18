"""The lab's modules as ARSO describes them (``Module``, ``Component``), with their capabilities' Execution."""

from .filling_module import filling_linear_axis, filling_module, filling_pump, filling_scale

# A module's AAS and the AASs of its components, built together.
MODULE_FACTORIES = {
    "fillingModule": filling_module,
    "fillingLinearAxis": filling_linear_axis,
    "fillingPump": filling_pump,
    "fillingScale": filling_scale,
}

__all__ = ["filling_module", "filling_linear_axis", "filling_pump", "filling_scale", "MODULE_FACTORIES"]
