#!/usr/bin/env python3

"""
DEBUG SCORING using JSONL input

To run:

$ test/debug.py

"""

from typing import Any, List, Dict

import json

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

# Specify a state and an ensemble of plans

xx: str = "NC"
plan_type: str = "upper"

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

plan_path: str = "../rdaensemble/temp/NC20U_county_weights_plans.jsonl"

### BOILERPLATE - DON'T CHANGE THIS ###

data: Dict[str, Dict[str, str | int]] = load_data(data_path)
shapes: Dict[str, Any] = load_shapes(shapes_path)
graph: Dict[str, List[str]] = load_graph(graph_path)
metadata: Dict[str, Any] = load_metadata(xx, data_path, plan_type)

### ANALYZE A PLAN IN THE ENSEMBLE ###

with open(plan_path, "r") as ensemble_stream:
    for i, line in enumerate(ensemble_stream):
        try:
            # Skip the metadata record
            record: Dict[str, Any] = json.loads(line.strip())
            if i == 0:
                assert record["_tag_"] == "metadata"
                continue

            assignments: List[Assignment] = [
                Assignment(geoid=k, district=v) for k, v in record["plan"].items()
            ]
            # assignments: List[Assignment] = load_plan(plan_path)

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

            break  # Only score one plan

        except Exception as e:
            print(f"Error analyzing {plan_path}: {e}")

### END ###
