"""
ANALYZE A PLAN
"""

from collections import defaultdict
from typing import Any, List, Dict, Tuple, Optional

import numpy as np
import miniball as mb
import math
from scipy.spatial.distance import pdist, squareform

import rdapy as rda
from rdabase import (
    census_fields,
    election_fields,
    GeoID,
    OUT_OF_STATE,
    Assignment,
    approx_equal,
    time_function,
)
from .discrete_compactness import (
    calc_cut_score,
    calc_spanning_tree_score,
    split_graph_by_districts,
)

### FIELD NAMES ###

total_pop_field: str = census_fields[0]
total_vap_field: str = census_fields[1]
# white_vap_field: str = census_fields[2]
# hispanic_vap_field: str = census_fields[3]
# black_vap_field: str = census_fields[4]
# native_vap_field: str = census_fields[5]
# asian_vap_field: str = census_fields[6]
# pacific_vap_field: str = census_fields[7]
# minority_vap_field: str = census_fields[8]

# total_votes_field: str = election_fields[0]
rep_votes_field: str = election_fields[1]
dem_votes_field: str = election_fields[2]
# oth_votes_field: str = election_fields[3]


# @time_function
def analyze_plan(
    assignments: List[Assignment],
    data: Dict[str, Dict[str, str | int]],
    shapes: Dict[str, Any],
    graph: Dict[str, List[str]],
    metadata: Dict[str, Any],
    alt_minority: bool = True,  # If False, don't add alternative minority opportunity metrics
    *,
    which: str = "all",  # Or just "partisan", "minority", "compactness", "splitting"
) -> Dict[str, Any]:
    """Analyze a plan."""

    n_districts: int = metadata["D"]
    n_counties: int = metadata["C"]
    county_to_index: Dict[str, int] = metadata["county_to_index"]
    district_to_index: Dict[int | str, int] = metadata["district_to_index"]

    aggregates: Dict[str, Any] = dict()
    district_props: List[Dict[str, float]] = list()
    minority_metrics: Dict[str, float] = dict()

    scorecard: Dict[str, Any] = dict()

    if which == "all" or which != "compactness":
        aggregates = aggregate_data_by_district(
            assignments,
            data,
            n_districts,
            n_counties,
            county_to_index,
            district_to_index,
        )

    if which == "all" or which == "partisan":
        # Include these with the partisan metrics
        scorecard["D"] = n_districts
        scorecard["C"] = n_counties

        deviation: float = calc_population_deviation(
            aggregates["pop_by_district"], aggregates["total_pop"], n_districts
        )
        scorecard["population_deviation"] = deviation

        partisan_metrics: Dict[str, Optional[float]] = calc_partisan_metrics(
            aggregates["total_d_votes"],
            aggregates["total_votes"],
            aggregates["d_by_district"],
            aggregates["tot_by_district"],
        )
        scorecard.update(partisan_metrics)
        scorecard["proportionality"] = rate_proportionality(
            scorecard["pr_deviation"],
            scorecard["estimated_vote_pct"],
            scorecard["estimated_seat_pct"],
        )
        scorecard["competitiveness"] = rate_competitiveness(
            scorecard["competitive_district_pct"]
        )

    if which == "all" or which == "minority":
        minority_metrics = calc_minority_metrics(
            aggregates["demos_totals"], aggregates["demos_by_district"], n_districts
        )
        scorecard.update(minority_metrics)
        scorecard["minority"] = rate_minority_opportunity(
            scorecard["opportunity_districts"],
            scorecard["proportional_opportunities"],
            scorecard["coalition_districts"],
            scorecard["proportional_coalitions"],
        )

        # Additional alternate minority ratings
        if alt_minority:
            alt_minority_metrics: Dict[str, float] = calc_alt_minority_metrics(
                aggregates["demos_totals"], aggregates["demos_by_district"], n_districts
            )
            subset: Dict[str, float] = {
                f"alt_{k}": v
                for k, v in alt_minority_metrics.items()
                if k
                in [
                    "opportunity_districts",
                    "opportunity_districts_pct",
                    "coalition_districts",
                ]
            }
            scorecard.update(subset)
            scorecard["minority_alt"] = rate_minority_opportunity(
                alt_minority_metrics["opportunity_districts"],
                alt_minority_metrics["proportional_opportunities"],
                alt_minority_metrics["coalition_districts"],
                alt_minority_metrics["proportional_coalitions"],
            )

    if which in ["all", "compactness", "extended"]:
        district_props = aggregate_shapes_by_district(
            assignments, shapes, graph, n_districts
        )
        compactness_metrics: Dict[str, float]
        compactness_by_district: List[Dict[str, float]]
        compactness_metrics, compactness_by_district = calc_compactness_metrics(
            district_props
        )

        # Additional discrete compactness metrics
        plan: Dict[str, int | str] = {a.geoid: a.district for a in assignments}
        cut_score: int = calc_cut_score(plan, graph)

        district_graphs = split_graph_by_districts(graph, plan)
        spanning_tree_by_district: List[Dict[str, float]] = [
            {"spanning_tree_score": calc_spanning_tree_score(g)}
            for g in district_graphs.values()
        ]
        spanning_tree_score: float = sum(
            d["spanning_tree_score"] for d in spanning_tree_by_district
        )

        compactness_metrics["cut_score"] = cut_score
        compactness_metrics["spanning_tree_score"] = spanning_tree_score
        scorecard.update(compactness_metrics)
        scorecard["compactness"] = rate_compactness(
            scorecard["reock"], scorecard["polsby_popper"]
        )

        # Combine the by-district metrics
        # assert len(compactness_by_district) == len(splitting_by_district)
        # assert len(compactness_by_district) == len(spanning_tree_by_district)

    if which in ["all", "splitting", "extended"]:
        splitting_metrics: Dict[str, float]
        splitting_by_district: List[Dict[str, float]]
        splitting_metrics, splitting_by_district = calc_splitting_metrics(
            aggregates["CxD"]
        )
        scorecard.update(splitting_metrics)
        scorecard["splitting"] = rate_splitting(
            scorecard["county_splitting"],
            scorecard["district_splitting"],
            n_counties,
            n_districts,
        )

    if which:  # Combine the by-district metrics
        by_district: List[Dict[str, float]] = list()
        by_district_metrics: List[List[Dict[str, float]]] = []
        if which == "all" or which == "extended":
            by_district_metrics = [
                compactness_by_district,
                spanning_tree_by_district,
                splitting_by_district,
            ]
            by_district = [{**x, **y, **z} for x, y, z in zip(*by_district_metrics)]
        elif which == "compactness":
            by_district_metrics = [compactness_by_district, spanning_tree_by_district]
            by_district = [{**x, **y} for x, y in zip(*by_district_metrics)]
        elif which == "splitting":
            by_district = splitting_by_district
        else:
            by_district_metrics = []

        scorecard["by_district"] = by_district

    # Trim the floating point numbers
    precision: int = 4
    int_metrics: List[str] = [
        "pr_seats",
        "proportional_opportunities",
        "proportional_coalitions",
        "proportionality",
        "competitiveness",
        "minority",
        "minority_alt",
        "compactness",
        "splitting",
    ]
    for metric in scorecard:
        if scorecard[metric] is None or metric == "by_district":
            continue
        if metric not in int_metrics:
            scorecard[metric] = round(scorecard[metric], precision)

    return scorecard


### HELPER FUNCTIONS ###


# @time_function
def aggregate_data_by_district(
    assignments: List[Assignment],
    data: Dict[str, Dict[str, str | int]],
    n_districts: int,
    n_counties: int,
    county_to_index: Dict[str, int],
    district_to_index: Dict[int | str, int],
) -> Dict[str, Any]:
    """Aggregate census & election data by district."""

    total_pop: int = 0
    pop_by_district: defaultdict[int | str, int] = defaultdict(int)

    total_votes: int = 0
    total_d_votes: int = 0
    d_by_district: Dict[int | str, int] = defaultdict(int)
    tot_by_district: Dict[int | str, int] = defaultdict(int)

    demos_totals: Dict[str, int] = defaultdict(int)
    demos_by_district: List[Dict[str, int]] = [
        defaultdict(int) for _ in range(n_districts + 1)
    ]

    CxD: List[List[float]] = [[0.0] * n_counties for _ in range(n_districts)]

    for a in assignments:
        # For population deviation

        pop: int = int(data[a.geoid][total_pop_field])
        pop_by_district[a.district] += pop
        total_pop += pop

        # For partisan metrics

        d: int = int(data[a.geoid][dem_votes_field])
        tot: int = int(data[a.geoid][dem_votes_field]) + int(
            data[a.geoid][rep_votes_field]
        )  # NOTE - Two-party vote total

        d_by_district[a.district] += d
        total_d_votes += d

        tot_by_district[a.district] += tot
        total_votes += tot

        # For minority opportunity metrics

        for demo in census_fields[1:]:  # Everything except total population
            demos_totals[demo] += int(data[a.geoid][demo])
            # NOTE - Generalize for str districts
            demos_by_district[int(a.district)][demo] += int(data[a.geoid][demo])

        # For county-district splitting

        county: str = GeoID(a.geoid).county[2:]

        i: int = district_to_index[a.district]
        j: int = county_to_index[county]

        CxD[i][j] += pop

    aggregates: Dict[str, Any] = {
        "total_pop": total_pop,
        "pop_by_district": pop_by_district,
        "total_votes": total_votes,
        "total_d_votes": total_d_votes,
        "d_by_district": d_by_district,
        "tot_by_district": tot_by_district,
        "demos_totals": demos_totals,
        "demos_by_district": demos_by_district[1:],  # Skip the dummy district
        "CxD": CxD,
    }

    return aggregates


def border_length(
    geoid: str,
    district: int | str,
    district_by_geoid: Dict[str, int | str],
    shapes: Dict[str, Any],
    graph: Dict[str, List[str]],
) -> float:
    """Sum the length of the border with other districts or the state border."""

    arc_length: float = 0.0

    for n in graph[geoid]:
        if n == OUT_OF_STATE:
            if OUT_OF_STATE in shapes[geoid]["arcs"]:
                arc_length += shapes[geoid]["arcs"][n]
        elif district_by_geoid[n] != district:
            arc_length += shapes[geoid]["arcs"][n]

    return arc_length


def arcs_are_symmetric(shapes: Dict[str, Any]) -> bool:
    symmetric: bool = True
    narcs: int = 0
    nasymmetric: int = 0

    for from_geoid, abstract in shapes.items():
        for to_geoid, from_border in abstract["arcs"].items():
            if to_geoid != "OUT_OF_STATE":
                narcs += 1
                to_border = shapes[to_geoid]["arcs"][from_geoid]
                if not approx_equal(from_border, to_border, places=4):
                    symmetric = False
                    nasymmetric += 1
                    print(
                        f"Arcs between {from_geoid} & {to_geoid} are not symmetric: {from_border} & {to_border}."
                    )

    if not symmetric:
        print(f"Total arcs: {narcs}, non-symmetric arcs: {nasymmetric}")

    return symmetric


# @time_function
def aggregate_shapes_by_district(
    assignments: List[Assignment],
    shapes: Dict[str, Any],
    graph: Dict[str, List[str]],
    n_districts: int,
    *,
    debug: bool = False,
) -> List[Dict[str, float]]:
    """Aggregate shape data by district for compactness calculations."""

    # Normalize the assignments & index districts by precinct

    plan: List[Dict] = list()
    district_by_geoid: Dict[str, int | str] = dict()
    geoid_field: str = "GEOID" if "GEOID" in assignments[0] else "GEOID20"
    district_field: str = "DISTRICT" if "DISTRICT" in assignments[0] else "District"

    if debug:
        arcs_are_symmetric(shapes)

    for a in assignments:
        plan.append({geoid_field: a.geoid, district_field: a.district})
        district_by_geoid[a.geoid] = a.district

    # Set up aggregates

    by_district: List[Dict[str, Any]] = [
        {"area": 0.0, "perimeter": 0.0, "exterior": list()}
        for _ in range(n_districts + 1)
    ]

    # Aggregate the shape properties

    for row in plan:
        geoid: str = row[geoid_field]
        district: int = row[district_field]

        by_district[district]["area"] += shapes[geoid]["area"]
        by_district[district]["perimeter"] += border_length(
            geoid, district, district_by_geoid, shapes, graph
        )
        by_district[district]["exterior"].extend(shapes[geoid]["exterior"])

    # Calculate district diameters

    implied_district_props: List[Dict[str, float]] = []
    for i, d in enumerate(by_district[1:]):  # Remove the dummy district
        # https://pypi.org/project/miniball/
        # https://github.com/marmakoide/miniball

        # print(f"District {i + 1}:")

        # lon, lat, r = rda.make_circle(d["exterior"])

        # S = np.random.randn(5, 2)
        # print(S)

        # points = np.array(d["exterior"])
        points = np.unique(d["exterior"], axis=0)
        # points = np.array(d["exterior"]).T  # Transpose gives shape (2,N)
        # print(points[:5])

        # diagnosis = is_matrix_singular(points)
        # print(diagnosis)

        # check_geometry(points)

        C, r2 = mb.get_bounding_ball(points)  # type: ignore
        r = math.sqrt(r2)

        # print(f"r: {r}, r': {r_prime} (diff: {r - r_prime})")

        # S = np.random.randn(100, 2)
        # _, r2 = mb.get_bounding_ball(S)  # type: ignore

        area: float = d["area"]
        perimeter: float = d["perimeter"]
        diameter: float = 2 * r

        implied_district_props.append(
            {"area": area, "perimeter": perimeter, "diameter": diameter}
        )

    return implied_district_props


# def safe_get_bounding_ball(S, epsilon=1e-7, rng=np.random.default_rng()):
#     """
#     Wrapper for get_bounding_ball with robust preprocessing.
#     """
#     try:
#         # Preprocess points
#         processed_points, metadata = preprocess_points(
#             S, min_distance=epsilon, scale=True, remove_duplicates=True
#         )

#         # Check if we have enough points after preprocessing
#         if len(processed_points) < 2:
#             raise ValueError(
#                 f"Not enough distinct points after preprocessing: {len(processed_points)} points"
#             )

#         # Run original bounding ball calculation
#         center, radius = mb.get_bounding_ball(processed_points, epsilon, rng)  # type: ignore

#         # Transform result back to original space
#         center, radius = postprocess_result(center, radius, metadata)

#         return center, radius

#     except Exception as e:
#         print(f"Error in bounding ball calculation: {str(e)}")
#         print("\nInput statistics:")
#         print(f"Original shape: {S.shape}")
#         print(f"Range: [{np.min(S)}, {np.max(S)}]")
#         print(f"Contains NaN: {np.any(np.isnan(S))}")
#         print(f"Contains inf: {np.any(np.isinf(S))}")
#         raise


# def preprocess_points(points, min_distance=1e-7, scale=True, remove_duplicates=True):
#     """
#     Preprocess points to avoid numerical stability issues in miniball calculation.

#     Parameters
#     ----------
#     points : ndarray
#         Input points array of shape (n_points, n_dimensions)
#     min_distance : float
#         Minimum distance between points to be considered distinct
#     scale : bool
#         Whether to scale points to improve numerical stability
#     remove_duplicates : bool
#         Whether to remove duplicate or very close points

#     Returns
#     -------
#     ndarray
#         Preprocessed points
#     dict
#         Preprocessing metadata for potentially reversing transformations
#     """
#     if not isinstance(points, np.ndarray):
#         points = np.array(points, dtype=np.float64)

#     # Store original points for reference
#     original_points = points.copy()

#     # Step 1: Remove any NaN or infinite values
#     valid_mask = np.all(np.isfinite(points), axis=1)
#     points = points[valid_mask]

#     if len(points) == 0:
#         raise ValueError("No valid points after removing NaN/infinite values")

#     # Step 2: Remove duplicate or very close points
#     if remove_duplicates and len(points) > 1:
#         # Compute pairwise distances
#         distances = pdist(points)
#         # Convert to square form for easier indexing
#         dist_matrix = squareform(distances)

#         # Find points that are too close
#         keep_mask = np.ones(len(points), dtype=bool)
#         for i in range(len(points)):
#             if keep_mask[i]:
#                 # Mark points that are too close to point i for removal
#                 too_close = dist_matrix[i] < min_distance
#                 too_close[i] = False  # Don't remove point i itself
#                 keep_mask[too_close] = False

#         points = points[keep_mask]

#     # Step 3: Center and scale points if requested
#     metadata = {}
#     if scale:
#         # Center points
#         center = np.mean(points, axis=0)
#         points = points - center
#         metadata["center"] = center

#         # Scale points to have reasonable magnitude
#         scale_factor = np.max(np.abs(points))
#         if scale_factor > 0:
#             points = points / scale_factor
#             metadata["scale"] = scale_factor

#     # Step 4: Add small jitter to remaining duplicate points if any exist
#     if len(points) > 1:
#         duplicates = True
#         while duplicates:
#             distances = pdist(points)
#             if np.any(distances < min_distance):
#                 # Add small random jitter to all points
#                 jitter = np.random.randn(*points.shape) * min_distance * 0.1
#                 points = points + jitter
#             else:
#                 duplicates = False

#     metadata.update(
#         {
#             "original_points": original_points,
#             "valid_mask": valid_mask,
#             "min_distance": min_distance,
#         }
#     )

#     return points, metadata


# def postprocess_result(center, radius, metadata):
#     """
#     Transform the miniball result back to original scale if preprocessing was applied.

#     Parameters
#     ----------
#     center : ndarray
#         Center point of the miniball in preprocessed space
#     radius : float
#         Radius of the miniball in preprocessed space
#     metadata : dict
#         Preprocessing metadata from preprocess_points

#     Returns
#     -------
#     ndarray, float
#         Center and radius in original space
#     """
#     if "scale" in metadata:
#         center = center * metadata["scale"]
#         radius = radius * metadata["scale"]

#     if "center" in metadata:
#         center = center + metadata["center"]

#     return center, radius


# def is_matrix_singular(A, tol=1e-10):
#     """
#     Check if a matrix is singular using rank and conditioning.

#     Args:
#         A: Input matrix (numpy array)
#         tol: Tolerance for numerical calculations

#     Returns:
#         dict: Diagnosis results including if matrix is singular and why
#     """
#     A = np.array(A, dtype=float)
#     min_dim = min(A.shape)
#     rank = np.linalg.matrix_rank(A)

#     diagnosis = {"is_singular": False, "reason": None, "rank": rank, "shape": A.shape}

#     # Check rank deficiency
#     if rank < min_dim:
#         diagnosis["is_singular"] = True
#         diagnosis["reason"] = f"Rank deficient: rank {rank} < min dimension {min_dim}"
#         return diagnosis

#     # Check condition number for numerical singularity
#     try:
#         cond = np.linalg.cond(A)
#         if cond > 1 / tol:
#             diagnosis["is_singular"] = True
#             diagnosis["reason"] = f"Ill-conditioned: condition number {cond:.2e}"
#         diagnosis["condition_number"] = cond
#     except np.linalg.LinAlgError:
#         diagnosis["is_singular"] = True
#         diagnosis["reason"] = "Could not compute condition number (likely singular)"

#     return diagnosis


# def analyze_point_geometry(points, tolerance=1e-8):
#     """
#     Analyzes a set of points to determine if they are nearly collinear or coplanar.

#     Parameters
#     ----------
#     points : ndarray
#         Array of points with shape (n, d) where n is number of points
#         and d is dimensionality
#     tolerance : float
#         Tolerance for considering singular values as zero

#     Returns
#     -------
#     dict
#         Dictionary containing analysis results
#     """
#     if len(points) < 2:
#         return {"status": "insufficient_points", "dimension": 0}

#     # Center the points
#     centered = points - np.mean(points, axis=0)

#     # Compute SVD of the centered points
#     _, singular_values, _ = np.linalg.svd(centered)

#     # Normalize singular values
#     normalized_sv = singular_values / singular_values[0]

#     # Count significant dimensions (singular values above tolerance)
#     significant_dims = np.sum(normalized_sv > tolerance)

#     # Determine geometric arrangement
#     dim = points.shape[1]
#     if significant_dims == 1:
#         status = "collinear"
#     elif significant_dims == 2 and dim > 2:
#         status = "coplanar"
#     else:
#         status = f"{significant_dims}_dimensional"

#     # Calculate additional metrics
#     max_deviation = 0
#     explanation = ""

#     if status == "collinear":
#         # Calculate maximum deviation from best-fit line
#         direction = centered[np.argmax(np.linalg.norm(centered, axis=1))]
#         direction = direction / np.linalg.norm(direction)
#         projections = np.outer(centered.dot(direction), direction)
#         deviations = np.linalg.norm(centered - projections, axis=1)
#         max_deviation = np.max(deviations)
#         explanation = (
#             f"Maximum deviation from line: {max_deviation:.2e}\n"
#             f"Points are effectively {status}"
#         )

#     elif status == "coplanar":
#         # Calculate maximum deviation from best-fit plane
#         normal = np.cross(centered[0], centered[1])
#         normal = normal / np.linalg.norm(normal)
#         deviations = np.abs(centered.dot(normal))
#         max_deviation = np.max(deviations)
#         explanation = (
#             f"Maximum deviation from plane: {max_deviation:.2e}\n"
#             f"Points are effectively {status}"
#         )

#     results = {
#         "status": status,
#         "singular_values": singular_values,
#         "normalized_singular_values": normalized_sv,
#         "significant_dimensions": significant_dims,
#         "max_deviation": max_deviation,
#         "explanation": explanation,
#     }

#     return results


# def check_geometry(points, tolerance=1e-8, verbose=True):
#     """
#     Convenient wrapper to analyze and print results about point geometry.

#     Parameters
#     ----------
#     points : ndarray
#         Input points to analyze
#     tolerance : float
#         Tolerance for geometric tests
#     verbose : bool
#         Whether to print detailed results

#     Returns
#     -------
#     bool
#         True if points are nearly collinear (2D) or coplanar (3D)
#     """
#     results = analyze_point_geometry(points, tolerance)

#     if verbose:
#         print("\nGeometric Analysis Results:")
#         print("--------------------------")
#         print(f"Status: {results['status']}")
#         print(f"Significant dimensions: {results['significant_dimensions']}")
#         print("\nSingular values (normalized):")
#         for i, sv in enumerate(results["normalized_singular_values"]):
#             print(f"  σ{i+1}: {sv:.2e}")

#         if results["explanation"]:
#             print("\n" + results["explanation"])

#     return results["status"] in ["collinear", "coplanar"]


# @time_function
def calc_population_deviation(
    pop_by_district: defaultdict[int, int], total_pop: int, n_districts: int
) -> float:
    """Calculate population deviation."""

    max_pop: int = max(pop_by_district.values())
    min_pop: int = min(pop_by_district.values())
    target_pop: int = int(total_pop / n_districts)

    deviation: float = rda.calc_population_deviation(max_pop, min_pop, target_pop)

    return deviation


# @time_function
def calc_partisan_metrics(
    total_d_votes: int,
    total_votes: int,
    d_by_district: Dict[int, int],
    tot_by_district: Dict[int, int],
) -> Dict[str, Optional[float]]:
    """Calulate partisan metrics."""

    partisan_metrics: Dict[str, Optional[float]] = dict()

    Vf: float = total_d_votes / total_votes
    Vf_array: List[float] = [
        d / tot for d, tot in zip(d_by_district.values(), tot_by_district.values())
    ]
    partisan_metrics["estimated_vote_pct"] = Vf

    all_results: dict = rda.calc_partisan_metrics(Vf, Vf_array)

    partisan_metrics["pr_deviation"] = all_results["bias"]["deviation"]
    partisan_metrics["pr_seats"] = all_results["bias"]["bestS"]
    partisan_metrics["pr_pct"] = all_results["bias"]["bestSf"]
    partisan_metrics["estimated_seats"] = all_results["bias"]["estS"]
    partisan_metrics["estimated_seat_pct"] = all_results["bias"]["estSf"]
    partisan_metrics["fptp_seats"] = all_results["bias"]["fptpS"]

    partisan_metrics["disproportionality"] = all_results["bias"]["prop"]
    partisan_metrics["efficiency_gap"] = all_results["bias"]["eG"]
    partisan_metrics["gamma"] = all_results["bias"]["gamma"]

    partisan_metrics["seats_bias"] = all_results["bias"]["bS50"]
    partisan_metrics["votes_bias"] = all_results["bias"]["bV50"]
    partisan_metrics["geometric_seats_bias"] = all_results["bias"]["bSV"]
    partisan_metrics["global_symmetry"] = all_results["bias"]["gSym"]

    partisan_metrics["declination"] = all_results["bias"]["decl"]
    partisan_metrics["mean_median_statewide"] = all_results["bias"]["mMs"]
    partisan_metrics["mean_median_average_district"] = all_results["bias"]["mMd"]
    partisan_metrics["turnout_bias"] = all_results["bias"]["tOf"]
    partisan_metrics["lopsided_outcomes"] = all_results["bias"]["lO"]

    partisan_metrics["competitive_districts"] = all_results["responsiveness"]["cD"]
    partisan_metrics["competitive_district_pct"] = all_results["responsiveness"]["cDf"]
    partisan_metrics["average_margin"] = calc_average_margin(Vf_array)

    partisan_metrics["responsiveness"] = all_results["responsiveness"]["littleR"]
    partisan_metrics["responsive_districts"] = all_results["responsiveness"]["rD"]
    partisan_metrics["responsive_district_pct"] = all_results["responsiveness"]["rDf"]
    partisan_metrics["overall_responsiveness"] = all_results["responsiveness"]["bigR"]

    partisan_metrics["avg_dem_win_pct"] = all_results["averageDVf"]
    partisan_metrics["avg_rep_win_pct"] = (
        1.0 - all_results["averageRVf"]
        if all_results["averageRVf"] is not None
        else None
    )

    return partisan_metrics


def calc_average_margin(Vf_array: List[float]) -> float:
    """Calculate the average margin of victory."""

    margin: float = sum([abs(v - 0.5000) for v in Vf_array]) / len(Vf_array)

    return margin


# @time_function
def calc_minority_metrics(
    demos_totals: Dict[str, int],
    demos_by_district: List[Dict[str, int]],
    n_districts: int,
) -> Dict[str, float]:
    """Calculate minority metrics."""

    statewide_demos: Dict[str, float] = dict()
    for demo in census_fields[2:]:  # Skip total population & total VAP
        simple_demo: str = demo.split("_")[0].lower()
        statewide_demos[simple_demo] = (
            demos_totals[demo] / demos_totals[total_vap_field]
        )

    by_district: List[Dict[str, float]] = list()
    for i in range(n_districts):
        district_demos: Dict[str, float] = dict()
        for demo in census_fields[2:]:  # Skip total population & total VAP
            simple_demo: str = demo.split("_")[0].lower()
            district_demos[simple_demo] = (
                demos_by_district[i][demo] / demos_by_district[i][total_vap_field]
            )

        by_district.append(district_demos)

    minority_metrics: Dict[str, float] = rda.calc_minority_opportunity(
        statewide_demos, by_district
    )

    return minority_metrics


def est_alt_minority_opportunity(mf: float, demo: Optional[str] = None) -> float:
    """
    Estimate the ALTERNATE opportunity for a minority representation.

    NOTE - This is a slightly modified clone of est_minority_opportunity in rdapy.
    """

    assert mf >= 0.0

    # range: list[float] = [0.37, 0.50]

    shift: float = 0.15  # For Black VAP % (and Minority)
    dilution: float = 0.50  # For other demos, dilute the Black shift by half
    if demo and (demo not in ["black", "minority"]):
        shift *= dilution

    wip_num: float = mf + shift
    oppty: float = (
        # NOTE - This is the one-line change from est_minority_opportunity in rdapy,
        # i.e., don't clip VAP % below 37%.
        max(min(rda.est_seat_probability(wip_num), 1.0), 0.0)
        # 0.0 if (mf < range[0]) else min(rda.est_seat_probability(wip_num), 1.0)
    )

    return oppty


def calc_alt_minority_opportunity(
    statewide_demos: dict[str, float], demos_by_district: list[dict[str, float]]
) -> dict[str, float]:
    """
    Estimate ALTERNATE minority opportunity (everything except the table which is used in DRA).

    NOTE - This is a clone of calc_minority_opportunity in rdapy that uses
    and slightly modified est_alt_minority_opportunity above instead.
    """

    n_districts: int = len(demos_by_district)

    # Determine statewide proportional minority districts by single demographics (ignoring'White')
    districts_by_demo: dict[str, int] = {
        x: rda.calc_proportional_districts(statewide_demos[x], n_districts)
        for x in rda.DEMOGRAPHICS[1:]
    }

    # Sum the statewide proportional districts for each single demographic
    total_proportional: int = sum(
        [v for k, v in districts_by_demo.items() if k not in ["white", "minority"]]
    )

    # Sum the opportunities for minority represention in each district
    oppty_by_demo: dict[str, float] = defaultdict(float)
    for district in demos_by_district:
        for d in rda.DEMOGRAPHICS[1:]:  # Ignore 'white'
            # NOTE - Use the est_alt_minority_opportunity above, instead of est_minority_opportunity in rdapy.
            oppty_by_demo[d] += est_alt_minority_opportunity(district[d], d)

    # The # of opportunity districts for each separate demographic and all minorities
    od: float = sum(
        [v for k, v in oppty_by_demo.items() if k not in ["white", "minority"]]
    )
    cd: float = oppty_by_demo["minority"]

    # The # of proportional districts for each separate demographic and all minorities
    pod: float = total_proportional
    pcd: float = districts_by_demo["minority"]

    results: dict[str, float] = {
        # "pivot_by_demographic": table, # For this, use dra-analytics instead
        "opportunity_districts": od,
        "proportional_opportunities": pod,
        "coalition_districts": cd,
        "proportional_coalitions": pcd,
        # "details": {} # None
    }

    return results


# @time_function
def calc_alt_minority_metrics(
    demos_totals: Dict[str, int],
    demos_by_district: List[Dict[str, int]],
    n_districts: int,
) -> Dict[str, float]:
    """
    Calculate alternate minority metrics.

    NOTE - This is a clone of calc_minority_metrics that uses calc_alt_minority_opportunity above,
    instead of calc_minority_opportunity in rdapy.
    """

    statewide_demos: Dict[str, float] = dict()
    for demo in census_fields[2:]:  # Skip total population & total VAP
        simple_demo: str = demo.split("_")[0].lower()
        statewide_demos[simple_demo] = (
            demos_totals[demo] / demos_totals[total_vap_field]
        )

    by_district: List[Dict[str, float]] = list()
    for i in range(n_districts):
        district_demos: Dict[str, float] = dict()
        for demo in census_fields[2:]:  # Skip total population & total VAP
            simple_demo: str = demo.split("_")[0].lower()
            district_demos[simple_demo] = (
                demos_by_district[i][demo] / demos_by_district[i][total_vap_field]
            )

        by_district.append(district_demos)

    # NOTE - Calc alternative minority metrics
    alt_minority_metrics: Dict[str, float] = calc_alt_minority_opportunity(
        statewide_demos, by_district
    )
    # alt_minority_metrics["opportunity_districts_pct"] = (
    #     alt_minority_metrics["opportunity_districts"]
    #     / alt_minority_metrics["proportional_opportunities"]
    # )

    return alt_minority_metrics


# @time_function
def calc_compactness_metrics(
    district_props: List[Dict[str, float]]
) -> Tuple[Dict[str, float], List[Dict[str, float]]]:
    """Calculate compactness metrics using implied district props."""

    tot_reock: float = 0
    tot_polsby: float = 0
    by_district: List[Dict[str, float]] = list()

    for i, d in enumerate(district_props):
        reock: float = rda.reock_formula(d["area"], d["diameter"] / 2)
        polsby: float = rda.polsby_formula(d["area"], d["perimeter"])
        by_district.append({"reock": reock, "polsby": polsby})

        tot_reock += reock
        tot_polsby += polsby

    avg_reock: float = tot_reock / len(district_props)
    avg_polsby: float = tot_polsby / len(district_props)

    compactness_metrics: Dict[str, float] = dict()
    compactness_metrics["reock"] = avg_reock
    compactness_metrics["polsby_popper"] = avg_polsby

    return compactness_metrics, by_district


# @time_function
def calc_splitting_metrics(
    CxD: List[List[float]],
) -> Tuple[Dict[str, float], List[Dict[str, float]]]:
    """Calculate county-district splitting metrics."""

    all_results: Dict[str, float] = rda.calc_county_district_splitting(CxD)

    splitting_metrics: Dict[str, float] = dict()
    splitting_metrics["county_splitting"] = all_results["county"]
    splitting_metrics["district_splitting"] = all_results["district"]

    # Calculate the # of counties split and the # of splits
    # In the CxD matrix, rows are districts, columns are counties.
    counties_split: int = 0
    county_splits: int = 0
    for j in range(len(CxD[0])):  # for each county
        # Find the number districts that have this county
        parts: int = 0
        for i in range(len(CxD)):  # for each district
            if CxD[i][j] > 0:
                parts += 1
        # If it's more than 1, increment the # of counties split and the # of splits
        if parts > 1:
            counties_split += 1
            county_splits += parts - 1

    splitting_metrics["counties_split"] = counties_split
    splitting_metrics["county_splits"] = county_splits

    # Calculate split scores by district
    # This is redundantly calculating intermediate values that rda.calc_county_district_splitting(CxD) above
    # does, but it's easier to recompute the constituents here than it is to tunnel them from rdapy.
    dT: list[float] = rda.district_totals(CxD)
    cT: list[float] = rda.county_totals(CxD)
    rD: list[list[float]] = rda.reduce_district_splits(CxD, cT)
    g: list[list[float]] = rda.calc_district_fractions(rD, dT)
    by_district: List[Dict[str, float]] = splitting_by_district(g)

    return splitting_metrics, by_district


def splitting_by_district(g: List[List[float]]) -> List[Dict[str, float]]:
    """Calculate split scores by district."""

    numD: int = len(g)
    by_district: List[Dict[str, float]] = list()

    for i in range(numD):
        split_score: float = rda.district_split_score(i, g)
        by_district.append({"district_splitting": split_score})

    return by_district


### RATING FUNCTIONS ###


# def rate_dimensions(
#     *,
#     proportionality: tuple,
#     competitiveness: tuple,
#     minority: tuple,
#     compactness: tuple,
#     splitting: tuple,
# ) -> Dict[str, int]:
#     """Rate the dimensions of a plan."""

#     ratings: Dict[str, int] = dict()

#     disproportionality, Vf, Sf = proportionality
#     ratings["proportionality"] = rda.rate_proportionality(disproportionality, Vf, Sf)

#     cdf = competitiveness[0]
#     ratings["competitiveness"] = rda.rate_competitiveness(cdf)

#     od, pod, cd, pcd = minority
#     ratings["minority"] = rda.rate_minority_opportunity(od, pod, cd, pcd)

#     avg_reock, avg_polsby = compactness
#     reock_rating: int = rda.rate_reock(avg_reock)
#     polsby_rating: int = rda.rate_polsby(avg_polsby)
#     ratings["compactness"] = rda.rate_compactness(reock_rating, polsby_rating)

#     county_splitting, district_splitting, n_counties, n_districts = splitting
#     county_rating: int = rda.rate_county_splitting(
#         county_splitting, n_counties, n_districts
#     )
#     district_rating: int = rda.rate_district_splitting(
#         district_splitting, n_counties, n_districts
#     )
#     ratings["splitting"] = rda.rate_splitting(county_rating, district_rating)

#     return ratings


def rate_proportionality(disproportionality: float, Vf: float, Sf: float) -> int:
    rating: int = rda.rate_proportionality(disproportionality, Vf, Sf)

    return rating


def rate_competitiveness(cdf: float) -> int:
    rating: int = rda.rate_competitiveness(cdf)

    return rating


def rate_minority_opportunity(od: float, pod: float, cd: float, pcd: float) -> int:
    rating: int = rda.rate_minority_opportunity(od, pod, cd, pcd)

    return rating


def rate_compactness(avg_reock: int, avg_polsby: int) -> int:
    reock_rating: int = rda.rate_reock(avg_reock)
    polsby_rating: int = rda.rate_polsby(avg_polsby)
    rating: int = rda.rate_compactness(reock_rating, polsby_rating)

    return rating


def rate_splitting(
    county_splitting: float,
    district_splitting: float,
    n_counties: int,
    n_districts: int,
) -> int:
    county_rating: int = rda.rate_county_splitting(
        county_splitting, n_counties, n_districts
    )
    district_rating: int = rda.rate_district_splitting(
        district_splitting, n_counties, n_districts
    )
    rating: int = rda.rate_splitting(county_rating, district_rating)

    return rating


### END ###
