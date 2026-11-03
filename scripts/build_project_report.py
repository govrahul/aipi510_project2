"""Build the rubric report from checked aggregate results using python-docx.

Run summarize_deliverable_results.py first. Uses no network or private cohort
rows; preserves the partner PDF. The report is also emitted as editable Markdown.
"""
import argparse
import json
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT=Path(__file__).resolve().parents[1]


def build(out):
    stats=json.loads((ROOT/'reports/deliverables/model_statistics.json').read_text())
    a,b,c,e,k=stats['models']
    doc=Document(); sec=doc.sections[0]
    sec.page_width=Inches(8.5);sec.page_height=Inches(11)
    sec.top_margin=sec.bottom_margin=Inches(.65)
    sec.left_margin=sec.right_margin=Inches(.8)
    for name in ['Normal','Title','Subtitle','Heading 1','Heading 2','Caption']:
        s=doc.styles[name];s.font.name='Calibri';s.font.color.rgb=RGBColor(0,0,0)
    for node in list(doc.styles.element.iter(qn('w:pBdr'))): node.getparent().remove(node)
    normal=doc.styles['Normal'];normal.font.size=Pt(10.5)
    normal.paragraph_format.space_after=Pt(6);normal.paragraph_format.line_spacing=1.05
    for name,size in [('Title',24),('Heading 1',17),('Heading 2',12)]:
        doc.styles[name].font.size=Pt(size)
        doc.styles[name].paragraph_format.space_before=Pt(11)
        doc.styles[name].paragraph_format.space_after=Pt(6)
    doc.styles['Caption'].font.size=Pt(9)
    doc.core_properties.title='Social media following and college athlete NIL valuation'
    doc.core_properties.author='Rahul Govil and Sam Teshome'
    doc.core_properties.subject='AIPI 510 Module Project 2 statistical analysis'
    footer=sec.footer.paragraphs[0];footer.alignment=WD_ALIGN_PARAGRAPH.RIGHT
    footer.add_run('AIPI 510  |  ')
    field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE');footer._p.append(field)
    footer.style='Caption'
    md=[]; pending_page=[False]
    def p(text,style=None):
        para=doc.add_paragraph(text,style)
        prev=para._p.getprevious()
        if prev is not None and prev.tag==qn('w:tbl'):para.paragraph_format.space_before=Pt(6)
        md.append(text+'\n')
    def h(text,level=1):
        heading=doc.add_heading(text,level)
        if pending_page[0]: heading.paragraph_format.page_break_before=True;pending_page[0]=False
        md.append('#'*(level+1)+' '+text+'\n')
    def page(): pending_page[0]=True
    def table(headers,rows,widths):
        t=doc.add_table(rows=1,cols=len(headers));t.autofit=False
        for col,width in zip(t.columns,widths):col.width=Inches(width)
        for cell,text in zip(t.rows[0].cells,headers):cell.text=text
        repeat=OxmlElement('w:tblHeader');t.rows[0]._tr.get_or_add_trPr().append(repeat)
        for row in rows:
            for cell,text in zip(t.add_row().cells,row):cell.text=str(text)
        for ri,row in enumerate(t.rows):
            row._tr.get_or_add_trPr().append(OxmlElement('w:cantSplit'))
            for i,cell in enumerate(row.cells):
                cell.width=Inches(widths[i]);cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER;tc=cell._tc.get_or_add_tcPr()
                sh=OxmlElement('w:shd');sh.set(qn('w:fill'),'203C55' if ri==0 else ('F2F5F7' if ri%2 else 'FFFFFF'));tc.append(sh)
                borders=OxmlElement('w:tcBorders')
                for side in ['top','left','bottom','right']:
                    edge=OxmlElement('w:'+side);edge.set(qn('w:val'),'single');edge.set(qn('w:sz'),'4');edge.set(qn('w:color'),'D9D9D9');borders.append(edge)
                tc.append(borders)
                margins=OxmlElement('w:tcMar')
                for side in ['top','left','bottom','right']:
                    z=OxmlElement('w:'+side);z.set(qn('w:w'),'90');z.set(qn('w:type'),'dxa');margins.append(z)
                tc.append(margins)
                for para in cell.paragraphs:
                    para.paragraph_format.space_after=Pt(2);para.paragraph_format.space_before=Pt(2)
                    for run in para.runs:
                        run.font.size=Pt(9);run.bold=ri==0
                        run.font.color.rgb=RGBColor.from_string('FFFFFF' if ri==0 else '000000')
        md.append('| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*len(headers))+' |')
        md.extend('| '+' | '.join(map(str,r))+' |' for r in rows);md.append('')
    def fig(name,caption,width=6.6,base='reports/eda/figures'):
        path=ROOT/base/name
        para=doc.add_paragraph();para.add_run().add_picture(str(path),width=Inches(width))
        para.paragraph_format.space_after=Pt(3)
        p(caption,'Caption');md.append(f'![{caption}](../../{base}/{name})\n')

    u=json.loads((ROOT/'figures/figure_data/unified_model_results.json').read_text()); ub,uf=u['Basketball'],u['Football']
    bo=json.loads((ROOT/'figures/figure_data/basketball_only_model.json').read_text()); bt=bo['terms']
    dg=json.loads((ROOT/'figures/figure_data/unified_model_diagnostics.json').read_text()); db,df,ds=dg['Basketball'],dg['Football'],dg['Football stars']
    sh=lambda r,k: round(r['share_of_explained'][k])
    ph=lambda x,pair: next(r['p_holm'] for r in x['posthoc'] if r['pair']==pair)
    sup=str.maketrans('-0123456789','⁻⁰¹²³⁴⁵⁶⁷⁸⁹')
    fp=lambda v: f"{v:.3f}" if v>=0.001 else (lambda m,e: f"{m} × 10{str(int(e)).translate(sup)}")(*f"{v:.1e}".split('e'))

    doc.add_paragraph('Social media following and college athlete NIL valuation','Title')
    md.append('# Social media following and college athlete NIL valuation\n')
    p('Rahul Govil and Sam Teshome\nAIPI 510 Module Project 2  |  November 2, 2026','Subtitle')

    h('Abstract')
    p(f"Name, image and likeness (NIL) rules now let college athletes earn money from their personal brand, and published NIL valuations are widely quoted. We asked how strongly an athlete's Instagram following is associated with that valuation, and whether the association looks the same in men's basketball and in football. We used two samples of 100 players each: football players drawn from the 1,000 highest football valuations on The Sideline NIL tracker, and Division I men's basketball players drawn evenly from the four value quarters of all 5,348 basketball listings. Our main model applies one ordinary least squares formula to each sport separately: log valuation on log followers, last-season performance and years in college, with HC3 robust standard errors. Doubling a player's followers was associated with about {ub['doubling_pct']:.0f}% higher valuation in basketball (95% CI {ub['doubling_ci'][0]:.0f}% to {ub['doubling_ci'][1]:.0f}%, p < 0.001) and {uf['doubling_pct']:.0f}% in football ({uf['doubling_ci'][0]:.0f}% to {uf['doubling_ci'][1]:.0f}%, p < 0.001). Followers accounted for roughly two thirds of the variation the model explained in both sports, well ahead of performance and experience. The difference between sports was not statistically significant (p = {u['sport_difference_in_follower_slope']['p']:.2f}). We also fitted a separate model for each sport using variables only that sport has. In football, adding recruiting stars, freshman status and position gave a similar {c['doubled_followers_percent']:.0f}% per doubling (p = {c['p_two_sided']:.3f}). In basketball, adding conference changed the picture: players in the five largest conferences were valued about {bt['big_conf']['pct']:.0f}% higher, and the follower effect fell to {bt['ln_f']['pct']:.0f}% and was no longer significant (p = {bt['ln_f']['p']:.2f}). The association is concentrated among the highest-valued players, the main model explains only 23 to 30% of the variation, and the data are a single snapshot, so the results describe association rather than cause.")

    h('Background and Motivation')
    p('The NCAA adopted an interim NIL policy on July 1, 2021 [1]. Since then, athletes have been able to sign endorsement and sponsorship deals, and several companies now publish estimated NIL values for thousands of players. Those estimates matter beyond curiosity. Recruits and families use them to compare offers, collectives use them to set budgets, and the public uses them to judge whether money is following athletic merit or attention.')
    p('Our question sits in the middle of that debate. If valuations mostly track social media reach, then the NIL market rewards audience size, which is only loosely connected to on-field ability. If they mostly track performance and experience, the market looks more like a traditional talent market. We cannot settle which mechanism drives the pattern, but we can measure how large the follower association is, how it compares with the performance measures available to us, and whether it differs between a small-roster sport (basketball, about 14 players per team) and a large-roster sport (FBS football, about 115). An NIL estimate is not a verified payment or a scholarship decision, and we treat it throughout as a published market estimate.')

    h('Null and Alternative Hypotheses')
    p('We tested three pre-specified hypotheses about the follower coefficient β, the change in log valuation per one-unit change in ln(1 + followers):')
    table(['','Null hypothesis','Alternative hypothesis','Result'],[
        ['H1 Football','β football = 0','β football ≠ 0',f"Rejected (p = {uf['p_followers']:.4f})"],
        ['H2 Basketball','β basketball = 0','β basketball ≠ 0',f"Rejected (p = {fp(ub['p_followers'])})"],
        ['H3 Sport difference','β basketball − β football = 0','The two slopes differ',f"Not rejected (p = {u['sport_difference_in_follower_slope']['p']:.3f})"]],[1.25,1.75,1.75,2.05])
    p('All three are tested with the main model, and all three tests are two-sided. Because they form one family, we used a Bonferroni-adjusted significance level of 0.05 / 3 = 0.0167. The original project proposal also asked whether the follower association changed after NIL began (H0: the follower-by-post-2021 interaction equals zero). We could not test that hypothesis, because follower counts from before 2021 and a common outcome measured in both eras are not available. We return to this in the Limitations section.')

    h('Description of Experimental Design')
    p('This is an observational study of secondary data, not a controlled experiment. We did not assign followers, NIL access or any treatment, so the design identifies associations rather than causal effects.')
    table(['Element','How it is handled in this study'],[
        ['Dependent variable','Natural log of the published NIL valuation in US dollars'],
        ['Independent variable of interest','Natural log of 1 + Instagram followers'],
        ['Covariates (main model, both sports)','Last-season performance percentile within sport; flag for no college statistics last season; years in college'],
        ['Covariates (sport-specific models)','Football: centered recruiting stars, freshman, stars × freshman, four position groups. Basketball: points per game, freshman, big conference, forward or center'],
        ['Control conditions','No untreated control group exists. Comparison comes from players with fewer followers within the same sport, from the second sport, and from a refit without the 25 highest-valued players'],
        ['Randomization','Stratified random sampling with seed 510; no random assignment of exposure']],[1.9,4.9])
    p('Football. The partner sample draws 100 players from the 1,000 highest football valuations: 25 from the lowest tier, 50 from the middle tier and 25 from the highest tier, using seed 510. Because rounded valuations tie, the tiers hold 266, 479 and 255 players, so the selection probabilities are 25/266, 50/479 and 25/255, close to proportional. Every sampled football player is valued at $350,000 or more, and 99 of the 100 play in a Power 4 conference. We reran the original script and reproduced all 100 players in the same order.')
    p('Basketball. We collected the full Sideline basketball listing (5,348 players, retrieved November 2, 2026), split it into four equal quarters by NIL rank, and drew 25 players at random from each quarter with seed 510. The sample was frozen before any follower counts were looked up, so the choice of players could not depend on how easy their accounts were to find. Unlike football, the basketball sample covers the whole market.')
    p('Because the football sample is limited to the top of its market and the basketball sample is not, the two samples cannot be pooled to estimate a sport main effect. We compare the slopes within each sport instead.')

    h('Power Analysis')
    p('The partner calculation assumed overall R squared 0.35 and used overall Cohen f squared equal to 0.35 divided by 0.65 or 0.538. Its reported 41 and 46 player requirements concern overall model fit. They do not justify power for one social coefficient or a social by sport interaction. A model can explain substantial variation through other predictors while the social term adds little information.')
    p('We therefore evaluated one added term using partial f squared equal to the difference between full and reduced R squared divided by one minus full R squared. The planning calculation uses a noncentral F distribution with numerator degrees of freedom 1, denominator N minus p minus 1, and noncentrality N times partial f squared. We use eight predictor degrees of freedom excluding the intercept, alpha 0.0167, and target power 0.80. The SciPy based implementation searches integer sample sizes [2].')
    table(['Assumed partial f squared','Required N','Power at N equals 100'],[
        [f"{r['partial_f2']:.2f}",r['required_n'],f"{r['power_at_100']:.3f}"] for r in stats['power']],[2.6,1.6,2.6])
    p('These are sensitivity scenarios rather than estimates of a true effect. The approximation assumes independent homoskedastic errors and a specified design. It is not the power of our HC3 or clustered Wald tests. School and athlete dependence, missingness, unequal selection, measurement error, and additional interaction parameters can increase the required sample. A 1000 player target offers collection capacity but does not by itself establish power for the planned comparison. We do not calculate retrospective observed power as evidence for the reported result.')

    h('Data Collection and Cleaning Procedures')
    p('Football. The football data come from the partner collection, which attributes NIL values to The Sideline [3] and adds Instagram followers, recruiting stars, position, class and PPA per play from public sources. We kept the inherited CSV files unchanged and recorded their SHA-256 hashes. The audit found 41 players with a PPA value of exactly zero and 30 nonzero PPA values for linemen and defenders, for whom an offensive per-play metric does not apply. We therefore treat zero PPA as missing, use PPA only in the replication model and the main model, and leave it out of the football-specific model.')
    p('Basketball. A Safari collection script expanded every public page of the Sideline basketball ranking and saved 108 hashed page snapshots (no login, private API or security workaround). After the sample was frozen, Instagram accounts were matched by name, school and basketball affiliation; team pages, fan pages and same-name non-athletes were rejected. Eighty follower counts were read directly from public profiles in the browser, and Sam supplied the remaining 20 from manual checks, which are labelled user_reported in the data. Last-season points per game (2025 to 2026) came from ESPN box scores via SportsDataverse [4]. Where a player was listed on two teams after a mid-season move, we kept the team where they played the most games. One player with no listed class year was given the sample median.')
    p('Shared cleaning rules. Missing values were never filled with zero. Players with no college statistics last season (42 in basketball and 41 in football, mostly freshmen) were kept and flagged rather than dropped. Performance was converted to a 0 to 100 percentile within each sport so the two sports are on a common scale. We did not infer race or any other demographic attribute from names or photos.')
    p('Raw and cleaned data. Raw inputs are Data/football_top1000.csv, Data/football_sample_100.csv and the partner\'s enriched file, plus the full basketball listing and page snapshots under Data/private/ (kept local because of size and source terms; hashes are in the collection manifests). Cleaned analysis files are Data/football_modeling_data.csv and Data/curated/basketball_instagram_100.csv. Supporting roster frames used for the transfer trend are summarized below.')
    table(['Source frame','Rows','Distinct athletes','Schools'],[
        ['Basketball 2018 to 2019',5590,5562,353],
        ['Basketball 2019 to 2020',5587,5575,353],
        ['Basketball 2025 to 2026',5680,5677,365],
        ['Football fall 2018',23755,23751,216],
        ['Football fall 2019',23985,23966,217],
        ['Football fall 2025',26327,26316,234],
        ['Football fall 2026 (in progress)',26094,26092,235]],[3.2,1.1,1.4,1.1])

    h('Statistical Analysis')
    h('Choice of test and rationale',2)
    p('NIL values and follower counts are both strongly right-skewed, so we modelled the natural log of valuation against ln(1 + followers). On this scale the follower coefficient converts directly to a percentage: doubling followers multiplies valuation by 2^β, so the effect size we report is 100 × (2^β − 1) percent. We used ordinary least squares with HC3 heteroskedasticity-robust standard errors because the residual spread is uneven (see assumption checks below), and HC3 is the most conservative of the standard corrections at n = 100. Each coefficient was tested with a two-sided Wald test.')
    p('Main model. To compare the sports on equal terms, we fitted the same formula to each sport separately (two regressions, 100 players each):')
    p('ln(NIL) = b0 + β·ln(1 + followers) + b1·performance percentile + b2·no-stats flag + b3·years in college + error')
    p('H3 was tested with a pooled model that adds a sport indicator and its interaction with each predictor, again with HC3 errors. To show which factor matters most, we split each model\'s R² among followers, performance and years in college with general dominance analysis, which averages each factor\'s added R² over every order in which it could enter, and bootstrapped this 1,000 times for 95% intervals. Sport-specific models. The main model can only use variables measured in both sports, so we also fitted one model per sport that adds what only that sport has. The football model adds centered recruiting stars, freshman status, their interaction and four position groups, and drops the unverified PPA measure and the near-constant conference indicator (99 of 100 football players are Power 4). The basketball model adds points per game (per 5 points), freshman status, membership in the five largest conferences (ACC, Big Ten, Big 12, SEC, Big East) and a forward-or-center indicator. Football robustness checks (the partner\'s original model, dropping the largest account, and school-clustered errors) are reported as supplementary.')
    h('Results: main model (same formula in each sport)',2)
    table(['','Basketball','Football'],[
        ['N',ub['n'],uf['n']],
        ['Follower β (95% CI)',f"{ub['beta_followers']:.3f} ({ub['ci'][0]:.3f} to {ub['ci'][1]:.3f})",f"{uf['beta_followers']:.3f} ({uf['ci'][0]:.3f} to {uf['ci'][1]:.3f})"],
        ['p value',fp(ub['p_followers']),f"{uf['p_followers']:.4f}"],
        ['Effect per doubling of followers',f"+{ub['doubling_pct']:.0f}% ({ub['doubling_ci'][0]:.0f}% to {ub['doubling_ci'][1]:.0f}%)",f"+{uf['doubling_pct']:.0f}% ({uf['doubling_ci'][0]:.0f}% to {uf['doubling_ci'][1]:.0f}%)"],
        ['Partial f² for followers',f"{db['partial_f2_followers']:.2f}",f"{df['partial_f2_followers']:.2f}"],
        ['Model R² (adjusted)',f"{ub['r2']:.2f} ({db['adj_r2']:.2f})",f"{uf['r2']:.2f} ({df['adj_r2']:.2f})"],
        ['Share of explained R²: followers',f"{sh(ub,'Instagram followers')}% ({ub['share_ci']['Instagram followers'][0]:.0f} to {ub['share_ci']['Instagram followers'][1]:.0f})",f"{sh(uf,'Instagram followers')}% ({uf['share_ci']['Instagram followers'][0]:.0f} to {uf['share_ci']['Instagram followers'][1]:.0f})"],
        ['Share: last-season performance',f"{sh(ub,'Last-season performance')}%",f"{sh(uf,'Last-season performance')}%"],
        ['Share: years in college',f"{sh(ub,'Years in college')}%",f"{sh(uf,'Years in college')}%"],
        ['Without the top 25 players',f"+{ub['without_top_quarter']['doubling_pct']:.0f}% (p = {ub['without_top_quarter']['p']:.2f})",f"+{uf['without_top_quarter']['doubling_pct']:.0f}% (p = {uf['without_top_quarter']['p']:.2f})"]],[2.5,2.15,2.15])
    p(f"Both follower slopes are well below the 0.0167 threshold, so we reject H1 and H2. Partial f² values of {db['partial_f2_followers']:.2f} and {df['partial_f2_followers']:.2f} are medium effects by Cohen's guidelines. The basketball slope is about twice the football slope, but the pooled interaction test gives p = {u['sport_difference_in_follower_slope']['p']:.3f}, so we do not reject H3. Performance was not significant in basketball (p = {ub['pvalues']['perf']:.2f}) and borderline in football (p = {uf['pvalues']['perf']:.3f}); years in college was significant at 0.05 only in basketball (p = {ub['pvalues']['year']:.3f}).")
    fig('fig10_feature_importance.png','Figure 1. Share of the model\'s explained variation in NIL value contributed by each factor, same model in both sports. Lines show 95% bootstrap ranges.',5.4,'figures')
    fig('fig11_follower_effect_top_market.png','Figure 2. Higher NIL value for twice the followers, with all 100 players and without the 25 highest-valued players. Lines show 95% confidence intervals.',5.4,'figures')
    h('Results: sport-specific models',2)
    p('Football-specific model. Adding recruiting stars, freshman status and position barely changes the football follower effect.')
    table(['Football model','N','β','95% CI','p','R²'],[
        ['Football-specific (position groups, HC3)',c['n'],f"{c['coefficient']:.3f}",f"{c['ci95'][0]:.3f} to {c['ci95'][1]:.3f}",f"{c['p_two_sided']:.4f}",f"{c['r_squared']:.3f}"],
        ['Supplementary: partner replication (HC3)',b['n'],f"{b['coefficient']:.3f}",f"{b['ci95'][0]:.3f} to {b['ci95'][1]:.3f}",f"{b['p_two_sided']:.4f}",f"{b['r_squared']:.3f}"],
        ['Supplementary: replication, largest account removed',e['n'],f"{e['coefficient']:.3f}",f"{e['ci95'][0]:.3f} to {e['ci95'][1]:.3f}",f"{e['p_two_sided']:.4f}",f"{e['r_squared']:.3f}"],
        ['Supplementary: school-clustered errors',k['n'],f"{k['coefficient']:.3f}",f"{k['ci95'][0]:.3f} to {k['ci95'][1]:.3f}",f"{k['p_two_sided']:.4f}",f"{k['r_squared']:.3f}"]],[2.8,.4,.6,1.3,.75,.55])
    p(f"In the football-specific model, doubling followers goes with {c['doubled_followers_percent']:.1f}% higher valuation (95% CI {c['doubled_followers_ci95_percent'][0]:.1f}% to {c['doubled_followers_ci95_percent'][1]:.1f}%), close to the {uf['doubling_pct']:.0f}% from the main model. The partner's original model gives {b['doubled_followers_percent']:.1f}%. All four football fits are positive and significant at 0.0167, so the football result does not hinge on one modelling choice or on the one player with more than a million followers. We did not choose a model by its p value or R².")
    fig('fig3_followers_vs_valuation.png','Figure 3. Football (supplementary): higher NIL value for twice the followers under different model choices. Lines show 95% confidence intervals; grey means not significant.',6.4,'figures')
    p(f"Basketball-specific model. Here the extra variables matter a great deal. The model explains {bo['r2']*100:.0f}% of the variation, against {ub['r2']*100:.0f}% for the main model.")
    order=['ln_f','ppg5','freshman','big_conf','frontcourt']
    table(['Basketball term','Effect on NIL value','95% CI','p'],[[bt[t]['label'],f"{bt[t]['pct']:+.0f}%",f"{bt[t]['pct_ci'][0]:+.0f}% to {bt[t]['pct_ci'][1]:+.0f}%",fp(bt[t]['p'])] for t in order],[3.2,1.4,1.5,.7])
    p(f"Players in the five largest conferences ({bo['n_big_conf']} of 100) are valued about {bt['big_conf']['pct']:.0f}% higher than otherwise similar players (median ${bo['median_nil_by_conf']['big']/1e3:.0f}K against ${bo['median_nil_by_conf']['other']/1e3:.0f}K), and conference alone explains {bo['r2_big_conf_only']*100:.0f}% of the variation. They also have more followers (median {bo['median_followers_by_conf']['big']:,.0f} against {bo['median_followers_by_conf']['other']:,.0f}). Once conference is in the model, the follower effect falls to {bt['ln_f']['pct']:+.0f}% per doubling (β = {bt['ln_f']['beta']:.3f}, 95% CI {bt['ln_f']['ci'][0]:.3f} to {bt['ln_f']['ci'][1]:.3f}, p = {bt['ln_f']['p']:.2f}). Freshmen are valued about {abs(bt['freshman']['pct']):.0f}% lower (p = {bt['freshman']['p']:.3f}); points per game and position show no clear effect. In basketball, then, much of the follower association in the main model reflects which conference a player is in. Football could not be checked the same way because nearly every sampled football player is in a Power 4 conference.")
    h('Assumption checks',2)
    p(f"Linearity and influence were checked with residual plots, leverage and Cook's distance. Heteroskedasticity was tested with the Breusch–Pagan test (main model: basketball p = {db['breusch_pagan_p']:.3f}, football p = {df['breusch_pagan_p']:.4f}; football-specific model p = {c['breusch_pagan_p']:.4f}), which is why we used HC3 errors throughout. Residual normality was tested with Jarque–Bera: basketball residuals were consistent with normality (p = {db['jarque_bera_p']:.2f}) but football residuals were not (p = {fp(df['jarque_bera_p'])}), mainly because of a few very high valuations. With n = 100 and robust errors this mostly affects precision rather than bias, but it is one reason we also report the rank-based tests below. Multicollinearity is low: the largest variance inflation factor is {db['max_vif']:.1f} in basketball, {df['max_vif']:.1f} in football and {max(v for kk,v in c['vif'].items() if kk!='Intercept'):.1f} in the football-specific model. Seven basketball and eight football players have Cook's distance above 4/n, and no leverage exceeds {max(db['max_leverage'],df['max_leverage']):.2f}; we kept them, since they are real valuations rather than errors. Independence is the weakest assumption, because players from the same school share a market. The school-clustered football fit (39 schools, supplementary) gives a slightly narrower interval, so clustering does not change the conclusion.")
    h('Post hoc tests',2)
    p(f"As a check that does not rely on the log-linear form, we split each sport into four equal follower groups and compared valuations with a Kruskal–Wallis test, followed by pairwise Mann–Whitney tests with Holm correction. Valuations differed across follower groups in both sports (basketball H = {db['follower_groups_kruskal']['H']:.1f}, p = {db['follower_groups_kruskal']['p']:.3f}, ε² = {db['follower_groups_kruskal']['epsilon_sq']:.2f}; football H = {df['follower_groups_kruskal']['H']:.1f}, p < 0.001, ε² = {df['follower_groups_kruskal']['epsilon_sq']:.2f}). In basketball, the only pair that survives correction is the second-lowest group against the highest (p = {ph(db['follower_groups_kruskal'],'Fewer vs Most'):.3f}). In football, the highest group differs from the two lowest (p < 0.001 and p = {ph(df['follower_groups_kruskal'],'Fewer vs Most'):.3f}) and the lowest differs from the second-highest (p = {ph(df['follower_groups_kruskal'],'Fewest vs More'):.3f}). This matches the regression: the gap is mostly between the most-followed players and everyone else.")
    p(f"The partner\'s draft also compared football valuations by recruiting stars. A Kruskal–Wallis test shows the star groups differ (H = {ds['H']:.1f}, p = {ds['p']:.3f}, ε² = {ds['epsilon_sq']:.2f}), but the Holm-corrected pairs show the difference is 5-star versus 4-star only (p = {ph(ds,'4-star vs 5-star'):.3f}); 3-star players (median ${ds['median']['3-star']/1e3:.0f}K) were not valued below 4-star players (median ${ds['median']['4-star']/1e3:.0f}K). There are only 13 five-star and 17 three-star players, so these comparisons are imprecise.")
    fig('fig8_nil_by_follower_group_by_sport.png','Figure 4. Median NIL value for four equal follower groups in each sport. Football was sampled only from the top 1,000 football valuations ($350,000 and up), so bar heights are not comparable across sports.',6.6,'figures')
    p('Transfers. As context, the share of each season\'s roster made up of players who transferred in rose from 2% in 2016 to 27% in 2026 in basketball, and from 1% to 16% in football over the same years (Figure 5). NIL arrived at the same time as the one-time transfer exception, so this trend cannot be attributed to NIL alone, and we did not test it formally.')
    fig('fig7_transfer_rate_by_sport.png','Figure 5. Share of each season\'s roster made up of players who transferred in, Division I men\'s basketball (orange) and FBS football (blue). The 2026 football season is in progress.',6.6,'figures')

    h('Interpretation of Results')
    p(f"In the main model, Instagram following is the strongest factor we measured in both sports. Doubling a player's followers goes with about {ub['doubling_pct']:.0f}% higher NIL value in basketball and {uf['doubling_pct']:.0f}% in football, and followers account for about two thirds of what the model explains. Last-season performance and years in college add comparatively little. In practical terms, two basketball players with the same scoring and class year, one with 5,000 followers and one with 10,000, would be expected to differ by roughly a third in published valuation.")
    p(f"The sport-specific models qualify this. In football the follower effect holds ({c['doubled_followers_percent']:.0f}% per doubling). In basketball, conference is the dominant factor, and once it is included the follower effect is small and not significant. Big-conference players have both more followers and higher valuations, so the main model partly credits followers for conference.")
    p('Three further features limit how far the results go. First, the effect lives at the top of the market. Once the 25 highest-valued players in each sport are removed, the follower slope is close to zero in basketball and small in football, and the post hoc tests show the same pattern. Followers mainly separate the most valuable players from everyone else, rather than raising values evenly. Second, the main model explains only 23% (basketball) to 30% (football) of the variation in log valuation, so most of what drives NIL estimates is not captured by the variables available in both sports. Third, the basketball slope looks larger than football, but the difference is not statistically significant, so we cannot claim followers matter more in one sport.')
    p('The pattern is consistent with three explanations that our data cannot separate: followers attract sponsors and raise value; fame from playing well drives both followers and valuation; or the valuation provider uses follower counts in its formula, which would build the association into the outcome.')

    h('Limitations')
    p('Observational, single-snapshot design. Followers and valuations were measured at about the same time, so we cannot say which comes first, and we cannot show valuations changing over time. The before-and-after NIL question in the original proposal could not be tested because pre-2021 follower counts and a common outcome do not exist in our data.')
    p('Selected and non-comparable samples. Football was sampled only from players valued at $350,000 or more, which restricts the range of the outcome and likely shrinks the football slope. Basketball covers the full market. That difference is why sport could not be tested as a main effect.')
    p('Measurement. The Sideline does not publish its valuation method, has only 235 distinct rounded values among the top 1,000 football players, and may use follower counts as an input. Twenty of the basketball follower counts were reported manually and have no exact measurement date. Football PPA has unverified values, and points per game is a rough performance measure for basketball. No defensive or position-appropriate football metric was available.')
    p('Statistical. With 100 players per sport the cross-sport comparison is underpowered (see Power Analysis), football residuals are not normal, and players at the same school are not fully independent. The Bonferroni threshold protects against false positives across the three tests but makes H3 harder to detect.')

    h('Conclusion and Recommendations')
    p("Using one formula in both sports, Instagram following is clearly and positively associated with published NIL valuation in men's basketball and football, and it outweighs the performance and experience measures available in both. The association is driven by the highest-valued players, and the two sports do not differ significantly. The sport-specific models show where this needs care: in football the follower effect holds after adding recruiting stars and position, but in basketball the conference a player is in is the dominant factor, and followers add little once it is known. These findings describe how the current NIL market values athletes; they do not show that followers cause higher value or that NIL changed recruiting.")
    p('For anyone building on this work, we recommend: (1) sampling football across its full NIL range, as we did for basketball, so sport can be tested directly; (2) recording follower counts with dates at regular intervals, which would allow a test of whether follower growth comes before valuation growth; (3) obtaining or documenting the valuation method, to rule out followers being an input; (4) collecting follower counts for a basketball sample drawn from the top of its market, and conference for any future football sample outside Power 4, so the conference finding can be checked in both sports; (5) adding position-appropriate performance measures for football and a richer measure than points per game for basketball; and (6) for the policy question, collecting a common outcome, such as offers or roster spots, in both the pre- and post-2021 eras.')

    page();h('References')
    refs=[
      '[1] NCAA. "The History of the NCAA." June 30, 2021 entry: interim NIL policy effective July 1, 2021. https://www.ncaa.org/about-us/history/ (accessed November 1, 2026).',
      '[2] Govil, R. and Teshome, S. AIPI 510 Project 2 repository: collection, cleaning and analysis scripts, data and tests. https://github.com/govrahul/aipi510_project2',
      '[3] The Sideline. NIL tracker, football and men\'s basketball rankings. https://thesideline.co (basketball listing retrieved November 2, 2026; football frame from the partner collection).',
      '[4] SportsDataverse. hoopR-data and cfb-data public data releases. https://github.com/sportsdataverse/hoopR-data and https://github.com/sportsdataverse/cfb-data',
      '[5] Seabold, S. and Perktold, J. (2010). statsmodels: Econometric and statistical modeling with Python. Proceedings of the 9th Python in Science Conference. https://www.statsmodels.org',
      '[6] Long, J. S. and Ervin, L. H. (2000). Using heteroscedasticity consistent standard errors in the linear regression model. The American Statistician, 54(3), 217–224.',
      '[7] Azen, R. and Budescu, D. V. (2003). The dominance analysis approach for comparing predictors in multiple regression. Psychological Methods, 8(2), 129–148.',
      '[8] Cohen, J. (1988). Statistical Power Analysis for the Behavioral Sciences (2nd ed.). Lawrence Erlbaum.',
      '[9] Holm, S. (1979). A simple sequentially rejective multiple test procedure. Scandinavian Journal of Statistics, 6(2), 65–70.',
    ]
    for ref in refs:p(ref)
    h('Appendix: Reproducibility')
    p('Every number in this report is produced by scripts in the repository [2]. Football regression results come from scripts/summarize_deliverable_results.py (saved to reports/deliverables/model_statistics.json; football input SHA-256 '+stats['source_sha256']+'). The main two-sport model, dominance shares, assumption checks and post hoc tests come from scripts/make_unified_figures.py (saved to figures/figure_data/unified_model_results.json and unified_model_diagnostics.json). This report is built by scripts/build_project_report.py. The README lists the full run order.')
    out.mkdir(parents=True,exist_ok=True)
    doc.save(out/'project2_report.docx')
    (ROOT/'reports/deliverables/project2_report.md').write_text('\n'.join(md))
    print(out/'project2_report.docx')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output-dir',type=Path,default=ROOT/'deliverables')
    build(parser.parse_args().output_dir)
