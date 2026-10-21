# User evaluation

Source: the repository's [evaluation summary](artifacts/user-evaluation-summary.json).
[Data provenance](data-provenance.md) defines the aggregation and cohort limits.
No external workbook is required to reproduce the calculations below.

## Learning scores

The Antutor score cohort contains 25 complete PRE/POST pairs. The two score means
are arithmetic means, not medians. Raw score changes and normalized gains are
separate measures.

| Measure | Result |
|---|---:|
| PRE mean (sample SD) | 3.52 (7.500667) |
| POST mean (sample SD) | 5.92 (8.260952) |
| Mean raw change | +2.40 |
| Paired raw-score t test | t(24)=1.306717, two-sided p=0.203692 |
| Raw-change Cohen's dz | 0.261343 |
| Mean normalized gain (sample SD) | 0.332947 (0.504211) |
| One-sample normalized-gain t test against zero | t(24)=3.301663, two-sided p=0.002999702 |
| Normalized-gain one-sample Cohen's d | 0.660333 |

Normalized gain uses the project score range −30..15:

```text
POST > PRE: g = (POST - PRE) / (15 - PRE)
POST ≤ PRE: g = (POST - PRE) / (PRE + 30)
```

The 25 recorded gains agree with this formula; none has a zero denominator.
The test uses `d = mean(g) / sample_sd(g)` and `t = d × sqrt(n)`.
It reproduces p≈0.003 and d≈0.66 as a test of normalized gain against zero.
The original test specification is not preserved, so this reconstruction does
not establish which procedure was used in the original analysis.

Those values must not be presented as the raw PRE/POST paired-test result.
The paired raw-score test gives p≈0.204, which is not significant at 0.05.
The gain formula uses different denominators for improvement and decline;
the two tests answer different questions.

## Usability survey

The score cohort and survey respondents are not assumed to be the same sample.
All nonmissing ratings are included separately for each question.

| Question | Valid n | Mean / 5 | Ratings ≥4 | Missing |
|---|---:|---:|---:|---:|
| Helpfulness for understanding economic concepts | 32 | 4.21875 → **4.22** | 25/32 = **78.125%** | 0 |
| Appropriateness of scaffolding hints | 31 | 4.096774 → **4.10** | 25/31 = **80.645%** | 1 |

Helpfulness ratings are 3:7, 4:11 and 5:14. Hint ratings are 2:4, 3:2,
4:12 and 5:13. Whether every hint respondent actually received a hint is unknown.
The complete helpfulness distribution yields 4.22, not 4.19. No undocumented
response exclusions or pooling of the two questions are applied.

## Interpretation limits

The concept-reading score cohort has 30 records with mean scores
6.666667 → 7.033333. Random assignment, exclusion criteria and participant linkage
are not established. Neither within-group gains nor the reconstructed tests
establish Antutor's causal superiority or a significant between-group difference.
These are historical evaluation scores, not responses re-scored by the current
application.

## Reproduction

From the repository root:

```sh
python -m pip install -r scripts/evaluation/requirements.txt
python scripts/evaluation/user_evaluation.py
```

The script reads the public aggregate JSON and prints the two tests and survey
statistics. `--summary path/to/summary.json` selects another dataset with the same
schema. The script does not alter the dataset or require private source files.
