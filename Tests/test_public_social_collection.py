"""Offline parser/design checks; fixtures are not empirical observations."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from collect_public_instagram import parse_public_profile, login_required
from build_basketball_handle_inputs import accepted_profile_links
from collect_instagram_safari import parse_snapshot
from prepare_basketball_social_sample import prepare
from collect_opendorse_instagram import parse_profile


def profile(label,handle='athlete.one'):
    return f'<meta property="og:url" content="https://www.instagram.com/{handle}/"><meta property="og:title" content="Athlete One (@{handle})"><meta property="og:description" content="{label} Followers, 22 Following">'


class PublicSocialTests(unittest.TestCase):
    def test_rounded_count_is_separate_from_displayed_integer(self):
        rounded=parse_public_profile(profile('37K'),'athlete.one')
        self.assertIsNone(rounded['Instagram_Followers'])
        self.assertEqual(rounded['Instagram_Followers_Approx'],37000)
        self.assertEqual(rounded['Instagram_Raw_Label'],'37K')
        exact=parse_public_profile(profile('9,876'),'athlete.one')
        self.assertEqual(exact['Instagram_Followers'],9876)
        self.assertIsNone(exact['Instagram_Followers_Approx'])

    def test_wrong_account_and_login_are_rejected(self):
        with self.assertRaises(ValueError):parse_public_profile(profile('37K','someone.else'),'athlete.one')
        with self.assertRaises(ValueError):parse_public_profile('<title>Login</title>','athlete.one')

    def test_login_shell_detected_even_when_http_is_successful(self):
        html='<meta property="og:title" content="Instagram"><meta name="description" content="Create an account or log in to Instagram">'
        self.assertTrue(login_required(html))
        self.assertFalse(login_required(profile('9,876')))

    def test_safari_tooltip_is_tied_to_the_requested_followers_link(self):
        s=dict(url='https://www.instagram.com/athlete.one/',title='Athlete',metadata=[],followerLinks=[
            dict(href='https://www.instagram.com/athlete.one/followers/',text='12.3K followers',title='',spans=['12,345'])])
        self.assertEqual(parse_snapshot(s,'athlete.one')['Instagram_Followers'],12345)
        s['followerLinks'][0]['href']='https://www.instagram.com/team/followers/'
        with self.assertRaises(ValueError):parse_snapshot(s,'athlete.one')
        s['url']='https://www.instagram.com/accounts/login/'
        with self.assertRaises(ValueError):parse_snapshot(s,'athlete.one')

    def test_named_roster_rejects_team_navigation_and_wrong_sport(self):
        evidence=dict(title="Athlete One - Men's Basketball - Fixture U",url='https://fixture.edu/athlete-one',
            Instagram_Link_Candidates=[dict(username='team',parent_class=['c-navigation__social-links'],context=''),
                dict(username='athlete.one',parent_class=['sidearm-roster-player-social'],context='')])
        result=accepted_profile_links(evidence,{'Player Name':'Athlete One'},Path('.'))
        self.assertEqual([r['username'] for r in result],['athlete.one'])
        evidence['title']="Athlete One - Women's Basketball - Fixture U"
        self.assertEqual(accepted_profile_links(evidence,{'Player Name':'Athlete One'},Path('.')),[])

    def test_opendorse_checks_school_sport_and_null_nickname(self):
        data=dict(firstName='Athlete',lastName='One',nickname=None,sports=["Men's Basketball"],
          currentTeams=['TCU Horned Frogs'],previousTeams=[],instagramUrl='www.instagram.com/athlete.one',instagramReach=1421)
        def html():return '<script id="__NEXT_DATA__">'+json.dumps({'props':{'pageProps':{'initialState':{'profile':{'profileData':data}}}}})+'</script>'
        r=parse_profile(html(),{'Player Name':'Athlete One','College':'TCU'})
        self.assertEqual(r['Instagram_Followers'],1421)
        with self.assertRaises(ValueError):parse_profile(html(),{'Player Name':'Athlete One','College':'Brown'})
        data['sports']=['Football']
        with self.assertRaises(ValueError):parse_profile(html(),{'Player Name':'Athlete One','College':'TCU'})

    def test_opendorse_zero_is_not_assumed_observed(self):
        data=dict(firstName='Athlete',lastName='One',nickname=None,sports=["Men's Basketball"],
          currentTeams=['TCU Horned Frogs'],previousTeams=[],instagramUrl='www.instagram.com/athlete.one',instagramReach=0)
        html='<script id="__NEXT_DATA__">'+json.dumps({'props':{'pageProps':{'initialState':{'profile':{'profileData':data}}}}})+'</script>'
        result=parse_profile(html,{'Player Name':'Athlete One','College':'TCU'})
        self.assertIsNone(result['Instagram_Followers'])
        self.assertEqual(result['Instagram_Count_Status'],'handle_observed_count_missing')

    def test_sample_requires_the_entire_source_frame(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'snapshot.json';p.write_text(json.dumps({'text':'Showing 25 of 5348 athletes','rankingRows':[]}))
            with self.assertRaisesRegex(ValueError,'Incomplete'):prepare(p,Path(temp)/'out')

    def test_sample_keeps_missing_position_and_freezes_balanced_draw(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'snapshot.json'
            rows=[dict(rank=str(i),name=f'Fixture {i}',position=None,college='Fixture U',value=f'${300-i}K',profile_url=f'https://thesideline.co/players/b-{i}-fixture') for i in range(1,201)]
            p.write_text(json.dumps({'url':'https://thesideline.co/nil-tracker/top-players/basketball','text':'Showing 200 of 200 athletes','rankingRows':rows}))
            a=prepare(p,Path(temp)/'out');self.assertEqual(a['sample_rows'],100)
            self.assertEqual(set(a['sample_per_quartile'].values()),{25})
            import pandas as pd
            d=pd.read_csv(Path(temp)/'out/basketball_sideline_sample_100_frozen.csv')
            self.assertTrue(d['Position'].isna().all())
            self.assertTrue(d['Instagram_Followers'].isna().all())
            self.assertTrue(d['Frame_Rank'].is_monotonic_increasing)


if __name__=='__main__':unittest.main()
