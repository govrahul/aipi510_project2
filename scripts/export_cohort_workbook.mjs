// Run with the bundled artifact-tool runtime; see docs/stratification_and_instagram.md.
import fs from 'node:fs/promises';
import path from 'node:path';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';

const source = process.argv[2] ?? 'Data/private/comparators/workbook_input.json';
const outputDir = process.argv[3] ?? 'outputs/nil-quartiles-20261101';
const input = JSON.parse(await fs.readFile(source, 'utf8'));
const workbook = Workbook.create();
const overview = workbook.worksheets.add('Overview');
overview.showGridLines = false;
overview.getRange('A2').values = [['Historical athlete samples']];
overview.getRange('A2').format.font = { name: 'Arial', size: 14, bold: true };
overview.getRange('A4:J4').values = [['Sport', 'Start year', 'Source season', 'Eligible frame', 'Sample', 'Q4 highest', 'Q3', 'Q2', 'Q1 lowest', 'Sampling scope']];
const numeric = new Set(['Sample_Row', 'Cohort_Year', 'Recorded_Production', 'Production_Percentile',
 'Selection_Probability', 'Sampling_Weight', 'Stratification_Value', 'Frame_Rank', 'Stratum_Population_N',
 'Games', 'Starts', 'Points_Per_Game', 'Rebounds_Per_Game', 'Assists_Per_Game', 'height', 'weight']);
const columns = ['Sample_Row', 'Quartile', 'Sport', 'Cohort_Year', 'Player_Name', 'College', 'Position',
 'athlete_id', 'Production_Metric', 'Recorded_Production', 'Production_Percentile',
 'Stratum_Population_N', 'Selection_Probability', 'Sampling_Weight', 'Metric_Tie_Crosses_Quartile',
 'Instagram_Username', 'Username_Verification_URL', 'Instagram_Followers', 'Instagram_Observed_At',
 'Instagram_Count_Status', 'Source_Response_SHA256'];
for (let k = 0; k < input.sheets.length; k++) {
 const spec = input.sheets[k];
 const summary = input.summary[k];
 if (spec.rows.length !== 1000) throw new Error('A cohort must contain exactly 1000 observations');
 const sheet = workbook.worksheets.add(spec.name);
 sheet.showGridLines = false;
 const matrix = spec.rows.map(row => columns.map(col => {
   const index = spec.columns.indexOf(col);
   const value = index < 0 ? null : row[index];
   return col === 'athlete_id' && value !== null ? String(value) : value;
 }));
 sheet.getRangeByIndexes(0, 0, 1, columns.length).values = [columns];
 sheet.getRangeByIndexes(1, 0, matrix.length, columns.length).values = matrix;
 sheet.getRangeByIndexes(0, 0, 1001, columns.length).format.font = { name: 'Arial', size: 10 };
 sheet.getRangeByIndexes(0, 0, 1, columns.length).format = {
   fill: '#243B53', font: { name: 'Arial', size: 10, bold: true, color: '#FFFFFF' },
   wrapText: true, rowHeight: 44, horizontalAlignment: 'center', verticalAlignment: 'center'
 };
 sheet.getRangeByIndexes(1, 0, 1000, columns.length).format.rowHeight = 18;
 for (let j = 0; j < columns.length; j++) {
   const range = sheet.getRangeByIndexes(0, j, 1001, 1);
   range.format.columnWidth = ['Player_Name', 'College'].includes(columns[j]) ? 25 : 19;
   if (numeric.has(columns[j])) sheet.getRangeByIndexes(1, j, 1000, 1).setNumberFormat(
     columns[j].includes('Percentile') || columns[j].includes('Probability') ? '0.0%' :
     columns[j] === 'Cohort_Year' ? '0' :
     columns[j] === 'Sampling_Weight' ? '0.000' : '#,##0');
 }
 sheet.getRange('I1:I1001').format.columnWidth = 30;
 sheet.getRange('Q1:Q1001').format.columnWidth = 30;
 sheet.getRange('T1:T1001').format.columnWidth = 34;
 sheet.getRange('U1:U1001').format.columnWidth = 68;
 sheet.freezePanes.freezeRows(1);
 sheet.freezePanes.freezeColumns(2);
 const table = sheet.tables.add('A1:U1001', true, `Cohort${k}`);
 table.showFilterButton = true;
 for (const start of [251, 501, 751]) sheet.getRange(`A${start+1}:U${start+1}`).format.borders = {
   top: {style: 'medium', color: '#9AA5B1'}
 };
 const row = k + 5;
 overview.getRange(`A${row}:D${row}`).values = [[summary.sport, summary.cohort, summary.source_season, summary.eligible]];
 overview.getRange(`E${row}:I${row}`).formulas = [[
   `=COUNTA('${spec.name}'!H2:H1001)`,
   ...['Q4_Highest','Q3_Upper_Middle','Q2_Lower_Middle','Q1_Lowest'].map(q =>
     `=COUNTIFS('${spec.name}'!B2:B1001,"${q}")`)
 ]];
 overview.getRange(`J${row}`).values = [[summary.sport === 'football' ? 'D1 QB/RB/FB/WR/TE only' : 'D1 recorded production']];
}
overview.getRange('A11').values = [['Metric: within-position percentile of recorded season production. Provisional sampling proxy.']];
overview.getRange('A12').values = [['Football: passing/rushing/receiving yards. Basketball: points. These are not NIL or scholarship outcomes.']];
overview.getRange('A13').values = [['Historical Instagram counts remain missing. No before/after regression has been run.']];
overview.getRange('A14').values = [['Basketball start years 2018/2019 mean 2018–19/2019–20. The latter season was shortened by COVID.']];
overview.getRange('A16').values = [['Current basketball NIL quartiles remain pending: a real NIL valuation frame is required.']];
overview.getRange('A18').values = [['Sources: ESPN exports via SportsDataverse; source hashes are retained on each data sheet.']];
overview.getRange('A19').values = [['https://py.sportsdataverse.org/docs/mbb/reference/loaders/player']];
overview.getRange('A20').values = [['https://github.com/sportsdataverse/sportsdataverse-data/releases/tag/espn_cfb_player_box']];
overview.getRange('A4:J8').format.font = { name: 'Arial', size: 10 };
overview.getRange('A4:J4').format = {fill:'#243B53',font:{name:'Arial',size:10,bold:true,color:'#FFFFFF'},wrapText:true,rowHeight:30};
overview.getRange('A5:J8').format.rowHeight = 22;
overview.getRange('A4:C8').format.columnWidth = 15;
overview.getRange('D4:I8').format.columnWidth = 13;
overview.getRange('J4:J8').format.columnWidth = 33;
overview.getRange('A11:J20').format.font = {name:'Arial',size:10};
overview.getRange('A11:J20').format.rowHeight = 22;
overview.getRange('A11:J20').format.wrapText = false;
workbook.recalculate();
const counts = overview.getRange('E5:I8').values;
for (const row of counts) if (row[0] !== 1000 || row.slice(1).some(v => v !== 250)) throw new Error('Quartile count failed');
console.log((await workbook.inspect({kind:'table',range:'Overview!A4:J8',include:'values,formulas',tableMaxRows:5,tableMaxCols:10,maxChars:1500})).ndjson);
await fs.mkdir(outputDir, {recursive:true});
const file = await SpreadsheetFile.exportXlsx(workbook);
await file.save(path.join(outputDir,'historical_quartile_samples.xlsx'));
const preview = await workbook.render({sheetName:'Overview',range:'A1:J20',scale:1.5,format:'png'});
await fs.writeFile(path.join(outputDir,'overview-preview.png'),new Uint8Array(await preview.arrayBuffer()));
const detail = await workbook.render({sheetName:input.sheets[0].name,range:'A1:K12',scale:1.2,format:'png'});
await fs.writeFile(path.join(outputDir,'data-preview.png'),new Uint8Array(await detail.arrayBuffer()));
