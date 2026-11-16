# QA: roda o bundle e captura screenshots reais DA JANELA do jogo.
# Uso: powershell -File tools\tests\capture_screens.ps1 -Exe <caminho> -OutDir <dir>
param(
    [Parameter(Mandatory = $true)][string]$Exe,
    [Parameter(Mandatory = $true)][string]$OutDir,
    [int]$BootSeconds = 8,
    [int]$PlaySeconds = 6
)

$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

Add-Type @"
using System;
using System.Runtime.InteropServices;
public class Win32Cap {
  [StructLayout(LayoutKind.Sequential)]
  public struct RECT { public int Left, Top, Right, Bottom; }
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hWnd, out RECT r);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
  [DllImport("user32.dll")] public static extern bool PostMessage(IntPtr hWnd, uint Msg, IntPtr wParam, IntPtr lParam);
  [DllImport("user32.dll")] public static extern bool SetFocus(IntPtr hWnd);
  [DllImport("user32.dll")] public static extern void keybd_event(byte bVk, byte bScan, uint dwFlags, UIntPtr dwExtraInfo);
}
"@

function Send-Key($handle, $vk) {
    # teclado sintetizado no nivel do SO (alcanca janelas que exigem foco)
    [Win32Cap]::keybd_event([byte]$vk, 0, 0, [UIntPtr]::Zero)
    Start-Sleep -Milliseconds 90
    [Win32Cap]::keybd_event([byte]$vk, 0, 2, [UIntPtr]::Zero)  # KEYEVENTF_KEYUP
    Start-Sleep -Milliseconds 150
}

if (-not (Test-Path $OutDir)) {
    New-Item -ItemType Directory -Path $OutDir | Out-Null
}

function Get-WindowRect($handle) {
    $r = New-Object Win32Cap+RECT
    [Win32Cap]::GetWindowRect($handle, [ref]$r) | Out-Null
    return $r
}

function Capture($handle, $Path) {
    $r = Get-WindowRect $handle
    $w = $r.Right - $r.Left
    $h = $r.Bottom - $r.Top
    if ($w -le 0 -or $h -le 0) { return $false }
    $bmp = New-Object System.Drawing.Bitmap($w, $h)
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.CopyFromScreen($r.Left, $r.Top, 0, 0, (New-Object System.Drawing.Size($w, $h)))
    $bmp.Save($Path, [System.Drawing.Imaging.ImageFormat]::Png)
    $g.Dispose()
    $bmp.Dispose()
    Write-Host "capturado $Path ($w x $h @ $($r.Left),$($r.Top))"
    return $true
}

$workDir = Split-Path -Parent $Exe
$proc = Start-Process -FilePath $Exe -WorkingDirectory $workDir -PassThru
Start-Sleep -Seconds $BootSeconds
$proc.Refresh()
$handle = $proc.MainWindowHandle
if ($handle -eq [IntPtr]::Zero) {
    Write-Host "janela nao encontrada; capturando tela inteira"
    $b = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
    $bmp = New-Object System.Drawing.Bitmap($b.Width, $b.Height)
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.CopyFromScreen($b.Location, [System.Drawing.Point]::Empty, $b.Size)
    $bmp.Save((Join-Path $OutDir "qa_01_boot.png"), [System.Drawing.Imaging.ImageFormat]::Png)
    $g.Dispose(); $bmp.Dispose()
} else {
    [Win32Cap]::SetForegroundWindow($handle) | Out-Null
    Start-Sleep -Milliseconds 600
    Capture $handle (Join-Path $OutDir "qa_01_boot.png")

    # VK_RETURN=13 (start) -- entra no nivel
    Send-Key $handle 13
    Start-Sleep -Seconds 4
    Capture $handle (Join-Path $OutDir "qa_02_enter.png")

    # VK_RIGHT=39: segura para andar; VK_SPACE=32: pulo
    [Win32Cap]::keybd_event(39, 0, 0, [UIntPtr]::Zero)
    Start-Sleep -Seconds $PlaySeconds
    Capture $handle (Join-Path $OutDir "qa_03_gameplay.png")
    [Win32Cap]::keybd_event(39, 0, 2, [UIntPtr]::Zero)

    Send-Key $handle 32
    Start-Sleep -Seconds 2
    Capture $handle (Join-Path $OutDir "qa_04_jump.png")
}

Stop-Process -Id $proc.Id -Force
Start-Sleep -Seconds 1
Write-Host "screenshots em $OutDir"
