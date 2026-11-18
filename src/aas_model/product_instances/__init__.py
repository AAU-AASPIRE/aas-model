"""Concrete product types of the example line; every call returns a newly authored instance."""

from .vial_2ml import vial_2ml

PRODUCT_FACTORIES = {"vial2mL": vial_2ml}

__all__ = ["vial_2ml", "PRODUCT_FACTORIES"]
