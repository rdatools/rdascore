"""
TEST SAMPLE SCORECARDS
"""

from typing import Any, Dict, List

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
    read_json,
    testdata_dir,
    approx_equal,
)

from rdascore.analyze import (
    analyze_plan,
    calc_compactness_metrics,
)


class TestScorecard:
    def test_scorecard(self) -> None:
        for xx in ["NC", "NJ"]:
            plan_path: str = f"sample/{xx}20C_baseline_100.csv"
            plan: List[Assignment] = load_plan(plan_path)

            data_project: str = "../rdabase"
            shared_data_dir: str = f"{data_project}/data/"

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
            metadata: Dict[str, Any] = load_metadata(xx, data_path)

            scorecard: Dict[str, Any] = analyze_plan(
                plan, data, shapes, graph, metadata
            )

            #

            expected_path: str = f"{testdata_dir}/{xx}_DRA_scorecard.json"
            expected: Dict[str, Any] = read_json(expected_path)

            decimals_path: str = f"{testdata_dir}/expected_decimal_places.json"
            approx_floats: Dict[str, int] = read_json(decimals_path)
            exact_ints: List[str] = [
                "pr_seats",
                "proportional_opportunities",
                "proportional_coalitions",
            ]
            approx_ints: List[str] = [
                # "kiwysi", # Disabled due to large runtime cost
                "proportionality",
                "competitiveness",
                "minority",
                "compactness",
                "splitting",
            ]

            for metric in exact_ints:
                assert scorecard[metric] == expected[metric]

            for metric in approx_ints:
                assert abs(scorecard[metric] - expected[metric]) <= 1

            for metric in approx_floats:
                assert approx_equal(
                    scorecard[metric], expected[metric], places=approx_floats[metric]
                )

    def test_compactness(self) -> None:
        for xx in ["NC", "NJ"]:
            profile_path = f"testdata/{xx}_root_profile.json"
            profile: Dict[str, Any] = read_json(profile_path)
            implicit_district_props: List[Dict[str, float]] = profile["shapes"]

            scorecard_path: str = f"{testdata_dir}/{xx}_DRA_scorecard.json"
            expected: Dict[str, Any] = read_json(scorecard_path)

            #

            actual: Dict[str, float] = calc_compactness_metrics(implicit_district_props)

            # decimals_path: str = f"{testdata_dir}/expected_decimal_places.json"
            # approx_floats: Dict[str, int] = read_json(decimals_path)

            for metric in ["reock", "polsby_popper"]:
                assert approx_equal(actual[metric], expected[metric], places=4)


### END ###
