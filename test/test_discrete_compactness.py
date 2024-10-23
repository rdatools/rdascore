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
        return f"n_{row}_{col}"

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

        # Example 10x10 grid graph in the paper
        graph = create_10x10_grid_graph()
        num_nodes = len(graph)
        assert num_nodes == 100
        num_edges = sum(len(neighbors) for neighbors in graph.values()) // 2
        assert num_edges == 180

    def test_spanning_tree_score(self) -> None:
        graph = {"A": ["B", "C"], "B": ["A", "C"], "C": ["A", "B"]}
        assert approx_equal(spanning_tree_score(graph), 1.0986122886681098, places=6)


### END ###
