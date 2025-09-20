param(
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]] $Args
)

# Clear the terminal for a clean test run
# ear-Host

# Run pytest via python -m pytest so we don't depend on pytest being on PATH.
# Usage: ./scripts/run-tests.ps1 [pytest-args]

$python = "python"

Write-Host "Running: $python -m pytest $($Args -join ' ')"

# Build pytest arguments; disable pytest-cov plugin by default to keep
# output focused on failures. If the user passed an explicit -p or --cov
# argument, respect it and do not inject the disable flag.
$argsLower = $Args | ForEach-Object { $_.ToLowerInvariant() }
$injectDisableCov = -not ($argsLower -contains '-p' -or $argsLower -match '--cov')

$pytestArgs = @('-m', 'pytest')
if ($injectDisableCov) {
    $pytestArgs += @('-p', 'no:cov')
}
$pytestArgs += $Args

# Invoke pytest directly so output streams to the console and the script
# returns the same exit code as pytest.
& $python @pytestArgs

exit $LASTEXITCODE
