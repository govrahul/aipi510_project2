"""Sampling and follower-date tests use synthetic fixtures only."""
from pathlib import Path
import sys
import unittest
from types import SimpleNamespace
import tempfile

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from sample_quartiles import sample_quartiles
from collect_instagram_counts import parse_response, exact_count, run as collect_counts
from build_basketball_nil_sample import build


class QuartileSocialTests(unittest.TestCase):
    def test_full_frame_sampling_is_balanced_ordered_and_reproducible(self):
        frame = pd.DataFrame({'athlete_id': [str(i) for i in range(4004)], 'value': range(4004)})
        full, a, audit = sample_quartiles(frame, 'value', ['athlete_id'])
        _, b, _ = sample_quartiles(frame.sample(frac=1, random_state=2), 'value', ['athlete_id'])
        pd.testing.assert_frame_equal(a, b)
        self.assertEqual(len(full), 4004)
        self.assertEqual(a.Quartile.value_counts().tolist(), [250] * 4)
        self.assertTrue(a.Frame_Rank.is_monotonic_increasing)
        self.assertTrue(a.Sampling_Weight.eq(1001 / 250).all())
        self.assertEqual(a.athlete_id.nunique(), 1000)

    def test_ties_are_flagged_and_incomplete_frames_refused(self):
        data = pd.DataFrame({'id': range(1000), 'metric': 1})
        _, sample, _ = sample_quartiles(data, 'metric', ['id'])
        self.assertTrue(sample.Metric_Tie_Crosses_Quartile.all())
        with self.assertRaises(ValueError):
            sample_quartiles(data.iloc[:999], 'metric', ['id'])
        with self.assertRaises(ValueError):
            sample_quartiles(pd.concat([data, data.iloc[:1]]), 'metric', ['id'])

    def test_follower_zero_preserved_and_rounded_count_rejected(self):
        payload = {'business_discovery': {'username': 'example', 'id': '1', 'followers_count': 0}}
        result = parse_response(payload, 'meta', 'example', '2026-11-01T12:00:00Z')
        self.assertEqual(result['Instagram_Followers'], 0)
        with self.assertRaises(ValueError):
            exact_count('12.3K')
        with self.assertRaisesRegex(ValueError, 'historical'):
            parse_response(payload, 'meta', 'example', '2026-11-01', '2018-12-01')

    def test_historical_counts_never_take_future_observations(self):
        payload = {'status': {'success': True}, 'data': {'id': {'username': 'example'},
            'daily': [{'date': '2018-05-01', 'followers': 10}, {'date': '2018-06-01', 'followers': 100}]}}
        result = parse_response(payload, 'socialblade', 'example', '2026-11-01', '2018-05-15', 30)
        self.assertEqual(result['Instagram_Followers'], 10)
        with self.assertRaises(ValueError):
            parse_response(payload, 'socialblade', 'wronguser', '2026-11-01', '2018-05-15')
        with self.assertRaises(ValueError):
            parse_response(payload, 'socialblade', 'example', '2026-11-01', '2017-01-01')

    def test_nil_sampling_precedes_performance_missingness(self):
        frame = pd.DataFrame({'Player Name': [f'Player {i}' for i in range(1000)],
                              'College': 'Example', 'Position': 'G', 'Valuation': ['$100K'] * 1000})
        frame.loc[0, 'Valuation'] = '$0'
        performance = pd.DataFrame([{'athlete_id': 1, 'Player_Name': 'Player 0',
                                    'College': 'Example', 'Position': 'G', 'Points_Per_Game': 5}])
        result, audit = build(frame, performance)
        self.assertEqual(len(result), 1000)
        self.assertEqual(result.Quartile.value_counts().tolist(), [250] * 4)
        self.assertEqual(result.Performance.notna().sum(), 1)
        self.assertEqual(result.Match_Status.eq('unmatched').sum(), 999)
        self.assertEqual(result.NIL_Valuation_USD.min(), 0)

    def test_historical_rows_are_retained_without_filling_current_counts(self):
        with tempfile.TemporaryDirectory() as name:
            folder = Path(name)
            source, output = folder/'input.csv', folder/'output.csv'
            pd.DataFrame({'athlete_id':['1','2'], 'Quartile':['Q4_Highest','Q1_Lowest'],
                'Period':['Pre_NIL','Pre_NIL'], 'Instagram_Username':['example1','example2'],
                'Username_Verification_URL':['https://example.org/a','https://example.org/b']}).to_csv(source,index=False)
            collect_counts(SimpleNamespace(input=source,output=output,provider='meta',env_file=None,
                responses_dir=folder,max_profiles=10,max_lag_days=30,allow_paid_requests=False))
            result=pd.read_csv(output)
            self.assertEqual(result.Quartile.tolist(),['Q4_Highest','Q1_Lowest'])
            self.assertTrue(result.Instagram_Followers.isna().all())
            self.assertTrue(result.Instagram_Collection_Note.str.contains('explicit Instagram_Target_Date').all())


if __name__ == '__main__':
    unittest.main()
