<#
.SYNOPSIS
  Runs a command in a fresh, visible PowerShell console window and screenshots it.
.DESCRIPTION
  Each lab step gets its own console window so the screenshot shows the banner,
  the command and its full output with nothing else in frame. The child window
  drops a sentinel file when the command finishes, so the parent knows exactly
  when the output is complete and it is safe to capture.
#>
param(
    [Parameter(Mandatory = $true)][string]$Banner,
    [Parameter(Mandatory = $true)][string]$Command,
    [Parameter(Mandatory = $true)][string]$OutFile,
    [string]$WorkDir      = "C:\Users\lokes\jenkins-lab",
    [int]   $Cols         = 118,
    [int]   $Rows         = 34,
    [int]   $TimeoutSec   = 300,
    [switch]$KeepOpen
)

$ErrorActionPreference = 'Stop'
$tools   = Split-Path -Parent $MyInvocation.MyCommand.Path
$token   = "JENKINS-LAB-$(Get-Random -Minimum 10000 -Maximum 99999)"
$tmpDir  = Join-Path $env:TEMP "jenkins-lab-steps"
New-Item -ItemType Directory -Force $tmpDir | Out-Null
$script  = Join-Path $tmpDir "$token.ps1"
$done    = Join-Path $tmpDir "$token.done"

@"
`$Host.UI.RawUI.WindowTitle = '$token'
try {
    `$Host.UI.RawUI.BufferSize = New-Object Management.Automation.Host.Size($Cols, 3000)
    `$Host.UI.RawUI.WindowSize  = New-Object Management.Automation.Host.Size($Cols, $Rows)
} catch { }
Set-Location '$WorkDir'
Write-Host '=== $Banner ===' -ForegroundColor Cyan
try { $Command } catch { Write-Host `$_.Exception.Message -ForegroundColor Red }
New-Item -ItemType File '$done' -Force | Out-Null
"@ | Set-Content -Path $script -Encoding utf8

$proc = Start-Process powershell.exe `
        -ArgumentList '-NoExit', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $script `
        -PassThru

# wait for the command inside the window to finish
$deadline = (Get-Date).AddSeconds($TimeoutSec)
while (-not (Test-Path $done) -and (Get-Date) -lt $deadline) { Start-Sleep -Milliseconds 400 }
if (-not (Test-Path $done)) { Write-Warning "Step '$Banner' did not signal completion within $TimeoutSec s; capturing anyway." }
Start-Sleep -Milliseconds 600

& (Join-Path $tools 'Capture-Window.ps1') -TitleContains $token -OutFile $OutFile

if (-not $KeepOpen) {
    try { Stop-Process -Id $proc.Id -Force -ErrorAction Stop } catch { }
}
Remove-Item $script, $done -Force -ErrorAction SilentlyContinue
