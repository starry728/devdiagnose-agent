param([ValidateSet('Setup','Start','Check')][string]$Action = 'Start')
$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Interpreter = Join-Path $ProjectRoot '.conda\devdiagnose\python.exe'
Set-Location -LiteralPath $ProjectRoot
$env:PYTHONNOUSERSITE = '1'
$env:PYTHONUTF8 = '1'
New-Item -ItemType Directory -Path (Join-Path $ProjectRoot '.runtime\tmp') -Force | Out-Null
$env:TEMP = Join-Path $ProjectRoot '.runtime\tmp'
$env:TMP = $env:TEMP
function Invoke-Checked {
    param([string]$Program, [string[]]$Arguments)
    & $Program @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Command failed (exit $LASTEXITCODE): $Program" }
}
if ($Action -eq 'Setup') {
    if (-not (Test-Path -LiteralPath $Interpreter)) {
        $BasePython = if ($env:CONDA_PYTHON_EXE) { $env:CONDA_PYTHON_EXE } elseif (Test-Path -LiteralPath 'D:\myApps\myMiniconda3\python.exe') { 'D:\myApps\myMiniconda3\python.exe' } else { 'python' }
        Invoke-Checked $BasePython @('-m','conda','create','--prefix',(Join-Path $ProjectRoot '.conda\devdiagnose'),'python=3.12','pip','--yes')
    }
    $Packages = if (Test-Path -LiteralPath 'requirements.lock.txt') { @('-m','pip','install','-r','requirements.lock.txt') } else { @('-m','pip','install','-e','.[dev]','--no-build-isolation') }
    Invoke-Checked $Interpreter $Packages
    Push-Location (Join-Path $ProjectRoot 'frontend')
    try { Invoke-Checked 'npm.cmd' @('ci'); Invoke-Checked 'npm.cmd' @('run','build') } finally { Pop-Location }
    Write-Host 'Setup complete.'
} elseif ($Action -eq 'Check') {
    Invoke-Checked $Interpreter @('-m','pytest','-q')
    Invoke-Checked $Interpreter @('-m','ruff','check','backend','tests')
    Push-Location (Join-Path $ProjectRoot 'frontend')
    try { Invoke-Checked 'npm.cmd' @('run','build') } finally { Pop-Location }
} else {
    if (-not (Test-Path -LiteralPath $Interpreter)) { throw 'Run .\scripts\Project.ps1 Setup first.' }
    if (-not (Test-Path -LiteralPath 'frontend\dist\index.html')) { throw 'Frontend is not built. Run .\scripts\Project.ps1 Setup.' }
    Write-Host 'DevDiagnose: http://127.0.0.1:8765 (Ctrl+C to stop)'
    Invoke-Checked $Interpreter @('-m','uvicorn','devdiagnose.api:app','--host','127.0.0.1','--port','8765')
}
