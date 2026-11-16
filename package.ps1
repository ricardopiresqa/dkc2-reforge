# Empacota o bundle Defold em dist/pirate-panic usando o JDK 25 e o bob.jar LOCAIS.
# - Caminhos relativos ao repositorio ($PSScriptRoot) - nenhum caminho absoluto de maquina.
# - NUNCA apaga nada (sem Remove-Item): saida existente => erro, escolha outro -OutDir.
# - `bundle --archive` faz build + archive + bundle num unico passo; SEM --archive o
#   bob nao gera build/default/game.arci e o bundler falha com "game.arci does not exist".
param(
    [string]$OutDir = "dist/pirate-panic",
    [string]$Platform = "x86_64-win32"
)

$ErrorActionPreference = "Stop"

$RepoRoot = $PSScriptRoot
$JavaHome = Join-Path $RepoRoot "tools\jdk-25.0.3+9"
$JavaExe  = Join-Path $JavaHome "bin\java.exe"
$BobJar   = Join-Path $RepoRoot "bob.jar"

if (-not (Test-Path $JavaExe)) {
    Write-Error "JDK 25 local nao encontrado em $JavaExe"
    exit 1
}
if (-not (Test-Path $BobJar)) {
    Write-Error "bob.jar nao encontrado em $BobJar"
    exit 1
}

$OutFull = Join-Path $RepoRoot $OutDir
if (Test-Path $OutFull) {
    Write-Error "Saida ja existe: $OutFull - nao sobrescrevo. Use outro -OutDir ou remova manualmente."
    exit 1
}

$env:JAVA_HOME = $JavaHome
$env:Path = "$JavaHome\bin;" + $env:Path

& $JavaExe -jar $BobJar build bundle --archive --platform $Platform --variant release --bundle-output $OutFull

if ($LASTEXITCODE -eq 0) {
    Write-Host "=== Bundle OK ==="
    Write-Host "Saida: $OutDir"
    Write-Host "Rode: .\play.ps1"
} else {
    Write-Error "Bundle falhou (exit $LASTEXITCODE) - ver docs/delivery/acceptance-matrix.md"
}
