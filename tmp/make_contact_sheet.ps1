param(
    [Parameter(Mandatory = $true)][string]$InputDirectory,
    [Parameter(Mandatory = $true)][int]$FirstPage,
    [Parameter(Mandatory = $true)][int]$LastPage,
    [Parameter(Mandatory = $true)][string]$OutputPath,
    [int]$Columns = 6,
    [int]$CellWidth = 480,
    [int]$CellHeight = 380
)

Add-Type -AssemblyName System.Drawing
$count = $LastPage - $FirstPage + 1
$rows = [Math]::Ceiling($count / $Columns)
$bitmap = New-Object System.Drawing.Bitmap ($Columns * $CellWidth), ($rows * $CellHeight)
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$graphics.Clear([System.Drawing.Color]::White)
$font = New-Object System.Drawing.Font 'Arial', 18
$brush = [System.Drawing.Brushes]::Black

try {
    for ($page = $FirstPage; $page -le $LastPage; $page++) {
        $index = $page - $FirstPage
        $col = $index % $Columns
        $row = [Math]::Floor($index / $Columns)
        $path = Join-Path $InputDirectory ('page-{0:D4}.jpg' -f $page)
        $source = [System.Drawing.Image]::FromFile($path)
        try {
            $scale = [Math]::Min(($CellWidth - 8) / $source.Width, ($CellHeight - 36) / $source.Height)
            $width = [int]($source.Width * $scale)
            $height = [int]($source.Height * $scale)
            $x = $col * $CellWidth + [int](($CellWidth - $width) / 2)
            $y = $row * $CellHeight + 28
            $graphics.DrawImage($source, $x, $y, $width, $height)
            $graphics.DrawString(('PDF page {0}' -f $page), $font, $brush, $col * $CellWidth + 4, $row * $CellHeight + 2)
        }
        finally {
            $source.Dispose()
        }
    }
    $bitmap.Save($OutputPath, [System.Drawing.Imaging.ImageFormat]::Jpeg)
}
finally {
    $font.Dispose()
    $graphics.Dispose()
    $bitmap.Dispose()
}
