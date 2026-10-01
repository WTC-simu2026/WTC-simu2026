import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";


const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(scriptDir, "../../..");
const sourcePath = path.join(root, "wtc1_simulation_v8/input/v9f_open_sources/SHPB_S355.xlsx");
const outputPath = path.join(root, "wtc1_simulation_v8/output/v9f_s355_workbook_inspection.json");
const previewPath = path.join(root, "tmp/v9f_artifact_tool/s355_overview.png");

const sourceBytes = await fs.readFile(sourcePath);
const input = await FileBlob.load(sourcePath);
const workbook = await SpreadsheetFile.importXlsx(input);
const workbookSummary = await workbook.inspect({
  kind: "workbook,sheet,table",
  include: "id,name",
  maxChars: 6000,
  tableMaxRows: 8,
  tableMaxCols: 12,
  tableMaxCellChars: 100,
});

const sheetName = "S355_TestOverview";
const sheet = workbook.worksheets.getItem(sheetName);
const usedRange = sheet.getUsedRange(false);
const values = usedRange.values;
const formulas = usedRange.formulas;

await fs.mkdir(path.dirname(previewPath), { recursive: true });
const preview = await workbook.render({
  sheetName,
  autoCrop: "all",
  scale: 2,
  format: "png",
});
await fs.writeFile(previewPath, new Uint8Array(await preview.arrayBuffer()));

const result = {
  source_path: path.relative(root, sourcePath).replaceAll("\\", "/"),
  source_size_bytes: sourceBytes.length,
  source_sha256: crypto.createHash("sha256").update(sourceBytes).digest("hex"),
  workbook_summary_ndjson: workbookSummary.ndjson,
  selected_sheet: sheetName,
  used_row_count: values.length,
  used_column_count: values.reduce((maximum, row) => Math.max(maximum, row.length), 0),
  values,
  formulas,
  preview_path: path.relative(root, previewPath).replaceAll("\\", "/"),
  source_modified: false,
  workbook_exported: false,
};

await fs.mkdir(path.dirname(outputPath), { recursive: true });
await fs.writeFile(outputPath, `${JSON.stringify(result, null, 2)}\n`, "utf8");
console.log(JSON.stringify({
  selected_sheet: result.selected_sheet,
  used_row_count: result.used_row_count,
  used_column_count: result.used_column_count,
  source_size_bytes: result.source_size_bytes,
  source_sha256: result.source_sha256,
  source_modified: result.source_modified,
  workbook_exported: result.workbook_exported,
  preview_path: result.preview_path,
}, null, 2));
