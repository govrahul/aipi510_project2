"""Guard the requested population cut, locked sample, and reviewed receipts."""
import sys
import tempfile
from pathlib import Path
import unittest
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from prepare_basketball_top1000_social import prepare
from finalize_basketball_top1000_social import merge_receipts,finalize
from import_manual_basketball_followers import merge_manual


class Top1000Tests(unittest.TestCase):
    def test_cut_before_quartiles_and_follower_independent_draw(self):
        with tempfile.TemporaryDirectory() as d:
            d=Path(d);n=1100
            data=pd.DataFrame({'athlete_id':[f'id{i:04}' for i in range(n)],
                'Frame_Rank':range(1,n+1),'NIL_Valuation_USD':range(n,0,-1),
                'Quartile':['legacy']*n,'Player Name':[f'Player{i}' for i in range(n)],
                'College':['Fixture']*n,'Instagram_Followers':[None]*n})
            # A tie across the cutoff must not expand the 1,000-row population.
            data.loc[999:1000,'NIL_Valuation_USD']=101
            source=d/'source.csv';data.to_csv(source,index=False)
            audit=prepare(source,d/'a');a=pd.read_csv(d/'a/basketball_top1000_sample_100_frozen.csv')
            self.assertEqual(audit['input_frame_rows'],1000)
            self.assertEqual(a.groupby('Quartile').size().tolist(),[25]*4)
            bands={'Q4_Highest':(1,250),'Q3_Upper_Middle':(251,500),'Q2_Lower_Middle':(501,750),'Q1_Lowest':(751,1000)}
            for q,(lo,hi) in bands.items():self.assertTrue(a.loc[a.Quartile.eq(q),'NIL_Global_Rank'].between(lo,hi).all())
            self.assertTrue(a.Sampling_Weight.eq(10).all())
            data['Instagram_Followers']=999;data.sample(frac=1,random_state=2).to_csv(source,index=False)
            prepare(source,d/'b');b=pd.read_csv(d/'b/basketball_top1000_sample_100_frozen.csv')
            self.assertEqual(a.athlete_id.tolist(),b.athlete_id.tolist());self.assertTrue(b.Instagram_Followers.isna().all())
            data.loc[0,'Frame_Rank']=9999;data.to_csv(source,index=False)
            with self.assertRaisesRegex(ValueError,'incomplete'):prepare(source,d/'bad')

    def test_repository_receipts_preserve_one_unknown_and_reject_mismatches(self):
        root=Path(__file__).resolve().parents[1];d=root/'replication/basketball_top1000'
        s=pd.read_csv(d/'basketball_top1000_sample_100_frozen.csv');r=pd.read_csv(d/'instagram_count_receipts.csv',dtype={'raw_label':str})
        v=pd.read_csv(d/'identity_reviews.csv');g=pd.read_csv(d/'google_lookup_receipts.csv')
        out=merge_receipts(s,r,v,g)
        self.assertEqual(len(out),100);self.assertEqual(out.Instagram_Followers.count(),99)
        self.assertTrue(out.loc[out.Sample_Row.eq(33),'Instagram_Followers'].isna().all())
        self.assertEqual(out.athlete_id.tolist(),s.athlete_id.tolist())
        completed,actions=merge_manual(out,pd.read_csv(d/'manual_count_reports.csv',dtype={'Raw_Label':str}))
        self.assertEqual(completed.Instagram_Followers.count(),100)
        alex=completed.loc[completed.Sample_Row.eq(33)].iloc[0]
        self.assertEqual(alex.Instagram_Followers,675);self.assertEqual(alex.Instagram_Count_Provenance,'user_reported')
        self.assertTrue(pd.isna(alex.Instagram_Observed_At));self.assertTrue(pd.isna(alex.Instagram_Username))
        bad=r.copy();bad.loc[0,'username']='wrong.account'
        with self.assertRaisesRegex(ValueError,'identity review'):merge_receipts(s,bad,v,g)
        with self.assertRaisesRegex(ValueError,'Duplicate'):merge_receipts(s,pd.concat([r,r.iloc[:1]]),v,g)
        bad=r.copy();bad.loc[0,'raw_label']='42,076'
        with self.assertRaisesRegex(ValueError,'conflicts'):merge_receipts(s,bad,v,g)
        bad=v.copy();bad.loc[[0,1],'athlete_id']=bad.loc[[1,0],'athlete_id'].to_numpy()
        with self.assertRaisesRegex(ValueError,'row/athlete'):merge_receipts(s,r,bad,g)


if __name__=='__main__':unittest.main()
