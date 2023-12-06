#!/usr/bin/env python3

"""
SAMPLE CODE

To run:

$ sample/sample_code.py

"""

import os
from typing import Any, List, Dict

import rdadata as rdd
from rdafn import (
    load_data,
    load_shapes,
    load_graph,
    load_metadata,
    load_plan,
    analyze_plan,
)

# Specify a state and an ensemble of plans

xx: str = "NJ"

### PATHS TO FILES ###

data_project: str = "../rdadata"
shared_data_dir: str = f"{data_project}/data/"
sample_dir: str = "sample"

data_path: str = rdd.path_to_file([shared_data_dir, xx]) + rdd.file_name(
    [xx, rdd.cycle, "data"], "_", "csv"
)
shapes_name: str = f"{xx}_{rdd.cycle}_shapes_simplified.json"
shapes_path: str = rdd.path_to_file([shared_data_dir, xx]) + shapes_name

graph_path: str = rdd.path_to_file([shared_data_dir, xx]) + rdd.file_name(
    [xx, rdd.cycle, "graph"], "_", "json"
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
        assignments: List[Dict[str, str | int]] = load_plan(plan_path)

        scorecard: Dict[str, Any] = analyze_plan(
            assignments,
            data,
            shapes,
            graph,
            metadata,
        )

        # Do something with the resulting "scorecard"

        print()
        print(f"Scorecard:")
        for metric in scorecard:
            print(f"{metric}: {scorecard[metric]}")
        print()

    except Exception as e:
        print(f"Error analyzing {plan_path}: {e}")

### END ###
