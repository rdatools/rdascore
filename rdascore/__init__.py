# rdascore/__init__.py

from .load import (
    load_plan,
    load_data,
    load_shapes,
    load_graph,
    load_metadata,
)
from .analyze import (
    analyze_plan,
    aggregate_data_by_district,
    aggregate_shapes_by_district,
    calc_compactness_metrics,  # Why is this exported? What uses it?
)

name: str = "rdascore"
