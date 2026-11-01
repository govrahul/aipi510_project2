"""Synthetic aggregation contracts; these fixtures are not athlete observations."""
import importlib.util
from pathlib import Path
import unittest

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('open_stats', ROOT / 'scripts/collect_basketball_open_stats.py')
stats = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stats)


def row(game, athlete=1, team=10, points=0, dnp=False, date='2026-01-01'):
    result = dict.fromkeys(stats.STATS, 0.0)
    result.update(season=2026, season_type=2, game_date=date, game_id=game,
                  athlete_id=athlete, team_id=team, athlete_display_name='Synthetic Player',
                  team_location='Example', athlete_position_abbreviation='G',
                  did_not_play=dnp, starter=False, points=points, minutes=0 if dnp else 12)
    return result


def membership():
    return pd.DataFrame([dict(league='mbb', season=2026, team_id='10', team_id_source='espn',
                              subdivision_id='mbb:d1', conference_id='mbb:example')])


class BasketballCollectionTests(unittest.TestCase):
    def test_dnp_and_missingness_do_not_become_performance_zeros(self):
        data = pd.DataFrame([row(1, points=10), row(2, points=0), row(3, dnp=True),
                             row(1, athlete=2, dnp=True), row(1, athlete=3, points=None)])
        result, audit = stats.summarize(data, membership(), 2026, '2026-10-31')
        result = result.set_index('athlete_id')
        self.assertEqual(result.loc[1, 'Games'], 2)
        self.assertEqual(result.loc[1, 'Points_Per_Game'], 5)
        self.assertEqual(result.loc[2, 'Games'], 0)
        self.assertTrue(pd.isna(result.loc[2, 'Points_Per_Game']))
        self.assertTrue(pd.isna(result.loc[3, 'points']))
        self.assertTrue(pd.isna(result.loc[1, 'FG_Pct']))
        self.assertEqual(audit['dnp_rows_excluded_from_game_denominators'], 2)

    def test_duplicate_player_game_is_rejected(self):
        data = pd.DataFrame([row(1), row(1)])
        with self.assertRaisesRegex(ValueError, 'Duplicate player-game'):
            stats.summarize(data, membership(), 2026, '2026-10-31')

    def test_dates_and_membership_are_season_specific(self):
        data = pd.DataFrame([row(1, points=4), row(2, points=100, date='2026-11-05'),
                             row(1, athlete=5, team=99)])
        result, audit = stats.summarize(data, membership(), 2026, '2026-10-31')
        self.assertEqual(audit['excluded_by_date_or_season_type'], 1)
        self.assertEqual(audit['division_i_player_team_rows'], 1)
        self.assertEqual(result.loc[result.athlete_id.eq(1), 'Points_Per_Game'].iloc[0], 4)
        bad = membership().assign(season=2025)
        with self.assertRaisesRegex(ValueError, 'seasons differ'):
            stats.summarize(data, bad, 2026, '2026-10-31')

    def test_same_names_and_transfer_ids_stay_separate(self):
        data = pd.DataFrame([row(1, athlete=1, team=10, points=2),
                             row(2, athlete=1, team=11, points=8),
                             row(1, athlete=2, team=10, points=20)])
        result, audit = stats.summarize(data, membership(), 2026, '2026-10-31')
        self.assertEqual(len(result), 3)
        self.assertEqual(audit['athlete_ids_on_multiple_teams'], 1)


if __name__ == '__main__':
    unittest.main()
