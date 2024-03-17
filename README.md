# rdascore

Compute Dave's Redistricting (DRA) analytics for an ensemble of redistricting plans.

## Installation

To clone the repository:

```bash
$ git clone https://github.com/alecramsay/rdascore
$ cd rdascore
```

To install the package:

```bash
$ pip install rdascore
```

As noted next, you probably also want to clone the companion [rdabase](https://github.com/alecramsay/rdabase) repository.

## Usage

There are both code and script examples of how to use this code in the `sample` directory.
That directory also contains some sample results from the main scoring function `analyze_plan()`.
The samples use data from the companion `rdabase` repo.

## Notes

With four exceptions, `analyze_plan()` computes all the analytics that DRA does:

-   For a variety of reasons, DRA's production TypeScript package 
    [dra-analytics](https://github.com/dra2020/dra-analytics) 
    does not calculate a few minor things that show up in the UI. 
    The Python port [rdapy](https://github.com/dra2020/rdapy) does not either.
    This repo uses the latter, so those few things also aren't in the "scorecard" output.
-   To keep the results simple, district-level results are suppressed. The scorecard is a simple flat
    dictionary of metric key/value pairs.
-   To maximize throughput KIWYSI compactness is not calculated. The simple naive approach to performing
    compactness calculations is to dissolve precinct shapes into district shapes, but dissolve is very
    expensive operation. Analyzing a congressional plan for North Carolina take ~60 seconds. A much 
    faster approach is to convert precinct shapes into topologies using TopoJSON like DRA does and then
    merging precincts into district shapes. That approach takes ~5 seconds, virtually all of the time
    being calling TopoJSON `merge()` from Python and marshalling the result back from JavaScript. I could
    have chosen to implement a Python native version of `merge()`. Instead, I chose to skip KIWYSI 
    compactness (which requires actual district shapes) and just calculate the two main compactness
    metrics in DRA: Reock and Polsby-Popper. Together these only depend on district area, perimeter, and
    diameter, and with some pre-processing once per state (analogous to converting shapes into a topology)
    these values can be imputed without ever creating the district shapes. The result is that analyzing
    a congressional plan for North Carolina &#8212; calculating *all* the analytics &#8212; takes a small fraction
    of a second.
-   Finally, we've already created the precinct contiguity graphs as part of finding root map candidates
    in our [rdaroot](https://github.com/rdatools/rdaroot) GitHub repo, and,
    by definition, the plans in our ensembles are contiguous.
    Hence, we don't check that.

## Testing

```bash
$ pytest --disable-warnings
```