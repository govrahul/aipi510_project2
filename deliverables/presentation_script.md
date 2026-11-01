# Project 2 presentation script

Nine slides with a target duration of 7 minutes 5 seconds. Rehearse aloud and leave room within the eight minute limit. Source references follow each speaking passage; they need not be read aloud. Speaking roles are for the authors to choose.

## Slide 1 Social media and college athlete NIL valuation

25 seconds. Our original motivation was whether social media matters differently in college athlete selection after NIL. We first analyzed the data we actually have: a current football valuation sample. This presentation reports that result and explains why it cannot yet answer the original policy question. The association is positive, but scholarship and policy effects remain unanswered. Sources: project report and reports/deliverables/model_statistics.json, November 1 2026.

## Slide 2 Research questions and hypotheses

50 seconds. The partner plan contains football and basketball slope tests, plus a social by sport interaction. Its within sport alternatives were positive; we report conservative two sided p values. The planned three test family uses alpha 0.05 divided by three, or 0.0167. For the original policy question, the null is zero social by post interaction on a common outcome. A sign change or a change in significance in separate models does not establish a difference. Historical NIL values are absent rather than zero. Source: NCAA history https://www.ncaa.org/about-us/history/ and project report hypotheses.

## Slide 3 Observational design and sampling

50 seconds. The three inherited football files are nested: a frame, a sample, and enriched versions of the same players. They are not 1200 independent observations. The original code uses valuation cutoffs and seed 510. Ties give populations 266, 479 and 255 with draws 25, 50 and 25. This is close to proportional allocation, rather than deliberate oversampling of the highest quarter. For new basketball work, quartiles come from the full available NIL frame before drawing 250 each. That frame is still missing. Weighting can target the frame but cannot recover athletes excluded from it. Source: Data/sample_data.py; scripts/sample_quartiles.py; project report design.

## Slide 4 Power for the social term

45 seconds. We corrected the distinction between overall model power and power for the social term. Partial f squared measures the extra R squared from that term relative to unexplained variation. With eight predictor degrees of freedom, one tested term, target power 80 percent and alpha 0.0167, the planning requirements are 527, 213 and 74 for the three scenarios shown. These assume independent homoskedastic errors. They are not exact power for HC3 or school clustered tests. We did not claim that 100 observations have adequate power merely because the full model fits reasonably well. Source: scripts/power_sensitivity.py and model_statistics.json.

## Slide 5 Followers and NIL are positively associated

65 seconds. The chart is descriptive and unadjusted. The coefficient beside it comes from the replicated multiple regression with the inherited controls. HC3 gives beta 0.207, a 95 percent interval from 0.079 to 0.335, and a two sided p value 0.00155. At alpha 0.0167 it is below the planned threshold; the family adjusted 98.33 percent interval is 0.050 to 0.363. At sufficiently large follower counts, doubling corresponds to about 15.4 percent higher modeled valuation, with a 95 percent interval about 5.6 to 26.1 percent. This is not an effect of acquiring followers. The inherited performance variable is unverified, and valuation may itself use social audience information. Chart coordinates are rounded to 12 significant digits for Excel portability; model calculations retain full precision. Source: inherited public football CSV and aggregate model_statistics.json.

## Slide 6 Model and influence checks

55 seconds. We retained the inherited model only as a replication benchmark. The alternative drops unverified PPA and a nearly constant conference flag, centers stars, includes both constituent main effects and the freshman interaction, and groups positions to avoid sparse cells. The positive coefficient persists, including the largest account omission and school clustered sensitivity with 39 clusters. Those checks address some uncertainty and influence concerns; they do not fix selection or confounding. Breusch Pagan p is 0.000373 in the alternative; nine Cook distance flags warrant review. The full raw correlation falls from 0.623 to 0.164 without the largest account. We did not choose a specification by its significance or delete that player from the main fit. Source: reports/eda and model_statistics.json.

## Slide 7 Coverage limits the remaining tests

55 seconds. We collected historical and current basketball and football source frames and career crosswalks. Basketball BPM has broad coverage, but about half the roster rows satisfy the provider qualification flag. Low minute rows have more extreme values; the metric is model derived and needs calibration review. In historical football, recruiting candidate availability is very different between FBS and FCS, so complete case selection changes the population. We do not yet have verified high school classification in those frames. Roughly 63 percent of 2018 athletes also occur in 2019 in each sport, which requires dependence aware analysis. Draft no match is unknown, and current careers have less follow up. Source: reports/eda/README.md and supporting coverage tables.

## Slide 8 A valid before and after comparison

45 seconds. To study the original question, we need the same outcome and eligible population on both sides of July 2021. If the outcome is an offer, we need documented offers and credible non offers, not absence of a public report. Followers must precede the decision. Current followers cannot reconstruct historical reach, and historical NIL values cannot be coded as zero. Sampling current players by NIL and historical players by stars also changes the target population. The interaction delta directly tests the change in association. Calendar changes, COVID and other policies still prevent an automatic causal NIL interpretation. Source: docs/research_design.md; scripts/analyze_prepost.py; project report recommendations.

## Slide 9 Conclusions and next steps

35 seconds. Our completed analysis supports a positive association in the selected football sample. It does not show that NIL changed scholarship decisions or that social popularity outweighs athletic ability. The next practical steps are validating football measurement timing and performance, completing basketball NIL and social collection, and defining one historical outcome with comparable sampling and follow up. The repository includes the collection code, aggregate results and a context README for partner review. We can present the completed observational result while being explicit about the comparisons that remain unanswered. Sources: project report and https://github.com/govrahul/aipi510_project2/pull/4.
