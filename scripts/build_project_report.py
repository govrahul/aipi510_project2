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
    def fig(name,caption,width=6.6):
        path=ROOT/'reports/eda/figures'/name
        para=doc.add_paragraph();para.add_run().add_picture(str(path),width=Inches(width))
        para.paragraph_format.space_after=Pt(3)
        p(caption,'Caption');md.append(f'![{caption}](../eda/figures/{name})\n')

    doc.add_paragraph('Social media following and college athlete NIL valuation','Title')
    md.append('# Social media following and college athlete NIL valuation\n')
    p('Rahul Govil and Sam Teshome\nAIPI 510 Module Project 2  |  November 1 2026','Subtitle')
    h('Abstract')
    p('We investigated whether social media reach is associated with college athlete valuation and assessed the data needed to compare that association across sports and before and after NIL implementation. The completed analysis uses 100 football players selected from a supplied top 1000 NIL valuation frame. We fit ordinary least squares models of log valuation against log followers and reported heteroskedasticity robust uncertainty and influence checks. The replicated follower coefficient was 0.207 with a 95% HC3 confidence interval of 0.079 to 0.335 and a two sided p value of 0.00155. An exploratory model that omits an unverified performance field gave a coefficient of 0.274 with an interval of 0.094 to 0.454. The association was positive across the specified checks, but uncertain source timing, outcome based selection, and missing validated performance controls limit interpretation. Basketball and historical source frames were collected, but they lack the social measurements and common outcomes needed for the planned comparisons. These results describe a selected current football sample; they do not establish an effect of NIL policy on scholarships.')
    h('Background and motivation')
    p('The NCAA adopted an interim name image and likeness policy effective July 1 2021 [1]. Social reach may influence commercial opportunities, while athletic visibility may also generate followers. Understanding their relationship therefore requires separating commercial valuation, athletic performance, and college selection. A high NIL estimate is not a scholarship decision or a verified payment. We use this distinction to define what our completed analysis can answer and what additional observations the original policy question requires.')
    h('Research questions and hypotheses')
    p('The current valuation hypotheses are H01 beta football equals zero, H02 beta basketball equals zero, and H03 beta social by sport equals zero. The partner plan specified positive alternatives for the two within sport slopes and a two sided alternative for the interaction. We report conservative two sided results throughout. A three test Bonferroni family uses alpha 0.05 divided by 3 or 0.0167. Only the football slope has observed data; the other tests remain unperformed.')
    p('The original policy hypothesis is H0 delta social by post equals zero versus H1 delta is nonzero for a common selection or evaluation outcome measured in both eras. A sign reversal is one possible pattern. A coefficient changing sign or significance in separate fits is not itself a test of the coefficient difference.')

    page();h('Study design and sampling')
    p('This is an observational secondary data study. We did not assign NIL access, manipulate followers, or randomize college decisions. Random sampling within a source frame improves coverage of that frame; it does not randomize exposure or identify a causal policy effect. There is no experimental control condition in the completed analysis. The proposed historical cohorts would be comparator groups after their measurements and inclusion rules are harmonized.')
    h('Completed football sample',2)
    p('The inherited files form nested layers: 1000 ranked players, a 100 player sample, and 100 enriched model records. We did not concatenate them as independent observations. The saved model sample covers 39 schools, including 99 Power 4 players. Its NIL estimates range from 350000 to 5000000 dollars. These inclusion restrictions prevent generalization to all college athletes or to prospects without a reported valuation.')
    p('The partner code uses seed 510 and valuation percentile cutoffs to draw 25 players from the lowest tier, 50 from the middle tier, and 25 from the highest tier. Rounded valuation ties produce tier populations of 266, 479, and 255, respectively. Thus the exact selection probabilities are 25/266, 50/479, and 25/255. This is close to a proportional allocation, not deliberate oversampling of the top quartile. The fits below reproduce the unweighted analysis; design weighted population estimates were not calculated.')
    p('A PDF based reconstruction was locked in a fresh context before accessing saved player rows. Fresh full source access was blocked. After the lock, the independent procedure on the shared frame overlapped with 11 of the partner 100 players. Original script replay reproduced all 100 in order. This checks sampling reproducibility, not source validity [2].')
    h('Revised basketball and historical samples',2)
    p('The requested basketball design selects 1000 athletes, 250 per full frame NIL quartile, with deterministic ties, seed 510, probabilities, weights, and rows sorted by stratum. It must not truncate the source to the top 1000 before forming quartiles. This final sample has not been generated because a real basketball NIL frame is missing. The code retains selected rows when later enrichment fails.')
    p('Historical football and basketball for cohort starts 2018 and 2019 will use verified high school recruiting stars, with the same provider continuous rating to order ties. Candidate football recruiting labels do not yet establish high school classification. No final recruiting stratified samples have been generated. Earlier production quartile samples are superseded and excluded from this analysis. A NIL selected current frame and a recruiting selected historical frame cannot be naively pooled to estimate the original change in slope.')
    h('Variables and measurement',2)
    table(['Role','Completed football analysis'],[
        ['Outcome','Natural log of positive reported NIL estimate in USD'],
        ['Social predictor','Natural log of one plus Instagram followers'],
        ['Replication controls','PPA per play, freshman, freshman by stars, Power 4, premium position'],
        ['Exploratory controls','Centered stars, freshman, stars by freshman, coarse position groups'],
        ['Validation gaps','Follower date and identity; performance control']],[1.35,5.45])

    page();h('Power analysis')
    p('The partner calculation assumed overall R squared 0.35 and used overall Cohen f squared equal to 0.35 divided by 0.65 or 0.538. Its reported 41 and 46 player requirements concern overall model fit. They do not justify power for one social coefficient or a social by sport interaction. A model can explain substantial variation through other predictors while the social term adds little information.')
    p('We therefore evaluated one added term using partial f squared equal to the difference between full and reduced R squared divided by one minus full R squared. The planning calculation uses a noncentral F distribution with numerator degrees of freedom 1, denominator N minus p minus 1, and noncentrality N times partial f squared. We use eight predictor degrees of freedom excluding the intercept, alpha 0.0167, and target power 0.80. The SciPy based implementation searches integer sample sizes [2].')
    table(['Assumed partial f squared','Required N','Power at N equals 100'],[
        [f"{r['partial_f2']:.2f}",r['required_n'],f"{r['power_at_100']:.3f}"] for r in stats['power']],[2.6,1.6,2.6])
    p('These are sensitivity scenarios rather than estimates of a true effect. The approximation assumes independent homoskedastic errors and a specified design. It is not the power of our HC3 or clustered Wald tests. School and athlete dependence, missingness, unequal selection, measurement error, and additional interaction parameters can increase the required sample. A 1000 player target offers collection capacity but does not by itself establish power for the planned comparison. We do not calculate retrospective observed power as evidence for the reported result.')
    h('Data collection and cleaning')
    p('The partner attributes the legacy NIL frame to The Sideline [3]. We preserve the inherited CSVs and their hashes. The original snapshot dates, follower identities and observation times, and precise valuation type remain unverified. The data represent estimates rather than confirmed compensation. Fuzzy matching and zero filled performance in the inherited collection are not treated as validated measurements.')
    p('New scripts collect ESPN and SportsDataverse performance and roster exports, recruiting candidates, basketball model derived box BPM, and draft crosswalks from public sources [4,5]. They retain source identifiers, request metadata and hashes. Matches require an accepted ID or reviewed identity evidence; ambiguous and unsupported values remain missing. Credentials and newly collected player level files are local and ignored by Git, while scripts, aggregates and source descriptions are reviewable. Raw and enriched records are not overwritten by analysis.')
    p('The audit flags 41 zero PPA values and 30 nonzero PPA values on defensive or offensive line positions, where the collected offensive metric is not applicable. Zero cannot safely represent missing performance. We retained PPA solely in the replication benchmark and omitted it in the exploratory alternative. Demographic attributes such as race were not inferred from names or images. Draft no match is unknown, not an undrafted outcome, and observed college seasons are a lower bound rather than completed career duration.')

    page();h('Statistical analysis and results')
    p('Ordinary least squares on natural log valuation reduces the influence of the long right tail and provides a conditional multiplicative interpretation. The social predictor is ln of one plus followers. The replication retains the original specification. The exploratory alternative includes centered star rating, freshman status, both main effects and their interaction, and defense, offensive line, skill offense and quarterback position groups. It omits unverified PPA and the nearly constant conference flag. It cannot be described as controlling for validated college performance.')
    table(['Model','N','Social beta','95 percent CI','Two sided p','R squared'],[
        ['Replication HC3',b['n'],f"{b['coefficient']:.3f}",f"{b['ci95'][0]:.3f} to {b['ci95'][1]:.3f}",f"{b['p_two_sided']:.5f}",f"{b['r_squared']:.3f}"],
        ['Position groups HC3',c['n'],f"{c['coefficient']:.3f}",f"{c['ci95'][0]:.3f} to {c['ci95'][1]:.3f}",f"{c['p_two_sided']:.5f}",f"{c['r_squared']:.3f}"],
        ['Largest audience omitted',e['n'],f"{e['coefficient']:.3f}",f"{e['ci95'][0]:.3f} to {e['ci95'][1]:.3f}",f"{e['p_two_sided']:.5f}",f"{e['r_squared']:.3f}"],
        ['School clustered',k['n'],f"{k['coefficient']:.3f}",f"{k['ci95'][0]:.3f} to {k['ci95'][1]:.3f}",f"{k['p_two_sided']:.5f}",f"{k['r_squared']:.3f}"]],[1.8,.35,.7,1.5,.85,.6])
    p('The HC3 benchmark p value is below 0.0167. Its family adjusted 98.33 percent confidence interval is 0.050 to 0.363. This rejects the zero slope benchmark under the stated statistical model but remains exploratory given source validity and post collection specification review. The partner HC1 calculation reproduces beta 0.207 and p 0.000327; HC3 gives wider uncertainty. The sensitivity fits are not additional confirmatory discoveries, and no model was chosen by its p value or R squared.')
    p(f"For sufficiently large follower counts, doubling followers corresponds to approximately {b['doubled_followers_percent']:.1f} percent higher modeled valuation in the replicated model, with a 95 percent interval of {b['doubled_followers_ci95_percent'][0]:.1f} to {b['doubled_followers_ci95_percent'][1]:.1f} percent. The alternative gives approximately {c['doubled_followers_percent']:.1f} percent, with an interval of {c['doubled_followers_ci95_percent'][0]:.1f} to {c['doubled_followers_ci95_percent'][1]:.1f} percent. The exact contrast at baseline F is 100 * (exp(beta * ln((1 + 2F)/(1 + F))) - 1). These are conditional associations, not returns from purchasing followers.")
    fig('03_football_model_checks.png','Figure 1. Fixed exploratory comparisons and residuals. Intervals are 95 percent, not family adjusted. The largest audience omission is a sensitivity check; all players remain in the main fits.')
    p('Basketball and the social by sport test were not run because paired valuation and follower inputs are absent. The before and after test was not run because historical social measurements and a comparable decision outcome are absent. No post hoc pairwise tests were warranted for the completed question.')

    page();h('Assumptions and diagnostics')
    p('Heteroskedasticity is visible in residual checks and supported by the exploratory Breusch Pagan test: p 0.0246 in the inherited specification and p 0.000373 in the position group alternative. We therefore report HC3 standard errors with a normal reference distribution. A separate sensitivity uses school clustered uncertainty with 39 schools, small sample correction, and a t reference distribution [6]. Clustering can change uncertainty; it does not remove school confounding or source errors.')
    p('The inherited model has VIF about 83 for freshman and 82 for freshman by uncentered stars. This is substantial structural collinearity, so it should not be dismissed simply because the terms form an interaction. The alternative centers stars and includes both constituent main effects. All fitted design matrices are full rank. Sparse categories and the single non Power 4 player still make the original conference term unstable.')
    p('The inherited residual Jarque Bera p value is approximately 5.3 times 10 to the minus 13. A sample size of 100 does not make residuals normal or guarantee reliable inference under influence and dependence. We inspected residual spread and influence instead of treating the central limit theorem as a blanket exemption. The alternative has nine Cook distance values above the descriptive 4/N threshold; its largest leverage is 0.489. Leave one out follower coefficients range from 0.212 to 0.314. Flags prompt identity and measurement review, not automatic deletion [7].')
    p('The raw Pearson correlation is 0.623 and falls to 0.164 when the largest account is omitted. The log correlation changes from 0.502 to 0.403, and full sample Spearman correlation is 0.520. These patterns support using a log scale for description while retaining influence checks. No transformation establishes linearity, independence, correct measurement, or a causal direction. Unmeasured athletic quality and simultaneous valuation and follower growth remain plausible confounders.')
    h('Basketball and historical cohort findings')
    table(['Source frame','Rows','Distinct athletes','Schools'],[
        ['Basketball 2018 to 2019',5590,5562,353],
        ['Basketball 2019 to 2020',5587,5575,353],
        ['Basketball 2025 to 2026',5680,5677,365],
        ['Football fall 2018',23755,23751,216],
        ['Football fall 2019',23985,23966,217],
        ['Football fall 2025',26327,26316,234],
        ['Football fall 2026 ongoing',26094,26092,235]],[3.2,1.1,1.4,1.1])
    p('These are supporting athlete team season source rows, not final samples or complete national counts. Basketball model derived BPM is observed for 4762, 4768, and 5015 rows, but only 2940, 2915, and 3114 satisfy the provider qualification flag. Low exposure rows have more extreme values, and descriptive between school variation accounts for about 52 to 65 percent of qualified BPM variation. The measure needs construction and cross season calibration review before serving as an evaluation outcome.')
    p('In 2018 football, candidate recruiting stars are available for 52.0 percent of FBS rows and 10.1 percent of FCS rows; none are verified as the requested high school classification. About 63 percent of athletes in each historical 2018 sport frame also occur in 2019. Complete case restriction changes coverage, and pooled seasons cannot be treated as independent athletes. Historical cohorts also have much longer observed career follow up than current cohorts.')

    page();h('Interpretation and limitations')
    p('We find a positive social reach and valuation association in the inherited selected football sample. Its sign persists across the specified checks, although its magnitude and uncertainty depend on controls and influence. The result is consistent with social reach contributing to commercial valuation, with athlete fame generating both followers and valuations, or with valuation formulas incorporating audience size. The present data do not distinguish these mechanisms.')
    p('Selection is on the dependent variable and excludes athletes below the supplied valuation threshold. The observed slope need not equal the slope in the full eligible population. Sampling weights cannot recover players absent from the source frame. The source has only 235 distinct rounded valuations among 1000 records, and we have not established whether its estimation method already uses followers. This may build the association into the outcome.')
    p('Follower identity, snapshot timing, recruiting classification and performance validity require review. The sample has limited conference and recruiting variation, with 70 four star labels. Position grouping improves cell sizes but cannot replace an athletic performance control. The observational design and same period measurements do not establish that followers precede valuation or college recruitment. A statistically nonzero coefficient therefore does not establish a causal scholarship effect or unfair compensation.')
    p('Historical and current career outcomes have unequal observation time. Missing draft matches are not verified negatives; overseas contracts have almost no reviewed coverage. Draft round is defined only among drafted players and differs by league. Years in college has no simple direction as a quality measure. Future draft and contract outcomes must not enter a pre decision regression as baseline predictors.')
    h('Conclusion and recommendations')
    p('The completed result supports a narrowly stated conclusion: reported Instagram reach is positively associated with reported NIL valuation among 100 selected football players. Basketball, cross sport, and policy conclusions remain unanswered. We recommend validating follower dates and identities, replacing unsupported PPA values with position appropriate evidence, and checking the valuation methodology before interpreting the coefficient as more than a descriptive association.')
    p('For current basketball, obtain a documented NIL frame, freeze its snapshot, draw 250 players from each full frame quartile, and collect dated social measurements before fitting the pre specified model. Compare sports using the social by sport interaction and its confidence interval with harmonized controls. Separate significant results or different signs do not establish an interaction.')
    p('For the original before and after question, define one common outcome and eligible population across eras, collect followers dated before each decision, and establish offers and verified non offers if studying scholarships. Test the social by post term directly with athlete and school dependence addressed. Historical NIL values cannot be set to zero or replaced by draft round while retaining the same interpretation. A redesigned career outcome study needs verified negatives and a common follow up horizon or a censoring aware method. Even a valid change in association would require additional assumptions to attribute it to NIL policy rather than other time trends.')
    h('Reproducibility')
    p('The repository contains collection and analysis scripts, aggregate EDA outputs, an input hash manifest, a source and missingness dictionary, and offline tests. The football analysis runs from checked in inputs. Larger newly collected player level frames remain local with source descriptions and collection scripts. The current review is PR 4 on sam/athlete-data-and-eda, stacked on the partner branch [2]. The submission checklist records repository and presentation actions that still require the authors.')

    page();h('References')
    refs=[
      '[1] NCAA. The History of the NCAA. June 30 2021 entry describes the interim NIL policy effective July 1 2021. https://www.ncaa.org/about-us/history/ Accessed November 1 2026.',
      '[2] Govil R and Teshome S. AIPI 510 Project 2 repository. Source scripts, inherited CSVs, EDA, source audits and reproducible deliverable statistics. https://github.com/govrahul/aipi510_project2 Review https://github.com/govrahul/aipi510_project2/pull/4 Analysis snapshot November 1 2026.',
      '[3] The Sideline. NIL tracker. https://thesideline.co Source attribution follows the partner collection. Original bulk snapshot and valuation method are unverified; fresh full frame collection was not completed.',
      '[4] SportsDataverse. Public data release and sport data repositories. https://github.com/sportsdataverse/sportsdataverse-data and https://github.com/sportsdataverse/hoopR-data and https://github.com/sportsdataverse/cfb-data Public exports used for roster, game, recruiting candidate and basketball model derived metric layers. Exact file sources and hashes are retained in the project collection manifests.',
      '[5] nflverse. Player crosswalks and draft sources. https://github.com/nflverse/nflverse-data Supplementary football career links; registry presence is not evidence of a professional contract.',
      '[6] statsmodels. RegressionResults get_robustcov_results documentation. https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.RegressionResults.get_robustcov_results.html Accessed November 1 2026.',
      '[7] statsmodels. Regression diagnostics example. https://www.statsmodels.org/stable/examples/notebooks/generated/regression_diagnostics.html Accessed November 1 2026.',
      '[8] AIPI 510. Module Project 2 Statistical Analysis guidelines. Course supplied Word rubric. Govil R and Teshome S. Analysis of the Impact of Social Media Presence on NIL Valuation. Partner supplied five page draft, undated. The present analysis distinguishes replicated results from planned tests and corrects the power and inference limitations discussed above.'
    ]
    for ref in refs:p(ref)
    h('Analysis evidence')
    p('The numeric results in this report are generated from reports/deliverables/model_statistics.json and the November 1 exploratory data analysis. The football input SHA256 is '+stats['source_sha256']+'. Model specifications, covariance conventions, p values, ordinary and family adjusted intervals, effect transformations, diagnostics and partial term power calculations are preserved in that aggregate file. The larger source frame hashes are in reports/eda/manifest.json.')
    out.mkdir(parents=True,exist_ok=True)
    doc.save(out/'project2_report.docx')
    (ROOT/'reports/deliverables/project2_report.md').write_text('\n'.join(md))
    print(out/'project2_report.docx')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output-dir',type=Path,default=ROOT/'deliverables')
    build(parser.parse_args().output_dir)
