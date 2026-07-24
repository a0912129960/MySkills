[CmdletBinding()]
param(
    [ValidateSet("Install", "Status", "Verify", "Uninstall")]
    [string]$Action = "Install",

    [string[]]$Skills = @(),

    [switch]$DryRun,

    [switch]$Yes,

    [switch]$AdoptExact,

    [switch]$BackupAndReplace,

    [switch]$RegisterQmdMcp,

    [Parameter(DontShow = $true)]
    [string]$StatePath = (
        Join-Path ([Environment]::GetFolderPath("LocalApplicationData")) "MySkills\state.json"
    )
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Import-Module -Force (Join-Path $PSScriptRoot "installer_core.psm1")
$dependencyModule = Join-Path $PSScriptRoot "dependencies\DependencyProbe.psm1"
if (Test-Path -LiteralPath $dependencyModule -PathType Leaf) {
    Import-Module -Force $dependencyModule
}

function Resolve-ManagedSkills {
    param(
        [Parameter(Mandatory = $true)]
        [object]$Inventory,
        [string[]]$RequestedNames
    )

    $managed = @($Inventory.skills | Where-Object { $_.state -eq "managed" })
    if ($RequestedNames.Count -eq 0) {
        return @($managed | Sort-Object -Property managed_name)
    }

    $byName = @{}
    foreach ($skill in $managed) {
        $byName[$skill.managed_name] = $skill
    }
    $unknown = @($RequestedNames | Where-Object { -not $byName.ContainsKey($_) })
    if ($unknown.Count -gt 0) {
        throw "Unknown Managed Skill: $($unknown -join ', ')"
    }
    return @(
        $RequestedNames |
            Select-Object -Unique |
            ForEach-Object { $byName[$_] }
    )
}

function Get-PlatformDefinitions {
    $userProfile = [Environment]::GetFolderPath("UserProfile")
    $localAppData = [Environment]::GetFolderPath("LocalApplicationData")
    return @(
        [PSCustomObject]@{
            Id = "codex"
            Commands = @(
                [PSCustomObject]@{ Command = "codex"; Arguments = @("--version") }
            )
            Destination = Join-Path $userProfile ".agents\skills"
            Support = "primary"
        },
        [PSCustomObject]@{
            Id = "claude-code"
            Commands = @(
                [PSCustomObject]@{ Command = "claude"; Arguments = @("--version") }
            )
            Destination = Join-Path $userProfile ".claude\skills"
            Support = "primary"
        },
        [PSCustomObject]@{
            Id = "antigravity-cli"
            Commands = @(
                [PSCustomObject]@{ Command = "agy"; Arguments = @("--version") },
                [PSCustomObject]@{
                    Command = Join-Path $localAppData "agy\bin\agy.exe"
                    Arguments = @("--version")
                }
            )
            Destination = Join-Path $userProfile ".gemini\antigravity-cli\skills"
            Support = "compatibility-copy"
        }
    )
}

function Invoke-ExecutableProbe {
    param(
        [Parameter(Mandatory = $true)]
        [object[]]$Candidates
    )

    foreach ($candidate in $Candidates) {
        $expanded = [Environment]::ExpandEnvironmentVariables(
            [string]$candidate.Command
        )
        $resolved = $null
        if ([IO.Path]::IsPathRooted($expanded)) {
            if (Test-Path -LiteralPath $expanded -PathType Leaf) {
                $resolved = $expanded
            }
        }
        else {
            $command = Get-Command $expanded -ErrorAction SilentlyContinue |
                Select-Object -First 1
            if ($null -ne $command) {
                $resolved = $command.Source
                if ([string]::IsNullOrWhiteSpace($resolved)) {
                    $resolved = $command.Definition
                }
            }
        }
        if ([string]::IsNullOrWhiteSpace($resolved)) {
            continue
        }

        try {
            $output = (& $resolved @($candidate.Arguments) 2>&1 | Out-String).Trim()
            $exitCode = $LASTEXITCODE
            if ($null -eq $exitCode) {
                $exitCode = 0
            }
            if ($exitCode -eq 0) {
                return [PSCustomObject]@{
                    Available = $true
                    Executable = $resolved
                    Output = $output
                }
            }
        }
        catch {
            continue
        }
    }

    return [PSCustomObject]@{
        Available = $false
        Executable = $null
        Output = $null
    }
}

function Read-State {
    param([string]$Path)

    $records = @{}
    $backups = @()
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        return [PSCustomObject]@{ Records = $records; Backups = $backups }
    }

    try {
        $document = Get-Content -Raw -LiteralPath $Path | ConvertFrom-Json
        if ($document.schema_version -ne 1) {
            throw "unsupported schema version"
        }
        foreach ($record in @($document.installations)) {
            $records["$($record.platform)|$($record.skill)"] = $record
        }
        $backups = @($document.backups)
    }
    catch {
        Write-Warning (
            "State is missing or invalid for ownership purposes; existing targets " +
            "will be treated as unowned. Details: $($_.Exception.Message)"
        )
        $records = @{}
        $backups = @()
    }
    return [PSCustomObject]@{ Records = $records; Backups = $backups }
}

function Write-State {
    param(
        [string]$Path,
        [hashtable]$Records,
        [object[]]$Backups
    )

    $parent = Split-Path -Parent ([IO.Path]::GetFullPath($Path))
    New-Item -ItemType Directory -Path $parent -Force | Out-Null
    $temporary = Join-Path $parent (".state-" + [Guid]::NewGuid().ToString("N") + ".json")
    try {
        $document = [ordered]@{
            schema_version = 1
            installations = @(
                $Records.Values | Sort-Object -Property platform, skill
            )
            backups = @($Backups)
        }
        $json = $document | ConvertTo-Json -Depth 10
        [IO.File]::WriteAllText(
            $temporary,
            $json + [Environment]::NewLine,
            (New-Object Text.UTF8Encoding($false))
        )
        Move-Item -LiteralPath $temporary -Destination $Path -Force
    }
    finally {
        if (Test-Path -LiteralPath $temporary) {
            Remove-Item -LiteralPath $temporary -Force
        }
    }
}

function Assert-TargetWithinDestination {
    param([string]$Target, [string]$Destination)

    $resolvedTarget = [IO.Path]::GetFullPath($Target)
    $resolvedDestination = [IO.Path]::GetFullPath($Destination).TrimEnd(
        [IO.Path]::DirectorySeparatorChar,
        [IO.Path]::AltDirectorySeparatorChar
    )
    $prefix = $resolvedDestination + [IO.Path]::DirectorySeparatorChar
    if (-not $resolvedTarget.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to operate outside destination: $resolvedTarget"
    }
}

function Get-TargetObservation {
    param(
        [string]$Source,
        [string]$Target,
        [AllowNull()]
        [object]$Record
    )

    $sourceHash = Get-DirectoryDigest -Path $Source
    $exists = Test-Path -LiteralPath $Target
    $actualHash = $null
    $isDirectory = Test-Path -LiteralPath $Target -PathType Container
    $isReparsePoint = $false
    if ($exists) {
        $item = Get-Item -LiteralPath $Target -Force
        $isReparsePoint = (
            ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0
        )
    }
    if ($isDirectory -and -not $isReparsePoint) {
        $actualHash = Get-DirectoryDigest -Path $Target
    }
    $recordedHash = $null
    if ($null -ne $Record) {
        $recordedHash = $Record.installed_hash
    }
    $status = Get-SkillDeploymentState `
        -TargetExists $exists `
        -SourceHash $sourceHash `
        -RecordedHash $recordedHash `
        -ActualHash $actualHash
    if ($exists -and (-not $isDirectory -or $isReparsePoint)) {
        $status = "UNOWNED"
    }
    return [PSCustomObject]@{
        Status = $status
        SourceHash = $sourceHash
        ActualHash = $actualHash
        IsReparsePoint = $isReparsePoint
    }
}

function New-StateRecord {
    param(
        [string]$Platform,
        [string]$Skill,
        [string]$Target,
        [string]$Hash
    )

    return [ordered]@{
        platform = $Platform
        skill = $Skill
        target = [IO.Path]::GetFullPath($Target)
        source_hash = $Hash
        installed_hash = $Hash
        last_verified_at = [DateTimeOffset]::UtcNow.ToString("o")
    }
}

function Get-ApplicableDependencies {
    param(
        [Parameter(Mandatory = $true)]
        [object]$Manifest,
        [Parameter(Mandatory = $true)]
        [object[]]$SelectedSkills
    )

    $byId = @{}
    foreach ($dependency in @($Manifest.dependencies)) {
        $byId[$dependency.id] = $dependency
    }
    $selectedIds = @{}
    foreach ($dependency in @($Manifest.dependencies)) {
        foreach ($consumer in @($dependency.consumers)) {
            $matches = $false
            foreach ($skill in $SelectedSkills) {
                if (
                    ($consumer.kind -eq "skill" -and
                        $consumer.name -eq $skill.managed_name) -or
                    ($consumer.kind -eq "category" -and
                        $consumer.name -eq $skill.category)
                ) {
                    $matches = $true
                    break
                }
            }
            if ($matches) {
                $selectedIds[$dependency.id] = $true
                break
            }
        }
    }

    $changed = $true
    while ($changed) {
        $changed = $false
        foreach ($id in @($selectedIds.Keys)) {
            foreach ($prerequisite in @($byId[$id].prerequisites)) {
                if (-not $selectedIds.ContainsKey($prerequisite)) {
                    $selectedIds[$prerequisite] = $true
                    $changed = $true
                }
            }
        }
    }
    return @(
        $Manifest.dependencies |
            Where-Object {
                $_.kind -ne "platform-cli" -and $selectedIds.ContainsKey($_.id)
            }
    )
}

function Get-AffectedRequiredSkills {
    param(
        [Parameter(Mandatory = $true)]
        [object]$Dependency,
        [Parameter(Mandatory = $true)]
        [object[]]$SelectedSkills
    )

    $affected = @()
    foreach ($consumer in @($Dependency.consumers)) {
        if ($consumer.requirement -ne "required") {
            continue
        }
        foreach ($skill in $SelectedSkills) {
            if (
                ($consumer.kind -eq "skill" -and
                    $consumer.name -eq $skill.managed_name) -or
                ($consumer.kind -eq "category" -and
                    $consumer.name -eq $skill.category)
            ) {
                $affected += $skill.managed_name
            }
        }
    }
    return @($affected | Select-Object -Unique)
}

function Confirm-DependencyInstall {
    param(
        [Parameter(Mandatory = $true)]
        [object]$Dependency,
        [switch]$Approve
    )

    if ($Approve) {
        return $true
    }
    $answer = Read-Host (
        "Install allowlisted dependency {0} {1}? [Y/N]" -f
        $Dependency.id, $Dependency.install_version
    )
    return $answer -match "^(?i:y|yes)$"
}

function Install-AllowlistedDependency {
    param(
        [Parameter(Mandatory = $true)]
        [object]$Dependency,
        [Parameter(Mandatory = $true)]
        [hashtable]$ProbeResults
    )

    if ($Dependency.id -eq "pyyaml") {
        $python = $ProbeResults["python"].command
        if ([string]::IsNullOrWhiteSpace($python)) {
            throw "A compatible Python command is required before installing PyYAML."
        }
        $venv = Join-Path (
            [Environment]::GetFolderPath("LocalApplicationData")
        ) "MySkills\venvs\skill-evaluator"
        $venvPython = Join-Path $venv "Scripts\python.exe"
        if (-not (Test-Path -LiteralPath $venvPython -PathType Leaf)) {
            $pythonArgs = @("-m", "venv", $venv)
            if ([IO.Path]::GetFileNameWithoutExtension($python) -eq "py") {
                $pythonArgs = @("-3") + $pythonArgs
            }
            & $python @pythonArgs
            if ($LASTEXITCODE -ne 0) {
                throw "Failed to create the private skill-evaluator environment."
            }
        }
        $requirements = Join-Path $repoRoot $Dependency.install.requirements_file
        & $venvPython -m pip install --require-hashes -r $requirements
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to install the pinned skill-evaluator requirements."
        }
        return
    }

    if ($Dependency.install.manager -eq "node") {
        $specification = "{0}@{1}" -f (
            $Dependency.install.package
        ), $Dependency.install_version
        $volta = Get-Command "volta" -CommandType Application -ErrorAction SilentlyContinue |
            Select-Object -First 1
        if ($null -ne $volta) {
            & $volta.Source install $specification
        }
        else {
            $npm = Get-Command "npm" -CommandType Application -ErrorAction Stop |
                Select-Object -First 1
            & $npm.Source install --global $specification
        }
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to install $specification."
        }
        return
    }

    throw "Unsupported allowlisted dependency installer: $($Dependency.id)"
}

function Get-PrivateToolPlan {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,
        [Parameter(Mandatory = $true)]
        [string]$Source,
        [Parameter(Mandatory = $true)]
        [hashtable]$Records
    )

    $target = Join-Path (
        [Environment]::GetFolderPath("LocalApplicationData")
    ) "MySkills\tools\$Name"
    $key = "tool|$Name"
    $record = $null
    if ($Records.ContainsKey($key)) {
        $record = $Records[$key]
    }
    $observation = Get-TargetObservation `
        -Source $Source `
        -Target $target `
        -Record $record
    return [PSCustomObject]@{
        Name = $Name
        Source = $Source
        Target = $target
        Key = $key
        Observation = $observation
    }
}

function Test-PrivateToolPlanAllowed {
    param(
        [Parameter(Mandatory = $true)]
        [object]$Plan
    )

    if (
        $Plan.Observation.Status -in @("MISSING", "CURRENT", "UPDATE_AVAILABLE")
    ) {
        return $true
    }
    if (
        $Plan.Observation.Status -eq "UNOWNED" -and
        $AdoptExact -and
        $null -ne $Plan.Observation.ActualHash -and
        $Plan.Observation.ActualHash -eq $Plan.Observation.SourceHash
    ) {
        return $true
    }
    if (
        $Plan.Observation.Status -in @("UNOWNED", "DRIFTED") -and
        $BackupAndReplace -and
        -not $Plan.Observation.IsReparsePoint
    ) {
        return $true
    }
    return $false
}

function Sync-PrivateToolSnapshot {
    param(
        [Parameter(Mandatory = $true)]
        [object]$Plan,
        [Parameter(Mandatory = $true)]
        [hashtable]$Records,
        [Parameter(Mandatory = $true)]
        [ref]$Backups
    )

    $status = $Plan.Observation.Status
    $hash = $Plan.Observation.SourceHash
    if ($status -eq "MISSING") {
        $hash = Install-DirectorySnapshot -Source $Plan.Source -Target $Plan.Target
    }
    elseif ($status -eq "UPDATE_AVAILABLE") {
        $hash = Update-DirectorySnapshot -Source $Plan.Source -Target $Plan.Target
    }
    elseif ($status -eq "UNOWNED") {
        if (
            $AdoptExact -and
            $Plan.Observation.ActualHash -eq $Plan.Observation.SourceHash
        ) {
            $hash = $Plan.Observation.SourceHash
        }
        else {
            $stamp = Get-Date -Format "yyyyMMdd-HHmmssfff"
            $backup = Join-Path (
                Join-Path (Split-Path -Parent $StatePath) "backups\$stamp\tool"
            ) $Plan.Name
            $backupHash = Backup-DirectorySnapshot `
                -Source $Plan.Target `
                -Backup $backup
            $hash = Update-DirectorySnapshot -Source $Plan.Source -Target $Plan.Target
            $Backups.Value += [ordered]@{
                platform = "tool"
                skill = $Plan.Name
                path = $backup
                hash = $backupHash
                created_at = [DateTimeOffset]::UtcNow.ToString("o")
            }
        }
    }
    elseif ($status -eq "DRIFTED") {
        $stamp = Get-Date -Format "yyyyMMdd-HHmmssfff"
        $backup = Join-Path (
            Join-Path (Split-Path -Parent $StatePath) "backups\$stamp\tool"
        ) $Plan.Name
        $backupHash = Backup-DirectorySnapshot `
            -Source $Plan.Target `
            -Backup $backup
        $hash = Update-DirectorySnapshot -Source $Plan.Source -Target $Plan.Target
        $Backups.Value += [ordered]@{
            platform = "tool"
            skill = $Plan.Name
            path = $backup
            hash = $backupHash
            created_at = [DateTimeOffset]::UtcNow.ToString("o")
        }
    }

    $Records[$Plan.Key] = New-StateRecord `
        -Platform "tool" `
        -Skill $Plan.Name `
        -Target $Plan.Target `
        -Hash $hash
}

function New-PrivateVenv {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,
        [Parameter(Mandatory = $true)]
        [string]$PythonCommand
    )

    $venv = Join-Path (
        [Environment]::GetFolderPath("LocalApplicationData")
    ) "MySkills\venvs\$Name"
    $parent = Split-Path -Parent $venv
    New-Item -ItemType Directory -Path $parent -Force | Out-Null
    $previous = Join-Path $parent (".$Name-previous-" + [Guid]::NewGuid().ToString("N"))
    $hadPrevious = Test-Path -LiteralPath $venv -PathType Container
    if ($hadPrevious) {
        Move-Item -LiteralPath $venv -Destination $previous
    }
    try {
        $arguments = @("-m", "venv", $venv)
        if ([IO.Path]::GetFileNameWithoutExtension($PythonCommand) -eq "py") {
            $arguments = @("-3") + $arguments
        }
        & $PythonCommand @arguments
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to create private environment $Name."
        }
        return [PSCustomObject]@{
            Path = $venv
            Python = Join-Path $venv "Scripts\python.exe"
            Previous = $previous
            HadPrevious = $hadPrevious
        }
    }
    catch {
        if (Test-Path -LiteralPath $venv) {
            Remove-Item -LiteralPath $venv -Recurse -Force
        }
        if ($hadPrevious -and (Test-Path -LiteralPath $previous)) {
            Move-Item -LiteralPath $previous -Destination $venv
        }
        throw
    }
}

function Complete-PrivateVenv {
    param(
        [Parameter(Mandatory = $true)]
        [object]$Transaction
    )

    if ($Transaction.HadPrevious -and (Test-Path -LiteralPath $Transaction.Previous)) {
        Remove-Item -LiteralPath $Transaction.Previous -Recurse -Force
    }
}

function Restore-PrivateVenv {
    param(
        [Parameter(Mandatory = $true)]
        [object]$Transaction
    )

    if (Test-Path -LiteralPath $Transaction.Path) {
        Remove-Item -LiteralPath $Transaction.Path -Recurse -Force
    }
    if (
        $Transaction.HadPrevious -and
        (Test-Path -LiteralPath $Transaction.Previous)
    ) {
        Move-Item -LiteralPath $Transaction.Previous -Destination $Transaction.Path
    }
}

function Get-ByteDigest {
    param(
        [Parameter(Mandatory = $true)]
        [byte[]]$Bytes
    )

    $sha256 = [Security.Cryptography.SHA256]::Create()
    try {
        return ([BitConverter]::ToString(
            $sha256.ComputeHash($Bytes)
        )).Replace("-", "").ToLowerInvariant()
    }
    finally {
        $sha256.Dispose()
    }
}

function Set-ManagedLauncher {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,
        [Parameter(Mandatory = $true)]
        [string]$Target,
        [Parameter(Mandatory = $true)]
        [byte[]]$Content,
        [Parameter(Mandatory = $true)]
        [ref]$Backups
    )

    if (Test-Path -LiteralPath $Target) {
        $existing = [IO.File]::ReadAllBytes($Target)
        if ((Get-ByteDigest $existing) -ne (Get-ByteDigest $Content)) {
            if (-not $BackupAndReplace) {
                throw "Unowned launcher differs and requires -BackupAndReplace: $Target"
            }
            $stamp = Get-Date -Format "yyyyMMdd-HHmmssfff"
            $backup = Join-Path (
                Join-Path (Split-Path -Parent $StatePath) "backups\$stamp\launcher"
            ) ([IO.Path]::GetFileName($Target))
            New-Item -ItemType Directory -Path (Split-Path -Parent $backup) -Force |
                Out-Null
            Copy-Item -LiteralPath $Target -Destination $backup
            if (
                (Get-FileHash -Algorithm SHA256 -LiteralPath $Target).Hash -ne
                (Get-FileHash -Algorithm SHA256 -LiteralPath $backup).Hash
            ) {
                throw "Launcher backup verification failed: $Target"
            }
            $Backups.Value += [ordered]@{
                platform = "launcher"
                skill = $Name
                path = $backup
                hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $backup).Hash.ToLowerInvariant()
                created_at = [DateTimeOffset]::UtcNow.ToString("o")
            }
        }
    }
    else {
        New-Item -ItemType Directory -Path (Split-Path -Parent $Target) -Force |
            Out-Null
    }
    [IO.File]::WriteAllBytes($Target, $Content)
}

function Install-EvaluatorRuntime {
    param(
        [Parameter(Mandatory = $true)]
        [string]$PythonCommand,
        [Parameter(Mandatory = $true)]
        [object]$ToolPlan,
        [Parameter(Mandatory = $true)]
        [hashtable]$Records,
        [Parameter(Mandatory = $true)]
        [ref]$Backups
    )

    $transaction = New-PrivateVenv `
        -Name "skill-evaluator" `
        -PythonCommand $PythonCommand
    try {
        $requirements = Join-Path $repoRoot (
            "requirements\skill-evaluator\requirements-lock.txt"
        )
        & $transaction.Python -m pip install --require-hashes -r $requirements
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to install the pinned evaluator requirements."
        }
        Sync-PrivateToolSnapshot `
            -Plan $ToolPlan `
            -Records $Records `
            -Backups $Backups

        $bin = Join-Path (
            [Environment]::GetFolderPath("LocalApplicationData")
        ) "MySkills\bin"
        $launcher = Join-Path $bin "skill-evaluator.cmd"
        $launcherSource = Join-Path $ToolPlan.Target "skill-evaluator.cmd"
        Set-ManagedLauncher `
            -Name "skill-evaluator" `
            -Target $launcher `
            -Content ([IO.File]::ReadAllBytes($launcherSource)) `
            -Backups $Backups
        & $launcher smoke --json
        if ($LASTEXITCODE -ne 0) {
            throw "skill-evaluator core smoke failed."
        }
        Complete-PrivateVenv -Transaction $transaction
    }
    catch {
        Restore-PrivateVenv -Transaction $transaction
        throw
    }
}

function Install-WikiRuntime {
    param(
        [Parameter(Mandatory = $true)]
        [string]$PythonCommand,
        [Parameter(Mandatory = $true)]
        [object]$ToolPlan,
        [Parameter(Mandatory = $true)]
        [hashtable]$Records,
        [Parameter(Mandatory = $true)]
        [ref]$Backups
    )

    $transaction = New-PrivateVenv `
        -Name "obsidian-wiki" `
        -PythonCommand $PythonCommand
    try {
        & $transaction.Python -m pip install `
            --no-deps `
            --no-build-isolation `
            $ToolPlan.Source
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to install the repository-owned obsidian-wiki tool."
        }
        Sync-PrivateToolSnapshot `
            -Plan $ToolPlan `
            -Records $Records `
            -Backups $Backups

        $bin = Join-Path (
            [Environment]::GetFolderPath("LocalApplicationData")
        ) "MySkills\bin"
        $launcher = Join-Path $bin "obsidian-wiki.cmd"
        $launcherText = @"
@echo off
"%LOCALAPPDATA%\MySkills\venvs\obsidian-wiki\Scripts\python.exe" -m obsidian_wiki %*
"@
        Set-ManagedLauncher `
            -Name "obsidian-wiki" `
            -Target $launcher `
            -Content ([Text.Encoding]::ASCII.GetBytes(
                $launcherText.Replace("`n", "`r`n")
            )) `
            -Backups $Backups
        & $launcher --version
        if ($LASTEXITCODE -ne 0) {
            throw "obsidian-wiki version smoke failed."
        }

        $smokeRoot = Join-Path $transaction.Path "installer-smoke"
        $smokeConfig = Join-Path $smokeRoot "config"
        $smokeVault = Join-Path $smokeRoot "vault"
        $oldConfigHome = $env:OBSIDIAN_WIKI_CONFIG_HOME
        try {
            $env:OBSIDIAN_WIKI_CONFIG_HOME = $smokeConfig
            & $transaction.Python -m obsidian_wiki setup --vault $smokeVault
            if ($LASTEXITCODE -ne 0) {
                throw "obsidian-wiki setup smoke failed."
            }
            & $transaction.Python -m obsidian_wiki doctor --json --strict
            if ($LASTEXITCODE -ne 0) {
                throw "obsidian-wiki doctor smoke failed."
            }
        }
        finally {
            $env:OBSIDIAN_WIKI_CONFIG_HOME = $oldConfigHome
            if (Test-Path -LiteralPath $smokeRoot) {
                Remove-Item -LiteralPath $smokeRoot -Recurse -Force
            }
        }
        Complete-PrivateVenv -Transaction $transaction
    }
    catch {
        Restore-PrivateVenv -Transaction $transaction
        throw
    }
}

function Register-QmdMcp {
    param(
        [Parameter(Mandatory = $true)]
        [object[]]$Platforms
    )

    foreach ($platform in $Platforms) {
        if (-not $platform.Available) {
            continue
        }
        if ($platform.Id -eq "codex") {
            & $platform.Executable mcp get qmd *> $null
            if ($LASTEXITCODE -ne 0) {
                & $platform.Executable mcp add qmd -- qmd mcp
                if ($LASTEXITCODE -ne 0) {
                    throw "Failed to register QMD MCP for Codex."
                }
            }
            & $platform.Executable mcp get qmd *> $null
            if ($LASTEXITCODE -ne 0) {
                throw "Codex cannot discover the QMD MCP registration."
            }
            Write-Output "MCP_VERIFIED`tcodex`tqmd"
        }
        elseif ($platform.Id -eq "claude-code") {
            & $platform.Executable mcp get qmd *> $null
            if ($LASTEXITCODE -ne 0) {
                & $platform.Executable mcp add --scope user qmd -- qmd mcp
                if ($LASTEXITCODE -ne 0) {
                    throw "Failed to register QMD MCP for Claude Code."
                }
            }
            & $platform.Executable mcp get qmd *> $null
            if ($LASTEXITCODE -ne 0) {
                throw "Claude Code cannot discover the QMD MCP registration."
            }
            Write-Output "MCP_VERIFIED`tclaude-code`tqmd"
        }
        elseif ($platform.Id -eq "antigravity-cli") {
            Write-Output (
                "MCP_UNSUPPORTED`tAntigravity CLI exposes no command-backed MCP " +
                "registration interface; Skill compatibility copy is unchanged."
            )
        }
    }
}

try {
    if ($PSVersionTable.PSVersion -lt [version]"5.1") {
        throw "Windows PowerShell 5.1 or later is required."
    }

    $inventoryPath = Join-Path $repoRoot "inventory\skills.json"
    $inventory = Get-Content -Raw -LiteralPath $inventoryPath | ConvertFrom-Json
    $selectedSkills = @(Resolve-ManagedSkills -Inventory $inventory -RequestedNames $Skills)
    $state = Read-State -Path $StatePath
    $records = $state.Records
    $backups = @($state.Backups)

    Write-Output "PREFLIGHT"
    Write-Output "PowerShell`t$($PSVersionTable.PSVersion)`tCOMPATIBLE"
    $platforms = @()
    foreach ($definition in Get-PlatformDefinitions) {
        $probe = Invoke-ExecutableProbe -Candidates $definition.Commands
        $platform = [PSCustomObject]@{
            Id = $definition.Id
            Destination = $definition.Destination
            Support = $definition.Support
            Available = $probe.Available
            Executable = $probe.Executable
        }
        $platforms += $platform
        $platformStatus = if ($platform.Available) { "AVAILABLE" } else { "NOT_INSTALLED" }
        Write-Output "$($platform.Id)`t$platformStatus`t$($platform.Support)"
    }

    $dependencyManifestPath = Join-Path $repoRoot "manifests\dependencies.json"
    $dependencyManifest = $null
    $applicableDependencies = @()
    $dependencyResults = @{}
    if (Test-Path -LiteralPath $dependencyManifestPath -PathType Leaf) {
        $dependencyManifest = Get-Content -Raw -LiteralPath $dependencyManifestPath |
            ConvertFrom-Json
        $applicableDependencies = @(
            Get-ApplicableDependencies `
                -Manifest $dependencyManifest `
                -SelectedSkills $selectedSkills
        )
        if ($applicableDependencies.Count -gt 0) {
            Write-Output "DEPENDENCIES"
        }
        foreach ($dependency in $applicableDependencies) {
            $result = Invoke-DependencyProbe -Dependency $dependency
            $dependencyResults[$dependency.id] = $result
            Write-Output (
                "$($dependency.id)`t$($result.status)`t" +
                "detected=$($result.version)`tminimum=$($dependency.minimum_version)`t" +
                "pinned=$($dependency.install_version)"
            )
        }
    }

    $wikiSkills = @($selectedSkills | Where-Object { $_.category -eq "wiki" })
    $evaluatorSkills = @(
        $selectedSkills | Where-Object { $_.managed_name -eq "skill-evaluator" }
    )
    $wikiToolPlan = $null
    $evaluatorToolPlan = $null
    if ($wikiSkills.Count -gt 0) {
        $wikiToolPlan = Get-PrivateToolPlan `
            -Name "obsidian-wiki" `
            -Source (Join-Path $repoRoot "tools\obsidian-wiki") `
            -Records $records
        Write-Output (
            "TOOL`tobsidian-wiki`t$($wikiToolPlan.Observation.Status)"
        )
    }
    if ($evaluatorSkills.Count -gt 0) {
        $evaluatorToolPlan = Get-PrivateToolPlan `
            -Name "skill-evaluator" `
            -Source (Join-Path $repoRoot "tools\skill-evaluator") `
            -Records $records
        Write-Output (
            "TOOL`tskill-evaluator`t$($evaluatorToolPlan.Observation.Status)"
        )
    }

    Write-Output "PLAN"
    Write-Output (
        "Action=$Action Skills=$($selectedSkills.Count) DryRun=$([bool]$DryRun)"
    )
    foreach ($skill in $selectedSkills) {
        Write-Output "Skill`t$($skill.managed_name)"
    }
    if ($DryRun) {
        Write-Output "DryRun: no dependency, Skill, configuration, or state changes will occur."
    }

    $dependencyBlocks = @{}
    foreach ($dependency in $applicableDependencies) {
        $result = $dependencyResults[$dependency.id]
        $available = $result.status -eq "COMPATIBLE"
        if (
            -not $available -and
            $dependency.kind -eq "installable" -and
            $Action -eq "Install"
        ) {
            if ($DryRun) {
                Write-Output (
                    "WOULD_OFFER_DEPENDENCY`t$($dependency.id)`t" +
                    "$($dependency.install_version)"
                )
                $available = $true
            }
            elseif (Confirm-DependencyInstall -Dependency $dependency -Approve:$Yes) {
                try {
                    Install-AllowlistedDependency `
                        -Dependency $dependency `
                        -ProbeResults $dependencyResults
                    $result = Invoke-DependencyProbe -Dependency $dependency
                    $dependencyResults[$dependency.id] = $result
                    $available = $result.status -eq "COMPATIBLE"
                    Write-Output "DEPENDENCY_$($result.status)`t$($dependency.id)"
                }
                catch {
                    Write-Output (
                        "DEPENDENCY_FAILED`t$($dependency.id)`t$($_.Exception.Message)"
                    )
                }
            }
        }

        if (-not $available) {
            foreach (
                $affectedSkill in Get-AffectedRequiredSkills `
                    -Dependency $dependency `
                    -SelectedSkills $selectedSkills
            ) {
                if (-not $dependencyBlocks.ContainsKey($affectedSkill)) {
                    $dependencyBlocks[$affectedSkill] = @()
                }
                $dependencyBlocks[$affectedSkill] += (
                    "{0} is {1}; {2}" -f
                    $dependency.id,
                    $result.status,
                    $dependency.guidance
                )
            }
        }
    }

    if ($evaluatorSkills.Count -gt 0) {
        foreach ($requiredPlatform in @("codex", "claude-code")) {
            $available = $platforms | Where-Object {
                $_.Id -eq $requiredPlatform -and $_.Available
            }
            if ($null -eq $available) {
                $dependencyBlocks["skill-evaluator"] += (
                    "$requiredPlatform is required as an evaluation target"
                )
            }
        }
        if (
            ($Action -eq "Verify" -and
                $evaluatorToolPlan.Observation.Status -ne "CURRENT") -or
            ($Action -eq "Install" -and
                -not (Test-PrivateToolPlanAllowed -Plan $evaluatorToolPlan))
        ) {
            $dependencyBlocks["skill-evaluator"] += (
                "managed evaluator tool is $($evaluatorToolPlan.Observation.Status)"
            )
        }
    }
    if (
        $wikiSkills.Count -gt 0 -and
        (
            ($Action -eq "Verify" -and
                $wikiToolPlan.Observation.Status -ne "CURRENT") -or
            ($Action -eq "Install" -and
                -not (Test-PrivateToolPlanAllowed -Plan $wikiToolPlan))
        )
    ) {
        foreach ($wikiSkill in $wikiSkills) {
            $dependencyBlocks[$wikiSkill.managed_name] += (
                "repository-owned Wiki tool is $($wikiToolPlan.Observation.Status)"
            )
        }
    }

    $installed = 0
    $skipped = 0
    $blocked = 0
    $requested = 0
    $stateChanged = $false

    if ($Action -eq "Install") {
        if ($wikiSkills.Count -gt 0) {
            $wikiBlocked = @(
                $wikiSkills | Where-Object {
                    $dependencyBlocks.ContainsKey($_.managed_name)
                }
            )
            if ($wikiBlocked.Count -eq 0) {
                if ($DryRun) {
                    Write-Output "WOULD_INSTALL_TOOL`tobsidian-wiki"
                }
                else {
                    try {
                        Install-WikiRuntime `
                            -PythonCommand $dependencyResults["python"].command `
                            -ToolPlan $wikiToolPlan `
                            -Records $records `
                            -Backups ([ref]$backups)
                        $stateChanged = $true
                        Write-Output "TOOL_INSTALLED`tobsidian-wiki"
                    }
                    catch {
                        foreach ($wikiSkill in $wikiSkills) {
                            $dependencyBlocks[$wikiSkill.managed_name] += (
                                "obsidian-wiki installation failed: $($_.Exception.Message)"
                            )
                        }
                    }
                }
            }
        }
        if (
            $evaluatorSkills.Count -gt 0 -and
            -not $dependencyBlocks.ContainsKey("skill-evaluator")
        ) {
            if ($DryRun) {
                Write-Output "WOULD_INSTALL_TOOL`tskill-evaluator"
            }
            else {
                try {
                    Install-EvaluatorRuntime `
                        -PythonCommand $dependencyResults["python"].command `
                        -ToolPlan $evaluatorToolPlan `
                        -Records $records `
                        -Backups ([ref]$backups)
                    $stateChanged = $true
                    Write-Output "TOOL_INSTALLED`tskill-evaluator"
                }
                catch {
                    $dependencyBlocks["skill-evaluator"] += (
                        "skill-evaluator installation failed: $($_.Exception.Message)"
                    )
                }
            }
        }
    }

    foreach ($skill in $selectedSkills) {
        if ($dependencyBlocks.ContainsKey($skill.managed_name)) {
            Write-Output (
                "BLOCKED`t$($skill.managed_name)`t" +
                ($dependencyBlocks[$skill.managed_name] -join "; ")
            )
            $blocked++
            continue
        }
        $source = Join-Path $repoRoot (
            "skills\{0}\{1}" -f $skill.category, $skill.managed_name
        )
        if (-not (Test-Path -LiteralPath $source -PathType Container)) {
            Write-Output (
                "BLOCKED`t$($skill.managed_name)`trepository source is missing: $source"
            )
            $blocked++
            continue
        }

        foreach ($targetId in @($skill.install_targets)) {
            $requested++
            $platform = $platforms | Where-Object { $_.Id -eq $targetId } |
                Select-Object -First 1
            if ($null -eq $platform -or -not $platform.Available) {
                Write-Output (
                    "SKIPPED_NOT_INSTALLED`t$targetId`t$($skill.managed_name)"
                )
                $skipped++
                continue
            }

            $target = Join-Path $platform.Destination $skill.managed_name
            Assert-TargetWithinDestination -Target $target -Destination $platform.Destination
            $key = "$targetId|$($skill.managed_name)"
            $record = $null
            if ($records.ContainsKey($key)) {
                $record = $records[$key]
            }
            $observation = Get-TargetObservation `
                -Source $source `
                -Target $target `
                -Record $record

            if ($Action -eq "Status") {
                Write-Output (
                    "$($observation.Status)`t$targetId`t$($skill.managed_name)`t$target"
                )
                continue
            }
            if ($Action -eq "Verify") {
                if ($observation.Status -eq "CURRENT") {
                    Write-Output "VERIFIED`t$targetId`t$($skill.managed_name)"
                    $installed++
                }
                else {
                    Write-Output (
                        "BLOCKED`t$targetId`t$($skill.managed_name)`t" +
                        "expected CURRENT, found $($observation.Status)"
                    )
                    $blocked++
                }
                continue
            }
            if ($Action -eq "Uninstall") {
                if ($observation.Status -eq "MISSING") {
                    $records.Remove($key)
                    Write-Output "SKIPPED_MISSING`t$targetId`t$($skill.managed_name)"
                    $skipped++
                    continue
                }
                if (
                    $observation.Status -eq "UNOWNED" -or
                    $observation.Status -eq "DRIFTED"
                ) {
                    Write-Output (
                        "BLOCKED`t$targetId`t$($skill.managed_name)`t" +
                        "refusing to remove $($observation.Status) target"
                    )
                    $blocked++
                    continue
                }
                if ($DryRun) {
                    Write-Output "WOULD_UNINSTALL`t$targetId`t$($skill.managed_name)"
                }
                else {
                    Remove-Item -LiteralPath $target -Recurse -Force
                    $records.Remove($key)
                    $stateChanged = $true
                    Write-Output "UNINSTALLED`t$targetId`t$($skill.managed_name)"
                }
                $installed++
                continue
            }

            switch ($observation.Status) {
                "CURRENT" {
                    Write-Output "CURRENT`t$targetId`t$($skill.managed_name)"
                    $skipped++
                }
                "MISSING" {
                    if ($DryRun) {
                        Write-Output "WOULD_INSTALL`t$targetId`t$($skill.managed_name)"
                    }
                    else {
                        $hash = Install-DirectorySnapshot -Source $source -Target $target
                        $records[$key] = New-StateRecord `
                            -Platform $targetId `
                            -Skill $skill.managed_name `
                            -Target $target `
                            -Hash $hash
                        $stateChanged = $true
                        Write-Output "INSTALLED`t$targetId`t$($skill.managed_name)"
                    }
                    $installed++
                }
                "UPDATE_AVAILABLE" {
                    if ($DryRun) {
                        Write-Output "WOULD_UPDATE`t$targetId`t$($skill.managed_name)"
                    }
                    else {
                        $hash = Update-DirectorySnapshot -Source $source -Target $target
                        $records[$key] = New-StateRecord `
                            -Platform $targetId `
                            -Skill $skill.managed_name `
                            -Target $target `
                            -Hash $hash
                        $stateChanged = $true
                        Write-Output "UPDATED`t$targetId`t$($skill.managed_name)"
                    }
                    $installed++
                }
                "UNOWNED" {
                    if (
                        $AdoptExact -and
                        $null -ne $observation.ActualHash -and
                        $observation.ActualHash -eq $observation.SourceHash
                    ) {
                        if ($DryRun) {
                            Write-Output "WOULD_ADOPT`t$targetId`t$($skill.managed_name)"
                        }
                        else {
                            $records[$key] = New-StateRecord `
                                -Platform $targetId `
                                -Skill $skill.managed_name `
                                -Target $target `
                                -Hash $observation.SourceHash
                            $stateChanged = $true
                            Write-Output "ADOPTED`t$targetId`t$($skill.managed_name)"
                        }
                        $installed++
                    }
                    elseif ($BackupAndReplace -and -not $observation.IsReparsePoint) {
                        if ($DryRun) {
                            Write-Output (
                                "WOULD_BACKUP_REPLACE`t$targetId`t$($skill.managed_name)"
                            )
                        }
                        else {
                            $stamp = Get-Date -Format "yyyyMMdd-HHmmssfff"
                            $backup = Join-Path (
                                Join-Path (Split-Path -Parent $StatePath) "backups\$stamp\$targetId"
                            ) $skill.managed_name
                            $backupHash = Backup-DirectorySnapshot `
                                -Source $target `
                                -Backup $backup
                            $hash = Update-DirectorySnapshot -Source $source -Target $target
                            $backups += [ordered]@{
                                platform = $targetId
                                skill = $skill.managed_name
                                path = $backup
                                hash = $backupHash
                                created_at = [DateTimeOffset]::UtcNow.ToString("o")
                            }
                            $records[$key] = New-StateRecord `
                                -Platform $targetId `
                                -Skill $skill.managed_name `
                                -Target $target `
                                -Hash $hash
                            $stateChanged = $true
                            Write-Output (
                                "BACKED_UP_REPLACED`t$targetId`t$($skill.managed_name)`t$backup"
                            )
                        }
                        $installed++
                    }
                    else {
                        Write-Output (
                            "BLOCKED`t$targetId`t$($skill.managed_name)`t" +
                            "unowned target; use -AdoptExact for an exact copy or " +
                            "-BackupAndReplace after review"
                        )
                        $blocked++
                    }
                }
                "DRIFTED" {
                    if ($BackupAndReplace) {
                        if ($DryRun) {
                            Write-Output (
                                "WOULD_BACKUP_REPLACE`t$targetId`t$($skill.managed_name)"
                            )
                        }
                        else {
                            $stamp = Get-Date -Format "yyyyMMdd-HHmmssfff"
                            $backup = Join-Path (
                                Join-Path (Split-Path -Parent $StatePath) "backups\$stamp\$targetId"
                            ) $skill.managed_name
                            $backupHash = Backup-DirectorySnapshot `
                                -Source $target `
                                -Backup $backup
                            $hash = Update-DirectorySnapshot -Source $source -Target $target
                            $backups += [ordered]@{
                                platform = $targetId
                                skill = $skill.managed_name
                                path = $backup
                                hash = $backupHash
                                created_at = [DateTimeOffset]::UtcNow.ToString("o")
                            }
                            $records[$key] = New-StateRecord `
                                -Platform $targetId `
                                -Skill $skill.managed_name `
                                -Target $target `
                                -Hash $hash
                            $stateChanged = $true
                            Write-Output (
                                "BACKED_UP_REPLACED`t$targetId`t$($skill.managed_name)`t$backup"
                            )
                        }
                        $installed++
                    }
                    else {
                        Write-Output (
                            "BLOCKED`t$targetId`t$($skill.managed_name)`t" +
                            "drift requires diff review and -BackupAndReplace"
                        )
                        $blocked++
                    }
                }
            }
        }
    }

    $qmdSelected = @(
        $selectedSkills | Where-Object { $_.managed_name -eq "qmd" }
    ).Count -gt 0
    if ($RegisterQmdMcp -and $qmdSelected -and $Action -eq "Install") {
        if ($DryRun) {
            Write-Output "WOULD_REGISTER_MCP`tqmd`tinstalled Agent CLIs"
        }
        elseif (
            $dependencyResults.ContainsKey("qmd") -and
            $dependencyResults["qmd"].status -eq "COMPATIBLE"
        ) {
            try {
                Register-QmdMcp -Platforms $platforms
            }
            catch {
                Write-Output "MCP_BLOCKED`tqmd`t$($_.Exception.Message)"
                $blocked++
            }
        }
        else {
            Write-Output "MCP_BLOCKED`tqmd`tQMD dependency is not compatible"
            $blocked++
        }
    }

    if ($stateChanged -and -not $DryRun) {
        Write-State -Path $StatePath -Records $records -Backups $backups
    }

    Write-Output "SUMMARY"
    Write-Output (
        "requested=$requested installed=$installed skipped=$skipped blocked=$blocked"
    )
    if ($blocked -gt 0) {
        Write-Error "INCOMPLETE: $blocked requested installation target(s) are blocked."
        exit 1
    }
    exit 0
}
catch {
    [Console]::Error.WriteLine($_.Exception.Message)
    exit 1
}
