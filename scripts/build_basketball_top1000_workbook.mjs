/** Clean view of the corrected 100-person social sample; full lineage in CSV. */
import fs from 'node:fs/promises';
import path from 'node:path';
import {Workbook,SpreadsheetFile} from '@oai/artifact-tool';
const root=path.resolve(process.argv[2]||'.');
const outdir=path.join(root,'outputs/basketball-top1000-20261103');await fs.mkdir(outdir,{recursive:true});
const input=await Workbook.fromCSV(await fs.readFile(path.join(root,'Data/curated/basketball_top1000_instagram_100.csv'),'utf8'),{sheetName:'Input'});
const matrix=input.worksheets.getItemAt(0).getUsedRange().values,headers=matrix[0];
const columns=['Sample_Row','Player Name','College','NIL_Global_Rank','Quartile','Instagram_Followers','NIL_Valuation_USD',
 'Instagram_Username','Instagram_Count_Status','Instagram_Observed_At','Position','Grade','Conference',
 'Instagram_Raw_Label','Instagram_Count_Precision','Instagram_Source_URL','Identity_Evidence_URL',
 'First_Instagram_Result_URL','Google_Search_URL','Google_Observed_At','Identity_Review_Note',
 'Sideline_Profile_URL','NIL_Retrieved_At','NIL_Evidence_Label','NIL_Value_Precision',
 'athlete_id','ESPN_Athlete_ID_Candidate','Selection_Probability','Sampling_Weight','Instagram_Reported_Date','Instagram_Manual_Source'];
const labels=['Sample row','Player','Source school','Top-1000 rank','NIL quartile','Instagram followers','NIL estimate (USD)',
 'Instagram handle','Count status','Observed at (UTC)','Position','Academic class','Conference',
 'Visible follower label','Count precision','Instagram profile URL','Identity evidence URL','First Instagram Google result',
 'Google search URL','Google observed (UTC)','Identity review note','Sideline player URL','NIL retrieved (UTC)',
 'NIL source label','NIL precision','Source athlete ID','ESPN ID (candidate)','Selection probability','Sampling weight','Manually reported on','Manual report source'];
const numeric=new Set(['Sample_Row','NIL_Global_Rank','Instagram_Followers','NIL_Valuation_USD','Selection_Probability','Sampling_Weight']);
const dates=new Set(['Instagram_Observed_At','Google_Observed_At','NIL_Retrieved_At','Instagram_Reported_Date']);
const ix=columns.map(c=>{const i=headers.indexOf(c);if(i<0)throw Error('Missing '+c);return i;});
const data=matrix.slice(1).map(row=>ix.map((i,j)=>{
 const v=row[i],c=columns[j];if(v===null||v===undefined||v==='')return null;
 if(numeric.has(c)){const n=Number(v);if(!Number.isFinite(n))throw Error('Invalid numeric value');return n;}
 if(dates.has(c))return new Date(v);
 if(c==='Quartile')return String(v).replaceAll('_',' ');
 if(c==='Instagram_Count_Status')return v==='observed_browser_integer_tooltip'?'Browser count recorded':v==='user_reported_count'?'User reported count':'Account unavailable';
 if(c==='Instagram_Count_Precision')return v==='visible_followers_link_integer_tooltip'?'Exact integer tooltip':'User report; display precision unknown';
 return String(v);
}));
if(data.length!==100||data.filter(r=>typeof r[5]==='number').length!==100)throw Error('Expected 100 rows and 100 counts');
if(data.filter(r=>r[8]==='Browser count recorded').length!==99||data.filter(r=>r[8]==='User reported count').length!==1)throw Error('Source labels changed');
const wb=Workbook.create(),s=wb.worksheets.add('Top 1000 social sample');s.showGridLines=false;
s.getRange('A1:AE101').values=[labels,...data];
const all=s.getRange('A1:AE101');all.format.font={name:'Arial',size:10,color:'#172536'};
all.format.verticalAlignment='center';all.format.rowHeight=23;all.format.columnWidth=23;
s.getRange('A1:A101').format.columnWidth=11;s.getRange('B1:B101').format.columnWidth=31;s.getRange('C1:C101').format.columnWidth=26;
s.getRange('D1:D101').format.columnWidth=13;s.getRange('E1:E101').format.columnWidth=23;
s.getRange('H1:H101').format.columnWidth=25;s.getRange('I1:I101').format.columnWidth=27;
for(const col of ['J','T','W'])s.getRange(`${col}1:${col}101`).format.columnWidth=27;
s.getRange('P1:S101').format.columnWidth=75;s.getRange('U1:U101').format.columnWidth=150;
s.getRange('V1:V101').format.columnWidth=75;s.getRange('Z1:Z101').format.columnWidth=68;
s.getRange('Y1:Y101').format.columnWidth=43;
s.getRange('O1:O101').format.columnWidth=46;s.getRange('AE1:AE101').format.columnWidth=125;
s.getRange('A1:AE1').format={fill:'#233952',font:{name:'Arial',size:10,bold:true,color:'#FFFFFF'},wrapText:true,rowHeight:40,horizontalAlignment:'center',verticalAlignment:'center'};
for(let r=2;r<=101;r++)if(r%2===0)s.getRange(`A${r}:AE${r}`).format.fill='#F3F6F9';
for(const row of [26,51,76,101])s.getRange(`A${row}:AE${row}`).format.borders={bottom:{style:'thin',color:'#70849C'}};
s.getRange('F2:F101').setNumberFormat('#,##0');s.getRange('G2:G101').setNumberFormat('"$"#,##0');
s.getRange('AB2:AB101').setNumberFormat('0%');s.getRange('AC2:AC101').setNumberFormat('0.0');
for(const col of ['J','T','W'])s.getRange(`${col}2:${col}101`).setNumberFormat('mm/dd/yy hh:mm:ss');
s.getRange('AD2:AD101').setNumberFormat('mm/dd/yy');
s.freezePanes.freezeRows(1);s.freezePanes.freezeColumns(3);s.tables.add('A1:AE101',true,'Top1000BasketballSocial');
// Sam supplied row 33's count; do not invent a profile or observed-at time.
wb.recalculate();
console.log((await wb.inspect({kind:'table',range:"'Top 1000 social sample'!A30:J35",include:'values',tableMaxRows:6,tableMaxCols:10,maxChars:2000})).ndjson);
for(const [name,range]of [['top','A1:I11'],['missing','A29:J36']]){
 const image=await wb.render({sheetName:s.name,range,scale:1.5,format:'png'});
 await fs.writeFile(path.join(outdir,`preview-${name}.png`),new Uint8Array(await image.arrayBuffer()));
}
const output=await SpreadsheetFile.exportXlsx(wb),target=path.join(outdir,'basketball_top1000_instagram_100.xlsx');
await output.save(target);await fs.copyFile(target,path.join(root,'Data/curated/basketball_top1000_instagram_100.xlsx'));
console.log('Exported corrected sample: 100 players; 99 browser observations; one user-reported count.');
