[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [string]$ManifestPath = (
        Join-Path (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)) `
            'manifests\dependencies.json'
    ),

    [string[]]$DependencyId,

    [switch]$DryRun
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

Import-Module (Join-Path $PSScriptRoot 'DependencyProbe.psm1') -Force

if (-not (Test-Path -LiteralPath $ManifestPath -PathType Leaf)) {
    Write-Error "Dependency manifest not found: $ManifestPath"
    exit 2
}

try {
    $manifest = Get-Content -Raw -LiteralPath $ManifestPath | ConvertFrom-Json
}
catch {
    Write-Error "Dependency manifest is not valid JSON: $($_.Exception.Message)"
    exit 2
}

if ($manifest.schema_version -ne 1 -or $null -eq $manifest.dependencies) {
    Write-Error 'Unsupported dependency manifest contract.'
    exit 2
}

$selected = @($manifest.dependencies)
$requestedIds = @(
    $DependencyId | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
)
if ($requestedIds.Count -gt 0) {
    $requested = @{}
    foreach ($id in $requestedIds) {
        $requested[$id] = $true
    }
    $selected = @($selected | Where-Object { $requested.ContainsKey([string]$_.id) })
    $found = @($selected | ForEach-Object { [string]$_.id })
    $missing = @($requestedIds | Where-Object { $found -notcontains $_ })
    if ($missing.Count -gt 0) {
        Write-Error "Unknown dependency id(s): $($missing -join ', ')"
        exit 2
    }
}

$results = @(
    foreach ($dependency in $selected) {
        Invoke-DependencyProbe -Dependency $dependency -DryRun:$DryRun
    }
)

ConvertTo-Json -InputObject @($results) -Depth 8
