<#
.SYNOPSIS
  Runs the JAR Jenkins archived and screenshots the game while it plays.
.NOTES
  Two Windows-specific details:
   * Lanterna refuses to start from `java.exe` when a console is attached
     ("To start java on Windows, use javaw!"), so the artifact is launched with
     `javaw.exe`. Lanterna then falls back to its Swing terminal emulator, a
     window titled "SwingTerminalFrame".
   * The snake moves right on a 150 ms tick and hits the wall about 1.5 s in,
     so a burst of frames is captured from the moment the window appears and
     the clearest one is kept.
#>
param(
    [string]$Jar    = "C:\Users\lokes\jenkins-lab\artifact-run\snake.jar",
    [string]$OutDir = "C:\Users\lokes\jenkins-lab\snake-frames"
)

$ErrorActionPreference = 'Stop'
$tools = Split-Path -Parent $MyInvocation.MyCommand.Path
$title = 'SwingTerminalFrame'
New-Item -ItemType Directory -Force $OutDir | Out-Null
Get-ChildItem $OutDir -Filter *.png | Remove-Item -Force

$proc = Start-Process javaw -ArgumentList '-jar', $Jar -PassThru

# wait for the Swing terminal window to exist
$deadline = (Get-Date).AddSeconds(30)
while ((Get-Date) -lt $deadline) {
    if (Get-Process | Where-Object { $_.MainWindowTitle -eq $title }) { break }
    Start-Sleep -Milliseconds 100
}
Write-Output "window appeared after $([int]((Get-Date) - $proc.StartTime).TotalMilliseconds) ms"

$offsets = @(0, 350, 700, 1050, 1400, 1800, 2600, 3600)
$prev = 0
foreach ($o in $offsets) {
    if ($o -gt $prev) { Start-Sleep -Milliseconds ($o - $prev) }
    $prev = $o
    try {
        & (Join-Path $tools 'Capture-Window.ps1') -TitleContains $title `
            -OutFile (Join-Path $OutDir ("frame-{0:d4}ms.png" -f $o)) -SettleMs 40 | Out-Null
        Write-Output "  captured +$o ms"
    } catch {
        Write-Warning "+$o ms: $($_.Exception.Message)"
    }
}

try { Stop-Process -Id $proc.Id -Force -ErrorAction Stop } catch { }
Get-ChildItem $OutDir | Select-Object Name, Length
