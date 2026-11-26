"""Concrete resource factories; every call returns a newly authored instance."""

from .software import orchestrator, production_planner
from .stations import (
    capping_station, dispensing_station, loading_station, inspection_station,
    unloading_station, stoppering_station,
)
from .systems import aau_filling_line, planar_table
from .transport import planar_shuttle_1, planar_shuttle_2, planar_shuttle_3


RESOURCE_FACTORIES = {
    "stopperingStation": stoppering_station,
    "cappingStation": capping_station,
    "dispensingStation": dispensing_station,
    "loadingStation": loading_station,
    "unloadingStation": unloading_station,
    "inspectionStation": inspection_station,
    "planarShuttle1": planar_shuttle_1,
    "planarShuttle2": planar_shuttle_2,
    "planarShuttle3": planar_shuttle_3,
    "planarTable": planar_table,
    "orchestrator": orchestrator,
    "productionPlanner": production_planner,
    "aauFillingLine": aau_filling_line,
}

__all__ = [
    "stoppering_station", "capping_station", "dispensing_station", "loading_station",
    "unloading_station", "inspection_station", "planar_shuttle_1", "planar_shuttle_2",
    "planar_shuttle_3", "planar_table", "orchestrator", "production_planner",
    "aau_filling_line", "RESOURCE_FACTORIES",
]
