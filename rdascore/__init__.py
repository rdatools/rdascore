# rdascore/__init__.py

from .analyze import (
    analyze_plan,
    aggregate_data_by_district,
    aggregate_shapes_by_district,
    calc_compactness_metrics,  # Why is this exported? What uses it?
)

name: str = "rdascore"
