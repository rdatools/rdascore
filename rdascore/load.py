"""
LOAD HELPERS
"""

from typing import Any, List, Dict
from rdabase import (
    read_csv,
    index_data,
    read_json,
    GeoID,
    COUNTIES_BY_STATE,
    DISTRICTS_BY_STATE,
    Assignment,
)


def load_data(data_path: str) -> Dict[str, Dict[str, str | int]]:
    """Load preprocessed census & election data and index it by GEOID."""

    data: List[Dict[str, str | int]] = read_csv(data_path, [str] + [int] * 13)
    indexed: Dict[str, Dict[str, str | int]] = index_data(data)

    return indexed


def load_shapes(shapes_path: str) -> Dict[str, Dict[str, Any]]:
    """Load preprocessed shape data and index it by GEOID."""

    shapes: Dict[str, Dict[str, Any]] = read_json(shapes_path)

    return shapes


def load_graph(graph_path: str) -> Dict[str, List[str]]:
    """Load the graph for a state."""

    graph: Dict[str, List[str]] = read_json(graph_path)

    return graph


def load_metadata(xx: str, data_path: str) -> Dict[str, Any]:
    """Load scoring-specific metadata for a state."""

    ### INFER COUNTY FIPS CODES ###

    data: list = read_csv(data_path, [str] + [int] * 13)

    counties: set[str] = set()
    for row in data:
        precinct: str = str(row["GEOID"] if "GEOID" in row else row["GEOID20"])
        county: str = GeoID(precinct).county[2:]
        counties.add(county)

    ### GATHER METADATA ###

    C: int = COUNTIES_BY_STATE[xx]
    D: int = DISTRICTS_BY_STATE[xx]["congress"]

    county_to_index: Dict[str, int] = {county: i for i, county in enumerate(counties)}

    district_to_index: Dict[int, int] = {
        district: i for i, district in enumerate(range(1, D + 1))
    }

    metadata: Dict[str, Any] = dict()
    metadata["C"] = C
    metadata["D"] = D
    metadata["county_to_index"] = county_to_index
    metadata["district_to_index"] = district_to_index

    return metadata


def load_plan(plan_file: str) -> List[Assignment]:
    """Read a precinct-assignment file."""

    raw_assignments: List[Dict[str, str | int]] = read_csv(plan_file, [str, int])
    assignments: List[Assignment] = [
        Assignment(geoid=str(p["GEOID"]), district=p["DISTRICT"])
        for p in raw_assignments
    ]

    return assignments


### END ###
