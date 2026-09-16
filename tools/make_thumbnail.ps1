<#
.SYNOPSIS
  Fit a printer photo into a PrusaSlicer Configuration Wizard thumbnail (180 x 256 PNG).

.DESCRIPTION
  PrusaSlicer shows <MODEL_ID>_thumbnail.png from %APPDATA%\PrusaSlicer\vendor\<Vendor>\
  in the Configuration Wizard. Every bundled vendor uses a 180 x 256 portrait PNG.
  This scales the source to fit inside that box (no cropping) and pads with white.
  Uses System.Drawing only, so PNG / JPG / BMP / GIF sources work without Python packages.

.EXAMPLE
  .\tools\make_thumbnail.ps1 -Source photo.png -Destination Potterbot\vendor\Potterbot\POTTERBOT9_thumbnail.png
#>
param(
    [Parameter(Mandatory = $true)] [string] $Source,
    [Parameter(Mandatory = $true)] [string] $Destination,
    [int] $Width = 180,
    [int] $Height = 256,
    [string] $Background = "White"
)

$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Drawing

$src = [System.Drawing.Image]::FromFile((Resolve-Path $Source).Path)
try {
    $scale = [Math]::Min($Width / $src.Width, $Height / $src.Height)
    $w = [int][Math]::Round($src.Width * $scale)
    $h = [int][Math]::Round($src.Height * $scale)
    $x = [int](($Width - $w) / 2)
    $y = [int](($Height - $h) / 2)

    $bmp = New-Object System.Drawing.Bitmap $Width, $Height
    try {
        $g = [System.Drawing.Graphics]::FromImage($bmp)
        try {
            $g.Clear([System.Drawing.Color]::FromName($Background))
            $g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
            $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
            $g.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
            $g.DrawImage($src, (New-Object System.Drawing.Rectangle $x, $y, $w, $h))
        }
        finally { $g.Dispose() }

        $destDir = Split-Path -Parent $Destination
        if ($destDir -and -not (Test-Path $destDir)) { New-Item -ItemType Directory -Path $destDir | Out-Null }
        $full = [System.IO.Path]::GetFullPath((Join-Path (Get-Location) $Destination))
        if ([System.IO.Path]::IsPathRooted($Destination)) { $full = $Destination }
        $bmp.Save($full, [System.Drawing.Imaging.ImageFormat]::Png)
        Write-Output "Wrote $full ($Width x $Height, image $w x $h)"
    }
    finally { $bmp.Dispose() }
}
finally { $src.Dispose() }
