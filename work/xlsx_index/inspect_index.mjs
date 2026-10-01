import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const path = new URL("./TT_Structural_Archived_Index_Apr_2019.xlsx", import.meta.url).pathname.replace(/^\/(.:)/, "$1");
const input = await FileBlob.load(path);
const workbook = await SpreadsheetFile.importXlsx(input);

const sheetSummary = await workbook.inspect({
  kind: "sheet",
  include: "id,name",
  maxChars: 4000,
});
console.log("SHEETS");
console.log(sheetSummary.ndjson);

for (const sheet of workbook.worksheets.items) {
  const used = sheet.getUsedRange(true);
  console.log(`SHEET=${sheet.name} RANGE=${used.address}`);
  console.log(JSON.stringify(used.values));
}
