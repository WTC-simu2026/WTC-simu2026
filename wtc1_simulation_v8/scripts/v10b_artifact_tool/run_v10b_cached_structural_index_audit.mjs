#!/usr/bin/env node
/** Build and validate the index-only WTC 1 V10B structural-document audit. */

import { createHash } from "node:crypto";
import { createReadStream } from "node:fs";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";


const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(SCRIPT_DIR, "../../..");
const CONFIG_PATH = path.join(ROOT, "wtc1_simulation_v8/data/v10b_cached_structural_index_audit.json");


function normalizeRelative(value) {
  return value.replaceAll("\\", "/");
}


function rootPath(relativePath) {
  return path.join(ROOT, ...normalizeRelative(relativePath).split("/"));
}


async function readJson(filePath) {
  return JSON.parse(await fs.readFile(filePath, "utf8"));
}


async function writeJson(filePath, value) {
  await fs.mkdir(path.dirname(filePath), { recursive: true });
  await fs.writeFile(filePath, `${JSON.stringify(value, null, 2)}\n`, "utf8");
}


async function writeText(filePath, value) {
  await fs.mkdir(path.dirname(filePath), { recursive: true });
  await fs.writeFile(filePath, `${value.trimEnd()}\n`, "utf8");
}


function csvValue(value) {
  if (value === null || value === undefined) return "";
  const text = String(value);
  if (/[",\r\n]/.test(text)) return `"${text.replaceAll('"', '""')}"`;
  return text;
}


async function writeCsv(filePath, rows, columns) {
  await fs.mkdir(path.dirname(filePath), { recursive: true });
  const lines = [columns.map(csvValue).join(",")];
  for (const row of rows) lines.push(columns.map((column) => csvValue(row[column])).join(","));
  await fs.writeFile(filePath, `${lines.join("\n")}\n`, "utf8");
}


function assert(condition, message) {
  if (!condition) throw new Error(message);
}


async function sha256(filePath) {
  return await new Promise((resolve, reject) => {
    const hash = createHash("sha256");
    const stream = createReadStream(filePath);
    stream.on("error", reject);
    stream.on("data", (chunk) => hash.update(chunk));
    stream.on("end", () => resolve(hash.digest("hex")));
  });
}


async function verifyFiles(fileMap, label) {
  const files = [];
  for (const [relativePath, expectedSha256] of Object.entries(fileMap)) {
    const filePath = rootPath(relativePath);
    let actualSha256 = null;
    let sizeBytes = null;
    try {
      const stat = await fs.stat(filePath);
      sizeBytes = stat.size;
      actualSha256 = await sha256(filePath);
    } catch {
      // The row below records the missing file and fails the audit.
    }
    files.push({
      path: normalizeRelative(relativePath),
      size_bytes: sizeBytes,
      expected_sha256: expectedSha256,
      actual_sha256: actualSha256,
      matches: actualSha256 === expectedSha256,
    });
  }
  const failures = files.filter((row) => !row.matches).map((row) => row.path);
  assert(failures.length === 0, `${label} hash failure: ${failures.join(", ")}`);
  return { count: files.length, all_match: true, files };
}


function blank(value) {
  return value === null || value === undefined || String(value).trim() === "";
}


function countBy(rows, keyFunction) {
  const counts = {};
  for (const row of rows) {
    const key = String(keyFunction(row));
    counts[key] = (counts[key] ?? 0) + 1;
  }
  return Object.fromEntries(Object.entries(counts).sort(([a], [b]) => a.localeCompare(b, undefined, { numeric: true })));
}


function sameJson(left, right) {
  return JSON.stringify(left) === JSON.stringify(right);
}


function unique(values) {
  return [...new Set(values)];
}


function priorityRank(priority) {
  return {
    P0_LOCALIZE_FIRST: 0,
    P1_PRIMARY_DETAIL: 1,
    P2_SUPPLEMENTAL: 2,
  }[priority];
}


function drawingRangeStatus(start, end) {
  if (!blank(start) && !blank(end)) return "COMPLETE_REGISTER_RANGE_STRING";
  if (!blank(start) || !blank(end)) return "PARTIAL_REGISTER_RANGE_STRING";
  return "MISSING_REGISTER_RANGE_STRING";
}


function flattenManifestEntries(manifests) {
  const rows = [];
  for (const manifest of manifests) {
    for (const entry of manifest.entries) {
      rows.push({ manifest_id: manifest.manifest_id, ...entry });
    }
  }
  return rows;
}


function manifestHitsForId(documentId, manifestEntries) {
  const needle = documentId.toUpperCase();
  return manifestEntries.filter((entry) => {
    const haystack = [entry.path, entry.relative_path, entry.id]
      .filter((value) => value !== null && value !== undefined)
      .join(" ")
      .toUpperCase();
    return haystack.includes(needle);
  });
}


async function main() {
  const started = process.hrtime.bigint();
  const generatedAtUtc = new Date().toISOString().replace(/\.\d{3}Z$/, "Z");
  const config = await readJson(CONFIG_PATH);
  assert(config.iteration === "V10B", "Unexpected iteration in V10B configuration");

  const regressionAudit = await verifyFiles(config.regression_files, "V10A immutable regression");
  const cachedIndexAudit = await verifyFiles(config.cached_index_files, "V10B cached index");
  const protectedBefore = await verifyFiles(config.protected_files, "Protected Blender master before V10B");
  assert(regressionAudit.count === config.gates.regression_hash_count_expected, "V10A regression count mismatch");
  assert(cachedIndexAudit.count === config.gates.cached_index_hash_count_expected, "Cached index count mismatch");

  const v10aSourceGateAudit = await readJson(rootPath("wtc1_simulation_v8/output/v10a_source_gate_audit.json"));
  assert(v10aSourceGateAudit.validation_status === "PASS", "V10A source-gate audit is not PASS");
  assert(v10aSourceGateAudit.requirement_count === 22, "V10A source-gate requirement count changed");
  const v10aRequirements = new Map(v10aSourceGateAudit.requirements.map((row) => [row.requirement_id, row]));

  const workbookPath = rootPath("work/xlsx_index/TT_Structural_Archived_Index_Apr_2019.xlsx");
  const workbook = await SpreadsheetFile.importXlsx(await FileBlob.load(workbookPath));
  const sheetInspection = await workbook.inspect({ kind: "sheet", include: "id,name", maxChars: 4000 });
  const sheetNames = workbook.worksheets.items.map((sheet) => sheet.name);
  assert(sameJson(sheetNames, config.workbook_expectations.sheet_names), "Structural index sheet names changed");
  const sheet1 = workbook.worksheets.getItem("Sheet1");
  const usedRange = sheet1.getUsedRange(true);
  assert(usedRange.address === config.workbook_expectations.sheet1_used_range, "Structural index used range changed");
  const values = usedRange.values;
  const header = values[0].map((value) => value ?? null);
  assert(sameJson(header, config.workbook_expectations.header), "Structural index header changed");

  const registerRows = values.slice(1).map((row, index) => ({
    register_row: index + 2,
    book_number: row[0],
    document_id: blank(row[1]) ? "" : String(row[1]).trim(),
    register_pdf_title: blank(row[2]) ? "" : String(row[2]).trim(),
    register_pdf_number: blank(row[3]) ? "" : String(row[3]).trim(),
    register_content_summary: blank(row[4]) ? "" : String(row[4]).trim(),
    register_file_or_folder_size: blank(row[5]) ? "" : String(row[5]).trim(),
    register_floors: blank(row[6]) ? "" : String(row[6]).trim(),
    register_area: blank(row[7]) ? "" : String(row[7]).trim(),
    register_tower_label: blank(row[8]) ? "" : String(row[8]).trim(),
    register_drawing_start: blank(row[9]) ? "" : String(row[9]).trim(),
    register_drawing_end: blank(row[10]) ? "" : String(row[10]).trim(),
  }));
  const nonblankRegisterRows = registerRows.filter((row) => row.document_id !== "");
  const rowsByDocumentId = new Map();
  for (const row of nonblankRegisterRows) {
    const existing = rowsByDocumentId.get(row.document_id) ?? [];
    existing.push(row);
    rowsByDocumentId.set(row.document_id, existing);
  }

  const targetDefinitions = [];
  config.target_groups.forEach((group, groupIndex) => {
    for (const document of group.documents) {
      targetDefinitions.push({
        group_index: groupIndex,
        group_id: group.group_id,
        subsystem: group.subsystem,
        group_description: group.description,
        transcription_scope: group.transcription_scope,
        minimum_acceptance: group.minimum_acceptance,
        document_id: document.document_id,
        priority: document.priority,
        priority_rank: priorityRank(document.priority),
      });
    }
  });
  assert(targetDefinitions.length === config.gates.selected_document_count_expected, "Selected document target count mismatch");
  assert(unique(targetDefinitions.map((row) => row.document_id)).length === targetDefinitions.length, "Duplicate document ID in V10B target definition");
  for (const target of targetDefinitions) {
    const matches = rowsByDocumentId.get(target.document_id) ?? [];
    assert(matches.length === 1, `${target.document_id} occurs ${matches.length} times in the structural register`);
  }

  const cachedManifests = [
    {
      manifest_id: "GENERAL_PDF_INDEX",
      path: "work/pdf_index/manifest.json",
      entries: await readJson(rootPath("work/pdf_index/manifest.json")),
    },
    {
      manifest_id: "OFFICIAL_PDF_INDEX",
      path: "work/official_index/manifest.json",
      entries: await readJson(rootPath("work/official_index/manifest.json")),
    },
    {
      manifest_id: "OFFICIAL_EXTRA_PDF_INDEX",
      path: "work/official_extra_index/manifest.json",
      entries: await readJson(rootPath("work/official_extra_index/manifest.json")),
    },
  ];
  const manifestEntries = flattenManifestEntries(cachedManifests);
  const qualityFlagsById = new Map();
  for (const flag of config.known_index_quality_flags) {
    if (flag.document_id === "ALL_SELECTED" || flag.document_id === "ALL_TOWER_A_OR_AB_SELECTED") continue;
    const rows = qualityFlagsById.get(flag.document_id) ?? [];
    rows.push(flag.flag);
    qualityFlagsById.set(flag.document_id, rows);
  }

  const selectedRows = targetDefinitions.map((target) => {
    const register = rowsByDocumentId.get(target.document_id)[0];
    const hits = manifestHitsForId(target.document_id, manifestEntries);
    const flags = ["FLOORS_FIELD_BLANK", "TOWER_TO_WTC1_MAPPING_UNVERIFIED", ...(qualityFlagsById.get(target.document_id) ?? [])];
    if (blank(register.register_drawing_start) && blank(register.register_drawing_end)) flags.push("DRAWING_RANGE_MISSING");
    if (register.register_tower_label.toUpperCase() === "B") flags.push("B_ONLY_REGISTER_ROW_DEFER_UNTIL_TOWER_MAPPING_CONFIRMED");
    return {
      ...register,
      group_id: target.group_id,
      subsystem: target.subsystem,
      priority: target.priority,
      priority_rank: target.priority_rank,
      drawing_range_status: drawingRangeStatus(register.register_drawing_start, register.register_drawing_end),
      index_evidence_class: "ARCHIVE_REGISTER_CLAIM_NOT_OFFICIAL_SOURCE",
      exact_payload_hit_in_selected_cached_manifests: hits.length > 0 ? "YES" : "NO",
      selected_cache_manifest_hit_count: hits.length,
      selected_cache_manifest_ids: unique(hits.map((row) => row.manifest_id)).join("|"),
      target_payload_read_v10b: "NO",
      floor93_99_directly_indexed: blank(register.register_floors) ? "NO" : "YES",
      tower_to_wtc1_mapping_verified: "NO",
      as_built_or_revision_authority_verified: "NO",
      quality_flags: unique(flags).join("|"),
      transcription_scope: target.transcription_scope,
      minimum_acceptance: target.minimum_acceptance,
    };
  });
  const selectedById = new Map(selectedRows.map((row) => [row.document_id, row]));
  const selectedManifestHitCount = selectedRows.filter((row) => row.selected_cache_manifest_hit_count > 0).length;
  const selectedFloorFieldNonblankCount = selectedRows.filter((row) => !blank(row.register_floors)).length;
  assert(selectedManifestHitCount === config.gates.selected_manifest_payload_hit_count_expected, "Unexpected exact target payload hit in selected cached manifests");
  assert(selectedFloorFieldNonblankCount === config.gates.selected_floor_field_nonblank_count_expected, "Unexpected floor field in selected register rows");

  const selectedBookCounts = countBy(selectedRows, (row) => row.book_number);
  const selectedPriorityCounts = countBy(selectedRows, (row) => row.priority);
  const selectedGroupCounts = countBy(selectedRows, (row) => row.group_id);
  const selectedTowerCounts = countBy(selectedRows, (row) => row.register_tower_label || "BLANK");
  const selectedDrawingRangeCounts = countBy(selectedRows, (row) => row.drawing_range_status);
  assert(sameJson(selectedBookCounts, config.workbook_expectations.selected_book_counts), "Selected book counts changed");
  assert(sameJson(selectedPriorityCounts, config.workbook_expectations.priority_counts), "Priority counts changed");

  const requirementRows = config.requirement_mapping.map((mapping) => {
    const sourceRequirement = v10aRequirements.get(mapping.requirement_id);
    assert(sourceRequirement, `Unknown V10A source requirement ${mapping.requirement_id}`);
    const candidateIds = unique(
      targetDefinitions
        .filter((target) => mapping.candidate_groups.includes(target.group_id))
        .sort((a, b) => a.priority_rank - b.priority_rank || a.group_index - b.group_index || a.document_id.localeCompare(b.document_id))
        .map((target) => target.document_id),
    );
    return {
      requirement_id: mapping.requirement_id,
      v10a_subsystem: sourceRequirement.subsystem,
      v10a_field_group: sourceRequirement.field_group,
      v10a_status: sourceRequirement.status,
      v10a_evidence_class: sourceRequirement.evidence_class,
      candidate_group_count: mapping.candidate_groups.length,
      candidate_groups: mapping.candidate_groups.join("|"),
      candidate_document_count: candidateIds.length,
      candidate_document_ids: candidateIds.join("|"),
      v10b_index_status: mapping.status,
      target_payload_read: "NO",
      content_transcribed: "NO",
      requirement_closed_after_v10b: "NO",
      remains_solver_blocking: "YES",
      note: mapping.note,
    };
  });
  assert(requirementRows.length === 22, "V10B requirement matrix must retain all 22 V10A requirements");
  assert(requirementRows.every((row) => row.remains_solver_blocking === "YES"), "A V10A source requirement was incorrectly closed");

  const priorityRows = [...selectedRows]
    .sort((a, b) => a.priority_rank - b.priority_rank || targetDefinitions.find((row) => row.document_id === a.document_id).group_index - targetDefinitions.find((row) => row.document_id === b.document_id).group_index || a.document_id.localeCompare(b.document_id))
    .map((row, index) => ({
      acquisition_sequence: index + 1,
      priority: row.priority,
      document_id: row.document_id,
      book_number: row.book_number,
      group_id: row.group_id,
      subsystem: row.subsystem,
      register_pdf_title: row.register_pdf_title,
      register_content_summary: row.register_content_summary,
      register_tower_label: row.register_tower_label,
      register_drawing_start: row.register_drawing_start,
      register_drawing_end: row.register_drawing_end,
      requested_payload: "EXACT_PDF_MATCHING_REGISTER_IDENTIFIER_ONLY",
      v10b_payload_status: "NOT_PRESENT_IN_SELECTED_CACHED_PDF_MANIFESTS_NOT_GLOBALLY_PROVEN_ABSENT",
      next_identity_gate: "LITERAL_IDENTIFIER_MATCH|SOURCE_PATH|BYTE_SIZE|SHA256|PROVENANCE_AND_REVISION_NOTE",
      transcription_scope: row.transcription_scope,
      minimum_acceptance: row.minimum_acceptance,
      prohibited_promotion: "NO_AS_BUILT_COORDINATE|NO_SECTION_ASSIGNMENT|NO_MATERIAL|NO_MASS|NO_STIFFNESS|NO_CAPACITY|NO_CONNECTION_LAW|NO_DAMAGE_STATE|NO_LOAD_PATH_CREDIT",
    }));

  const inventoryRows = [...selectedRows].sort((a, b) => a.register_row - b.register_row);
  const inventoryColumns = [
    "register_row", "book_number", "document_id", "register_pdf_title", "register_pdf_number",
    "register_content_summary", "register_file_or_folder_size", "register_floors", "register_area",
    "register_tower_label", "register_drawing_start", "register_drawing_end", "group_id", "subsystem",
    "priority", "drawing_range_status", "index_evidence_class", "exact_payload_hit_in_selected_cached_manifests",
    "selected_cache_manifest_hit_count", "selected_cache_manifest_ids", "target_payload_read_v10b",
    "floor93_99_directly_indexed", "tower_to_wtc1_mapping_verified", "as_built_or_revision_authority_verified",
    "quality_flags",
  ];
  const requirementColumns = [
    "requirement_id", "v10a_subsystem", "v10a_field_group", "v10a_status", "v10a_evidence_class",
    "candidate_group_count", "candidate_groups", "candidate_document_count", "candidate_document_ids",
    "v10b_index_status", "target_payload_read", "content_transcribed", "requirement_closed_after_v10b",
    "remains_solver_blocking", "note",
  ];
  const priorityColumns = [
    "acquisition_sequence", "priority", "document_id", "book_number", "group_id", "subsystem",
    "register_pdf_title", "register_content_summary", "register_tower_label", "register_drawing_start",
    "register_drawing_end", "requested_payload", "v10b_payload_status", "next_identity_gate",
    "transcription_scope", "minimum_acceptance", "prohibited_promotion",
  ];

  const outputs = Object.fromEntries(Object.entries(config.outputs).map(([key, relativePath]) => [key, rootPath(relativePath)]));
  await writeCsv(outputs.document_inventory_csv, inventoryRows, inventoryColumns);
  await writeCsv(outputs.requirement_matrix_csv, requirementRows, requirementColumns);
  await writeCsv(outputs.priority_matrix_csv, priorityRows, priorityColumns);

  const protectedAfter = await verifyFiles(config.protected_files, "Protected Blender master after V10B");
  const checks = {
    v10a_regression_hashes: regressionAudit.all_match,
    cached_index_hashes: cachedIndexAudit.all_match,
    protected_blender_master_before: protectedBefore.all_match,
    protected_blender_master_after: protectedAfter.all_match,
    workbook_sheet_names: sameJson(sheetNames, config.workbook_expectations.sheet_names),
    workbook_sheet1_used_range: usedRange.address === config.workbook_expectations.sheet1_used_range,
    workbook_header_exact: sameJson(header, config.workbook_expectations.header),
    target_document_count: selectedRows.length === config.gates.selected_document_count_expected,
    all_target_ids_unique: unique(selectedRows.map((row) => row.document_id)).length === selectedRows.length,
    all_target_ids_exactly_once_in_register: targetDefinitions.every((target) => (rowsByDocumentId.get(target.document_id) ?? []).length === 1),
    selected_book_counts: sameJson(selectedBookCounts, config.workbook_expectations.selected_book_counts),
    priority_counts: sameJson(selectedPriorityCounts, config.workbook_expectations.priority_counts),
    selected_floor_fields_all_blank: selectedFloorFieldNonblankCount === 0,
    selected_cached_manifest_payload_hits_zero: selectedManifestHitCount === 0,
    target_drawing_payload_read_count_zero: config.source_policy.target_drawing_payload_read === false,
    all_v10a_requirements_retained: requirementRows.length === 22,
    all_v10a_requirements_remain_blocking: requirementRows.every((row) => row.remains_solver_blocking === "YES"),
    physical_assignment_count_zero: config.gates.physical_assignment_count_expected === 0,
    source_archive_not_read_or_rescanned: config.source_policy.source_archive_read === false && config.source_policy.source_archive_rescanned === false,
    official_sources_directory_not_read: config.source_policy.official_sources_directory_read === false,
    no_network_or_external_contact: config.source_policy.network_access_authorized === false && config.source_policy.external_contact_authorized === false,
    solver_blender_thermal_gates_closed: config.source_policy.structural_solver_authorized === false && config.source_policy.blender_authorized === false && config.source_policy.thermal_continuation_authorized === false,
  };
  assert(Object.values(checks).every(Boolean), `V10B validation failure: ${Object.entries(checks).filter(([, passed]) => !passed).map(([name]) => name).join(", ")}`);

  const sourceManifest = {
    iteration: "V10B",
    generated_at_utc: generatedAtUtc,
    validation_status: "PASS",
    scope: "Hashed cached index workbook and three cached PDF manifests only. No target drawing payload, source archive, work/official_sources, network or external contact.",
    v10a_regression_files: regressionAudit,
    cached_index_files: cachedIndexAudit,
    protected_blender_master_before: protectedBefore,
    protected_blender_master_after: protectedAfter,
    source_policy: config.source_policy,
  };
  const registerAudit = {
    iteration: "V10B",
    generated_at_utc: generatedAtUtc,
    validation_status: "PASS",
    workbook: {
      path: "work/xlsx_index/TT_Structural_Archived_Index_Apr_2019.xlsx",
      sha256: config.cached_index_files["work/xlsx_index/TT_Structural_Archived_Index_Apr_2019.xlsx"],
      evidence_class: "ARCHIVE_REGISTER_CLAIM_NOT_OFFICIAL_SOURCE",
      sheet_inspection_ndjson: sheetInspection.ndjson,
      sheet_names: sheetNames,
      sheet1_used_range: usedRange.address,
      sheet1_header: header,
      nonblank_document_row_count: nonblankRegisterRows.length,
    },
    selected_document_count: selectedRows.length,
    selected_book_counts: selectedBookCounts,
    selected_group_counts: selectedGroupCounts,
    selected_priority_counts: selectedPriorityCounts,
    selected_tower_label_counts: selectedTowerCounts,
    selected_drawing_range_status_counts: selectedDrawingRangeCounts,
    selected_floor_field_nonblank_count: selectedFloorFieldNonblankCount,
    selected_exact_payload_hit_count_in_selected_cached_manifests: selectedManifestHitCount,
    target_payload_read_count: 0,
    target_content_transcription_count: 0,
    solver_property_assignment_count: 0,
    known_index_quality_flags: config.known_index_quality_flags,
    selected_rows: inventoryRows,
  };
  const cachePresenceAudit = {
    iteration: "V10B",
    generated_at_utc: generatedAtUtc,
    validation_status: "PASS",
    selected_cached_manifest_count: cachedManifests.length,
    selected_cached_manifest_entry_count: manifestEntries.length,
    manifests: cachedManifests.map((manifest) => ({
      manifest_id: manifest.manifest_id,
      path: manifest.path,
      entry_count: manifest.entries.length,
    })),
    target_document_count: selectedRows.length,
    exact_target_document_hit_count: selectedManifestHitCount,
    interpretation: "No exact WTCI target identifier appears in the three selected cached PDF manifests. This does not prove that the payloads are absent from the read-only source archive or elsewhere; V10B performs no archive scan.",
    rows: selectedRows.map((row) => ({
      document_id: row.document_id,
      selected_cache_manifest_hit_count: row.selected_cache_manifest_hit_count,
      selected_cache_manifest_ids: row.selected_cache_manifest_ids,
      target_payload_read: false,
    })),
  };
  const modelGate = {
    iteration: "V10B",
    generated_at_utc: generatedAtUtc,
    validation_status: "PASS",
    checks,
    qualification: {
      cached_register_audit_complete: true,
      exact_document_identifiers_located_in_register: true,
      prioritized_acquisition_transcription_matrix_complete: true,
      target_payload_acquired: false,
      target_payload_content_transcribed: false,
      tower_a_to_wtc1_mapping_verified: false,
      floor93_99_document_assignment_verified: false,
      as_built_or_revision_authority_verified: false,
      member_sections_assigned: false,
      material_properties_assigned: false,
      connection_laws_assigned: false,
      physical_damage_states_assigned: false,
      structural_solver_ready: false,
      structural_solver_executed: false,
      blender_executed: false,
      physical_validation: false,
    },
    decision: "PASS for a bounded cached-index audit only. The source-acquisition, transcription and structural solver-readiness gates remain CLOSED.",
  };

  const elapsedBeforeResults = Number(process.hrtime.bigint() - started) / 1e9;
  const results = {
    iteration: "V10B",
    dataset_version: config.dataset.version,
    generated_at_utc: generatedAtUtc,
    validation_status: "PASS",
    run: {
      node: process.version,
      platform: `${process.platform}-${process.arch}`,
      hostname: os.hostname(),
      artifact_tool: "SpreadsheetFile.importXlsx via bundled workspace dependency",
      elapsed_seconds_before_final_serialization: Number(elapsedBeforeResults.toFixed(3)),
      deterministic: true,
      structural_solver_executed: false,
      blender_executed: false,
    },
    random_seed: config.dataset.random_seed,
    random_draw_used: config.dataset.random_draw_used,
    scope: config.dataset.scope,
    input_manifest: normalizeRelative(config.outputs.source_manifest),
    output_files: Object.fromEntries(Object.entries(config.outputs).map(([key, value]) => [key, normalizeRelative(value)])),
    observed_or_transcribed_facts: [
      "The hashed structural archive index workbook contains three sheets; Sheet1 uses A1:K95 and exposes eleven named columns.",
      "Each of the 53 predeclared exact WTCI document identifiers occurs once in the register.",
      "The selected rows cover Drawing Books 1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 13 and 20.",
      "All 53 selected register rows have a blank Floors field.",
      "No exact target identifier appears in the 214 entries of the three selected cached PDF manifests.",
    ],
    official_model_results: [
      "V10B creates no official-model result. The 22 V10A source-gate records are inherited only to map documentary needs and remain blocking."
    ],
    archive_claims_used: [
      "The cached April 2019 structural archive index asserts document identifiers, descriptive titles, file-size strings, Tower A/B labels and some drawing-number ranges. Its chain of custody, revision authority and WTC 1 mapping are not independently verified by V10B."
    ],
    model_hypotheses: [
      "P0, P1 and P2 are research-workflow priorities based on expected localization value, not probabilities, authenticity rankings or proof that a payload contains the needed data.",
      "Candidate-group links to V10A requirements are acquisition hypotheses until exact payloads, revisions, floor applicability and cross-references are transcribed.",
    ],
    derived_results: {
      selected_document_count: selectedRows.length,
      selected_book_counts: selectedBookCounts,
      selected_group_counts: selectedGroupCounts,
      priority_counts: selectedPriorityCounts,
      priority_zero_document_count: selectedPriorityCounts.P0_LOCALIZE_FIRST,
      requirement_matrix_row_count: requirementRows.length,
      requirement_closed_count: 0,
      selected_floor_field_nonblank_count: selectedFloorFieldNonblankCount,
      selected_cached_manifest_payload_hit_count: selectedManifestHitCount,
      target_payload_read_count: 0,
      target_content_transcription_count: 0,
      source_archive_read_count: 0,
      physical_assignment_count: 0,
      solver_readiness: false,
      structural_solver_executed: false,
      blender_executed: false,
    },
    contradictions_and_missing_information: [
      "The register's Floors column is blank for every selected row, so it cannot establish Floors 93-99 applicability.",
      "The register uses Tower A/B labels but does not independently establish Tower A as WTC 1 or certify revision/as-built authority.",
      "WTCI-000024-L has a Book 7 row whose recorded endpoint is '2 - C/2'; WTCI-000019-L contains '4 - B! - 300'. Both strings are preserved and require source verification.",
      "No target drawing payload is opened, so no beam mark, section, connection, slab, truss, perimeter or hat-truss property is transcribed.",
      "No exact target ID is present in the three selected cached PDF manifests, but archive-wide absence is not inferred because V10B performs no archive scan.",
    ],
    checks,
    model_gate: modelGate.qualification,
    source_policy: config.source_policy,
    next_iteration: config.next_iteration,
  };

  const checkLines = Object.entries(checks).map(([name, passed]) => `- ${name}: ${passed ? "PASS" : "FAIL"}`).join("\n");
  const p0Ids = priorityRows.filter((row) => row.priority === "P0_LOCALIZE_FIRST").map((row) => row.document_id).join(", ");
  const report = `# WTC 1 - V10B - audit borne de l'index structurel cache

**Validation generale : PASS**

> PASS D'INDEX UNIQUEMENT - AUCUN PLAN CIBLE OUVERT - AUCUNE PROPRIETE SOLVEUR - PORTE D'ACQUISITION ET PORTE SOLVEUR FERMEES

## Conclusion

V10B localise **${selectedRows.length} identifiants documentaires exacts** dans le classeur d'index structurel cache d'avril 2019. Ils couvrent les Books 1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 13 et 20 et sont relies aux 22 exigences documentaires de V10A. Une matrice d'acquisition et de transcription classe ${selectedPriorityCounts.P0_LOCALIZE_FIRST} cibles P0, ${selectedPriorityCounts.P1_PRIMARY_DETAIL} cibles P1 et ${selectedPriorityCounts.P2_SUPPLEMENTAL} cibles P2.

Ce resultat ne ferme aucune exigence physique. Le champ "Floors" est vide pour les ${selectedRows.length} lignes selectionnees, aucun contenu de plan n'est lu, et aucun identifiant cible n'apparait dans les ${manifestEntries.length} entrees des trois manifestes PDF caches selectionnes. Cette derniere absence est strictement locale aux manifestes inspectes : elle ne prouve pas l'absence des fichiers dans l'archive source.

## 1. Faits directement observes ou transcrits

- Le classeur hache contient trois feuilles; Sheet1 occupe ${usedRange.address} avec onze colonnes nommees.
- Les 53 identifiants predeclares apparaissent chacun exactement une fois dans le registre.
- Comptes par priorite : P0=${selectedPriorityCounts.P0_LOCALIZE_FIRST}, P1=${selectedPriorityCounts.P1_PRIMARY_DETAIL}, P2=${selectedPriorityCounts.P2_SUPPLEMENTAL}.
- Cibles P0 : ${p0Ids}.
- Aucun champ de niveau n'est renseigne dans les 53 lignes selectionnees.
- Aucun plan, PDF ou TIFF cible n'est ouvert ou copie pendant V10B.

## 2. Resultats de modeles officiels

- V10B ne produit aucun resultat de modele officiel.
- Les 22 exigences V10A sont reprises uniquement pour relier les besoins documentaires aux familles de plans. Elles restent toutes bloquantes.

## 3. Affirmations provenant des archives

- Le classeur affirme l'existence d'identifiants WTCI, de titres descriptifs, de tailles, d'etiquettes Tower A/B et de certaines plages de dessins.
- Ces champs sont des affirmations de registre d'archive. V10B ne verifie ni chaine de transmission, ni autorite de revision, ni statut as-built, ni correspondance Tower A vers WTC 1.
- Les chaines possiblement fautives "2 - C/2" pour WTCI-000024-L et "4 - B! - 300" pour WTCI-000019-L sont conservees sans correction silencieuse.

## 4. Hypotheses propres au modele

- Les priorites P0/P1/P2 sont des choix de workflow fondes sur la valeur attendue pour localiser les pages pertinentes; elles ne mesurent ni authenticite ni probabilite de contenu utile.
- Le rattachement d'une famille de documents a une exigence V10A est une hypothese d'acquisition tant que les plans exacts, revisions, niveaux et renvois ne sont pas transcrits.
- Aucune affectation Tower A/WTC 1 ou niveaux 93-99 n'est inferee depuis le titre seul.

## 5. Resultats derives

- Documents cibles : ${selectedRows.length}.
- Familles documentaires : ${config.target_groups.length}.
- Lignes de matrice des exigences : ${requirementRows.length}.
- Exigences fermees : 0.
- Entrees des manifestes PDF caches inspectees : ${manifestEntries.length}.
- Identifiants cibles presents dans ces manifestes : ${selectedManifestHitCount}.
- Contenus de plans lus : 0.
- Coordonnees, sections, materiaux, masses, rigidites, capacites, lois de connexion, dommages et credits de chemin de charge assignes : 0.

## 6. Contradictions et informations manquantes

- Le registre ne fournit aucune valeur de niveau pour les cibles selectionnees.
- Les etiquettes Tower A/B ne sont pas une preuve autonome de correspondance WTC 1/WTC 2.
- Les payloads exacts, leurs empreintes, leurs revisions et leurs provenances restent non acquis.
- Les plans de conception ne pourraient de toute facon pas etablir seuls l'etat de dommage physique du 11 septembre 2001 ni les conditions aux limites d'un modele tronque.
- L'absence de cible dans trois manifestes caches n'est pas extrapolee a toute l'archive.

## Portes de validation

${checkLines}

**Decision :** audit d'index PASS; portes d'acquisition, de transcription physique et de preparation au solveur **FERMEES**.

## Livrables principaux

- Audit du registre : ${normalizeRelative(config.outputs.register_audit)}
- Inventaire cible : ${normalizeRelative(config.outputs.document_inventory_csv)}
- Matrice exigences-documents : ${normalizeRelative(config.outputs.requirement_matrix_csv)}
- Matrice priorisee : ${normalizeRelative(config.outputs.priority_matrix_csv)}
- Audit de presence en cache : ${normalizeRelative(config.outputs.cache_presence_audit)}
- Porte solveur : ${normalizeRelative(config.outputs.model_gate)}

## Etape suivante predeclaree - V10C

${config.next_iteration.objective}
`;

  await writeJson(outputs.source_manifest, sourceManifest);
  await writeJson(outputs.register_audit, registerAudit);
  await writeJson(outputs.cache_presence_audit, cachePresenceAudit);
  await writeJson(outputs.model_gate, modelGate);
  await writeJson(outputs.results, results);
  await writeText(outputs.report, report);

  const missingOrEmpty = [];
  for (const [name, filePath] of Object.entries(outputs)) {
    try {
      const stat = await fs.stat(filePath);
      if (stat.size === 0) missingOrEmpty.push(name);
    } catch {
      missingOrEmpty.push(name);
    }
  }
  assert(missingOrEmpty.length === 0, `Missing or empty V10B outputs: ${missingOrEmpty.join(", ")}`);
  await verifyFiles(config.protected_files, "Protected Blender master final V10B");

  const elapsedSeconds = Number(process.hrtime.bigint() - started) / 1e9;
  console.log(JSON.stringify({
    iteration: "V10B",
    status: "PASS",
    selected_document_count: selectedRows.length,
    priority_counts: selectedPriorityCounts,
    requirement_matrix_row_count: requirementRows.length,
    requirements_closed: 0,
    selected_cached_manifest_payload_hit_count: selectedManifestHitCount,
    target_payload_read_count: 0,
    solver_readiness: false,
    solver_executed: false,
    blender_executed: false,
    elapsed_seconds: Number(elapsedSeconds.toFixed(3)),
  }, null, 2));
}


main().catch((error) => {
  console.error(error.stack ?? String(error));
  process.exitCode = 1;
});
