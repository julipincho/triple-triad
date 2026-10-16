$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
$projectRoot = Split-Path -Parent $PSScriptRoot
$evidenceRoot = Join-Path $projectRoot 'auditoria/migracion_avatares_20261015'
$manifestPath = Join-Path $evidenceRoot 'generados.json'
$items = Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
$masterRoot = Join-Path $evidenceRoot 'masters'
$exportRoot = Join-Path $evidenceRoot 'exportados'
New-Item -ItemType Directory -Force -Path $masterRoot,$exportRoot | Out-Null
foreach ($item in $items) {
    if ($item.id -notmatch '^[a-z0-9_]+$') { throw 'Invalid asset ID' }
    $masterPath = Join-Path $masterRoot ($item.id + '.png')
    Copy-Item -LiteralPath $item.path -Destination $masterPath
    $sourceImage = [System.Drawing.Image]::FromFile($masterPath)
    $width = 256
    $height = 256
    if ($item.tipo -eq 'fondo') { $width = 1280; $height = 720 }
    $exportImage = New-Object System.Drawing.Bitmap($width, $height, ([System.Drawing.Imaging.PixelFormat]::Format32bppArgb))
    $graphics = [System.Drawing.Graphics]::FromImage($exportImage)
    try {
        $graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::NearestNeighbor
        $graphics.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::Half
        $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::None
        $graphics.CompositingMode = [System.Drawing.Drawing2D.CompositingMode]::SourceCopy
        $graphics.DrawImage($sourceImage, (New-Object System.Drawing.Rectangle(0, 0, $width, $height)), 0, 0, $sourceImage.Width, $sourceImage.Height, [System.Drawing.GraphicsUnit]::Pixel)
        $exportPath = Join-Path $exportRoot ($item.id + '.png')
        $exportImage.Save($exportPath, [System.Drawing.Imaging.ImageFormat]::Png)
        $item | Add-Member -NotePropertyName source_path -NotePropertyValue $item.path -Force
        $item.path = $exportPath
    }
    finally { $graphics.Dispose(); $exportImage.Dispose(); $sourceImage.Dispose() }
}
$json = ConvertTo-Json -InputObject @($items) -Depth 10
[System.IO.File]::WriteAllText($manifestPath, $json, (New-Object System.Text.UTF8Encoding($false)))
Write-Output ('Normalized {0} new assets; masters preserved.' -f $items.Count)
