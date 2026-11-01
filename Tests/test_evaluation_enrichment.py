import sys
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from collect_evaluation_sources import normalize_nba_draft
from collect_recruiting import normalize_recruits
from enrich_player_evaluations import recruiting_sample, attach_recruit, attach_draft, apply_reviewed_events, join_evaluation_to_nil


class EvaluationTests(unittest.TestCase):
    def test_high_school_classification_and_unrated_not_zero(self):
        records=[dict(id='1',year=2016,name='A',stars=0,rating=0,recruitType='HighSchool'),
                 dict(id='2',year=2016,name='B',stars=5,rating=.99,recruitType='JUCO')]
        frame=normalize_recruits(records,'football',2016)
        self.assertEqual(len(frame),1)
        self.assertTrue(frame.Recruit_HS_Verified.iloc[0])
        self.assertTrue(pd.isna(frame.Recruit_Stars.iloc[0]))
        with self.assertRaises(ValueError): normalize_recruits(records,'football',2018)

    def test_star_sampling_excludes_unverified_and_orders_stars_before_rating(self):
        frame=pd.DataFrame(dict(athlete_id=[str(i) for i in range(1200)],team_id='1',
            Recruit_Stars=[5]*300+[4]*300+[3]*300+[2]*300,
            Recruit_Rating=[.1]*300+[.9]*900,Recruit_HS_Verified=True,Recruit_Provider='one_scale'))
        frame.loc[1199,'Recruit_HS_Verified']=False
        sample,audit=recruiting_sample(frame)
        self.assertEqual(len(sample),1000)
        self.assertEqual(set(sample.Quartile.value_counts()),{250})
        self.assertNotIn('1199',sample.athlete_id.values)
        self.assertEqual(sample.Recruit_Stars.iloc[0],5)
        frame['Recruit_HS_Verified']=False
        sample,audit=recruiting_sample(frame)
        self.assertIsNone(sample)
        self.assertEqual(audit['eligible'],0)

    def test_recruit_class_is_not_roster_year_and_ambiguous_stays_missing(self):
        player=dict(Player_Name='Athlete',College='School',team_id='9')
        key=('football','athlete','school')
        records=[dict(Recruit_Class_Year=2016,Recruit_Stars=4,Recruit_HS_Verified=True)]
        result=attach_recruit(player,'football',2018,{key:records},{})
        self.assertEqual(result['Recruit_Class_Year'],2016)
        result=attach_recruit(player,'football',2015,{key:records},{})
        self.assertIsNone(result['Recruit_Stars'])
        result=attach_recruit(player,'football',2018,{key:records*2},{})
        self.assertEqual(result['Recruit_Match_Status'],'ambiguous_official_identity')

    def test_draft_no_match_is_unknown_and_future_outcome_rejected(self):
        player=dict(Player_Name='Athlete',College='School')
        key=('football','athlete','school')
        future=dict(Draft_Year=2027,Draft_Round=1)
        result=attach_draft(player,'football',2026,{key:[future]},'2026-11-01')
        self.assertIsNone(result['Draft_Round'])
        self.assertIsNone(result['Overseas_Professional_Contract'])
        self.assertIsNone(result['College_Years_Total'])
        self.assertIn('unknown',result['Draft_Status'])

    def test_nba_asset_year_offset_and_secondary_disagreement(self):
        stats=pd.DataFrame(dict(season=[2020],player_name=['Athlete'],overall_pick=[5],round_number=[1]))
        espn=pd.DataFrame(dict(season=[2019],athlete_display_name=['Athlete'],overall_pick=[4],round=[1]))
        result=normalize_nba_draft(stats,espn,2019)
        self.assertEqual(result.Draft_Year.iloc[0],2019)
        self.assertFalse(result.Draft_Source_Agreement.iloc[0])
        with self.assertRaises(ValueError): normalize_nba_draft(stats,espn,2020)

    def test_nil_evaluation_join_keeps_quartiles_and_unmatched_rows(self):
        sample=pd.DataFrame(dict(Quartile=['Q4_Highest','Q1_Lowest'],Match_Status=['unmatched','exact_name_team'],
            Performance_API_ID=['1','1'],Performance_Team=['School','School']))
        evaluations=pd.DataFrame(dict(athlete_id=['1'],College=['School'],College_Box_BPM=[3.5]))
        result=join_evaluation_to_nil(sample,evaluations)
        self.assertEqual(result.Quartile.tolist(),sample.Quartile.tolist())
        self.assertTrue(pd.isna(result.College_Box_BPM.iloc[0]))
        self.assertEqual(result.College_Box_BPM.iloc[1],3.5)
        self.assertEqual(len(result),2)

    def test_reviewed_contract_preserves_observation_date_precision(self):
        data=pd.DataFrame(dict(Sport=['basketball'],athlete_id=['1'],Overseas_Professional_Contract=[None],
            Overseas_Contract_Status=[None],Overseas_Club=[None],Overseas_League=[None],
            Overseas_Contract_Date=[None],Overseas_Contract_Observed_By=[None],Overseas_Evidence_URL=[None]))
        event=dict(Sport='basketball',athlete_id='1',Event_Type='overseas_professional_contract',
            Event_Date='2026-11-01',Event_Date_Precision='observed_by',Evidence_URL='https://league.example/contract',Identity_Verified=True)
        result=apply_reviewed_events(data,pd.DataFrame([event]),'2026-11-01')
        self.assertTrue(result.Overseas_Professional_Contract.iloc[0])
        self.assertIsNone(result.Overseas_Contract_Date.iloc[0])
        event['Event_Date']='2027-01-01'
        with self.assertRaises(ValueError): apply_reviewed_events(data,pd.DataFrame([event]),'2026-11-01')


if __name__=='__main__': unittest.main()
