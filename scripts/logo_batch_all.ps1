#Requires -Version 5.1
<#
.SYNOPSIS
  Build flat + gradient + twist-depth for key UTM fonts (quality flat, no scrub).
#>
param(
    [string]$Src = "$env:USERPROFILE\Downloads\Logo-luxury-original.png",
    [string]$OutDir = "$env:USERPROFILE\Downloads"
)

$ErrorActionPreference = "Stop"
$here = $PSScriptRoot
$fonts = @("HelvetIns", "AvoBold", "TimesBold", "SwissBold", "Facebook", "Neutra")
$styles = "flat,gradient,twist-depth"

foreach ($f in $fonts) {
    Write-Host "`n=== $f ===" -ForegroundColor Yellow
    & "$here\logo_build.ps1" -Font $f -Styles $styles -Src $Src -OutDir $OutDir -Proof
}

# Main default: HelvetIns flat (user preferred)
& "$here\logo_build.ps1" -Font HelvetIns -Style flat -Main -Src $Src -OutDir $OutDir
Write-Host "`nAll batch done." -ForegroundColor Green
