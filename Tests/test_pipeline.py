"""Offline contract tests. Synthetic fixtures are NOT project observations."""
import importlib.util
from pathlib import Path
import unittest
import numpy as np
import pandas as pd
from statsmodels.stats.power import FTestPowerF2

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


collector = load('collect_performance')
sampling = load('prepare_sample')
prepost = load('analyze_prepost')
power = load('power_sensitivity')


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.sample = pd.DataFrame([
            {'Player Name': 'Exact Player', 'College': 'Duke', 'Position': 'QB'},
            {'Player Name': 'Different Player', 'College': 'Duke', 'Position': 'QB'},
            {'Player Name': 'Defender', 'College': 'Duke', 'Position': 'CB'}])
        self.records = [{'name': 'Exact Player', 'team': 'Duke', 'position': 'QB',
                         'season': 2025, 'id': '1', 'averagePPA': {'all': 0.0}},
                        {'name': 'Defender', 'team': 'Duke', 'position': 'WR',
                         'season': 2025, 'id': '2', 'averagePPA': {'all': .7}}]

    def test_missing_stays_missing_and_observed_zero_survives(self):
        frame = collector.records_to_frame(self.records, 'football', 2025)
        result = collector.join_sample(self.sample, frame, 'football')
        self.assertEqual(result.loc[0, 'Performance'], 0.0)
        self.assertTrue(pd.isna(result.loc[1, 'Performance']))
        self.assertTrue(pd.isna(result.loc[2, 'Performance']))
        self.assertEqual(result.loc[2, 'Match_Status'], 'metric_not_applicable')

    def test_wrong_team_and_duplicate_identity_do_not_match(self):
        frame = collector.records_to_frame(self.records, 'football', 2025)
        result = collector.join_sample(self.sample.assign(College='Kansas'), frame, 'football')
        self.assertTrue(result.Performance.isna().all())
        result = collector.join_sample(self.sample, pd.concat([frame, frame]), 'football')
        self.assertEqual(result.loc[0, 'Match_Status'], 'ambiguous')

    def test_basketball_schema_and_missing_metric(self):
        records = [{'name': 'Example Athlete', 'team': 'Duke', 'position': 'G',
                    'season': 2025, 'athleteId': 123, 'PORPAG': None}]
        frame = collector.records_to_frame(records, 'basketball', 2025)
        sample = pd.DataFrame([{'Player Name': 'Example Athlete', 'College': 'Duke', 'Position': 'G'}])
        result = collector.join_sample(sample, frame, 'basketball')
        self.assertEqual(result.loc[0, 'Match_Status'], 'metric_missing')
        with self.assertRaises(ValueError):
            collector.records_to_frame(records, 'basketball', 2024)

    def test_sampling_is_reproducible_and_preserves_rank_strata(self):
        frame = pd.DataFrame({'Player Name': [f'Player {i:04}' for i in range(1000)],
                              'College': 'Example', 'Position': 'G', 'Conference': 'ACC',
                              'Grade': 'Senior', 'Valuation': '$100K'})
        population, a = sampling.prepare(frame)
        _, b = sampling.prepare(frame)
        pd.testing.assert_frame_equal(a, b)
        self.assertEqual(a.Valuation_Tier.value_counts().to_dict(),
                         {'Middle_50': 50, 'Top_25': 25, 'Bottom_25': 25})
        self.assertEqual(len(a.drop_duplicates(['Player Name', 'College'])), 100)
        self.assertEqual(population.raw_val.unique().tolist(), [100000.0])
        for invalid in ['', 'unknown', '$0', '-1', None]:
            with self.assertRaises(ValueError):
                sampling.parse_valuation(invalid)

    @staticmethod
    def synthetic_decisions():
        rng = np.random.default_rng(510)
        n = 400
        years = rng.integers(2017, 2025, n)
        followers = rng.integers(100, 10000, n)
        performance = rng.normal(size=n)
        probability = np.clip(.3 + .08 * (years > 2021) + .05 * performance, .05, .95)
        return pd.DataFrame(dict(athlete_id=[str(i) for i in range(n)], sport='football',
            school=rng.choice(['Example A', 'Example B', 'Example C'], n),
            position=rng.choice(['QB', 'WR'], n), decision_date=[f'{y}-02-01' for y in years],
            followers=followers, follower_observed_at=[f'{y-1}-12-01' for y in years],
            athletic_score=performance, performance_observed_at=[f'{y-1}-11-01' for y in years],
            scholarship_offer=rng.binomial(1, probability),
            decision_source_url='https://example.org/decision',
            social_source_url='https://example.org/social',
            performance_source_url='https://example.org/performance'))

    def test_prepost_rejects_leakage_and_selected_only_outcomes(self):
        data = self.synthetic_decisions()
        bad = data.copy()
        bad.loc[0, 'follower_observed_at'] = '2030-01-01'
        with self.assertRaisesRegex(ValueError, 'look-ahead'):
            prepost.validate(bad)
        with self.assertRaisesRegex(ValueError, 'non-offered'):
            prepost.validate(data.assign(scholarship_offer=1))
        with self.assertRaisesRegex(ValueError, 'Both pre-'):
            prepost.validate(data.loc[pd.to_datetime(data.decision_date).dt.year < 2021])

    def test_prepost_interaction_uses_clustered_inference(self):
        fitted = prepost.fit(self.synthetic_decisions())
        self.assertIn('log_followers:post', fitted.params)
        self.assertEqual(fitted.cov_type, 'cluster')
        self.assertEqual(int(fitted.nobs), 400)

    def test_partial_power_matches_statsmodels_and_increases(self):
        expected = FTestPowerF2().power(effect_size=.15, df_num=1, df_denom=93,
                                        alpha=.05/3, ncc=6)
        self.assertAlmostEqual(power.power(100, 6, .15), expected)
        self.assertGreater(power.required_n(6, .02), power.required_n(6, .15))


if __name__ == '__main__':
    unittest.main()
