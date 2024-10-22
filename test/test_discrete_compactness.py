"""
TEST DISCRETE COMPACTNESS
"""

from typing import Any, Dict, List

from rdabase import (
    #     Assignment,
    #     load_plan,
    #     load_data,
    #     load_shapes,
    #     load_graph,
    #     load_metadata,
    #     path_to_file,
    #     file_name,
    #     cycle,
    #     read_json,
    #     testdata_dir,
    approx_equal,
)

from rdascore import (
    cut_edges,
    spanning_tree_score,
    spanning_trees,
)


class TestScorecard:
    def test_spanning_trees(self) -> None:
        graph = {"A": ["B", "C"], "B": ["A", "C"], "C": ["A", "B"]}
        assert spanning_trees(graph) == 3

    def test_spanning_tree_score(self) -> None:
        graph = {"A": ["B", "C"], "B": ["A", "C"], "C": ["A", "B"]}
        assert approx_equal(spanning_tree_score(graph), 1.0986122886681098, places=6)


### END ###
