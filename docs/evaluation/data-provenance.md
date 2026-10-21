# Evaluation data provenance

The repository keeps public evaluation aggregates and a historical benchmark
chart. Deployment settings are preserved separately as a normalized configuration
record. These artifacts contain no learner identities, free-text responses,
server addresses or credentials.

| Artifact | Representation | Reproduction scope |
|---|---|---|
| [User evaluation summary](artifacts/user-evaluation-summary.json) | Score moments and survey rating frequencies from project evaluation records | Recompute means, t statistics, p values, effect sizes and response proportions |
| [Historical cache chart](artifacts/semantic-cache-historical.png) | Original Git image, unchanged | Read the two reported timings and recompute their relative reduction |
| [Historical GPU configuration](../deployment/gcp-vllm-historical.json) | Normalized hardware, server and client settings from project operating records | Inspect the documented deployment configuration; not replay an exact historical run |

## User evaluation aggregates

The Antutor score cohort contains all 25 complete PRE/POST pairs in the evaluation
score table. Blank rows and a summary formula are excluded. A separate headerless
10-row table is excluded because its cohort membership and overlap are unknown.
The concept-reading cohort contains 30 scored records; formatting-only rows are
excluded. The selection linking these records to the broader survey is unknown.
No participant linkage between score cohorts and usability responses is assumed.

For each score measure, the public data retain `n`, the arithmetic mean and the
sample standard deviation (`ddof=1`). The paired raw-change standard deviation is
computed from individual POST−PRE differences, not from independent group SDs.
Normalized gains use the asymmetric formula documented in
[user-evaluation.md](user-evaluation.md). Survey data retain counts at each rating
and the number of missing responses. They do not combine distinct questions.

Aggregation removes row-level scores, identifiers, timestamps and free text.
It preserves enough statistics for the stated calculations but does not expose
individual pairing, validate the original scoring or establish cohort selection.
Public reproduction therefore covers calculations from the aggregates, not an
independent audit of individual responses.

## Historical cache chart

The PNG is byte-identical to
[`performance_test/cache_optimization_result.png` at `1c5e5ba`](https://github.com/tangerineYR/antutor/blob/1c5e5ba/performance_test/cache_optimization_result.png).
SHA-256: `43746231a32d009a7be59f6a8d9f479fa9aafd96ebd5e6752b313baee06862d4`.
Its timing labels are integer milliseconds. No timing samples or successful-run
manifest accompany the image; see [measurement limits](semantic-cache-historical.md).

## Historical GPU configuration

[gcp-vllm-historical.json](../deployment/gcp-vllm-historical.json) consolidates the
recorded L4 hardware and subsequent 14B server/client settings. It preserves the
model identifier and inference options while omitting credentials and addresses.
The earlier 8B stage remains identified separately. Unknown model revisions and
image digests are `null`; no release pin or execution timestamp is invented.
This is a curated configuration record, not independent proof of a running server.
