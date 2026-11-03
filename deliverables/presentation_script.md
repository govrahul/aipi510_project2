# Project 2 presentation script

Nine presented slides with a target duration of 7 minutes 5 seconds, inside the eight minute limit. Slides 5 to 9 were rewritten on November 2 2026 with the new basketball Instagram data and one model fitted the same way in both sports. Slides 10 onward are backup for questions and are not presented. Source references follow each speaking passage; they need not be read aloud. Speaking roles are for the authors to choose.

## Slide 1 Social media and college athlete NIL valuation

25 seconds. Our original motivation was whether social media matters differently in college athlete selection after NIL. We first analyzed the data we actually have: a current football valuation sample. This presentation reports that result and explains why it cannot yet answer the original policy question. The association is positive, but scholarship and policy effects remain unanswered. Sources: project report and reports/deliverables/model_statistics.json, November 1 2026.

## Slide 2 Research questions and hypotheses

50 seconds. The partner plan contains football and basketball slope tests, plus a social by sport interaction. Its within sport alternatives were positive; we report conservative two sided p values. The planned three test family uses alpha 0.05 divided by three, or 0.0167. For the original policy question, the null is zero social by post interaction on a common outcome. A sign change or a change in significance in separate models does not establish a difference. Historical NIL values are absent rather than zero. Source: NCAA history https://www.ncaa.org/about-us/history/ and project report hypotheses.

## Slide 3 Observational design and sampling

50 seconds. The three inherited football files are nested: a frame, a sample, and enriched versions of the same players. They are not 1200 independent observations. The original code uses valuation cutoffs and seed 510. Ties give populations 266, 479 and 255 with draws 25, 50 and 25. This is close to proportional allocation, rather than deliberate oversampling of the highest quarter. For new basketball work, quartiles come from the full available NIL frame before drawing 250 each. That frame is still missing. Weighting can target the frame but cannot recover athletes excluded from it. Source: Data/sample_data.py; scripts/sample_quartiles.py; project report design.

## Slide 4 Power for the social term

45 seconds. We corrected the distinction between overall model power and power for the social term. Partial f squared measures the extra R squared from that term relative to unexplained variation. With eight predictor degrees of freedom, one tested term, target power 80 percent and alpha 0.0167, the planning requirements are 527, 213 and 74 for the three scenarios shown. These assume independent homoskedastic errors. They are not exact power for HC3 or school clustered tests. We did not claim that 100 observations have adequate power merely because the full model fits reasonably well. Source: scripts/power_sensitivity.py and model_statistics.json.

## Slide 5 Transfers rose in both sports after NIL, fastest in basketball

45 seconds. This slide shows how rosters have changed over time in both sports. Each pair of bars is one season: orange is Division I men's basketball, blue is FBS football. Before 2021, only a few percent of any roster had transferred in. Since NIL began in July 2021, that share has climbed every year: to 27 percent in basketball and 16 percent in football. Basketball moved faster. Basketball rosters are small, about 14 players a team against about 115 in football, so each basketball player is far more visible. One caution: NIL arrived together with the one-time transfer rule, so we can't credit the rise to NIL alone. Source: figures/fig7_transfer_rate_by_sport and figure_data/roster_trends.csv.

## Slide 6 In both sports, more followers goes with a higher NIL value

50 seconds. Now NIL value. In each sport we split the 100 players into four equal groups by Instagram followers, and show the typical NIL value in each group. Both sports climb from left to right. In basketball, typical value goes from about 49 thousand dollars for players with the fewest followers to 261 thousand for those with the most, more than five times higher. In football it goes from 379 thousand to 700 thousand. Don't compare the heights of orange against blue directly. The football sample was drawn only from the top 1,000 football NIL values, all at least 350 thousand dollars, while basketball covers the whole market. The pattern within each sport is the point. Typical following also differs: about 2,500 for basketball players and 11,000 for football players. These values are one November 2026 snapshot, so this shows today's pattern, not change over time. Sources: Data/curated/basketball_instagram_100.csv, Data/football_modeling_data.csv, figures/fig8_nil_by_follower_group_by_sport.

## Slide 7 Followers are the strongest factor in both sports

75 seconds. To compare the sports fairly we fit the exact same model in each: NIL value explained by Instagram followers, last-season performance, and years in college. Performance is ranked within each sport, points per game for basketball and the partner's performance score for football, and players with no college stats last season, mostly freshmen, are flagged. Left: twice the followers goes with about 35 percent higher NIL value in basketball and 17 percent in football, holding the other factors fixed. Both are statistically clear. The basketball number looks larger, but the gap between the sports is not quite statistically clear, p 0.08. Right: how much of what the model explains comes from each factor. Followers account for roughly two-thirds in both sports, 64 and 69 percent. Performance accounts for 12 to 20 percent, and years in college the rest. Two honest limits. The model explains only 23 percent of the differences in basketball and 30 percent in football, so most of what drives NIL value is not in our data. And our performance measures are rough: football's performance score has unverified values, and basketball points per game only exists for the 58 players who played last season. Sport type itself can't be tested, because the two samples were drawn from different price ranges. Sources: scripts/make_unified_figures.py, figures/figure_data/unified_model_results.json.

## Slide 8 The follower effect lives at the top of the market

45 seconds. A stress test. If we leave out the 25 highest-valued players in each sport and refit the same model, the follower effect almost disappears: about plus 1 percent in basketball and plus 4 percent in football. So the strong overall result comes mainly from the top of the market, where big audiences and big valuations go together. Among ordinary players, followers barely separate NIL values. We also can't say which comes first. Followers might raise NIL value, famous players might attract both, or the valuation source might use follower counts in its estimates. With one snapshot in time we can't separate these. Source: figures/fig11_follower_effect_top_market.

## Slide 9 Conclusions

40 seconds. Our answer: among the things we could measure, social media following is the strongest factor linked to NIL value in both basketball and football, accounting for about two-thirds of what the model explains, well ahead of last-season performance and years in college. Three cautions. The effect is concentrated among the top-valued players. Most of the variation in NIL value is still unexplained. And this is a single snapshot, so it shows association, not cause. To strengthen the case we would collect follower counts dated before each valuation, verified performance statistics, and draw both sports from the same NIL price range so sport itself can be compared. Sources: project report and figures/figure_data/unified_model_results.json.

## Backup slides (not presented)

- Slide 10: Backup slides
- Slide 11: Followers and NIL are positively associated
- Slide 12: What moves NIL value, and how we checked it
- Slide 13: The follower link comes from the top-valued players
- Slide 14: Recruiting stars don’t line up with NIL value
- Slide 15: Coverage limits the remaining tests
- Slide 16: Rosters changed after July 2021
- Slide 17: A valid before and after comparison
