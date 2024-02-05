# rdascore/__init__.py

from .analyze import (
    analyze_plan,
    aggregate_data_by_district,
    aggregate_shapes_by_district,
    calc_population_deviation,
    calc_partisan_metrics,
    calc_minority_metrics,
    calc_compactness_metrics,
    calc_splitting_metrics,
    rate_dimensions,
)

name: str = "rdascore"
