[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Vault,

    [Parameter(Mandatory = $true)]
    [ValidateSet('ArchiveOnly', 'Rebuild', 'Restore')]
    [string]$Mode,

    [string]$ArchiveRoot,
    [string]$RestoreFrom,
    [switch]$ConfirmDestructive
)

$ErrorActionPreference = 'Stop'
$vaultPath = [System.IO.Path]::GetFullPath((Resolve-Path -LiteralPath $Vault).Path)
if (-not (Test-Path -LiteralPath $vaultPath -PathType Container)) {
    throw "Vault not found: $vaultPath"
}
if (-not ((Test-Path -LiteralPath (Join-Path $vaultPath 'index.md')) -or
          (Test-Path -LiteralPath (Join-Path $vaultPath '.manifest.json')))) {
    throw 'Refusing operation because the target does not look like a Wiki vault.'
}
if (($Mode -eq 'Rebuild' -or $Mode -eq 'Restore') -and -not $ConfirmDestructive) {
    throw "$Mode requires -ConfirmDestructive after explicit user approval."
}

if ([string]::IsNullOrWhiteSpace($ArchiveRoot)) {
    if ([string]::IsNullOrWhiteSpace($env:LOCALAPPDATA)) {
        throw 'LOCALAPPDATA is required when -ArchiveRoot is not supplied.'
    }
    $ArchiveRoot = Join-Path $env:LOCALAPPDATA 'MySkills\wiki-archives'
}
$archiveRootPath = [System.IO.Path]::GetFullPath($ArchiveRoot)
if ($archiveRootPath.StartsWith($vaultPath + [System.IO.Path]::DirectorySeparatorChar,
        [System.StringComparison]::OrdinalIgnoreCase)) {
    throw 'ArchiveRoot must be outside the live vault.'
}
$null = New-Item -ItemType Directory -Path $archiveRootPath -Force

function Get-RelativePath {
    param([string]$Base, [string]$Path)
    $baseUri = New-Object System.Uri(($Base.TrimEnd('\') + '\'))
    $pathUri = New-Object System.Uri($Path)
    [System.Uri]::UnescapeDataString($baseUri.MakeRelativeUri($pathUri).ToString()).Replace('/', '\')
}

function Get-Inventory {
    param([string]$Root)
    $items = @()
    Get-ChildItem -LiteralPath $Root -Recurse -File |
        Where-Object { $_.Name -ne 'inventory.json' } |
        Sort-Object -Property FullName |
        ForEach-Object {
            $items += [pscustomobject]@{
                path = Get-RelativePath -Base $Root -Path $_.FullName
                sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
                length = $_.Length
            }
        }
    @($items)
}

function New-VerifiedArchive {
    param([string]$SourceVault)
    $timestamp = Get-Date -Format 'yyyyMMdd-HHmmss-fff'
    $safeName = ([System.IO.Path]::GetFileName($SourceVault) -replace '[^A-Za-z0-9._-]', '_')
    $destination = Join-Path (Join-Path $archiveRootPath $safeName) $timestamp
    $null = New-Item -ItemType Directory -Path $destination -Force

    Get-ChildItem -LiteralPath $SourceVault -Force |
        Where-Object { $_.Name -notin @('.obsidian', '_archives') } |
        ForEach-Object {
            Copy-Item -LiteralPath $_.FullName -Destination $destination -Recurse
        }

    $sourceInventory = @(Get-Inventory -Root $SourceVault |
        Where-Object {
            $_.path -notlike '.obsidian\*' -and
            $_.path -notlike '_archives\*'
        })
    $archiveInventory = @(Get-Inventory -Root $destination)
    $sourceJson = $sourceInventory | ConvertTo-Json -Depth 5 -Compress
    $archiveJson = $archiveInventory | ConvertTo-Json -Depth 5 -Compress
    if ($sourceJson -ne $archiveJson) {
        throw "Archive verification failed: $destination"
    }
    $inventoryDocument = [pscustomobject]@{
        format = 1
        source_vault = $SourceVault
        created_at = (Get-Date).ToUniversalTime().ToString('o')
        files = $archiveInventory
    }
    $inventoryDocument | ConvertTo-Json -Depth 8 |
        Set-Content -LiteralPath (Join-Path $destination 'inventory.json') -Encoding UTF8
    return $destination
}

function Assert-Archive {
    param([string]$Path)
    $resolved = [System.IO.Path]::GetFullPath((Resolve-Path -LiteralPath $Path).Path)
    $inventoryPath = Join-Path $resolved 'inventory.json'
    if (-not (Test-Path -LiteralPath $inventoryPath -PathType Leaf)) {
        throw "Archive inventory not found: $inventoryPath"
    }
    $expected = Get-Content -LiteralPath $inventoryPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $actual = @(Get-Inventory -Root $resolved)
    $expectedJson = @($expected.files) | ConvertTo-Json -Depth 5 -Compress
    $actualJson = $actual | ConvertTo-Json -Depth 5 -Compress
    if ($expectedJson -ne $actualJson) {
        throw "Archive digest verification failed: $resolved"
    }
    return $resolved
}

function Clear-LiveWiki {
    Get-ChildItem -LiteralPath $vaultPath -Force |
        Where-Object { $_.Name -notin @('.obsidian', '_archives') } |
        ForEach-Object {
            $resolved = [System.IO.Path]::GetFullPath($_.FullName)
            if (-not $resolved.StartsWith($vaultPath + [System.IO.Path]::DirectorySeparatorChar,
                    [System.StringComparison]::OrdinalIgnoreCase)) {
                throw "Refusing to clear path outside vault: $resolved"
            }
            Remove-Item -LiteralPath $resolved -Recurse -Force
        }
}

$currentArchive = New-VerifiedArchive -SourceVault $vaultPath
$result = [ordered]@{
    status = 'archived'
    mode = $Mode
    vault_path = $vaultPath
    archive_path = $currentArchive
    archive_status = 'verified'
}

if ($Mode -eq 'Rebuild') {
    Clear-LiveWiki
    $null = New-Item -ItemType Directory -Path (Join-Path $vaultPath '_raw') -Force
    foreach ($name in @('index.md', 'hot.md', 'log.md')) {
        Set-Content -LiteralPath (Join-Path $vaultPath $name) -Value "# $name" -Encoding UTF8
    }
    Set-Content -LiteralPath (Join-Path $vaultPath '.manifest.json') -Value '{"sources":{}}' -Encoding UTF8
    $result.status = 'rebuilt'
}
elseif ($Mode -eq 'Restore') {
    if ([string]::IsNullOrWhiteSpace($RestoreFrom)) {
        throw 'Restore requires -RestoreFrom.'
    }
    $restorePath = Assert-Archive -Path $RestoreFrom
    Clear-LiveWiki
    Get-ChildItem -LiteralPath $restorePath -Force |
        Where-Object { $_.Name -ne 'inventory.json' } |
        ForEach-Object {
            Copy-Item -LiteralPath $_.FullName -Destination $vaultPath -Recurse
        }
    $result.status = 'restored'
    $result.restore_source = $restorePath
}

[pscustomobject]$result | ConvertTo-Json -Depth 6
