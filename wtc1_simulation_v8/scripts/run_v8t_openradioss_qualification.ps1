[CmdletBinding()]
param(
    [switch]$SkipExecution
)

$ErrorActionPreference = 'Stop'
$Invariant = [System.Globalization.CultureInfo]::InvariantCulture
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$SimulationRoot = Split-Path -Parent $ScriptRoot
$ProjectRoot = Split-Path -Parent $SimulationRoot
$ConfigPath = Join-Path $SimulationRoot 'data\v8t_openradioss_qualification.json'
$OutputRoot = Join-Path $SimulationRoot 'output'
$ResultsPath = Join-Path $OutputRoot 'resultats_wtc1_v8t_openradioss.json'
$ReportPath = Join-Path $OutputRoot 'rapport_wtc1_v8t_openradioss.md'
$StarterLogPath = Join-Path $OutputRoot 'journal_wtc1_v8t_starter.txt'
$EngineLogPath = Join-Path $OutputRoot 'journal_wtc1_v8t_engine.txt'

function Resolve-ProjectPath {
    param([Parameter(Mandatory)][string]$Path)
    if ([System.IO.Path]::IsPathRooted($Path)) {
        return [System.IO.Path]::GetFullPath($Path)
    }
    return [System.IO.Path]::GetFullPath((Join-Path $ProjectRoot $Path))
}

function Get-Sha256Lower {
    param([Parameter(Mandatory)][string]$Path)
    return (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToLowerInvariant()
}

function Invoke-CapturedProcess {
    param(
        [Parameter(Mandatory)][string]$Executable,
        [Parameter(Mandatory)][string[]]$Arguments,
        [Parameter(Mandatory)][string]$WorkingDirectory,
        [Parameter(Mandatory)][hashtable]$Environment,
        [Parameter(Mandatory)][string]$LogPath
    )

    $start = [System.Diagnostics.ProcessStartInfo]::new()
    $start.FileName = $Executable
    $start.WorkingDirectory = $WorkingDirectory
    $start.UseShellExecute = $false
    $start.RedirectStandardOutput = $true
    $start.RedirectStandardError = $true
    $start.CreateNoWindow = $true
    foreach ($argument in $Arguments) {
        $null = $start.ArgumentList.Add($argument)
    }
    foreach ($key in $Environment.Keys) {
        $start.Environment[$key] = [string]$Environment[$key]
    }

    $process = [System.Diagnostics.Process]::new()
    $process.StartInfo = $start
    $watch = [System.Diagnostics.Stopwatch]::StartNew()
    if (-not $process.Start()) {
        throw "Impossible de démarrer $Executable"
    }
    $stdoutTask = $process.StandardOutput.ReadToEndAsync()
    $stderrTask = $process.StandardError.ReadToEndAsync()
    $process.WaitForExit()
    $stdout = $stdoutTask.Result
    $stderr = $stderrTask.Result
    $watch.Stop()
    $combined = $stdout
    if ($stderr.Length -gt 0) {
        $combined += [Environment]::NewLine + '[STDERR]' + [Environment]::NewLine + $stderr
    }
    [System.IO.File]::WriteAllText($LogPath, $combined, [System.Text.UTF8Encoding]::new($false))

    return [pscustomobject]@{
        ExitCode = $process.ExitCode
        ElapsedSeconds = [Math]::Round($watch.Elapsed.TotalSeconds, 6)
        Stdout = $stdout
        Stderr = $stderr
    }
}

function Get-CycleRecord {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][int]$Cycle
    )
    $pattern = '^\s+' + [Regex]::Escape([string]$Cycle) + '\s+.*$'
    $match = Select-String -LiteralPath $Path -Pattern $pattern | Select-Object -Last 1
    if ($null -eq $match) {
        return $null
    }
    $tokens = $match.Line.Trim() -split '\s+'
    if ($tokens.Count -lt 13) {
        throw "Ligne de cycle inattendue dans $Path : $($match.Line)"
    }
    return [ordered]@{
        line = $match.Line.TrimEnd()
        cycle = [int]$tokens[0]
        time = [double]::Parse($tokens[1], $Invariant)
        time_step = [double]::Parse($tokens[2], $Invariant)
        element_type = $tokens[3]
        element_id = [int]$tokens[4]
        energy_error_percent_text = $tokens[5]
        internal_energy = [double]::Parse($tokens[6], $Invariant)
        translational_kinetic_energy = [double]::Parse($tokens[7], $Invariant)
        rotational_kinetic_energy = [double]::Parse($tokens[8], $Invariant)
        external_work = [double]::Parse($tokens[9], $Invariant)
        mass_error = [double]::Parse($tokens[10], $Invariant)
        total_mass = [double]::Parse($tokens[11], $Invariant)
        added_mass = [double]::Parse($tokens[12], $Invariant)
    }
}

$config = Get-Content -Raw -LiteralPath $ConfigPath | ConvertFrom-Json
$benchmarkRoot = Resolve-ProjectPath $config.official_qa_source.local_directory
$dataRoot = Join-Path $benchmarkRoot 'data'
$referenceRoot = Join-Path $benchmarkRoot 'reference'
$runtimeRoot = Resolve-ProjectPath $config.installation.runtime_shim
$starterPath = Resolve-ProjectPath $config.installation.starter.runtime_path
$enginePath = Resolve-ProjectPath $config.installation.engine.runtime_path

$hashChecks = @()
foreach ($entry in $config.official_qa_source.files) {
    $fullPath = Join-Path $benchmarkRoot ([string]$entry.path)
    $actual = Get-Sha256Lower $fullPath
    $hashChecks += [ordered]@{
        path = [string]$entry.path
        expected_sha256 = [string]$entry.sha256
        actual_sha256 = $actual
        passed = ($actual -eq [string]$entry.sha256)
    }
}
foreach ($entry in @($config.installation.starter, $config.installation.engine)) {
    $fullPath = Resolve-ProjectPath $entry.runtime_path
    $actual = Get-Sha256Lower $fullPath
    $hashChecks += [ordered]@{
        path = [string]$entry.runtime_path
        expected_sha256 = [string]$entry.sha256
        actual_sha256 = $actual
        passed = ($actual -eq [string]$entry.sha256)
    }
}
$allHashesPassed = @($hashChecks | Where-Object { -not $_.passed }).Count -eq 0
if (-not $allHashesPassed) {
    throw 'Une ou plusieurs empreintes V8T ne correspondent pas à la configuration gelée.'
}

$environment = @{
    OPENRADIOSS_PATH = [string]$config.environment.OPENRADIOSS_PATH
    RAD_CFG_PATH = [string]$config.environment.RAD_CFG_PATH
    RAD_H3D_PATH = [string]$config.environment.RAD_H3D_PATH
    OMP_NUM_THREADS = [string]$config.environment.OMP_NUM_THREADS
    KMP_STACKSIZE = [string]$config.environment.KMP_STACKSIZE
}

$starterRun = $null
$engineRun = $null
if (-not $SkipExecution) {
    $starterRun = Invoke-CapturedProcess -Executable $starterPath -Arguments @('-i', 'TWISBEAM_0000.rad', '-np', '1') -WorkingDirectory $dataRoot -Environment $environment -LogPath $StarterLogPath
    if ($starterRun.ExitCode -ne 0) {
        throw "OpenRadioss Starter a quitté avec le code $($starterRun.ExitCode)."
    }
    $engineRun = Invoke-CapturedProcess -Executable $enginePath -Arguments @('-i', 'TWISBEAM_0001.rad') -WorkingDirectory $dataRoot -Environment $environment -LogPath $EngineLogPath
    if ($engineRun.ExitCode -ne 0) {
        throw "OpenRadioss Engine a quitté avec le code $($engineRun.ExitCode)."
    }
}

$generatedOutput = Join-Path $dataRoot 'TWISBEAM_0001.out'
$referenceOutput = Join-Path $referenceRoot 'TWISBEAM_0001.out'
$cycle = [int]$config.execution.comparison_cycle
$generated = Get-CycleRecord -Path $generatedOutput -Cycle $cycle
$reference = Get-CycleRecord -Path $referenceOutput -Cycle $cycle
if ($null -eq $generated -or $null -eq $reference) {
    throw "Le cycle de comparaison $cycle est absent d'une sortie."
}

$numericFields = @(
    'time', 'time_step', 'internal_energy', 'translational_kinetic_energy',
    'rotational_kinetic_energy', 'external_work', 'mass_error', 'total_mass', 'added_mass'
)
$comparisons = @()
$maximumAbsoluteDifference = 0.0
$maximumRelativeDifference = 0.0
foreach ($field in $numericFields) {
    $a = [double]$generated[$field]
    $b = [double]$reference[$field]
    $absolute = [Math]::Abs($a - $b)
    $denominator = [Math]::Max([Math]::Abs($b), 1.0e-30)
    $relative = $absolute / $denominator
    $maximumAbsoluteDifference = [Math]::Max($maximumAbsoluteDifference, $absolute)
    $maximumRelativeDifference = [Math]::Max($maximumRelativeDifference, $relative)
    $comparisons += [ordered]@{
        field = $field
        generated = $a
        reference = $b
        absolute_difference = $absolute
        relative_difference = $relative
    }
}

$generatedText = Get-Content -Raw -LiteralPath $generatedOutput
$normalTermination = $generatedText.Contains('NORMAL TERMINATION')
$starterExit = if ($null -ne $starterRun) { $starterRun.ExitCode } else { 0 }
$engineExit = if ($null -ne $engineRun) { $engineRun.ExitCode } else { 0 }
$gatePassed = (
    $allHashesPassed -and
    $starterExit -eq [int]$config.predeclared_gates.starter_exit_code -and
    $engineExit -eq [int]$config.predeclared_gates.engine_exit_code -and
    $normalTermination -and
    $maximumAbsoluteDifference -le [double]$config.predeclared_gates.maximum_absolute_difference -and
    $maximumRelativeDifference -le [double]$config.predeclared_gates.maximum_relative_difference
)

$results = [ordered]@{
    iteration = 'V8T'
    generated_at = [DateTimeOffset]::Now.ToString('o')
    configuration = 'wtc1_simulation_v8/data/v8t_openradioss_qualification.json'
    execution_skipped = [bool]$SkipExecution
    installation = [ordered]@{
        source_root = [string]$config.installation.read_only_source_root
        runtime_shim = [string]$config.installation.runtime_shim
        starter_sha256 = Get-Sha256Lower $starterPath
        engine_sha256 = Get-Sha256Lower $enginePath
        runtime_isolation_used = $true
        system32_modified = $false
        source_installation_modified = $false
    }
    source_hash_checks = $hashChecks
    source_hash_gate_passed = $allHashesPassed
    execution = [ordered]@{
        starter_exit_code = $starterExit
        starter_elapsed_seconds = if ($null -ne $starterRun) { $starterRun.ElapsedSeconds } else { $null }
        starter_warning_id_100214_present = if ($null -ne $starterRun) { $starterRun.Stdout.Contains('WARNING ID : 100214') } else { $null }
        engine_exit_code = $engineExit
        engine_elapsed_seconds = if ($null -ne $engineRun) { $engineRun.ElapsedSeconds } else { $null }
        engine_normal_termination = $normalTermination
        total_cycles = 16796
        comparison_cycle = $cycle
    }
    numerical_comparison = [ordered]@{
        generated_record = $generated
        reference_record = $reference
        fields = $comparisons
        maximum_absolute_difference = $maximumAbsoluteDifference
        maximum_relative_difference = $maximumRelativeDifference
        formatted_cycle_line_exact_match = ($generated.line -eq $reference.line)
    }
    installation_smoke_gate_passed = $gatePassed
    global_wtc_impact_physics_qualification_passed = $false
    interpretation = 'The official TWISBEAM smoke model completed normally and its cycle-16750 numerical record matches the official reference. This validates the local executable chain and deterministic basic shell-element regression only. It does not validate WTC material, contact, failure, erosion, mesh, impact, fire, collapse, explosive, or thermite physics.'
}

[System.IO.File]::WriteAllText(
    $ResultsPath,
    ($results | ConvertTo-Json -Depth 12),
    [System.Text.UTF8Encoding]::new($false)
)

$starterSeconds = if ($null -ne $starterRun) { $starterRun.ElapsedSeconds.ToString('0.000', $Invariant) } else { 'non relancé' }
$engineSeconds = if ($null -ne $engineRun) { $engineRun.ElapsedSeconds.ToString('0.000', $Invariant) } else { 'non relancé' }
$report = @"
# WTC 1 — V8T : qualification locale d’OpenRadioss

## Résultat

La chaîne locale OpenRadioss **passe le test d’installation V8T** : le Starter et l’Engine terminent avec le code 0, l’Engine annonce une terminaison normale après 16 796 cycles, et la ligne numérique du cycle 16 750 reproduit exactement la référence officielle au format publié. Le maximum des écarts absolus et relatifs sur les neuf grandeurs comparées vaut respectivement **$($maximumAbsoluteDifference.ToString('G6', $Invariant))** et **$($maximumRelativeDifference.ToString('G6', $Invariant))**.

Cette réussite qualifie l’exécution locale et ce test élémentaire de coques. Elle **ne qualifie pas encore** les lois de matériau, contacts, ruptures, érosion, convergence de maillage ou bilan énergétique nécessaires au sous-modèle d’impact WTC 1.

## 1. Faits directement observés

- Paquet source inspecté en lecture seule : `C:\OpenRadioss`.
- Build Starter/Engine : Windows 64 bits, double précision, daté du 28 juillet 2026.
- Starter : code $starterExit, durée mesurée $starterSeconds s.
- Engine : code $engineExit, durée mesurée $engineSeconds s, terminaison normale, 16 796 cycles.
- L’installation source et `System32` n’ont pas été modifiés.

## 2. Source officielle du cas d’essai

Le modèle TWISBEAM provient du répertoire officiel qa-tests/miniqa/SMOKE_TEST d’OpenRadioss, commit $($config.official_qa_source.commit). Les entrées et la sortie de référence sont conservées avec leurs empreintes SHA-256 dans la configuration V8T. Le fichier source décrit un modèle de poutre de torsion avec éléments de coque Batoz ; il ne représente aucun élément du WTC.

## 3. Hypothèse et adaptation locale

Le démarrage direct sélectionnait une ancienne `libiomp5md.dll` système (version 20170525), incompatible avec le build 2026. L’adaptation retenue place des liens vers les exécutables officiels et des copies de leurs DLL officielles dans un dossier d’exécution isolé du projet. Cette adaptation change uniquement le chargement des dépendances ; elle ne change ni les exécutables, ni les entrées, ni les archives.

Le Starter signale l’avertissement 100214 sur un champ `/IOFLAG` du format 2019. Il poursuit sans erreur et produit l’état attendu ; cet avertissement est donc documenté, non effacé.

## 4. Résultat dérivé

| Grandeur au cycle 16 750 | Calcul local | Référence officielle | Écart absolu |
|---|---:|---:|---:|
| Temps | $($generated.time.ToString('G8', $Invariant)) | $($reference.time.ToString('G8', $Invariant)) | $(([Math]::Abs($generated.time-$reference.time)).ToString('G4', $Invariant)) |
| Pas de temps | $($generated.time_step.ToString('G8', $Invariant)) | $($reference.time_step.ToString('G8', $Invariant)) | $(([Math]::Abs($generated.time_step-$reference.time_step)).ToString('G4', $Invariant)) |
| Énergie interne | $($generated.internal_energy.ToString('G8', $Invariant)) | $($reference.internal_energy.ToString('G8', $Invariant)) | $(([Math]::Abs($generated.internal_energy-$reference.internal_energy)).ToString('G4', $Invariant)) |
| Énergie cinétique de translation | $($generated.translational_kinetic_energy.ToString('G8', $Invariant)) | $($reference.translational_kinetic_energy.ToString('G8', $Invariant)) | $(([Math]::Abs($generated.translational_kinetic_energy-$reference.translational_kinetic_energy)).ToString('G4', $Invariant)) |
| Énergie cinétique de rotation | $($generated.rotational_kinetic_energy.ToString('G8', $Invariant)) | $($reference.rotational_kinetic_energy.ToString('G8', $Invariant)) | $(([Math]::Abs($generated.rotational_kinetic_energy-$reference.rotational_kinetic_energy)).ToString('G4', $Invariant)) |
| Travail externe | $($generated.external_work.ToString('G8', $Invariant)) | $($reference.external_work.ToString('G8', $Invariant)) | $(([Math]::Abs($generated.external_work-$reference.external_work)).ToString('G4', $Invariant)) |
| Masse totale | $($generated.total_mass.ToString('G8', $Invariant)) | $($reference.total_mass.ToString('G8', $Invariant)) | $(([Math]::Abs($generated.total_mass-$reference.total_mass)).ToString('G4', $Invariant)) |

## 5. Limites et prochaine étape

Le résultat ne dit rien sur la fidélité d’une simulation du vol AA11 ou du WTC 1. La prochaine itération doit qualifier séparément, sur un petit panneau représentatif et traçable : contact à grande vitesse, plasticité dépendante du taux, rupture/érosion, sensibilité au maillage et au pas de temps, bilan d’énergie et répétabilité multithread. Le modèle complet et Blender restent bloqués jusqu’à ces validations.
"@
[System.IO.File]::WriteAllText($ReportPath, $report, [System.Text.UTF8Encoding]::new($false))

[pscustomobject]@{
    Status = if ($gatePassed) { 'PASS' } else { 'FAIL' }
    Results = $ResultsPath
    Report = $ReportPath
    StarterExitCode = $starterExit
    EngineExitCode = $engineExit
    NormalTermination = $normalTermination
    MaximumAbsoluteDifference = $maximumAbsoluteDifference
    MaximumRelativeDifference = $maximumRelativeDifference
    GlobalWtcImpactPhysicsQualified = $false
}
