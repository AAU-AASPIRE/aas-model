"""Batches of the example line; every call returns a newly authored instance."""

from .vial_2ml_batch import vial_2ml_batch

BATCH_FACTORIES = {"vial2mLBatch": vial_2ml_batch}

__all__ = ["vial_2ml_batch", "BATCH_FACTORIES"]
