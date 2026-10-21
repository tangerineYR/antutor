"""Recompute evaluation statistics from the repository aggregate dataset."""
import argparse
import json
import math
from pathlib import Path

from scipy.stats import t as student_t

ROOT = Path(__file__).resolve().parents[2]
DEFAULT = ROOT / 'docs/evaluation/artifacts/user-evaluation-summary.json'


def one_sample(summary):
    n, avg, sd = summary['n'], summary['mean'], summary['sample_sd']
    effect = avg / sd
    t = effect * math.sqrt(n)
    return {'t': t, 'df': n - 1, 'p_two_sided': float(2 * student_t.sf(abs(t), n - 1)),
            'cohens_d': effect}


def analyze(summary):
    ratings = {}
    for name, data in summary['survey'].items():
        counts = {int(k): v for k,v in data['counts'].items()}
        n = sum(counts.values())
        positive = sum(v for k,v in counts.items() if k >= 4)
        ratings[name] = {'n': n, 'missing': data['missing'],
                         'mean': sum(k*v for k,v in counts.items())/n,
                         'positive_count': positive, 'positive_percent': 100*positive/n}
    return {'antutor_normalized_gain_vs_zero': one_sample(summary['antutor']['normalized_gain']),
            'antutor_paired_raw_score_change': one_sample(summary['antutor']['raw_change']),
            'survey': ratings}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--summary', type=Path, default=DEFAULT,
                        help='Aggregate JSON dataset (defaults to the repository artifact)')
    args = parser.parse_args()
    summary = json.loads(args.summary.read_text())
    print(json.dumps(analyze(summary), indent=2, ensure_ascii=False))
