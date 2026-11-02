/** Editable nine-slide presentation; shared by live session and local export.
 * Call populatePresentation(presentation, evidence) inside artifactSession.run,
 * or see deliverables/README.md for the file-authoring command. No data requests.
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';

const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const C={ink:'#203C55',teal:'#147D80',muted:'#586977',grid:'#D9E0E5',white:'#FFFFFF'};
export async function loadEvidence() {
  const stats=JSON.parse(await fs.readFile(path.join(ROOT,'reports/deliverables/model_statistics.json'),'utf8'));
  // Only public legacy football rows enter the chart. Private cohort rows are not embedded.
  const text=await fs.readFile(path.join(ROOT,'Data/football_modeling_data.csv'),'utf8');
  // This file's relevant numeric columns contain no escaped comma fields; use a
  // quote-aware row parser to keep quoted names/colleges aligned as well.
  const parse=line=>line.match(/("(?:[^"]|"")*"|[^,]*)(,|$)/g).slice(0,-1).map(x=>x.replace(/,$/,'').replace(/^"|"$/g,'').replace(/""/g,'"'));
  const lines=text.trim().split(/\r?\n/);const headers=parse(lines.shift());
  const values=lines.map(parse);const ix=headers.indexOf('Instagram Followers'),iy=headers.indexOf('Valuation');
  if(ix<0||iy<0||values.length!==100)throw Error('Unexpected inherited football schema');
  return {...stats,scatter:values.map(row=>({x:Number(Math.log1p(Number(row[ix])).toPrecision(12)),y:Number(Math.log(Number(row[iy])).toPrecision(12))}))};
}

export function populatePresentation(presentation, ev) {
  presentation.theme.defaultFont='Arial';
  const slides=[];
  function text(slide,value,x,y,w,h,size=27,color=C.ink,bold=false){
    const shape=slide.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
    shape.text=value;shape.text.style={fontFamily:'Arial',fontSize:size,color,bold};return shape;
  }
  function slide(title,subtitle=''){
    const s=presentation.slides.add({width:1280,height:720,background:{fill:C.white}});slides.push(s);
    text(s,title,64,42,1152,100,44,C.ink,true);
    if(subtitle)text(s,subtitle,64,142,1152,55,25,C.muted);
    text(s,'AIPI 510  |  Govil and Teshome  |  November 1 2026',64,676,1050,25,16,C.muted);
    text(s,String(slides.length).padStart(2,'0'),1160,676,55,25,16,C.muted);return s;
  }
  function line(s,value,y){text(s,value,76,y,1128,85,29);}
  function table(s,values,top=215,widths=[420,170,310,250]){
    const t=s.tables.add({rows:values.length,columns:values[0].length,left:64,top,width:1152,height:values.length*64,values,columnWidths:widths});
    t.borders.assign({style:'solid',fill:C.grid,width:1});
    for(let r=0;r<values.length;r++)for(let c=0;c<values[0].length;c++){
      const cell=t.getCell(r,c);cell.fill=r===0?C.ink:(r%2?'#F2F5F7':C.white);
      cell.text.style={fontFamily:'Arial',fontSize:23,bold:r===0,color:r===0?C.white:C.ink};
    }return t;
  }
  let s=slide('Social media and college athlete\nNIL valuation');
  text(s,'A positive association in a selected football sample',64,278,1100,100,35,C.teal,true);
  text(s,'Rahul Govil and Sam Teshome',64,421,1100,60,28);
  text(s,'Current valuation results and the data needed for a before and after comparison',64,508,1080,95,27,C.muted);
  s.speakerNotes.text='25 seconds. Our original motivation was whether social media matters differently in college athlete selection after NIL. We first analyzed the data we actually have: a current football valuation sample. This presentation reports that result and explains why it cannot yet answer the original policy question. The association is positive, but scholarship and policy effects remain unanswered. Sources: project report and reports/deliverables/model_statistics.json, November 1 2026.';

  s=slide('Research questions and hypotheses','NCAA interim NIL policy took effect July 1 2021');
  line(s,'Current valuation: is the follower coefficient different from zero?',225);
  line(s,'Cross sport: does the social slope differ between football and basketball?',340);
  line(s,'Before and after: does social by post differ from zero for one common outcome?',455);
  text(s,'Valuation, scholarship offers, and later career outcomes measure different things',76,579,1110,55,24,C.teal,true);
  s.speakerNotes.text='50 seconds. The partner plan contains football and basketball slope tests, plus a social by sport interaction. Its within sport alternatives were positive; we report conservative two sided p values. The planned three test family uses alpha 0.05 divided by three, or 0.0167. For the original policy question, the null is zero social by post interaction on a common outcome. A sign change or a change in significance in separate models does not establish a difference. Historical NIL values are absent rather than zero. Source: NCAA history https://www.ncaa.org/about-us/history/ and project report hypotheses.';

  s=slide('Observational design and sampling','Random sampling does not randomize followers or NIL exposure');
  text(s,'Completed football',76,225,510,50,32,C.teal,true);
  text(s,'Top 1000 frame\n100 modeled athletes\n39 schools and 99 Power 4 players',76,291,530,180,30);
  text(s,'Requested basketball',688,225,510,50,32,C.teal,true);
  text(s,'Full NIL frame first\n250 from each quartile\n1000 selected before enrichment',688,291,510,180,30);
  text(s,'Legacy 25 / 50 / 25 allocation is nearly proportional; rounded ties change tier sizes',76,525,1128,78,25);
  s.speakerNotes.text='50 seconds. The three inherited football files are nested: a frame, a sample, and enriched versions of the same players. They are not 1200 independent observations. The original code uses valuation cutoffs and seed 510. Ties give populations 266, 479 and 255 with draws 25, 50 and 25. This is close to proportional allocation, rather than deliberate oversampling of the highest quarter. For new basketball work, quartiles come from the full available NIL frame before drawing 250 each. That frame is still missing. Weighting can target the frame but cannot recover athletes excluded from it. Source: Data/sample_data.py; scripts/sample_quartiles.py; project report design.';

  s=slide('Power for the social term','Overall model fit does not justify power for one coefficient or interaction');
  s.charts.add('bar',{position:{left:64,top:218,width:770,height:360},categories:['0.02','0.05','0.15'],series:[{name:'Required N',values:ev.power.map(x=>x.required_n),fill:C.teal}],barOptions:{direction:'column',gapWidth:110},hasLegend:false,
    xAxis:{title:{text:'Assumed partial f squared',textStyle:{fontSize:23}},textStyle:{fontSize:24,fill:C.ink}},
    yAxis:{title:{text:'Required sample size',textStyle:{fontSize:23}},min:0,max:600,majorUnit:200,textStyle:{fontSize:22,fill:C.ink},majorGridlines:{fill:C.grid,width:1}},
    dataLabels:{showValue:true,position:'outEnd',textStyle:{fontSize:25,fill:C.ink,bold:true}}});
  text(s,'80% target power\nalpha = 0.0167\n1 tested term\n8 predictor degrees of freedom',887,255,320,230,27);
  text(s,'Planning assumes independent homoskedastic errors; clustering and missingness need allowance',76,598,1128,50,23,C.muted);
  s.speakerNotes.text='45 seconds. We corrected the distinction between overall model power and power for the social term. Partial f squared measures the extra R squared from that term relative to unexplained variation. With eight predictor degrees of freedom, one tested term, target power 80 percent and alpha 0.0167, the planning requirements are 527, 213 and 74 for the three scenarios shown. These assume independent homoskedastic errors. They are not exact power for HC3 or school clustered tests. We did not claim that 100 observations have adequate power merely because the full model fits reasonably well. Source: scripts/power_sensitivity.py and model_statistics.json.';

  s=slide('Followers and NIL are positively associated','100 selected football players with both measurements');
  s.charts.add('scatter',{position:{left:64,top:215,width:730,height:375},series:[{name:'Football athletes',xValues:ev.scatter.map(x=>x.x),values:ev.scatter.map(x=>x.y),fill:C.teal,marker:{symbol:'circle',size:7,fill:C.teal}}],scatterOptions:{style:'marker'},hasLegend:false,
    xAxis:{title:{text:'ln(1 + Instagram followers)',textStyle:{fontSize:22}},min:7,max:14,majorUnit:2,numberFormatCode:'0',textStyle:{fontSize:21,fill:C.ink}},
    yAxis:{title:{text:'ln(NIL estimate in USD)',textStyle:{fontSize:22}},min:12.5,max:16,majorUnit:1,numberFormatCode:'0.0',textStyle:{fontSize:21,fill:C.ink},majorGridlines:{fill:C.grid,width:1}}});
  text(s,'Replicated model HC3',847,223,355,45,27,C.teal,true);
  text(s,'beta = 0.207\n95% CI 0.079 to 0.335\ntwo sided p = 0.00155',847,292,355,170,28);
  text(s,'About 15.4% higher modeled valuation for twice the followers',847,492,355,120,27);
  text(s,'Conditional selected sample association; follower timing and performance remain unverified',76,618,1128,42,22,C.muted);
  s.speakerNotes.text='65 seconds. The chart is descriptive and unadjusted. The coefficient beside it comes from the replicated multiple regression with the inherited controls. HC3 gives beta 0.207, a 95 percent interval from 0.079 to 0.335, and a two sided p value 0.00155. At alpha 0.0167 it is below the planned threshold; the family adjusted 98.33 percent interval is 0.050 to 0.363. At sufficiently large follower counts, doubling corresponds to about 15.4 percent higher modeled valuation, with a 95 percent interval about 5.6 to 26.1 percent. This is not an effect of acquiring followers. The inherited performance variable is unverified, and valuation may itself use social audience information. Chart coordinates are rounded to 12 significant digits for Excel portability; model calculations retain full precision. Source: inherited public football CSV and aggregate model_statistics.json.';

  s=slide('Model and influence checks','Specified sensitivities remain exploratory');
  const [a,b,c,e,k]=ev.models;
  table(s,[['Model','Social beta','95% interval','Two sided p'],
    ...[['Replication HC3',b],['Position groups HC3',c],['Largest audience omitted',e],['School clustered',k]].map(([label,r])=>[label,r.coefficient.toFixed(3),r.ci95.map(v=>v.toFixed(3)).join(' to '),r.p_two_sided.toFixed(5)])],213,[420,170,310,250]);
  text(s,'41 PPA zeros and 30 nonzero defense or line values require review',76,559,1128,45,25,C.teal,true);
  text(s,'Alternative omits PPA; it cannot claim adjustment for validated college performance',76,608,1128,44,23,C.muted);
  s.speakerNotes.text='55 seconds. We retained the inherited model only as a replication benchmark. The alternative drops unverified PPA and a nearly constant conference flag, centers stars, includes both constituent main effects and the freshman interaction, and groups positions to avoid sparse cells. The positive coefficient persists, including the largest account omission and school clustered sensitivity with 39 clusters. Those checks address some uncertainty and influence concerns; they do not fix selection or confounding. Breusch Pagan p is 0.000373 in the alternative; nine Cook distance flags warrant review. The full raw correlation falls from 0.623 to 0.164 without the largest account. We did not choose a specification by its significance or delete that player from the main fit. Source: reports/eda and model_statistics.json.';

  s=slide('Coverage limits the remaining tests','Large roster frames do not supply missing social or decision measurements');
  table(s,[['Basketball season','Source rows','BPM observed','BPM qualified'],
    ['2018 to 2019','5590','4762','2940'],
    ['2019 to 2020','5587','4768','2915'],
    ['2025 to 2026','5680','5015','3114']],211,[420,220,250,260]);
  text(s,'No paired NIL and social inputs in these basketball or historical frames',76,503,1128,65,28,C.teal,true);
  text(s,'2018 football candidate stars: 52% FBS vs 10% FCS; high school classification unverified',76,589,1128,60,24);
  s.speakerNotes.text='55 seconds. We collected historical and current basketball and football source frames and career crosswalks. Basketball BPM has broad coverage, but about half the roster rows satisfy the provider qualification flag. Low minute rows have more extreme values; the metric is model derived and needs calibration review. In historical football, recruiting candidate availability is very different between FBS and FCS, so complete case selection changes the population. We do not yet have verified high school classification in those frames. Roughly 63 percent of 2018 athletes also occur in 2019 in each sport, which requires dependence aware analysis. Draft no match is unknown, and current careers have less follow up. Source: reports/eda/README.md and supporting coverage tables.';

  s=slide('A valid before and after comparison','Test the change in social slope on a common outcome');
  text(s,'Y = baseline terms + beta social + gamma post\n      + delta social by post + error',76,225,1110,130,35,C.teal,true);
  line(s,'Measure followers before the same kind of decision in both eras',401);
  line(s,'Use comparable populations and address athlete and school dependence',483);
  text(s,'Delta tests the slope change. Different outcome scales cannot support that comparison.',76,591,1128,60,25,C.muted);
  s.speakerNotes.text='45 seconds. To study the original question, we need the same outcome and eligible population on both sides of July 2021. If the outcome is an offer, we need documented offers and credible non offers, not absence of a public report. Followers must precede the decision. Current followers cannot reconstruct historical reach, and historical NIL values cannot be coded as zero. Sampling current players by NIL and historical players by stars also changes the target population. The interaction delta directly tests the change in association. Calendar changes, COVID and other policies still prevent an automatic causal NIL interpretation. Source: docs/research_design.md; scripts/analyze_prepost.py; project report recommendations.';

  s=slide('Conclusions and next steps');
  text(s,'Supported now',76,215,1080,45,32,C.teal,true);
  text(s,'A positive follower and valuation association\nin a selected football sample',76,279,1090,100,35);
  text(s,'Next collection priorities',76,425,1080,45,32,C.teal,true);
  text(s,'Verify football measurements\nObtain the basketball NIL frame and dated followers\nDefine a common historical outcome and follow up',76,489,1120,150,28);
  s.speakerNotes.text='35 seconds. Our completed analysis supports a positive association in the selected football sample. It does not show that NIL changed scholarship decisions or that social popularity outweighs athletic ability. The next practical steps are validating football measurement timing and performance, completing basketball NIL and social collection, and defining one historical outcome with comparable sampling and follow up. The repository includes the collection code, aggregate results and a context README for partner review. We can present the completed observational result while being explicit about the comparisons that remain unanswered. Sources: project report and https://github.com/govrahul/aipi510_project2/pull/4.';
  return slides;
}

export async function buildFile(){
  const {Presentation,PresentationFile}=await import('@oai/artifact-tool');
  const p=Presentation.create({slideSize:{width:1280,height:720}});
  populatePresentation(p,await loadEvidence());
  const build=path.join(ROOT,'outputs/deliverable-qa/presentation');await fs.mkdir(build,{recursive:true});
  for(let i=0;i<p.slides.items.length;i++){
    const img=await p.export({slide:p.slides.items[i],format:'png',scale:1.5});
    await fs.writeFile(path.join(build,`slide-${i+1}.png`),new Uint8Array(await img.arrayBuffer()));
  }
  const out=path.join(ROOT,'deliverables');await fs.mkdir(out,{recursive:true});
  const draft=path.join(build,'candidate.pptx');await(await PresentationFile.exportPptx(p)).save(draft);
  const skill=process.env.PRESENTATIONS_SKILL_DIR;
  if(!skill)throw Error('Set PRESENTATIONS_SKILL_DIR to the installed presentations skill directory');
  const {finalizePresentation}=await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')));
  await finalizePresentation({workspaceDir:ROOT,candidatePath:draft,finalPath:path.join(out,'project2_presentation.pptx'),
    pythonExecutable:process.env.ARTIFACT_PYTHON,
    integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),
    layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),
    layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit','--require-native-table-slide','6','--require-native-table-slide','7'],
    explicitTotalSlideCount:9,requiredNativeChartOwnerSlides:[4,5],requiredNativeTableOwnerSlides:[6,7],
    materializeLiteralChartWorkbooks:true,fontPolicy:{basis:'design',families:['Arial']},
    verifyArtifactToolImport:true,receiptPath:path.join(build,'validation.json')});
}
if(typeof process!=='undefined'&&process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url))await buildFile();
