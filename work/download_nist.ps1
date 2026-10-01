$ErrorActionPreference = 'Stop'
$out = Join-Path $PSScriptRoot 'official_sources'
New-Item -ItemType Directory -Force -Path $out | Out-Null

$docs = [ordered]@{
  'ncstar1.pdf' = 'https://nvlpubs.nist.gov/nistpubs/Legacy/NCSTAR/ncstar1.pdf'
  'ncstar1-1a.pdf' = 'https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=101000'
  'ncstar1-2a.pdf' = 'https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=101013'
  'ncstar1-3.pdf' = 'https://nvlpubs.nist.gov/nistpubs/Legacy/NCSTAR/ncstar1-3.pdf'
  'ncstar1-3a.pdf' = 'https://nvlpubs.nist.gov/nistpubs/Legacy/NCSTAR/ncstar1-3a.pdf'
  'ncstar1-3b.pdf' = 'https://nvlpubs.nist.gov/nistpubs/Legacy/NCSTAR/ncstar1-3b.pdf'
  'ncstar1-3c.pdf' = 'https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=101019'
  'ncstar1-3d.pdf' = 'https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=101021'
  'ncstar1-6.pdf' = 'https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=101279'
  'ncstar1-6c.pdf' = 'https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=101043'
  'ncstar1-6d.pdf' = 'https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=101366'
}

foreach ($entry in $docs.GetEnumerator()) {
  $dest = Join-Path $out $entry.Key
  if (-not (Test-Path -LiteralPath $dest)) {
    & curl.exe -L --fail --silent --show-error $entry.Value -o $dest
    if ($LASTEXITCODE -ne 0) { throw "Download failed: $($entry.Value)" }
  }
  $item = Get-Item -LiteralPath $dest
  [pscustomobject]@{ Name = $item.Name; MB = [math]::Round($item.Length / 1MB, 2) }
}
