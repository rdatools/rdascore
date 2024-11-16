#!/usr/bin/env python3

"""
SAMPLE CODE

To run:

$ test/profile_compactness.py

"""

from typing import Any, List, Dict

import os, time

from rdabase import (
    Assignment,
    load_plan,
    load_data,
    load_shapes,
    load_graph,
    load_metadata,
    path_to_file,
    file_name,
    cycle,
)
from rdascore import (
    analyze_plan,
    aggregate_shapes_by_district,
)

# Specify a state and an ensemble of plans

xx: str = "NJ"
which: str = "all"

### PATHS TO FILES ###

data_project: str = "../rdabase"
shared_data_dir: str = f"{data_project}/data/"
sample_dir: str = "sample"

data_path: str = path_to_file([shared_data_dir, xx]) + file_name(
    [xx, cycle, "data"], "_", "csv"
)
shapes_name: str = f"{xx}_{cycle}_shapes_simplified.json"
shapes_path: str = path_to_file([shared_data_dir, xx]) + shapes_name

graph_path: str = path_to_file([shared_data_dir, xx]) + file_name(
    [xx, cycle, "graph"], "_", "json"
)

### AN ENSEMBLE OF PLAN CSV FILES ON DISK ###

ensemble: List[str] = [
    os.path.expanduser(f"{sample_dir}/") + x
    for x in [
        f"{xx}20C_baseline_100.csv",
        # More plans here ...
    ]
]

### BOILERPLATE - DON'T CHANGE THIS ###

data: Dict[str, Dict[str, str | int]] = load_data(data_path)
shapes: Dict[str, Any] = load_shapes(shapes_path)
graph: Dict[str, List[str]] = load_graph(graph_path)
metadata: Dict[str, Any] = load_metadata(xx, data_path)

### ANALYZE EACH PLAN IN THE ENSEMBLE ###

for plan_path in ensemble:
    try:
        assignments: List[Assignment] = load_plan(plan_path)

        n_districts: int = metadata["D"]
        size: int = 100

        tic: float = time.perf_counter()

        for i in range(size):
            print(f"Run {i + 1} of {size} ...")
            district_props: List[Dict[str, float]] = aggregate_shapes_by_district(
                assignments, shapes, graph, n_districts, debug=True
            )

        toc: float = time.perf_counter()
        print(f"Time = {toc - tic: 0.1f} seconds / {size} runs.")

    except Exception as e:
        print(f"Error analyzing {plan_path}: {e}")

### END ###
