# rdafn/__init__.py

from .load import (
    load_plan,
    load_data,
    load_shapes,
    load_graph,
    load_metadata,
)
from .analyze import (
    analyze_plan,
    aggregate_shapes_by_district,
    calc_compactness_metrics,
)

name: str = "rdafn"
