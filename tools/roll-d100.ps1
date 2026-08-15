param(
    [Parameter(Mandatory = $true)][string]$Id,
    [string]$SceneId,
    [Parameter(Mandatory = $true)][string]$Subject,
    [Parameter(Mandatory = $true)][string]$Intent,
    [Parameter(Mandatory = $true)][ValidateSet('execution', 'reaction', 'arrangement')][string]$Scope,
    [Parameter(Mandatory = $true)][string]$Stakes,
    [Parameter(Mandatory = $true)][ValidateRange(1, 100)][int]$Difficulty,
    [ValidateRange(0, 10)][int]$CharacterScore,
    [string[]]$Modifier = @(),
    [string]$EventId,
    [string]$Journal
)

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
    if ($pythonCommand) { $pythonPath = $pythonCommand.Source }
}
if (-not $pythonPath) {
    throw 'Nie znaleziono Pythona. Oczekiwano Anacondy albo polecenia python w PATH.'
}

$arguments = @(
    (Join-Path $PSScriptRoot 'roll_d100.py'),
    '--id', $Id,
    '--subject', $Subject,
    '--intent', $Intent,
    '--scope', $Scope,
    '--stakes', $Stakes,
    '--difficulty', $Difficulty
)
if ($SceneId) { $arguments += @('--scene-id', $SceneId) }
if ($PSBoundParameters.ContainsKey('CharacterScore')) {
    $arguments += @('--character-score', $CharacterScore)
}
foreach ($entry in $Modifier) { $arguments += @('--modifier', $entry) }
if ($EventId) { $arguments += @('--event-id', $EventId) }
if ($Journal) { $arguments += @('--journal', $Journal) }

& $pythonPath @arguments
exit $LASTEXITCODE
