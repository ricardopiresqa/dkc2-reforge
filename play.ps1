# Roda o executavel do bundle gerado por package.ps1.
# Caminho relativo ao repositorio ($PSScriptRoot) - nenhum caminho absoluto de maquina.
param(
    [string]$BundleDir = "dist/pirate-panic",
    [switch]$BuildFirst
)

$ErrorActionPreference = "Stop"

$RepoRoot = $PSScriptRoot

if ($BuildFirst) {
    & (Join-Path $RepoRoot "package.ps1")
    if ($LASTEXITCODE -ne 0) {
        Write-Error "package.ps1 falhou, sem bundle para rodar"
        exit 1
    }
}

$BundleFull = Join-Path $RepoRoot $BundleDir
if (-not (Test-Path $BundleFull)) {
    Write-Error "Bundle nao encontrado em $BundleDir - rode .\package.ps1 primeiro"
    exit 1
}

# Layout do bundle varia com o titulo do projeto; localiza o .exe dentro dele.
$Exe = Get-ChildItem $BundleFull -Recurse -Filter *.exe | Select-Object -First 1
if (-not $Exe) {
    Write-Error "Nenhum .exe em $BundleDir - bundle incompleto (ver docs/delivery/acceptance-matrix.md)"
    exit 1
}

Write-Host "Executando: $($Exe.FullName)"
& $Exe.FullName
exit $LASTEXITCODE