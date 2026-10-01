[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$HarnessRoot = Split-Path -Parent $PSScriptRoot
$ProjectRoot = Split-Path -Parent $HarnessRoot

$required = @(
    'AGENTS.md',
    '.codex\config.toml',
    'harness\state.json',
    'harness\sources.json',
    'harness\experiments\registry.jsonl',
    'harness\snapshots\source_hashes.json',
    'wtc1_simulation_v8\output\rapport_wtc1_v8g_composants.md',
    'wtc1_simulation_v8\output\resultats_wtc1_v8g_composants.json',
    'wtc1_simulation_v8\data\v8h_core_beam_network.json',
    'wtc1_simulation_v8\scripts\run_v8h_mechanical_core_transfer.py',
    'wtc1_simulation_v8\output\rapport_wtc1_v8h_transfert_mecanique.md',
    'wtc1_simulation_v8\output\resultats_wtc1_v8h_transfert_mecanique.json',
    'wtc1_simulation_v8\output\synthese_wtc1_v8h_transfert_mecanique.png',
    'wtc1_simulation_v8\data\v8i_core_slab_catenary.json',
    'wtc1_simulation_v8\scripts\run_v8i_core_slab_catenary.py',
    'wtc1_simulation_v8\output\rapport_wtc1_v8i_dalle_catenary.md',
    'wtc1_simulation_v8\output\resultats_wtc1_v8i_dalle_catenary.json',
    'wtc1_simulation_v8\output\synthese_wtc1_v8i_dalle_catenary.png',
    'wtc1_simulation_v8\data\v8j_cold_load_path_gate.json',
    'wtc1_simulation_v8\scripts\run_v8j_cold_load_path_gate.py',
    'wtc1_simulation_v8\output\rapport_wtc1_v8j_gate_froid.md',
    'wtc1_simulation_v8\output\resultats_wtc1_v8j_gate_froid.json',
    'wtc1_simulation_v8\output\synthese_wtc1_v8j_gate_froid.png',
    'wtc1_simulation_v8\data\v8k_floor96_nist_topology.json',
    'wtc1_simulation_v8\scripts\run_v8k_floor96_nist_topology.py',
    'wtc1_simulation_v8\output\rapport_wtc1_v8k_topologie_nist.md',
    'wtc1_simulation_v8\output\resultats_wtc1_v8k_topologie_nist.json',
    'wtc1_simulation_v8\output\synthese_wtc1_v8k_topologie_nist.png',
    'wtc1_simulation_v8\data\v8l_multistory_cold_frame.json',
    'wtc1_simulation_v8\scripts\run_v8l_multistory_cold_frame.py',
    'wtc1_simulation_v8\output\rapport_wtc1_v8l_multietages_froid.md',
    'wtc1_simulation_v8\output\resultats_wtc1_v8l_multietages_froid.json',
    'wtc1_simulation_v8\output\synthese_wtc1_v8l_multietages_froid.png',
    'wtc1_simulation_v8\data\v8m_core_floor_perimeter_coupling.json',
    'wtc1_simulation_v8\scripts\run_v8m_core_floor_perimeter_coupling.py',
    'wtc1_simulation_v8\output\rapport_wtc1_v8m_couplage_perimetre_froid.md',
    'wtc1_simulation_v8\output\resultats_wtc1_v8m_couplage_perimetre_froid.json',
    'wtc1_simulation_v8\output\synthese_wtc1_v8m_couplage_perimetre_froid.png',
    'wtc1_simulation_v8\data\v8n_inverse_core_redistribution.json',
    'wtc1_simulation_v8\scripts\run_v8n_inverse_core_redistribution.py',
    'wtc1_simulation_v8\output\rapport_wtc1_v8n_redistribution_inverse_froide.md',
    'wtc1_simulation_v8\output\resultats_wtc1_v8n_redistribution_inverse_froide.json',
    'wtc1_simulation_v8\output\synthese_wtc1_v8n_redistribution_inverse_froide.png',
    'wtc1_simulation_v8\data\v8o_anisotropic_bubble_graph.json',
    'wtc1_simulation_v8\scripts\run_v8o_anisotropic_bubble_graph.py',
    'wtc1_simulation_v8\output\digitisation_wtc1_v8o_floor98.json',
    'wtc1_simulation_v8\output\rapport_wtc1_v8o_graphe_anisotrope.md',
    'wtc1_simulation_v8\output\resultats_wtc1_v8o_graphe_anisotrope.json',
    'wtc1_simulation_v8\output\synthese_wtc1_v8o_graphe_anisotrope.png',
    'wtc1_simulation_v8\data\v8p_vertical_state_graph.json',
    'wtc1_simulation_v8\scripts\run_v8p_vertical_state_graph.py',
    'wtc1_simulation_v8\output\digitisation_wtc1_v8p_verticale.json',
    'wtc1_simulation_v8\output\rapport_wtc1_v8p_graphe_vertical.md',
    'wtc1_simulation_v8\output\resultats_wtc1_v8p_graphe_vertical.json',
    'wtc1_simulation_v8\output\synthese_wtc1_v8p_graphe_vertical.png',
    'wtc1_simulation_v8\data\v8q_floor_network_flow.json',
    'wtc1_simulation_v8\scripts\run_v8q_floor_network_flow.py',
    'wtc1_simulation_v8\output\rapport_wtc1_v8q_flux_reseau.md',
    'wtc1_simulation_v8\output\resultats_wtc1_v8q_flux_reseau.json',
    'wtc1_simulation_v8\output\synthese_wtc1_v8q_flux_reseau.png',
    'wtc1_simulation_v8\data\v8r_capacity_bounded_flow.json',
    'wtc1_simulation_v8\scripts\run_v8r_capacity_bounded_flow.py',
    'wtc1_simulation_v8\output\rapport_wtc1_v8r_flux_bornes.md',
    'wtc1_simulation_v8\output\resultats_wtc1_v8r_flux_bornes.json',
    'wtc1_simulation_v8\output\synthese_wtc1_v8r_flux_bornes.png',
    'wtc1_simulation_v8\data\v8s_wtc1_aircraft_impact_replay.json',
    'wtc1_simulation_v8\scripts\run_v8s_wtc1_aircraft_impact_replay.py',
    'wtc1_simulation_v8\output\rapport_wtc1_v8s_impact_avion.md',
    'wtc1_simulation_v8\output\resultats_wtc1_v8s_impact_avion.json',
    'wtc1_simulation_v8\output\synthese_wtc1_v8s_impact_avion.png',
    'wtc1_simulation_v8\data\v8t_openradioss_qualification.json',
    'wtc1_simulation_v8\scripts\run_v8t_openradioss_qualification.ps1',
    'wtc1_simulation_v8\output\rapport_wtc1_v8t_openradioss.md',
    'wtc1_simulation_v8\output\resultats_wtc1_v8t_openradioss.json',
    'wtc1_simulation_v8\output\journal_wtc1_v8t_starter.txt',
    'wtc1_simulation_v8\output\journal_wtc1_v8t_engine.txt',
    'wtc1_simulation_v8\data\v8w_projectile_freeflight_pairwise_contact.json',
    'wtc1_simulation_v8\scripts\generate_v8w_pairwise_contact.py',
    'wtc1_simulation_v8\scripts\run_v8w_pairwise_contact.py',
    'wtc1_simulation_v8\output\rapport_wtc1_v8w_contact_pairwise.md',
    'wtc1_simulation_v8\output\resultats_wtc1_v8w_contact_pairwise.json',
    'wtc1_simulation_v8\data\v8x_mesh_driver_diagnostic.json',
    'wtc1_simulation_v8\scripts\generate_v8x_mesh_driver.py',
    'wtc1_simulation_v8\scripts\run_v8x_mesh_driver.py',
    'wtc1_simulation_v8\output\rapport_wtc1_v8x_mailles_erosion.md',
    'wtc1_simulation_v8\output\resultats_wtc1_v8x_mailles_erosion.json',
    'wtc1_simulation_v8\data\v8y_nonlocal_failure_regularization.json',
    'wtc1_simulation_v8\scripts\generate_v8y_nonlocal_failure.py',
    'wtc1_simulation_v8\scripts\run_v8y_nonlocal_failure.py',
    'wtc1_simulation_v8\output\rapport_wtc1_v8y_rupture_nonlocale.md',
    'wtc1_simulation_v8\output\resultats_wtc1_v8y_rupture_nonlocale.json',
    'wtc1_simulation_v8\openradioss_runtime\v20260728-win64\starter_win64.exe',
    'wtc1_simulation_v8\openradioss_runtime\v20260728-win64\engine_win64.exe',
    'wtc1_simulation_v8\openradioss_benchmarks\official_smoke_test\data\TWISBEAM_0000.rad',
    'wtc1_simulation_v8\openradioss_benchmarks\official_smoke_test\data\TWISBEAM_0001.rad',
    'wtc1_simulation_v8\openradioss_benchmarks\official_smoke_test\data\TWISBEAMD0B',
    'wtc1_simulation_v8\openradioss_benchmarks\official_smoke_test\reference\TWISBEAM_0001.out',
    'wtc1_3d_v4\output\WTC1_V4_2_MASTER.blend'
)

$missing = @()
foreach ($relative in $required) {
    if (-not (Test-Path -LiteralPath (Join-Path $ProjectRoot $relative))) {
        $missing += $relative
    }
}
if ($missing.Count -gt 0) {
    throw "Fichiers requis manquants: $($missing -join ', ')"
}

$jsonFiles = @(
    'harness\state.json',
    'harness\sources.json',
    'wtc1_simulation_v8\data\v8h_core_beam_network.json',
    'wtc1_simulation_v8\data\v8i_core_slab_catenary.json',
    'wtc1_simulation_v8\data\v8j_cold_load_path_gate.json',
    'wtc1_simulation_v8\data\v8k_floor96_nist_topology.json',
    'wtc1_simulation_v8\data\v8l_multistory_cold_frame.json',
    'wtc1_simulation_v8\data\v8m_core_floor_perimeter_coupling.json',
    'wtc1_simulation_v8\data\v8n_inverse_core_redistribution.json',
    'wtc1_simulation_v8\data\v8o_anisotropic_bubble_graph.json',
    'wtc1_simulation_v8\data\v8p_vertical_state_graph.json',
    'wtc1_simulation_v8\output\resultats_wtc1_v8g_composants.json',
    'wtc1_simulation_v8\output\resultats_wtc1_v8h_transfert_mecanique.json',
    'wtc1_simulation_v8\output\resultats_wtc1_v8i_dalle_catenary.json',
    'wtc1_simulation_v8\output\resultats_wtc1_v8j_gate_froid.json',
    'wtc1_simulation_v8\output\resultats_wtc1_v8k_topologie_nist.json',
    'wtc1_simulation_v8\output\resultats_wtc1_v8l_multietages_froid.json',
    'wtc1_simulation_v8\output\resultats_wtc1_v8m_couplage_perimetre_froid.json',
    'wtc1_simulation_v8\output\resultats_wtc1_v8n_redistribution_inverse_froide.json',
    'wtc1_simulation_v8\output\digitisation_wtc1_v8o_floor98.json',
    'wtc1_simulation_v8\output\resultats_wtc1_v8o_graphe_anisotrope.json',
    'wtc1_simulation_v8\output\digitisation_wtc1_v8p_verticale.json',
    'wtc1_simulation_v8\output\resultats_wtc1_v8p_graphe_vertical.json',
    'wtc1_simulation_v8\data\v8q_floor_network_flow.json',
    'wtc1_simulation_v8\output\resultats_wtc1_v8q_flux_reseau.json',
    'wtc1_simulation_v8\data\v8r_capacity_bounded_flow.json',
    'wtc1_simulation_v8\output\resultats_wtc1_v8r_flux_bornes.json',
    'wtc1_simulation_v8\data\v8s_wtc1_aircraft_impact_replay.json',
    'wtc1_simulation_v8\output\resultats_wtc1_v8s_impact_avion.json',
    'wtc1_simulation_v8\data\v8t_openradioss_qualification.json',
    'wtc1_simulation_v8\output\resultats_wtc1_v8t_openradioss.json',
    'wtc1_simulation_v8\data\v8w_projectile_freeflight_pairwise_contact.json',
    'wtc1_simulation_v8\output\resultats_wtc1_v8w_contact_pairwise.json',
    'wtc1_simulation_v8\data\v8x_mesh_driver_diagnostic.json',
    'wtc1_simulation_v8\output\resultats_wtc1_v8x_mailles_erosion.json',
    'wtc1_simulation_v8\data\v8y_nonlocal_failure_regularization.json',
    'wtc1_simulation_v8\output\resultats_wtc1_v8y_rupture_nonlocale.json'
)
foreach ($relative in $jsonFiles) {
    $null = Get-Content -Raw -LiteralPath (Join-Path $ProjectRoot $relative) | ConvertFrom-Json
}

$registry = Join-Path $ProjectRoot 'harness\experiments\registry.jsonl'
$lines = @(Get-Content -LiteralPath $registry | Where-Object { $_.Trim().Length -gt 0 })
foreach ($line in $lines) {
    $null = $line | ConvertFrom-Json
}

$sources = Get-Content -Raw -LiteralPath (Join-Path $ProjectRoot 'harness\sources.json') | ConvertFrom-Json
$state = Get-Content -Raw -LiteralPath (Join-Path $ProjectRoot 'harness\state.json') | ConvertFrom-Json
$archiveRoots = @($sources.sources | Where-Object { $_.kind -eq 'local_archive' })
$unavailable = @($archiveRoots | Where-Object { -not (Test-Path -LiteralPath $_.path -PathType Container) })

$snapshot = Get-Content -Raw -LiteralPath (Join-Path $ProjectRoot 'harness\snapshots\source_hashes.json') | ConvertFrom-Json
$hashFailures = @()
foreach ($entry in $snapshot.files) {
    $fullPath = Join-Path $ProjectRoot ([string]$entry.path)
    if (-not (Test-Path -LiteralPath $fullPath -PathType Leaf)) {
        $hashFailures += "missing:$($entry.path)"
        continue
    }
    $actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $fullPath).Hash.ToLowerInvariant()
    if ($actual -ne ([string]$entry.sha256).ToLowerInvariant()) {
        $hashFailures += "changed:$($entry.path)"
    }
}
if ($hashFailures.Count -gt 0) {
    throw "Echec des empreintes: $($hashFailures -join ', ')"
}

[pscustomobject]@{
    Status = 'PASS'
    ProjectRoot = $ProjectRoot
    RegistryEntries = $lines.Count
    RequiredFiles = $required.Count
    SourceArchivesDeclared = $archiveRoots.Count
    SourceArchivesUnavailable = $unavailable.Count
    SourceHashesVerified = @($snapshot.files).Count
    CurrentIteration = [string]$state.current_iteration
    NextIteration = [string]$state.next_iteration
}
