"""
CUT SCORE AND SPANNING TREE SCORE
based on "Discrete Geometry for Electoral Geography" by Moon Duchin and Bridget Eileen Tenner
"""

from typing import Any, List, Dict
import numpy as np
from scipy.linalg import det

from rdabase import OUT_OF_STATE


def cut_edges(plan: Dict[str, int | str], graph: Dict[str, List[str]]) -> int:
    """Given a plan and a graph, return the number of cut edges. Definition 3 in Section 5.4."""

    precision: int = 4
    cuts, edges, boundaries, nodes = 0, 0, 0, 0

    for node, neighbors in graph.items():
        if node == OUT_OF_STATE:
            continue
        nodes += 1
        boundary: bool = False

        for neighbor in neighbors:
            if neighbor == OUT_OF_STATE:
                continue
            edges += 1

            if plan[node] != plan[neighbor]:
                cuts += 1
                boundary = True

        if boundary:
            boundaries += 1

    # cut_pct: float = round(cuts / edges, precision)
    # boundary_pct: float = round(boundaries / nodes, precision)

    return cuts


def spanning_tree_score(graph: Dict[str, List[str]]) -> float:
    """Calculate the spanning tree score for a graph. Definition 4 in Section 5.5.

    For a graph with 3 spanning trees, the score is ln(3) = 1.0986122886681098.
    """

    return np.log(spanning_trees(graph))


def spanning_trees(graph: Dict[str, List[str]]) -> int:
    """
    Calculate the number of spanning trees in an undirected graph using Kirchhoff's matrix tree theorem.

    Parameters:
    graph: Dictionary where keys are vertices and values are lists of adjacent vertices

    Returns:
    int: Number of spanning trees in the graph

    Example:
    >>> graph = {
    ...     'A': ['B', 'C'],
    ...     'B': ['A', 'C'],
    ...     'C': ['A', 'B']
    ... }
    >>> count_spanning_trees(graph)
    3
    """
    # Convert the graph to an adjacency matrix
    adjacency_matrix, vertices = convert_graph_to_matrix(graph)

    # Calculate the degree matrix
    degree_matrix = np.diag(np.sum(adjacency_matrix, axis=1))

    # Calculate the Laplacian matrix
    laplacian_matrix = degree_matrix - adjacency_matrix

    # Remove the last row and column to create the reduced Laplacian
    reduced_laplacian = laplacian_matrix[:-1, :-1]

    # Calculate the determinant of the reduced Laplacian
    # The determinant might be complex, so we take the real part and round it
    determinant = det(reduced_laplacian)
    num_spanning_trees = int(round(float(np.real(determinant))))

    return num_spanning_trees


### HELPERS ###


def convert_graph_to_matrix(
    graph: Dict[str, List[str]]
) -> tuple[np.ndarray, list[str]]:
    """
    Convert an adjacency list representation to an adjacency matrix.

    Parameters:
    graph: Dictionary where keys are vertices and values are lists of adjacent vertices

    Returns:
    tuple: (adjacency matrix as numpy array, list of vertex names in order)
    """
    # Create a mapping of vertex names to indices
    vertices = sorted(graph.keys())
    vertex_to_index = {vertex: i for i, vertex in enumerate(vertices)}
    n = len(vertices)

    # Create the adjacency matrix
    adjacency_matrix = np.zeros((n, n), dtype=int)
    for vertex, neighbors in graph.items():
        i = vertex_to_index[vertex]
        for neighbor in neighbors:
            j = vertex_to_index[neighbor]
            adjacency_matrix[i, j] = 1
            adjacency_matrix[j, i] = 1  # Make sure the graph is undirected

    return adjacency_matrix, vertices


def validate_graph(graph: Dict[str, List[str]]) -> bool:
    """
    Verify that a graph is valid: undirected and connected.

    Parameters:
    graph: Dictionary where keys are vertices and values are lists of adjacent vertices

    Returns:
    bool: True if the graph is valid, False otherwise
    """
    # Check if graph is empty
    if not graph:
        return False

    # Check if all edges are bidirectional
    for vertex, neighbors in graph.items():
        for neighbor in neighbors:
            if vertex not in graph[neighbor]:
                return False

    # Check if graph is connected using DFS
    visited = set()
    start_vertex = next(iter(graph))

    def dfs(v):
        visited.add(v)
        for neighbor in graph[v]:
            if neighbor not in visited:
                dfs(neighbor)

    dfs(start_vertex)

    return len(visited) == len(graph)


### END ###
