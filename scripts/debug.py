#!/usr/bin/env python3

"""
DEBUG SCORING A PLAN

$ scripts/debug.py

"""

import os
from typing import Any, List, Dict

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
)

### HARD-CODED PARAMETERS ###

xx: str = "NC"
plan_type: str = "congress"
ensemble: List[str] = ["testdata/NC20C_random_plan.csv"]

### PATHS TO FILES ###

data_project: str = "../rdabase"
shared_data_dir: str = f"{data_project}/data/"
# sample_dir: str = "sample"

data_path: str = path_to_file([shared_data_dir, xx]) + file_name(
    [xx, cycle, "data"], "_", "csv"
)
shapes_name: str = f"{xx}_{cycle}_shapes_simplified.json"
shapes_path: str = path_to_file([shared_data_dir, xx]) + shapes_name

graph_path: str = path_to_file([shared_data_dir, xx]) + file_name(
    [xx, cycle, "graph"], "_", "json"
)


### BOILERPLATE - DON'T CHANGE THIS ###

data: Dict[str, Dict[str, str | int]] = load_data(data_path)
shapes: Dict[str, Any] = load_shapes(shapes_path)
graph: Dict[str, List[str]] = load_graph(graph_path)
metadata: Dict[str, Any] = load_metadata(xx, data_path, plan_type)

### ANALYZE EACH PLAN IN THE ENSEMBLE ###

for plan_path in ensemble:
    try:
        assignments: List[Assignment] = load_plan(plan_path)

        scorecard: Dict[str, Any] = analyze_plan(
            assignments, data, shapes, graph, metadata, alt_minority=True
        )

        # Do something with the resulting "scorecard"

        print()
        print(f"Scorecard:")
        for metric in scorecard:
            print(f"{metric}: {scorecard[metric]}")
        print()

    except Exception as e:
        print(f"Error analyzing {plan_path}: {e}")
