$ErrorActionPreference = 'Stop'

$pythonCandidates = @(
    'C:\ProgramData\anaconda3\python.exe',
    'C:\Users\User\anaconda3\python.exe',
    'C:\Users\User\Anaconda3\python.exe'
)

$pythonPath = $pythonCandidates |
    Where-Object { Test-Path -LiteralPath $_ } |
    Select-Object -First 1

if (-not $pythonPath) {
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCommand) {
        $pythonPath = $pythonCommand.Source
    }
}

if (-not $pythonPath) {
    throw 'Nie znaleziono Pythona. Oczekiwano Anacondy albo polecenia python w PATH.'
}

& $pythonPath (Join-Path $PSScriptRoot 'validate_project.py')
exit $LASTEXITCODE

