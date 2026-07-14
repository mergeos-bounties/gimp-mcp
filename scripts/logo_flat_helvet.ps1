#Requires -Version 5.1
# Quick: HelvetIns flat only — preserves original metal, solid flat UTM text
param(
    [string]$Src = "$env:USERPROFILE\Downloads\Logo-luxury-original.png",
    [string]$OutDir = "$env:USERPROFILE\Downloads"
)
& "$PSScriptRoot\logo_build.ps1" -Font HelvetIns -Style flat -Main -Proof -Src $Src -OutDir $OutDir
explorer $OutDir
