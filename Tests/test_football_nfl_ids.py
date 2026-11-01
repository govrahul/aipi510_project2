import sys
import unittest
from pathlib import Path
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from enrich_football_nfl_ids import supplement


class FootballIDTests(unittest.TestCase):
    def fixture(self):
        frame=pd.DataFrame([dict(athlete_id='123',Player_Name='Alex Athlete',College='Earlier Transfer School',
            Draft_Year=None,Draft_Round=None,Draft_Overall_Pick=None)])
        players=pd.DataFrame([dict(espn_id='123',display_name='Alex Athlete',pfr_id='AthlAl01',gsis_id='00-00001',
            rookie_season=2019,last_season=2025,draft_year=2019,draft_round=1,draft_pick=10)])
        picks=pd.DataFrame([dict(pfr_player_id='AthlAl01',season=2019,round=1,pick=10)])
        return frame,players,picks

    def test_id_join_handles_transfer_school_without_fuzzy_names(self):
        frame,players,picks=self.fixture()
        result=supplement(frame,players,picks,2018)
        self.assertEqual(result.Draft_Overall_Pick.iloc[0],10)
        self.assertEqual(result.Draft_Status.iloc[0],'exact_ESPN_ID_name_and_PFR_draft_record')
        self.assertEqual(len(result),len(frame))

    def test_name_and_duplicate_id_conflicts_remain_unresolved(self):
        frame,players,picks=self.fixture()
        players.loc[0,'display_name']='Different Athlete'
        result=supplement(frame,players,picks,2018)
        self.assertTrue(pd.isna(result.Draft_Round.iloc[0]))
        self.assertIn('name_disagreement',result.NFL_ID_Match_Status.iloc[0])
        result=supplement(frame,pd.concat([players,players]),picks,2018)
        self.assertIn('duplicate',result.NFL_ID_Match_Status.iloc[0])

    def test_pro_history_predating_cohort_is_flagged_not_used_as_future_outcome(self):
        frame,players,picks=self.fixture()
        result=supplement(frame,players,picks,2025)
        self.assertTrue(pd.isna(result.Draft_Round.iloc[0]))
        self.assertIsNotNone(result.NFL_College_Identity_Timing_Flag.iloc[0])

    def test_draft_source_conflict_is_explicit_and_not_overwritten(self):
        frame,players,picks=self.fixture()
        frame.loc[0,['Draft_Year','Draft_Round','Draft_Overall_Pick']]=[2019,2,40]
        result=supplement(frame,players,picks,2018)
        self.assertEqual(result.Draft_Overall_Pick.iloc[0],40)
        self.assertEqual(result.Draft_Status.iloc[0],'conflicting_outcome_sources_needs_review')


if __name__=='__main__': unittest.main()
