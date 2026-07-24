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
    $obsidianRoot = $obsidianPath.TrimEnd(
        [System.IO.Path]::DirectorySeparatorChar,
        [System.IO.Path]::AltDirectorySeparatorChar
    ) + [System.IO.Path]::DirectorySeparatorChar
    if (-not $backupPath.StartsWith($obsidianRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw 'Restore backup must be inside the selected vault .obsidian directory.'
    }
    $null = Get-Content -LiteralPath $backupPath -Raw -Encoding UTF8 | ConvertFrom-Json
    Copy-Item -LiteralPath $backupPath -Destination $graphPath -Force
    $restoredDocument = Get-Content -LiteralPath $graphPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $restoredHash = (Get-FileHash -LiteralPath $graphPath -Algorithm SHA256).Hash.ToLowerInvariant()
    $backupHash = (Get-FileHash -LiteralPath $backupPath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($restoredHash -ne $backupHash) {
        throw 'Restored graph settings do not match the selected backup.'
    }
    $logPath = Join-Path $vaultPath 'log.md'
    if (Test-Path -LiteralPath $logPath -PathType Leaf) {
        $logLine = '- [' + (Get-Date).ToUniversalTime().ToString('o') +
            "] GRAPH_COLORIZE mode=Restore groups=$(@($restoredDocument.colorGroups).Count) " +
            " backup=$([System.IO.Path]::GetFileName($backupPath))"
        Add-Content -LiteralPath $logPath -Value $logLine -Encoding UTF8
    }
    [pscustomobject]@{
        status = 'restored'
        graph_path = $graphPath
        backup_path = $backupPath
        backup_status = 'verified'
        backup_sha256 = $backupHash
    } | ConvertTo-Json -Depth 5
    exit 0
}

if (-not (Test-Path -LiteralPath $graphPath -PathType Leaf)) {
    $minimal = @'
{
  "collapse-filter": true,
  "search": "",
  "showTags": false,
  "showAttachments": false,
  "hideUnresolved": false,
  "showOrphans": true,
  "collapse-color-groups": false,
  "colorGroups": [],
  "collapse-display": true,
  "showArrow": false,
  "textFadeMultiplier": 0,
  "nodeSizeMultiplier": 1,
  "lineSizeMultiplier": 1,
  "collapse-forces": true,
  "centerStrength": 0.518713248970312,
  "repelStrength": 10,
  "linkStrength": 1,
  "linkDistance": 250,
  "scale": 1,
  "close": true
}
'@
    [System.IO.File]::WriteAllText(
        $graphPath,
        $minimal,
        (New-Object System.Text.UTF8Encoding($false))
    )
}

$raw = Get-Content -LiteralPath $graphPath -Raw -Encoding UTF8
$document = $raw | ConvertFrom-Json
$timestamp = Get-Date -Format 'yyyyMMdd-HHmm'
$backupPath = Join-Path $obsidianPath "graph.json.backup-$timestamp"
$sourceHash = (Get-FileHash -LiteralPath $graphPath -Algorithm SHA256).Hash.ToLowerInvariant()
$backupReused = Test-Path -LiteralPath $backupPath -PathType Leaf
if (-not $backupReused) {
    Copy-Item -LiteralPath $graphPath -Destination $backupPath
}
$backupHash = (Get-FileHash -LiteralPath $backupPath -Algorithm SHA256).Hash.ToLowerInvariant()
if (-not $backupReused -and $sourceHash -ne $backupHash) {
    throw 'Graph settings backup verification failed.'
}
$null = Get-Content -LiteralPath $backupPath -Raw -Encoding UTF8 | ConvertFrom-Json

$palette = @(
    5142951, 15896107, 14767961, 7780786, 5873999,
    15583048, 11565217, 16751527, 10253663, 12234924
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
    $categories = @('concepts', 'entities', 'skills', 'references', 'synthesis', 'projects', 'journal')
    @($categories | Where-Object {
        $categoryPath = Join-Path $vaultPath $_
        (Test-Path -LiteralPath $categoryPath -PathType Container) -and
        @(Get-ChildItem -LiteralPath $categoryPath -Recurse -File -Filter '*.md').Count -gt 0
    })
}

function Get-Tags {
    $counts = @{}
    Get-ChildItem -LiteralPath $vaultPath -Recurse -File -Filter '*.md' |
        Where-Object {
            $_.FullName -notlike "$obsidianPath*" -and
            $_.FullName -notlike "$(Join-Path $vaultPath '_raw')*" -and
            $_.FullName -notlike "$(Join-Path $vaultPath '_archives')*" -and
            $_.FullName -notlike "$(Join-Path $vaultPath 'node_modules')*" -and
            $_.Name -notin @('index.md', 'log.md', '_insights.md')
        } |
        ForEach-Object {
            $text = Get-Content -LiteralPath $_.FullName -Raw -Encoding UTF8
            if ($text -match '(?ms)^---\s*\r?\n(.*?)\r?\n---') {
                $frontmatter = $Matches[1]
                $found = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::OrdinalIgnoreCase)
                $collectingTags = $false
                foreach ($line in @($frontmatter -split '\r?\n')) {
                    if ($line -match '^\s*tags\s*:\s*(.*)$') {
                        $collectingTags = $true
                        $value = $Matches[1].Trim()
                        if ($value -match '^\[([^\]]*)\]$') {
                            foreach ($tag in $Matches[1].Split(',')) {
                                $clean = $tag.Trim().Trim('"').Trim("'")
                                if (-not [string]::IsNullOrWhiteSpace($clean)) {
                                    $null = $found.Add($clean)
                                }
                            }
                            $collectingTags = $false
                        }
                        elseif (-not [string]::IsNullOrWhiteSpace($value)) {
                            $clean = $value.Trim('"').Trim("'")
                            $null = $found.Add($clean)
                            $collectingTags = $false
                        }
                        continue
                    }
                    if (-not $collectingTags) {
                        continue
                    }
                    if ($line -match '^\s*-\s*["'']?([A-Za-z0-9][A-Za-z0-9_/-]*)') {
                        $null = $found.Add($Matches[1])
                        continue
                    }
                    if ($line -match '^\S[^:]*\s*:') {
                        $collectingTags = $false
                    }
                    elseif (-not [string]::IsNullOrWhiteSpace($line) -and $line -notmatch '^\s*#') {
                        $collectingTags = $false
                    }
                }
                foreach ($tag in $found) {
                    if ($tag -like 'visibility/*') {
                        continue
                    }
                    if (-not $counts.ContainsKey($tag)) {
                        $counts[$tag] = 0
                    }
                    $counts[$tag]++
                }
            }
        }
    @($counts.GetEnumerator() |
        Sort-Object @{Expression='Value'; Descending=$true}, @{Expression='Key'; Descending=$false} |
        Select-Object -First 10 |
        ForEach-Object { $_.Key })
}

$groups = @()
$effectiveMode = $Mode
switch ($Mode) {
    'ByCategory' {
        $items = @(Get-Categories)
        for ($index = 0; $index -lt $items.Count; $index++) {
            $groups += New-ColorGroup -Query "path:`"$($items[$index])`"" -Color $palette[$index]
        }
    }
    'ByTag' {
        $items = @(Get-Tags)
        if ($items.Count -eq 0) {
            $items = @(Get-Categories)
            $effectiveMode = 'ByCategory'
            for ($index = 0; $index -lt $items.Count; $index++) {
                $groups += New-ColorGroup -Query "path:`"$($items[$index])`"" -Color $palette[$index]
            }
            break
        }
        for ($index = 0; $index -lt $items.Count; $index++) {
            $groups += New-ColorGroup -Query "tag:#$($items[$index])" -Color $palette[$index]
        }
    }
    'ByVisibility' {
        $items = @('pii', 'internal', 'public')
        $colors = @(14767961, 15896107, 5873999)
        for ($index = 0; $index -lt $items.Count; $index++) {
            $groups += New-ColorGroup -Query "tag:#visibility/$($items[$index])" -Color $colors[$index]
        }
    }
    'Combined' {
        $visibility = @('pii', 'internal', 'public')
        $visibilityColors = @(14767961, 15896107, 5873999)
        for ($index = 0; $index -lt $visibility.Count; $index++) {
            $groups += New-ColorGroup -Query "tag:#visibility/$($visibility[$index])" -Color $visibilityColors[$index]
        }
        $tags = @(Get-Tags)
        for ($index = 0; $index -lt $tags.Count; $index++) {
            $groups += New-ColorGroup -Query "tag:#$($tags[$index])" -Color $palette[$index]
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

function Set-JsonArrayProperty {
    param(
        [string]$Json,
        [string]$PropertyName,
        [string]$ArrayJson
    )
    $pattern = '"' + [regex]::Escape($PropertyName) + '"\s*:'
    $match = [regex]::Match($Json, $pattern)
    if (-not $match.Success) {
        $closing = $Json.LastIndexOf('}')
        if ($closing -lt 0) {
            throw 'Graph settings root is not a JSON object.'
        }
        $prefix = $Json.Substring(0, $closing).TrimEnd()
        $separator = if ($prefix.EndsWith('{')) { '' } else { ',' }
        return $prefix + $separator + [Environment]::NewLine +
            '  "' + $PropertyName + '": ' + $ArrayJson +
            [Environment]::NewLine + $Json.Substring($closing)
    }

    $start = $Json.IndexOf('[', $match.Index + $match.Length)
    if ($start -lt 0) {
        throw "$PropertyName is not a JSON array."
    }
    $depth = 0
    $inString = $false
    $escaped = $false
    $end = -1
    for ($index = $start; $index -lt $Json.Length; $index++) {
        $character = $Json[$index]
        if ($inString) {
            if ($escaped) {
                $escaped = $false
            }
            elseif ($character -eq '\') {
                $escaped = $true
            }
            elseif ($character -eq '"') {
                $inString = $false
            }
            continue
        }
        if ($character -eq '"') {
            $inString = $true
        }
        elseif ($character -eq '[') {
            $depth++
        }
        elseif ($character -eq ']') {
            $depth--
            if ($depth -eq 0) {
                $end = $index
                break
            }
        }
    }
    if ($end -lt 0) {
        throw "$PropertyName array is not terminated."
    }
    return $Json.Substring(0, $start) + $ArrayJson + $Json.Substring($end + 1)
}

$groupsJson = ConvertTo-Json -InputObject @($groups) -Depth 20 -Compress
$json = Set-JsonArrayProperty -Json $raw -PropertyName 'colorGroups' -ArrayJson $groupsJson
[System.IO.File]::WriteAllText($graphPath, $json, (New-Object System.Text.UTF8Encoding($false)))
$verified = Get-Content -LiteralPath $graphPath -Raw -Encoding UTF8 | ConvertFrom-Json
if (@($verified.colorGroups).Count -ne @($groups).Count) {
    throw 'Graph colorGroups verification failed.'
}
$logPath = Join-Path $vaultPath 'log.md'
if (Test-Path -LiteralPath $logPath -PathType Leaf) {
    $logLine = '- [' + (Get-Date).ToUniversalTime().ToString('o') +
        "] GRAPH_COLORIZE mode=$effectiveMode groups=$(@($groups).Count) " +
        "backup=$([System.IO.Path]::GetFileName($backupPath))"
    Add-Content -LiteralPath $logPath -Value $logLine -Encoding UTF8
}

[pscustomobject]@{
    status = 'updated'
    mode = $effectiveMode
    graph_path = $graphPath
    backup_path = $backupPath
    backup_status = 'verified'
    backup_sha256 = $backupHash
    backup_reused = $backupReused
    group_count = @($groups).Count
} | ConvertTo-Json -Depth 5
