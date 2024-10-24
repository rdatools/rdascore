# Scores (Metrics)

These are the metrics ("scores") calculated for a plan, when you score it using `analyze_plan()`. 
They are grouped below in the order that they appear in the scorecard dictionary.

## General

*   **D** &ndash; The number of districts.
*   **C** &ndash; The number of counties.
*   **population_deviation** &ndash; The population deviation of the plan.
*   **estimated_vote_pct** &ndash; The Democratic two-party vote share.

## Partisan Bias

The measures of partisan bias (in this section) and responsiveness (in the next section) are described in some detail in
[Advanced Measures of Bias &amp; Responsiveness](https://medium.com/dra-2020/advanced-measures-of-bias-responsiveness-c1bf182d29a9).
Many use [fractional seat probabilities](https://lipid.phys.cmu.edu/nagle/Technical/FractionalSeats2.pdf).

*   **pr_deviation** &ndash; The deviation from pr_seats. Smaller is better, and zero is perfect.
*   **pr_seats** &ndash; The integral number of seats closest to proportional representation.
*   **pr_pct** &ndash; pr_seats as a percentage of the number of districts.
*   **estimated_seats** &ndash; The estimated number of fractional Democratic seats.
*   **estimated_seat_pct** &ndash; estimated_seats as a percentage of the number of districts.
*   **fptp_seats** &ndash; The estimated number of Democratic seats using "first past the post" (FPTP), all-or-nothing accounting.
*   **disproportionality** &ndash; estimated_vote_pct minus estimated_seat_pct.
*   **efficiency_gap** &ndash; The efficiency gap. Smaller absolute value is better. Positive values favor Republicans; negative values favor Democrats.
*   **gamma** &ndash; A new measure of bias that combines seats and responsiveness.
*   **seats_bias** (αₛ) &ndash; The seats bias at 50% Democratic vote share.
*   **votes_bias** (αᵥ) &ndash; The votes bias at 50% Democratic vote share.
*   **geometric_seats_bias** (β) &ndash; The seats bias at the statewide Democratic vote share, not 50% (aka "partisan bias").
*   **global_symmetry** (GS) &ndash; A combination of seats and votes bias.
*   **declination** (δ) &ndash; The declination angle (in degrees), calculated using fractional seats and votes. Smaller is better.
*   **mean_median_statewide** &ndash; The statewide Democratic two-party vote share minus the median Democratic two-party district vote share.
*   **mean_median_average_district** &ndash; The mean Democratic two-party district vote share minus the median Democratic two-party district vote share.
*   **turnout_bias** (TO) &ndash; The difference between the statewide Democratic vote share and the average their average district vote share.
*   **lopsided_outcomes** (LO) &ndash; The difference between the average two-party vote shares for the Democratic and Republican wins.

## Competitiveness & Responsiveness

*   **competitive_districts** &ndash; The estimated number of competitive districts, using fractional seat probabilities. Bigger is better.
*   **competitive_district_pct** &ndash; competitive_districts as a percentage of the number of districts (D).
*   **average_margin** &ndash; The average margin of victory. Smaller is better.
*   **responsiveness** (ρ) &ndash; The slope of the seats-votes curve at the statewide Democratic vote share.
*   **responsive_districts** &ndash; The likely number of responsive districts, using fractional seat probabilities.
*   **responsive_district_pct** &ndash; responsive_districts as a percentage of the number of districts (D).
*   **overall_responsiveness** (R) &ndash; An overall measure of responsiveness which you can think of as a winner’s bonus.
*   **avg_dem_win_pct** &ndash; The average Democratic two-party vote share in districts won by Democrats.
*   **avg_rep_win_pct** &ndash; The average Republican two-party vote share in districts won by Republicans.

## Opportunity for Minority Representation

*   **opportunity_districts** &ndash; The estimated number of single race or ethnicity minority opportunity districts, using fractional seat probabilities (and DRA's method).
*   **proportional_opportunities** &ndash; The proportional number of single race or ethnicity minority opportunity districts, based on statewide VAP.
*   **coalition_districts** &ndash; The estimated number of all-minorities-together coalition districts, using fractional seat probabilities (and DRA's method).
*   **proportional_coalitions** &ndash; The proportional number of all-minorities-together coalition districts, based on statewide VAP.
*   **alt_opportunity_districts** &ndash; The estimated number of single race or ethnicity minority opportunity districts, using fractional seat probabilities. Unlike opportunity_districts, this "alt" metric means does not clip below the 37% threshold (like DRA does). The results are more continuous.
*   **alt_coalition_districts** &ndash; The estimated number of all-minorities-together coalition districts, using fractional seat probabilities. Unlike coalition_districts, this "alt" metric does not clip below the 37% threshold (like DRA does). The results are more continuous.

## Compactness

*   **reock** &ndash; The average Reock measure of compactnes for the districts. Bigger is better.
*   **polsby_popper** &ndash; The average Polsby-Popper measure of compactness for the districts. Bigger is better.
*   **cut_score** &ndash; The number of edges between nodes (precincts) in the contiguity graph that are cut (cross district boundaries). A measure of compactness using discrete geometry. Smaller is better.
*   **spanning_tree_score** &ndash; The spanning tree scrore. Another measure of compactness using discrete geometry. Bigger is better.
*   **population_compactness** &ndash; The population compactness of the map. Lower is more *energy* compact. Smaller is better.

## County-District Splitting

The county and district splitting measures are described in
[Measuring County &amp; District Splitting](https://medium.com/dra-2020/measuring-county-district-splitting-48a075bcce39).

*   **county_splitting** &ndash; A measure of the degree of county splitting. Smaller is better, and 1.0 (no splitting) is the best.
*   **district_splitting** &ndash; A measure of the degree of district splitting. Smaller is better, and 1.0 (no splitting) is the best.
*   **counties_split** &ndash; The number of counties split across districts. Smaller is better.
*   **county_splits** &ndash; The number of *times* counties are split, e.g, a county may be split more than once. Smaller is better.

## Dave's Redistricting Ratings

*   **proportionality** &ndash; DRA's propoprtionality rating. Integers [0-100], where bigger is better.
*   **competitiveness** &ndash; DRA's competitiveness rating. Integers [0-100], where bigger is better.
*   **minority** &ndash; DRA's minority opportunity rating. Integers [0-100], where bigger is better.
*   **compactness** &ndash; DRA's compactness rating. Integers [0-100], where bigger is better.
*   **splitting** &ndash; DRA's county-district splitting rating. Integers [0-100], where bigger is better.
*   **minority_alt** &ndash; A modified version of DRA's minority opportunity rating that uses `alt_opportunity_districts` and `alt_coalition_districts` (i.e., does not clip below the 37% threshold) making the results more continuous.

## By District

*  **by_district** &ndash; `reock`, `polsby_popper`, `cut_score`, and `spanning_tree_score` by district (with zero-based indexing, i.e., district 1 is the first element [0] in the list).