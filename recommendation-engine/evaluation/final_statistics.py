"""Prespecified paired NDCG comparisons; no tuning or outcome-dependent exclusions."""
import numpy as np
import pandas as pd
from scipy.stats import permutation_test

COHORTS = ('0', '1-4', '5-19', '20+')
COMPARISONS = (('switching_without_genai', 'fixed_hybrid'),
               ('switching_with_genai', 'switching_without_genai'))


def holm(values):
    values = np.asarray(values, dtype=float)
    if values.ndim != 1 or not np.isfinite(values).all() or ((values < 0) | (values > 1)).any():
        raise ValueError('Finite probabilities required')
    order = np.argsort(values, kind='stable')
    adjusted = np.minimum(1, np.maximum.accumulate(values[order] * np.arange(len(values), 0, -1)))
    result = np.empty_like(values)
    result[order] = adjusted
    return result.tolist()


def analyze(rows, resamples=2000, permutations=9999, seed=42):
    frame = pd.DataFrame(rows)
    reports = []
    for first, second in COMPARISONS:
        left = frame[frame.model == first].set_index('visitorid')
        right = frame[frame.model == second].set_index('visitorid')
        if left.empty or left.index.has_duplicates or right.index.has_duplicates or set(left.index) != set(right.index):
            raise ValueError('Unique matched users required')
        right = right.reindex(left.index)
        if not left.cohort.equals(right.cohort):
            raise ValueError('Paired cohorts must agree')
        if not left.cohort.isin(COHORTS).all():
            raise ValueError('Unknown cohort')
        # Approved proposal H1: 1-19 events; H2: 0-19 events.
        primary_cohorts = ('1-4', '5-19') if first == 'switching_without_genai' else ('0', '1-4', '5-19')
        mask = left.cohort.isin(primary_cohorts)
        left, right = left[mask], right[mask]
        if left.empty:
            raise ValueError('No users in the proposal hypothesis cohorts')
        for data in (left.ndcg.to_numpy(), right.ndcg.to_numpy()):
            if not np.isfinite(data).all() or ((data < 0) | (data > 1)).any():
                raise ValueError('Finite NDCG in [0, 1] required')
        delta = (left.ndcg - right.ndcg).to_numpy()
        groups = [np.flatnonzero(left.cohort.to_numpy() == label) for label in COHORTS]
        groups = [g for g in groups if len(g)]
        weights = np.zeros(len(delta))
        for g in groups:
            weights[g] = 1 / (len(groups) * len(g))
        rng = np.random.default_rng(seed)
        bootstrap = np.mean([rng.choice(delta[g], size=(resamples, len(g))).mean(axis=1) for g in groups], axis=0)
        # Fixed weights retain the equal-cohort statistic under within-user swaps.
        if not np.any(delta) or len(delta) < 2:
            pvalue = 1.0
        else:
            pvalue = float(permutation_test((delta * weights,), np.sum,
                permutation_type='samples', vectorized=False, n_resamples=permutations,
                batch=128, alternative='two-sided', rng=np.random.default_rng(seed)).pvalue)
        reports.append({'first': first, 'second': second, 'users': len(delta),
            'primary_cohorts': list(primary_cohorts),
            'cohort_sizes': {label: int((left.cohort == label).sum()) for label in COHORTS},
            'equal_cohort_mean_ndcg_difference': float(np.sum(delta * weights)),
            'paired_bootstrap_95_percentile_interval': np.quantile(bootstrap, [.025, .975]).tolist(),
            'two_sided_paired_label_swap_p': pvalue,
            'wins': int((delta > 0).sum()), 'ties': int((delta == 0).sum()), 'losses': int((delta < 0).sum())})
    for report, adjusted in zip(reports, holm([r['two_sided_paired_label_swap_p'] for r in reports])):
        report['holm_p'] = adjusted
        report['reject_at_family_alpha_05'] = adjusted < .05
    return {'comparisons': reports, 'seed': seed, 'bootstrap_resamples': resamples,
            'permutation_resamples_max': permutations,
            'limitations': ['Label-swap test assumes exchangeability of paired condition scores under the null.',
                           'Bootstrap intervals are marginal, not multiplicity-adjusted; Holm applies to the two p-values.',
                           'Observed cohorts have equal weight; this is not population-frequency-weighted effectiveness.',
                           'Significance does not establish practical benefit or external validity.']}
