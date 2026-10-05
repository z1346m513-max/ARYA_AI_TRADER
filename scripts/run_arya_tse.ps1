param(
    [Parameter(Position=0)]
    [ValidateSet("analyze", "list-symbols", "scan")]
    [string]$Command = "list-symbols",
    [Parameter(Position=1)]
    [string]$Ticker = "FOOLAD"
)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root
if (Test-Path ".\.venv\Scripts\Activate.ps1") { .\.venv\Scripts\Activate.ps1 }
$env:PYTHONPATH = "src"
switch ($Command) {
    "analyze" { python -m arya.cli.main analyze --ticker $Ticker }
    "list-symbols" { python -m arya.cli.main list-symbols }
    "scan" { python -m arya.cli.main scan }
}
