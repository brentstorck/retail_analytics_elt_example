# run.ps1 — one-shot local pipeline for Windows/PowerShell.
# Usage:  .\run.ps1            (full pipeline)
#         .\run.ps1 -DbtOnly   (skip extract/load, just rebuild dbt)

param(
    [switch]$DbtOnly
)

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot

# Loader and dbt must agree on the warehouse location.
if (-not $env:DUCKDB_PATH) {
    $env:DUCKDB_PATH = Join-Path $root "warehouse\retail.duckdb"
}
$env:DBT_PROFILES_DIR = Join-Path $root "retail_dbt"
Write-Host "DUCKDB_PATH = $env:DUCKDB_PATH" -ForegroundColor Cyan

if (-not $DbtOnly) {
    Write-Host "==> extract" -ForegroundColor Green
    python -m pipeline.extract
    Write-Host "==> load" -ForegroundColor Green
    python -m pipeline.load
}

Write-Host "==> dbt deps + seed + build" -ForegroundColor Green
Push-Location (Join-Path $root "retail_dbt")
try {
    dbt deps
    dbt seed
    dbt build
    dbt docs generate
} finally {
    Pop-Location
}

Write-Host "==> export marts for Hex" -ForegroundColor Green
python -m pipeline.export

Write-Host "Done. Try: streamlit run dashboard/app.py" -ForegroundColor Cyan
