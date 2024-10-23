"""
ANALYZE A PLAN
"""

from collections import defaultdict
from typing import Any, List, Dict, Tuple, Optional

import rdapy as rda
from rdabase import (
    census_fields,
    election_fields,
    GeoID,
    OUT_OF_STATE,
    Assignment,
    approx_equal,
)
from .discrete_compactness import (
    calc_cut_score,
    calc_spanning_tree_score,
    split_graph_by_districts,
    remove_out_of_state_border,
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
    alt_minority: bool = False,  # If True, add an alternative minority opportunity rating
) -> Dict[str, Any]:
    """Analyze a plan."""

    n_districts: int = metadata["D"]
    n_counties: int = metadata["C"]
    county_to_index: Dict[str, int] = metadata["county_to_index"]
    district_to_index: Dict[int | str, int] = metadata["district_to_index"]

    ### AGGREGATE DATA & SHAPES BY DISTRICT ###

    aggregates: Dict[str, Any] = aggregate_data_by_district(
        assignments, data, n_districts, n_counties, county_to_index, district_to_index
    )
    district_props: List[Dict[str, float]] = aggregate_shapes_by_district(
        assignments, shapes, graph, n_districts
    )

    ### CALCULATE THE METRICS ###

    deviation: float = calc_population_deviation(
        aggregates["pop_by_district"], aggregates["total_pop"], n_districts
    )
    partisan_metrics: Dict[str, Optional[float]] = calc_partisan_metrics(
        aggregates["total_d_votes"],
        aggregates["total_votes"],
        aggregates["d_by_district"],
        aggregates["tot_by_district"],
    )
    minority_metrics: Dict[str, float] = calc_minority_metrics(
        aggregates["demos_totals"], aggregates["demos_by_district"], n_districts
    )
    compactness_metrics: Dict[str, float]
    compactness_by_district: List[Dict[str, float]]
    compactness_metrics, compactness_by_district = calc_compactness_metrics(
        district_props
    )

    splitting_metrics: Dict[str, float]
    splitting_by_district: List[float]
    splitting_metrics, splitting_by_district = calc_splitting_metrics(aggregates["CxD"])

    # Added: Discrete compactness metrics

    plan: Dict[str, int | str] = {a.geoid: a.district for a in assignments}
    stripped_graph: Dict[str, List[str]] = remove_out_of_state_border(graph)
    cut_score: int = calc_cut_score(plan, stripped_graph)
    district_graphs = split_graph_by_districts(stripped_graph, plan)
    # TODO - HERE
    # spanning_tree_score = sum(
    #     [calc_spanning_tree_score(g) for g in district_graphs.values()]
    # )

    # Added: Alternate minority ratings
    if alt_minority:
        alt_minority_metrics: Dict[str, float] = calc_alt_minority_metrics(
            aggregates["demos_totals"], aggregates["demos_by_district"], n_districts
        )

    scorecard: Dict[str, Any] = dict()
    scorecard["D"] = n_districts
    scorecard["C"] = n_counties
    scorecard["population_deviation"] = deviation
    scorecard.update(partisan_metrics)
    scorecard.update(minority_metrics)
    if alt_minority:
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
    scorecard.update(compactness_metrics)
    scorecard["compactness_by_district"] = compactness_by_district
    scorecard.update(splitting_metrics)
    scorecard["splitting_by_district"] = splitting_by_district

    ### RATE THE DIMENSIONS ###

    ratings: Dict[str, int] = rate_dimensions(
        proportionality=(
            scorecard["pr_deviation"],
            scorecard["estimated_vote_pct"],
            scorecard["estimated_seat_pct"],
        ),
        competitiveness=(scorecard["competitive_district_pct"],),
        minority=(
            scorecard["opportunity_districts"],
            scorecard["proportional_opportunities"],
            scorecard["coalition_districts"],
            scorecard["proportional_coalitions"],
        ),
        compactness=(scorecard["reock"], scorecard["polsby_popper"]),
        splitting=(
            scorecard["county_splitting"],
            scorecard["district_splitting"],
            n_counties,
            n_districts,
        ),
    )

    if alt_minority:
        ratings["minority_alt"] = rda.rate_minority_opportunity(
            alt_minority_metrics["opportunity_districts"],
            alt_minority_metrics["proportional_opportunities"],
            alt_minority_metrics["coalition_districts"],
            alt_minority_metrics["proportional_coalitions"],
        )

    scorecard.update(ratings)

    ### TRIM THE FLOATING POINT RESULTS ###

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
    by_district_metrics: List[str] = [
        "compactness_by_district",
        "splitting_by_district",
    ]  # Pass the by-district metrics up to the caller raw, unrounded
    for metric in scorecard:
        if scorecard[metric] is None or metric in by_district_metrics:
            continue
        if metric not in int_metrics:
            scorecard[metric] = round(scorecard[metric], precision)

    return scorecard


### HELPER FUNCTIONS ###


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


def aggregate_shapes_by_district(
    assignments: List[Assignment],
    shapes: Dict[str, Any],
    graph: Dict[str, List[str]],
    n_districts: int,
) -> List[Dict[str, float]]:
    """Aggregate shape data by district for compactness calculations."""

    # Normalize the assignments & index districts by precinct

    plan: List[Dict] = list()
    district_by_geoid: Dict[str, int | str] = dict()
    geoid_field: str = "GEOID" if "GEOID" in assignments[0] else "GEOID20"
    district_field: str = "DISTRICT" if "DISTRICT" in assignments[0] else "District"

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
        # print(f"District {i + 1}: {d}")  # DEBUG
        _, _, r = rda.make_circle(d["exterior"])

        area: float = d["area"]
        perimeter: float = d["perimeter"]
        diameter: float = 2 * r

        implied_district_props.append(
            {"area": area, "perimeter": perimeter, "diameter": diameter}
        )

        # print(
        #     f"District {i + 1}: Area = {area}, Perimeter = {perimeter}, Diameter = {diameter}"
        # )  # DEBUG

    return implied_district_props


def calc_population_deviation(
    pop_by_district: defaultdict[int, int], total_pop: int, n_districts: int
) -> float:
    """Calculate population deviation."""

    max_pop: int = max(pop_by_district.values())
    min_pop: int = min(pop_by_district.values())
    target_pop: int = int(total_pop / n_districts)

    deviation: float = rda.calc_population_deviation(max_pop, min_pop, target_pop)

    return deviation


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


# NOTE - This is a slightly modified clone of est_minority_opportunity in rdapy.
def est_alt_minority_opportunity(mf: float, demo: Optional[str] = None) -> float:
    """Estimate the ALTERNATE opportunity for a minority representation.

    NOTE - Shift minority proportions up, so 37% minority scores like 52% share,
      but use the uncompressed seat probability distribution. This makes a 37%
      district have a ~70% chance of winning, and a 50% district have a >99% chance.
      Below 37 % has no chance.
    NOTE - Sam Wang suggest 90% probability for a 37% district. That seems a little
      too abrupt and all or nothing, so I backed off to the ~70%.
    """

    assert mf >= 0.0

    range: list[float] = [0.37, 0.50]

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


# NOTE - This is a clone of calc_minority_opportunity in rdapy that uses
# and slightly modified est_alt_minority_opportunity above instead.
def calc_alt_minority_opportunity(
    statewide_demos: dict[str, float], demos_by_district: list[dict[str, float]]
) -> dict[str, float]:
    """Estimate ALTERNATE minority opportunity (everything except the table which is used in DRA)."""

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


# NOTE - This is a clone of calc_minority_metrics that uses calc_alt_minority_opportunity above,
# instead of calc_minority_opportunity in rdapy.
def calc_alt_minority_metrics(
    demos_totals: Dict[str, int],
    demos_by_district: List[Dict[str, int]],
    n_districts: int,
) -> Dict[str, float]:
    """Calculate alternate minority metrics."""

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
    alt_minority_metrics["opportunity_districts_pct"] = (
        alt_minority_metrics["opportunity_districts"]
        / alt_minority_metrics["proportional_opportunities"]
    )

    return alt_minority_metrics


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


def calc_splitting_metrics(
    CxD: List[List[float]],
) -> Tuple[Dict[str, float], List[float]]:
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
    by_district: List[float] = splitting_by_district(g)

    return splitting_metrics, by_district


def splitting_by_district(g: List[List[float]]) -> List[float]:
    """Calculate split scores by district."""

    numD: int = len(g)
    by_district: List[float] = list()

    for i in range(numD):
        split_score: float = rda.district_split_score(i, g)
        by_district.append(split_score)

    return by_district


def rate_dimensions(
    *,
    proportionality: tuple,
    competitiveness: tuple,
    minority: tuple,
    compactness: tuple,
    splitting: tuple,
) -> Dict[str, int]:
    """Rate the dimensions of a plan."""

    ratings: Dict[str, int] = dict()

    disproportionality, Vf, Sf = proportionality
    ratings["proportionality"] = rda.rate_proportionality(disproportionality, Vf, Sf)

    cdf = competitiveness[0]
    ratings["competitiveness"] = rda.rate_competitiveness(cdf)

    od, pod, cd, pcd = minority
    ratings["minority"] = rda.rate_minority_opportunity(od, pod, cd, pcd)

    avg_reock, avg_polsby = compactness
    reock_rating: int = rda.rate_reock(avg_reock)
    polsby_rating: int = rda.rate_polsby(avg_polsby)
    ratings["compactness"] = rda.rate_compactness(reock_rating, polsby_rating)

    county_splitting, district_splitting, n_counties, n_districts = splitting
    county_rating: int = rda.rate_county_splitting(
        county_splitting, n_counties, n_districts
    )
    district_rating: int = rda.rate_district_splitting(
        district_splitting, n_counties, n_districts
    )
    ratings["splitting"] = rda.rate_splitting(county_rating, district_rating)

    return ratings


### END ###
