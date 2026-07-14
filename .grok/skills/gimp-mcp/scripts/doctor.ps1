#Requires -Version 5.1
<#
.SYNOPSIS
  Health-check gimp-mcp + optional local GIMP console (live).
.PARAMETER Live
  Set GIMP_MCP_MODE=live and run live-smoke.
.PARAMETER Repo
  Optional path to gimp-mcp repo (for pytest).
#>
param(
    [switch]$Live,
    [string]$Repo = ""
)

$ErrorActionPreference = "Continue"

function Write-Section([string]$Title) {
    Write-Host ""
    Write-Host "=== $Title ===" -ForegroundColor Cyan
}

$consoleCandidates = @(
    "$env:LOCALAPPDATA\Programs\GIMP 3\bin\gimp-console.exe",
    "$env:LOCALAPPDATA\Programs\GIMP 3\bin\gimp-console-3.exe",
    "$env:LOCALAPPDATA\Programs\GIMP 3\bin\gimp-console-3.2.exe",
    "C:\Program Files\GIMP 3\bin\gimp-console.exe",
    "C:\Program Files\GIMP 2\bin\gimp-console.exe"
)

Write-Section "gimp-mcp CLI"
$cli = Get-Command gimp-mcp -ErrorAction SilentlyContinue
if (-not $cli) {
    Write-Host "FAIL: gimp-mcp not on PATH." -ForegroundColor Red
    Write-Host '  pip install "git+https://github.com/mergeos-bounties/gimp-mcp.git"'
    exit 1
}
Write-Host "OK: $($cli.Source)"
& gimp-mcp version

Write-Section "GIMP console discovery"
$found = $null
foreach ($c in $consoleCandidates) {
    if (Test-Path -LiteralPath $c) {
        Write-Host "FOUND: $c"
        if (-not $found) { $found = $c }
    }
}
if ($found) {
    $env:GIMP_MCP_BIN = $found
    try {
        Write-Host ((& $found --version 2>&1 | Out-String).Trim())
    } catch {
        Write-Host "WARN: could not run --version: $_" -ForegroundColor Yellow
    }
} else {
    Write-Host "WARN: no gimp-console in common paths (mock still works)" -ForegroundColor Yellow
}

Write-Section "doctor (mock)"
$env:GIMP_MCP_MODE = "mock"
& gimp-mcp doctor

if ($Live) {
    Write-Section "doctor (live)"
    $env:GIMP_MCP_MODE = "live"
    if ($found) { $env:GIMP_MCP_BIN = $found }
    & gimp-mcp doctor
    Write-Section "live-smoke"
    & gimp-mcp live-smoke
} else {
    Write-Section "demo (mock)"
    & gimp-mcp demo
}

if ($Repo -and (Test-Path -LiteralPath (Join-Path $Repo "pyproject.toml"))) {
    Write-Section "pytest"
    Push-Location $Repo
    try {
        if (Get-Command pytest -ErrorAction SilentlyContinue) {
            & pytest -q
        } else {
            Write-Host "SKIP: pytest not on PATH"
        }
    } finally {
        Pop-Location
    }
}

Write-Section "done"
Write-Host "Tip: re-run with -Live to exercise gimp-console."
