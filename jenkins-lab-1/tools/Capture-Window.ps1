<#
.SYNOPSIS
  Captures an on-screen window (matched by its title) to a PNG file.
.NOTES
  Uses Graphics.CopyFromScreen over the window's rectangle after bringing it to
  the foreground. This is more reliable for console host windows than PrintWindow,
  which frequently returns an all-black bitmap for conhost/Windows Terminal.
#>
param(
    [Parameter(Mandatory = $true)][string]$TitleContains,
    [Parameter(Mandatory = $true)][string]$OutFile,
    [int]$SettleMs = 900
)

Add-Type -AssemblyName System.Drawing

if (-not ("WinCap" -as [type])) {
    Add-Type @"
using System;
using System.Runtime.InteropServices;
public class WinCap {
    [StructLayout(LayoutKind.Sequential)]
    public struct RECT { public int Left, Top, Right, Bottom; }

    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hWnd, out RECT r);
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
    [DllImport("user32.dll")] public static extern bool IsIconic(IntPtr hWnd);
    [DllImport("dwmapi.dll")] public static extern int DwmGetWindowAttribute(IntPtr hWnd, int attr, out RECT val, int size);
}
"@
}

# --- locate the window -------------------------------------------------------
$proc = Get-Process |
        Where-Object { $_.MainWindowTitle -and $_.MainWindowTitle -like "*$TitleContains*" } |
        Select-Object -First 1

if (-not $proc) { throw "No visible window whose title contains '$TitleContains'." }
$hwnd = $proc.MainWindowHandle

# --- bring it to the front and let the compositor settle ---------------------
if ([WinCap]::IsIconic($hwnd)) { [void][WinCap]::ShowWindow($hwnd, 9) }  # SW_RESTORE
[void][WinCap]::SetForegroundWindow($hwnd)
Start-Sleep -Milliseconds $SettleMs

# --- measure: prefer the DWM frame bounds so the drop shadow is excluded -----
$rect = New-Object WinCap+RECT
$size = [Runtime.InteropServices.Marshal]::SizeOf([type]"WinCap+RECT")
if ([WinCap]::DwmGetWindowAttribute($hwnd, 9, [ref]$rect, $size) -ne 0) {   # DWMWA_EXTENDED_FRAME_BOUNDS
    [void][WinCap]::GetWindowRect($hwnd, [ref]$rect)
}

$w = $rect.Right - $rect.Left
$h = $rect.Bottom - $rect.Top
if ($w -le 0 -or $h -le 0) { throw "Window '$($proc.MainWindowTitle)' reported a zero-size rectangle." }

# --- grab the pixels ---------------------------------------------------------
$bmp = New-Object System.Drawing.Bitmap($w, $h)
$gfx = [System.Drawing.Graphics]::FromImage($bmp)
$gfx.CopyFromScreen($rect.Left, $rect.Top, 0, 0, (New-Object System.Drawing.Size($w, $h)))

$dir = Split-Path -Parent $OutFile
if ($dir -and -not (Test-Path $dir)) { New-Item -ItemType Directory -Force $dir | Out-Null }
$bmp.Save($OutFile, [System.Drawing.Imaging.ImageFormat]::Png)

$gfx.Dispose(); $bmp.Dispose()
Write-Output "Saved $OutFile  ($w x $h)  from window '$($proc.MainWindowTitle)'"
