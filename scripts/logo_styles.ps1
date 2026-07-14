#Requires -Version 5.1
# One font → all styles
param(
    [Parameter(Mandatory = $false)]
    [string]$Font = "HelvetIns",
    [switch]$Main
)
& "$PSScriptRoot\logo_build.ps1" -Font $Font -Styles "flat,gradient,twist-depth" -Main:$Main -Proof
