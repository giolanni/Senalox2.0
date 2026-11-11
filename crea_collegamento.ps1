# Run via Crea_collegamento.bat, or powershell -File .\crea_collegamento.ps1
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
try {
    $repo = $PSScriptRoot
    $target = Join-Path $repo 'avvia_senalox.bat'
    $icon = Join-Path $repo 'assets\icons\SenaLox.ico'
    foreach ($file in @($target, $icon)) {
        if (-not (Test-Path -LiteralPath $file -PathType Leaf)) {
            throw "File non trovato: $file"
        }
    }
    $desktop = [Environment]::GetFolderPath([Environment+SpecialFolder]::DesktopDirectory)
    if ([string]::IsNullOrWhiteSpace($desktop) -or -not (Test-Path -LiteralPath $desktop -PathType Container)) {
        throw 'Cartella Desktop non disponibile per questo utente.'
    }
    $linkPath = Join-Path $desktop 'SenaLox.lnk'
    $shell = New-Object -ComObject WScript.Shell
    $link = $shell.CreateShortcut($linkPath)
    $link.TargetPath = $target
    $link.WorkingDirectory = $repo
    $link.IconLocation = "$icon,0"
    $link.Description = 'Avvia SenaLox'
    $link.Save()
    Write-Host "Collegamento creato o aggiornato: $linkPath"
    Write-Host 'Se sposti il repository, esegui nuovamente Crea_collegamento.bat.'
    exit 0
} catch {
    Write-Host ("ERRORE: " + $_.Exception.Message) -ForegroundColor Red
    exit 1
}
