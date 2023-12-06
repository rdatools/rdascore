#!/usr/bin/env python3

"""
SAMPLE COMMAND-LINE SCRIPT FOR ANALYZING AN ENSEMBLE OF PLANS

To run:

$ sample/sample_script.py -s NJ

For documentation, type:

$ sample/sample_script.py -h

"""

import argparse
from argparse import ArgumentParser, Namespace

import os
from typing import Any, List, Dict, Generator

import rdadata as rdd
from rdafn import (
    load_data,
    load_shapes,
    load_graph,
    load_metadata,
    load_plan,
    analyze_plan,
)


### PLAN GENERATOR ###


def plans_from_ensemble(
    xx: str, ensemble_path: str
) -> Generator[List[Dict[str, str | int]], None, None]:
    """Return plans (assignments) one at a time from an ensemble file"""

    # Replace this with code that reads an ensemble file and returns plans one at a time
    ensemble: List[List[Dict[str, str | int]]] = [
        load_plan(os.path.expanduser("sample/") + f"{xx}20C_baseline_100.csv")
    ]

    for plan in ensemble:
        yield plan


def main() -> None:
    """Analyze an ensemble of plans"""

    args: Namespace = parse_args()

    xx: str = args.state
    ensemble_path: str = args.ensemble

    verbose: bool = args.verbose

    ### PATHS TO FILES ###

    data_project: str = "../rdadata"
    shared_data_dir: str = f"{data_project}/data/"

    data_path: str = rdd.path_to_file([shared_data_dir, xx]) + rdd.file_name(
        [xx, rdd.cycle, "data"], "_", "csv"
    )
    shapes_name: str = f"{xx}_{rdd.cycle}_shapes_simplified.json"
    shapes_path: str = rdd.path_to_file([shared_data_dir, xx]) + shapes_name

    graph_path: str = rdd.path_to_file([shared_data_dir, xx]) + rdd.file_name(
        [xx, rdd.cycle, "graph"], "_", "json"
    )

    ### BOILERPLATE - DON'T CHANGE THIS ###

    data: Dict[str, Dict[str, str | int]] = load_data(data_path)
    shapes: Dict[str, Any] = load_shapes(shapes_path)
    graph: Dict[str, List[str]] = load_graph(graph_path)
    metadata: Dict[str, Any] = load_metadata(xx, data_path)

    ### ANALYZE EACH PLAN IN THE ENSEMBLE ###

    for assignments in plans_from_ensemble(xx, ensemble_path):
        try:
            scorecard: Dict[str, Any] = analyze_plan(
                assignments,
                data,
                shapes,
                graph,
                metadata,
            )

            # Do something with the resulting "scorecard"

            print(scorecard)

        except Exception as e:
            print(f"Error analyzing plan: {e}")


def parse_args() -> Namespace:
    parser: ArgumentParser = argparse.ArgumentParser(
        description="Analyze an ensemble of plans"
    )

    parser.add_argument(
        "-s",
        "--state",
        default="NJ",
        help="The two-character state code (e.g., NJ)",
        type=str,
    )
    parser.add_argument(
        "-e",
        "--ensemble",
        default="~/Downloads/",
        help="Path to ensemble file",
        type=str,
    )
    parser.add_argument(
        "-v", "--verbose", dest="verbose", action="store_true", help="Verbose mode"
    )

    args: Namespace = parser.parse_args()
    return args


if __name__ == "__main__":
    main()

### END ###
