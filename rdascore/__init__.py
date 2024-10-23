# rdascore/__init__.py

from .analyze import (
    analyze_plan,
    aggregate_data_by_district,
    aggregate_shapes_by_district,
    arcs_are_symmetric,
    calc_population_deviation,
    calc_partisan_metrics,
    calc_minority_metrics,
    est_alt_minority_opportunity,
    calc_alt_minority_opportunity,
    calc_compactness_metrics,
    calc_splitting_metrics,
    rate_dimensions,
)
from .discrete_compactness import (
    calc_cut_score,
    calc_spanning_tree_score,
    split_graph_by_districts,
    remove_out_of_state_border,
)

name: str = "rdascore"
