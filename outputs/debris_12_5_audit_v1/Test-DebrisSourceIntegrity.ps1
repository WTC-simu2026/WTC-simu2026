[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$baselinePath = Join-Path $scriptRoot 'source_hashes_baseline.json'
$resultPath = Join-Path $scriptRoot 'source_integrity_after.json'

$baseline = Get-Content -LiteralPath $baselinePath -Raw | ConvertFrom-Json
$checks = foreach ($entry in $baseline) {
    if (-not (Test-Path -LiteralPath $entry.path -PathType Leaf)) {
        [pscustomobject]@{
            path = $entry.path
            expected_size_bytes = [long]$entry.size_bytes
            actual_size_bytes = $null
            expected_sha256 = $entry.sha256
            actual_sha256 = $null
            status = 'MISSING'
        }
        continue
    }

    $item = Get-Item -LiteralPath $entry.path
    $actualHash = (Get-FileHash -LiteralPath $entry.path -Algorithm SHA256).Hash.ToLowerInvariant()
    $matches = ($item.Length -eq [long]$entry.size_bytes) -and ($actualHash -eq $entry.sha256)
    [pscustomobject]@{
        path = $entry.path
        expected_size_bytes = [long]$entry.size_bytes
        actual_size_bytes = [long]$item.Length
        expected_sha256 = $entry.sha256
        actual_sha256 = $actualHash
        status = if ($matches) { 'MATCH' } else { 'MISMATCH' }
    }
}

$overall = if (($checks.status | Where-Object { $_ -ne 'MATCH' }).Count -eq 0) { 'PASS' } else { 'FAIL' }
$result = [ordered]@{
    schema_version = 1
    generated_utc = [DateTime]::UtcNow.ToString('o')
    purpose = 'Lecture seule : comparaison des tailles et SHA-256 avant/apres audit.'
    overall_status = $overall
    source_count = $checks.Count
    checks = @($checks)
}

$result | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $resultPath -Encoding utf8
$result

if ($overall -ne 'PASS') {
    exit 1
}
