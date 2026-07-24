[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern("^[a-z0-9]+(?:-[a-z0-9]+)*$")]
    [string]$Name,

    [Parameter(Mandatory = $true)]
    [ValidateSet("engineering", "productivity", "wiki", "obsidian", "qmd")]
    [string]$Category,

    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$Description,

    [Parameter(Mandatory = $true)]
    [ValidateSet("explicit", "implicit")]
    [string]$Invocation,

    [Parameter(DontShow = $true)]
    [string]$Root = (Split-Path -Parent $PSScriptRoot)
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = "Stop"

try {
    $resolvedRoot = [IO.Path]::GetFullPath($Root)
    $skillsRoot = Join-Path $resolvedRoot "skills"
    $target = Join-Path (Join-Path $skillsRoot $Category) $Name
    $resolvedTarget = [IO.Path]::GetFullPath($target)
    $prefix = [IO.Path]::GetFullPath($skillsRoot).TrimEnd(
        [IO.Path]::DirectorySeparatorChar,
        [IO.Path]::AltDirectorySeparatorChar
    ) + [IO.Path]::DirectorySeparatorChar
    if (-not $resolvedTarget.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to scaffold outside the repository skills directory."
    }
    if (Test-Path -LiteralPath $resolvedTarget) {
        throw "Skill directory already exists: $resolvedTarget"
    }

    $agents = Join-Path $resolvedTarget "agents"
    New-Item -ItemType Directory -Path $agents -Force | Out-Null
    try {
        $manualLine = ""
        $allowImplicit = "true"
        if ($Invocation -eq "explicit") {
            $manualLine = "disable-model-invocation: true`n"
            $allowImplicit = "false"
        }
        $skillText = @"
---
name: $Name
description: >-
  $Description
$manualLine---

# $Name

Describe the workflow, its boundaries, and its observable output.
"@.Replace("`r`n", "`n")

        $displayName = ($Name -split "-") |
            ForEach-Object {
                if ($_.Length -eq 0) { $_ } else {
                    $_.Substring(0, 1).ToUpperInvariant() + $_.Substring(1)
                }
            }
        $prompt = "Use `$" + $Name + " for this workflow."
        $metadata = @"
interface:
  display_name: "$($displayName -join ' ')"
  short_description: "$Description"
  default_prompt: "$prompt"
policy:
  allow_implicit_invocation: $allowImplicit
"@.Replace("`r`n", "`n")

        $utf8 = New-Object Text.UTF8Encoding($false)
        [IO.File]::WriteAllText(
            (Join-Path $resolvedTarget "SKILL.md"),
            $skillText,
            $utf8
        )
        [IO.File]::WriteAllText(
            (Join-Path $agents "openai.yaml"),
            $metadata,
            $utf8
        )
    }
    catch {
        if (Test-Path -LiteralPath $resolvedTarget) {
            Remove-Item -LiteralPath $resolvedTarget -Recurse -Force
        }
        throw
    }

    Write-Output "Created $resolvedTarget"
    Write-Output (
        "Next: add the candidate and its targets to inventory/skills.json, sync the " +
        "repository manifests, then run skill-evaluator against the current directory " +
        "digest. Creation is incomplete until a passing source-controlled attestation exists."
    )
    exit 0
}
catch {
    [Console]::Error.WriteLine($_.Exception.Message)
    exit 1
}
