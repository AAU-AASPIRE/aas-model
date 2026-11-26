"""The AAS of a product type and its recipe (``docs/lab-aas.md``)."""

from .asset import (
    PLANS, BillOfMaterial, ProductPart, PartQuantity, PartQuantityUnit, Product, ProductEntry, ProductNameplate,
    plan_id,
)

__all__ = ["PLANS", "BillOfMaterial", "ProductPart", "PartQuantity", "PartQuantityUnit", "Product", "ProductEntry",
           "ProductNameplate", "plan_id"]
