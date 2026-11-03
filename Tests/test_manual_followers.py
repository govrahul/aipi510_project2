"""Manual reports must not become fabricated browser measurements."""
import sys
from pathlib import Path
import unittest
import pandas as pd

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from import_manual_basketball_followers import merge_manual


class ManualFollowerTests(unittest.TestCase):
    def fixture(self):
        d=pd.DataFrame([dict(athlete_id='fixture:a',Sample_Row=1,Quartile='Q4',Frame_Rank=2,NIL_Valuation_USD=200,
              **{'Player Name':'Athlete A','College':'Fixture U'},Instagram_Followers=971,Instagram_Count_Status='observed_browser_integer_tooltip',Instagram_Username='athlete.a',Username_Verification_URL='https://fixture.edu/a',Instagram_Observed_At='2026-11-02T20:00:00Z'),
            dict(athlete_id='fixture:b',Sample_Row=2,Quartile='Q1',Frame_Rank=90,NIL_Valuation_USD=20,
              **{'Player Name':'Athlete B','College':'Fixture V'},Instagram_Followers=None,Instagram_Count_Status='not_collected',Instagram_Username='old.handle',Username_Verification_URL='https://fixture.edu/b',Instagram_Observed_At=None)])
        m=pd.DataFrame([dict(athlete_id='fixture:a',Player_Name='Athlete A',College='Fixture U',Instagram_Followers=971,Raw_Label='971',Reported_Date='2026-11-02',Source_Reference='user_annotation'),
                        dict(athlete_id='fixture:b',Player_Name='Athlete B',College='Fixture V',Instagram_Followers=0,Raw_Label='0',Reported_Date='2026-11-02',Source_Reference='user_chat')])
        return d,m

    def test_corroboration_missing_dates_zero_and_source_distinction(self):
        d,m=self.fixture();out,actions=merge_manual(d,m)
        self.assertEqual(len(out),2);self.assertEqual([a['action'] for a in actions],['corroborates_existing_count','filled_missing_count'])
        self.assertEqual(out.Instagram_Followers.tolist(),[971,0])
        self.assertEqual(out.Instagram_Count_Provenance.tolist(),['browser_observed','user_reported'])
        self.assertEqual(out.Instagram_Observed_At.iloc[0],d.Instagram_Observed_At.iloc[0])
        self.assertTrue(pd.isna(out.Instagram_Observed_At.iloc[1]));self.assertTrue(pd.isna(out.Instagram_Source_URL.iloc[1]))
        self.assertTrue(pd.isna(out.Instagram_Username.iloc[1]));self.assertEqual(out.Prior_Sourced_Instagram_Username.iloc[1],'old.handle')
        again,_=merge_manual(out,m);self.assertEqual(again.Instagram_Count_Provenance.tolist(),out.Instagram_Count_Provenance.tolist())

    def test_conflicts_and_wrong_identity_are_rejected(self):
        d,m=self.fixture();m.loc[0,'Instagram_Followers']=999
        with self.assertRaisesRegex(ValueError,'conflicts'):merge_manual(d,m)
        d,m=self.fixture();m.loc[1,'College']='Other U'
        with self.assertRaisesRegex(ValueError,'name/school'):merge_manual(d,m)


if __name__=='__main__':unittest.main()
