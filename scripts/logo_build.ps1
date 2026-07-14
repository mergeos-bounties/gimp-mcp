#Requires -Version 5.1
<#
.SYNOPSIS
  Build Gold One logo variants (UTM fonts).
.EXAMPLE
  .\logo_build.ps1
  .\logo_build.ps1 -Font HelvetIns -Style flat -Main
  .\logo_build.ps1 -Font TimesBold -Styles flat,gradient,twist-depth
  .\logo_build.ps1 -AllFonts -Style flat
  .\logo_build.ps1 -ListFonts
#>
param(
    [string]$Font = "HelvetIns",
    [string]$Style = "flat",
    [string]$Styles = "",
    [switch]$AllFonts,
    [switch]$ListFonts,
    [switch]$Main,
    [switch]$Proof,
    [string]$Src = "$env:USERPROFILE\Downloads\Logo-luxury-original.png",
    [string]$OutDir = "$env:USERPROFILE\Downloads"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
if (-not $Root) { $Root = "D:\ThanhTrucSolutions\mcp\GIMP-mcp" }
$py = Join-Path $Root "scripts\logo_variants.py"

$argsList = @($py)
if ($ListFonts) { $argsList += "--list-fonts" }
else {
    $argsList += @("--font", $Font, "--src", $Src, "--out-dir", $OutDir)
    if ($Styles) { $argsList += @("--styles", $Styles) }
    else { $argsList += @("--style", $Style) }
    if ($AllFonts) { $argsList += "--all-fonts" }
    if ($Main) { $argsList += "--main" }
    if ($Proof) { $argsList += "--proof" }
}

Write-Host "python $($argsList -join ' ')" -ForegroundColor Cyan
& python @argsList
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "Done. Output: $OutDir" -ForegroundColor Green
