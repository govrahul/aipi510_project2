/** Readable Excel view of the completed cohort; full provenance stays in CSV.
 * Requires the bundled @oai/artifact-tool runtime, not a network service.
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import {Workbook,SpreadsheetFile} from '@oai/artifact-tool';

const root=path.resolve(process.argv[2]||'.');
const outputDir=path.join(root,'outputs/basketball-followers-20261102');
await fs.mkdir(outputDir,{recursive:true});
const parsed=await Workbook.fromCSV(await fs.readFile(path.join(root,'Data/curated/basketball_instagram_100.csv'),'utf8'),{sheetName:'CSV input'});
const matrix=parsed.worksheets.getItemAt(0).getUsedRange().values;
const headers=matrix[0];
const columns=['Sample_Row','Player Name','College','Quartile','Instagram_Followers','NIL_Valuation_USD',
  'Instagram_Count_Provenance','Position','Grade','Conference','Instagram_Username','Instagram_Observed_At',
  'Instagram_Reported_Date','Instagram_Count_Precision','Instagram_Manual_Source','Instagram_Source_URL',
  'Username_Verification_URL','Sideline_Profile_URL','athlete_id','ESPN_Athlete_ID_Candidate',
  'Instagram_Raw_Label','Instagram_Integer_Tooltip','Selection_Probability','Sampling_Weight'];
const numbers=new Set(['Sample_Row','Instagram_Followers','NIL_Valuation_USD','Selection_Probability','Sampling_Weight']);
const dates=new Set(['Instagram_Observed_At','Instagram_Reported_Date']);
const sourceIndex=columns.map(c=>{const i=headers.indexOf(c);if(i<0)throw Error('Missing '+c);return i;});
const data=matrix.slice(1).map(row=>sourceIndex.map((ix,j)=>{
  const v=row[ix],c=columns[j];
  if(v===null||v===undefined||v==='')return null;
  if(numbers.has(c)){const n=Number(v);if(!Number.isFinite(n))throw Error('Invalid numeric '+c);return n;}
  if(dates.has(c)){const d=new Date(v);if(!Number.isFinite(d.getTime()))throw Error('Invalid date '+c);return d;}
  return String(v);
}));
if(data.length!==100||data.some(r=>typeof r[4]!=='number'))throw Error('Expected 100 recorded follower counts');
const wb=Workbook.create(),s=wb.worksheets.add('Basketball cohort');
s.showGridLines=false;s.getRangeByIndexes(0,0,101,columns.length).values=[columns,...data];
const all=s.getRange('A1:X101');all.format.font={name:'Arial',size:10,color:'#172536'};
all.format.verticalAlignment='center';all.format.rowHeight=23;all.format.columnWidth=22;
s.getRange('B1:B101').format.columnWidth=31;s.getRange('C1:C101').format.columnWidth=26;
s.getRange('A1:A101').format.columnWidth=10;s.getRange('D1:D101').format.columnWidth=23;
s.getRange('E1:G101').format.columnWidth=23;s.getRange('K1:K101').format.columnWidth=24;
s.getRange('L1:M101').format.columnWidth=25;
s.getRange('N1:N101').format.columnWidth=53;s.getRange('O1:O101').format.columnWidth=24;
s.getRange('P1:S101').format.columnWidth=75;
s.getRange('A1:X1').format={fill:'#233952',font:{name:'Arial',size:10,bold:true,color:'#FFFFFF'},wrapText:true,rowHeight:40,horizontalAlignment:'center',verticalAlignment:'center'};
for(let row=2;row<=101;row++)if(row%2===0)s.getRange(`A${row}:X${row}`).format.fill='#F3F6F9';
for(const row of [26,51,76,101])s.getRange(`A${row}:X${row}`).format.borders={bottom:{style:'thin',color:'#70849C'}};
s.getRange('A2:A101').setNumberFormat('0');s.getRange('E2:E101').setNumberFormat('#,##0');
s.getRange('F2:F101').setNumberFormat('"$"#,##0');s.getRange('W2:W101').setNumberFormat('0.000000');
s.getRange('X2:X101').setNumberFormat('0.00');s.getRange('L2:L101').setNumberFormat('mm/dd/yy hh:mm:ss');
s.getRange('M2:M101').setNumberFormat('mm/dd/yy');s.getRange('L1').values=[['Instagram_Observed_At_UTC']];
s.freezePanes.freezeRows(1);s.freezePanes.freezeColumns(3);
s.tables.add('A1:X101',true,'BasketballInstagramCohort');
wb.recalculate();
const values=s.getRange('A2:X101').values;
if(values.filter(r=>r[6]==='browser_observed').length!==80||values.filter(r=>r[6]==='user_reported').length!==20)throw Error('Source provenance count mismatch');
const inspect=await wb.inspect({kind:'table',range:'Basketball cohort!A52:G58',include:'values',tableMaxRows:7,tableMaxCols:7,maxChars:2200});
console.log(inspect.ndjson);
const errors=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:20},summary:'Final data export scan'});
console.log(errors.ndjson);
for(const [name,range]of [['top','A1:G12'],['manual','A52:G65']]){
  const preview=await wb.render({sheetName:s.name,range,scale:1.5,format:'png'});
  await fs.writeFile(path.join(outputDir,`preview-${name}.png`),new Uint8Array(await preview.arrayBuffer()));
}
const output=await SpreadsheetFile.exportXlsx(wb);const target=path.join(outputDir,'basketball_instagram_100.xlsx');
await output.save(target);await fs.copyFile(target,path.join(root,'Data/curated/basketball_instagram_100.xlsx'));
console.log('Saved 100-row Excel view; 80 browser observations and 20 user reports. Full provenance CSV retained.');
