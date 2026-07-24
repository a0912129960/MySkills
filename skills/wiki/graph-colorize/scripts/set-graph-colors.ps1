[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Vault,

    [Parameter(Mandatory = $true)]
    [ValidateSet('ByTag', 'ByCategory', 'ByVisibility', 'Combined', 'Custom', 'Clear', 'Restore')]
    [string]$Mode,

    [string]$CustomMap,
    [string]$RestoreBackup
)

$ErrorActionPreference = 'Stop'
$vaultPath = [System.IO.Path]::GetFullPath((Resolve-Path -LiteralPath $Vault).Path)
$obsidianPath = Join-Path $vaultPath '.obsidian'
$graphPath = Join-Path $obsidianPath 'graph.json'

if (-not (Test-Path -LiteralPath $obsidianPath -PathType Container)) {
    throw "Obsidian configuration directory not found: $obsidianPath"
}

if ($Mode -eq 'Restore') {
    if ([string]::IsNullOrWhiteSpace($RestoreBackup)) {
        throw 'Restore requires -RestoreBackup.'
    }
    $backupPath = [System.IO.Path]::GetFullPath((Resolve-Path -LiteralPath $RestoreBackup).Path)
    if (-not $backupPath.StartsWith($obsidianPath, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw 'Restore backup must be inside the selected vault .obsidian directory.'
    }
    $null = Get-Content -LiteralPath $backupPath -Raw -Encoding UTF8 | ConvertFrom-Json
    Copy-Item -LiteralPath $backupPath -Destination $graphPath -Force
    $null = Get-Content -LiteralPath $graphPath -Raw -Encoding UTF8 | ConvertFrom-Json
    [pscustomobject]@{
        status = 'restored'
        graph_path = $graphPath
        backup_path = $backupPath
    } | ConvertTo-Json -Depth 5
    exit 0
}

if (-not (Test-Path -LiteralPath $graphPath -PathType Leaf)) {
    throw "Obsidian graph settings not found: $graphPath"
}

$raw = Get-Content -LiteralPath $graphPath -Raw -Encoding UTF8
$document = $raw | ConvertFrom-Json
$timestamp = Get-Date -Format 'yyyyMMdd-HHmmss-fff'
$backupPath = Join-Path $obsidianPath "graph.json.myskills.$timestamp.bak"
Copy-Item -LiteralPath $graphPath -Destination $backupPath

$palette = @(
    0xE57373, 0x64B5F6, 0x81C784, 0xFFD54F, 0xBA68C8,
    0x4DB6AC, 0xFF8A65, 0x7986CB, 0xA1887F, 0x90A4AE
)

function New-ColorGroup {
    param([string]$Query, [int]$Color)
    [pscustomobject]@{
        query = $Query
        color = [pscustomobject]@{
            a = 1
            rgb = $Color
        }
    }
}

function Get-Categories {
    $excluded = @('.obsidian', '_raw', '_archives', 'attachments')
    @(Get-ChildItem -LiteralPath $vaultPath -Directory |
        Where-Object { $excluded -notcontains $_.Name } |
        Sort-Object -Property Name |
        ForEach-Object { $_.Name })
}

function Get-Tags {
    $tags = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::OrdinalIgnoreCase)
    Get-ChildItem -LiteralPath $vaultPath -Recurse -File -Filter '*.md' |
        Where-Object {
            $_.FullName -notlike "$obsidianPath*" -and
            $_.FullName -notlike "$(Join-Path $vaultPath '_raw')*" -and
            $_.FullName -notlike "$(Join-Path $vaultPath '_archives')*"
        } |
        ForEach-Object {
            $text = Get-Content -LiteralPath $_.FullName -Raw -Encoding UTF8
            foreach ($match in [regex]::Matches($text, '(?m)(?<![\w/])#([A-Za-z0-9][A-Za-z0-9_/-]*)')) {
                $null = $tags.Add($match.Groups[1].Value)
            }
            if ($text -match '(?ms)^---\s*\r?\n(.*?)\r?\n---') {
                foreach ($match in [regex]::Matches($Matches[1], '(?m)^\s*-\s*["'']?([A-Za-z0-9][A-Za-z0-9_/-]*)')) {
                    $null = $tags.Add($match.Groups[1].Value)
                }
            }
        }
    @($tags | Sort-Object)
}

$groups = @()
switch ($Mode) {
    'ByCategory' {
        $items = @(Get-Categories)
        for ($index = 0; $index -lt $items.Count; $index++) {
            $groups += New-ColorGroup -Query "path:$($items[$index])" -Color $palette[$index % $palette.Count]
        }
    }
    'ByTag' {
        $items = @(Get-Tags)
        for ($index = 0; $index -lt $items.Count; $index++) {
            $groups += New-ColorGroup -Query "tag:#$($items[$index])" -Color $palette[$index % $palette.Count]
        }
    }
    'ByVisibility' {
        $items = @('private', 'personal', 'shared', 'public')
        for ($index = 0; $index -lt $items.Count; $index++) {
            $groups += New-ColorGroup -Query "tag:#visibility/$($items[$index])" -Color $palette[$index]
        }
    }
    'Combined' {
        $visibility = @('private', 'personal', 'shared', 'public')
        for ($index = 0; $index -lt $visibility.Count; $index++) {
            $groups += New-ColorGroup -Query "tag:#visibility/$($visibility[$index])" -Color $palette[$index]
        }
        $categories = @(Get-Categories)
        for ($index = 0; $index -lt $categories.Count; $index++) {
            $groups += New-ColorGroup -Query "path:$($categories[$index])" -Color $palette[($index + 4) % $palette.Count]
        }
    }
    'Custom' {
        if ([string]::IsNullOrWhiteSpace($CustomMap)) {
            throw 'Custom mode requires -CustomMap.'
        }
        $customPath = [System.IO.Path]::GetFullPath((Resolve-Path -LiteralPath $CustomMap).Path)
        $mapping = Get-Content -LiteralPath $customPath -Raw -Encoding UTF8 | ConvertFrom-Json
        foreach ($property in @($mapping.psobject.Properties | Sort-Object -Property Name)) {
            $hex = [string]$property.Value
            if ($hex -notmatch '^#[0-9A-Fa-f]{6}$') {
                throw "Invalid custom color for $($property.Name): $hex"
            }
            $color = [Convert]::ToInt32($hex.Substring(1), 16)
            $groups += New-ColorGroup -Query $property.Name -Color $color
        }
    }
    'Clear' {
        $groups = @()
    }
}

if ($document.psobject.Properties.Name -contains 'colorGroups') {
    $document.colorGroups = @($groups)
}
else {
    $document | Add-Member -MemberType NoteProperty -Name colorGroups -Value @($groups)
}

$json = $document | ConvertTo-Json -Depth 100
[System.IO.File]::WriteAllText($graphPath, $json + [Environment]::NewLine, (New-Object System.Text.UTF8Encoding($false)))
$verified = Get-Content -LiteralPath $graphPath -Raw -Encoding UTF8 | ConvertFrom-Json
if (@($verified.colorGroups).Count -ne @($groups).Count) {
    throw 'Graph colorGroups verification failed.'
}

[pscustomobject]@{
    status = 'updated'
    mode = $Mode
    graph_path = $graphPath
    backup_path = $backupPath
    group_count = @($groups).Count
} | ConvertTo-Json -Depth 5
