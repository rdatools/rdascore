"""
TEST DISCRETE COMPACTNESS
"""

from typing import Any, Dict, List

from rdabase import approx_equal
from rdascore import (
    cut_edges,
    spanning_tree_score,
    spanning_trees,
    split_graph_by_districts,
)


def create_10x10_grid_graph():
    """
    Creates a 10x10 grid graph represented as an adjacency list.
    Each node is labeled as 'n_row_col' (e.g., 'n_0_0' for top-left node).
    Returns a dictionary where keys are nodes and values are lists of adjacent nodes.
    """
    graph = {}
    rows, cols = 10, 10

    # Helper function to generate node name
    def node_name(row, col):
        return f"{row}_{col}"

    # Helper function to check if coordinates are valid
    def is_valid(row, col):
        return 0 <= row < rows and 0 <= col < cols

    # Generate nodes and edges
    for row in range(rows):
        for col in range(cols):
            current_node = node_name(row, col)
            graph[current_node] = []

            # Check all four directions (right, down, left, up)
            directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
            for dr, dc in directions:
                new_row, new_col = row + dr, col + dc
                if is_valid(new_row, new_col):
                    graph[current_node].append(node_name(new_row, new_col))

    return graph


class TestScorecard:
    def test_spanning_trees(self) -> None:
        # Example graph: a triangle
        graph = {"A": ["B", "C"], "B": ["A", "C"], "C": ["A", "B"]}
        assert spanning_trees(graph) == 3

        # Example graph: a square with a diagonal
        # A -- B
        # | \  |
        # D -- C
        graph = {
            "A": ["B", "C", "D"],
            "B": ["A", "C"],
            "C": ["A", "B", "D"],
            "D": ["A", "C"],
        }
        assert spanning_trees(graph) == 8

        # Example graph: the 10x10 grid in the paper
        graph = create_10x10_grid_graph()
        num_nodes = len(graph)
        assert num_nodes == 100
        num_edges = sum(len(neighbors) for neighbors in graph.values()) // 2
        assert num_edges == 180

    def test_spanning_tree_score(self) -> None:
        graph = {"A": ["B", "C"], "B": ["A", "C"], "C": ["A", "B"]}
        assert approx_equal(spanning_tree_score(graph), 1.0986122886681098, places=6)

    def test_10x10_examples(self) -> None:
        graph = create_10x10_grid_graph()

        # Left example: Four square districts

        plan: Dict[str, int | str] = {
            "0_0": 1,
            "0_1": 1,
            "0_2": 1,
            "0_3": 1,
            "0_4": 1,
            "0_5": 4,
            "0_6": 4,
            "0_7": 4,
            "0_8": 4,
            "0_9": 4,
            "1_0": 1,
            "1_1": 1,
            "1_2": 1,
            "1_3": 1,
            "1_4": 1,
            "1_5": 4,
            "1_6": 4,
            "1_7": 4,
            "1_8": 4,
            "1_9": 4,
            "2_0": 1,
            "2_1": 1,
            "2_2": 1,
            "2_3": 1,
            "2_4": 1,
            "2_5": 4,
            "2_6": 4,
            "2_7": 4,
            "2_8": 4,
            "2_9": 4,
            "3_0": 1,
            "3_1": 1,
            "3_2": 1,
            "3_3": 1,
            "3_4": 1,
            "3_5": 4,
            "3_6": 4,
            "3_7": 4,
            "3_8": 4,
            "3_9": 4,
            "4_0": 1,
            "4_1": 1,
            "4_2": 1,
            "4_3": 1,
            "4_4": 1,
            "4_5": 4,
            "4_6": 4,
            "4_7": 4,
            "4_8": 4,
            "4_9": 4,
            "5_0": 2,
            "5_1": 2,
            "5_2": 2,
            "5_3": 2,
            "5_4": 2,
            "5_5": 3,
            "5_6": 3,
            "5_7": 3,
            "5_8": 3,
            "5_9": 3,
            "6_0": 2,
            "6_1": 2,
            "6_2": 2,
            "6_3": 2,
            "6_4": 2,
            "6_5": 3,
            "6_6": 3,
            "6_7": 3,
            "6_8": 3,
            "6_9": 3,
            "7_0": 2,
            "7_1": 2,
            "7_2": 2,
            "7_3": 2,
            "7_4": 2,
            "7_5": 3,
            "7_6": 3,
            "7_7": 3,
            "7_8": 3,
            "7_9": 3,
            "8_0": 2,
            "8_1": 2,
            "8_2": 2,
            "8_3": 2,
            "8_4": 2,
            "8_5": 3,
            "8_6": 3,
            "8_7": 3,
            "8_8": 3,
            "8_9": 3,
            "9_0": 2,
            "9_1": 2,
            "9_2": 2,
            "9_3": 2,
            "9_4": 2,
            "9_5": 3,
            "9_6": 3,
            "9_7": 3,
            "9_8": 3,
            "9_9": 3,
        }
        cuts: int = cut_edges(plan, graph)
        assert cuts == 20

        district_graphs = split_graph_by_districts(graph, plan)
        plan_spanning_tree_score = sum(
            [spanning_tree_score(g) for g in district_graphs.values()]
        )
        assert approx_equal(plan_spanning_tree_score, 80.56, places=2)

        # Middle example

        # Right example


### END ###
