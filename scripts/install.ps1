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
    $dependencyRecords = @{}
    $backups = @()
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        return [PSCustomObject]@{
            Records = $records
            DependencyRecords = $dependencyRecords
            Backups = $backups
        }
    }

    try {
        $document = Get-Content -Raw -LiteralPath $Path | ConvertFrom-Json
        if ($document.schema_version -ne 1) {
            throw "unsupported schema version"
        }
        foreach ($record in @($document.installations)) {
            $records["$($record.platform)|$($record.skill)"] = $record
        }
        if ($document.PSObject.Properties.Name -contains "dependencies") {
            foreach ($record in @($document.dependencies)) {
                $dependencyRecords[[string]$record.id] = $record
            }
        }
        $backups = @($document.backups)
    }
    catch {
        Write-Warning (
            "State is missing or invalid for ownership purposes; existing targets " +
            "will be treated as unowned. Details: $($_.Exception.Message)"
        )
        $records = @{}
        $dependencyRecords = @{}
        $backups = @()
    }
    return [PSCustomObject]@{
        Records = $records
        DependencyRecords = $dependencyRecords
        Backups = $backups
    }
}

function Write-State {
    param(
        [string]$Path,
        [hashtable]$Records,
        [hashtable]$DependencyRecords,
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
            dependencies = @(
                $DependencyRecords.Values | Sort-Object -Property id
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
        "Install allowlisted dependency {0} {1}? [Y/N/A/Q]" -f
        $Dependency.id, $Dependency.install_version
    )
    return $answer
}

function Get-AvailableDependencyRelease {
    param(
        [Parameter(Mandatory = $true)]
        [object]$Dependency,
        [Parameter(Mandatory = $true)]
        [hashtable]$ProbeResults
    )

    $result = [ordered]@{
        status = "NOT_APPLICABLE"
        version = $null
        source = $null
        details = $null
    }
    if ($Dependency.kind -ne "installable") {
        return [PSCustomObject]$result
    }

    try {
        if ($Dependency.install.manager -eq "node") {
            $npm = Get-Command "npm" -CommandType Application -ErrorAction Stop |
                Select-Object -First 1
            $output = (& $npm.Source view $Dependency.install.package version --json 2>&1 |
                Out-String).Trim()
            if ($LASTEXITCODE -ne 0) {
                throw $output
            }
            $parsed = $output | ConvertFrom-Json
            if ($parsed -is [array]) {
                $parsed = $parsed[-1]
            }
            $result.status = "AVAILABLE"
            $result.version = ([version]([string]$parsed)).ToString()
            $result.source = "npm"
            return [PSCustomObject]$result
        }

        if ($Dependency.install.manager -eq "pip") {
            $python = $ProbeResults["python"].command
            if ([string]::IsNullOrWhiteSpace($python)) {
                throw "Compatible Python is unavailable."
            }
            $arguments = @(
                "-m", "pip", "index", "versions", $Dependency.install.package,
                "--disable-pip-version-check"
            )
            if ([IO.Path]::GetFileNameWithoutExtension($python) -eq "py") {
                $arguments = @("-3") + $arguments
            }
            $output = (& $python @arguments 2>&1 | Out-String).Trim()
            if ($LASTEXITCODE -ne 0) {
                throw $output
            }
            $match = [regex]::Match(
                $output,
                "(?im)^\s*LATEST:\s*(\d+(?:\.\d+){1,3})\s*$"
            )
            if (-not $match.Success) {
                throw "Package source output did not report LATEST."
            }
            $result.status = "AVAILABLE"
            $result.version = ([version]$match.Groups[1].Value).ToString()
            $result.source = "configured-pip-index"
            return [PSCustomObject]$result
        }
    }
    catch {
        $result.status = "UNAVAILABLE"
        $result.details = $_.Exception.Message
        return [PSCustomObject]$result
    }

    $result.status = "UNAVAILABLE"
    $result.details = "No package-source query is defined."
    return [PSCustomObject]$result
}

function Get-DependencyPackageOwnership {
    param(
        [Parameter(Mandatory = $true)]
        [object]$Dependency,
        [Parameter(Mandatory = $true)]
        [object]$ProbeResult,
        [AllowNull()]
        [object]$PreviousRecord
    )

    if ($ProbeResult.status -eq "MISSING") {
        return [PSCustomObject]@{
            ownership = "absent"
            manager = $null
            path = $null
        }
    }
    if (
        $null -ne $PreviousRecord -and
        $PreviousRecord.PSObject.Properties.Name -contains "ownership" -and
        $PreviousRecord.PSObject.Properties.Name -contains "path" -and
        $PreviousRecord.PSObject.Properties.Name -contains "manager" -and
        $PreviousRecord.ownership -eq "installed_by_myskills" -and
        [string]$PreviousRecord.path -eq [string]$ProbeResult.command
    ) {
        return [PSCustomObject]@{
            ownership = "installed_by_myskills"
            manager = [string]$PreviousRecord.manager
            path = [string]$PreviousRecord.path
        }
    }
    if ($Dependency.id -eq "pyyaml") {
        $managedRoot = Join-Path (
            [Environment]::GetFolderPath("LocalApplicationData")
        ) "MySkills\venvs\skill-evaluator"
        $command = [IO.Path]::GetFullPath([string]$ProbeResult.command)
        $prefix = [IO.Path]::GetFullPath($managedRoot).TrimEnd("\") + "\"
        if ($command.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) {
            return [PSCustomObject]@{
                ownership = "installed_by_myskills"
                manager = "private-venv"
                path = $managedRoot
            }
        }
    }
    if ($Dependency.install.manager -eq "node") {
        try {
            $volta = Get-Command "volta" -CommandType Application `
                -ErrorAction SilentlyContinue |
                Select-Object -First 1
            if ($null -ne $volta) {
                $executableName = [IO.Path]::GetFileNameWithoutExtension(
                    [string]$ProbeResult.command
                )
                $voltaPath = (& $volta.Source which $executableName 2>&1 |
                    Out-String).Trim()
                if (
                    $LASTEXITCODE -eq 0 -and
                    [string]$ProbeResult.command -eq $voltaPath
                ) {
                    return [PSCustomObject]@{
                        ownership = "preexisting"
                        manager = "volta"
                        path = $voltaPath
                    }
                }
            }
            $npm = Get-Command "npm" -CommandType Application -ErrorAction Stop |
                Select-Object -First 1
            $root = (& $npm.Source root --global 2>&1 | Out-String).Trim()
            if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($root)) {
                throw "npm global root is unavailable."
            }
            $packagePath = Join-Path $root (
                ([string]$Dependency.install.package).Replace("/", "\")
            )
            $packageJson = Join-Path $packagePath "package.json"
            if (Test-Path -LiteralPath $packageJson -PathType Leaf) {
                $metadata = Get-Content -Raw -LiteralPath $packageJson |
                    ConvertFrom-Json
                if ([string]$metadata.version -eq [string]$ProbeResult.version) {
                    return [PSCustomObject]@{
                        ownership = "preexisting"
                        manager = "npm"
                        path = $packagePath
                    }
                }
            }
        }
        catch {
            # Unknown package origins are intentionally preserved.
        }
    }
    return [PSCustomObject]@{
        ownership = "preexisting"
        manager = "unknown"
        path = [string]$ProbeResult.command
    }
}

function Test-NewerDependencyVersion {
    param(
        [AllowNull()][string]$Candidate,
        [AllowNull()][string]$Baseline
    )
    if (
        [string]::IsNullOrWhiteSpace($Candidate) -or
        [string]::IsNullOrWhiteSpace($Baseline)
    ) {
        return $false
    }
    return [version]$Candidate -gt [version]$Baseline
}

function Set-PythonRequirementLock {
    param(
        [Parameter(Mandatory = $true)]
        [object]$Dependency,
        [Parameter(Mandatory = $true)]
        [string]$Version
    )

    $uri = "https://pypi.org/pypi/{0}/{1}/json" -f (
        $Dependency.install.package
    ), $Version
    $metadata = Invoke-RestMethod -Uri $uri -Method Get
    $hashes = @(
        $metadata.urls |
            ForEach-Object { [string]$_.digests.sha256 } |
            Where-Object { $_ -match "^[0-9a-f]{64}$" } |
            Sort-Object -Unique
    )
    if ($hashes.Count -eq 0) {
        throw "PyPI reported no SHA-256 release artifacts for $Version."
    }
    $lines = @(
        "# Hashes are from the PyPI release metadata for all published artifacts.",
        "$($Dependency.install.package)==$Version \"
    )
    for ($index = 0; $index -lt $hashes.Count; $index++) {
        $suffix = if ($index -lt $hashes.Count - 1) { " \" } else { "" }
        $lines += "    --hash=sha256:$($hashes[$index])$suffix"
    }
    $requirements = Join-Path $repoRoot $Dependency.install.requirements_file
    [IO.File]::WriteAllText(
        $requirements,
        ($lines -join [Environment]::NewLine) + [Environment]::NewLine,
        (New-Object Text.UTF8Encoding($false))
    )
}

function Install-AllowlistedDependency {
    param(
        [Parameter(Mandatory = $true)]
        [object]$Dependency,
        [Parameter(Mandatory = $true)]
        [hashtable]$ProbeResults,
        [string]$Version = $Dependency.install_version,
        [AllowNull()]
        [string]$Manager
    )

    if ($Dependency.id -eq "pyyaml") {
        $requirements = Join-Path $repoRoot $Dependency.install.requirements_file
        $locked = Get-Content -Raw -LiteralPath $requirements
        if ($locked -notmatch (
            "(?im)^\s*{0}=={1}\s*\\?\s*$" -f
            [regex]::Escape([string]$Dependency.install.package),
            [regex]::Escape($Version)
        )) {
            throw "The hash lock does not authorize $($Dependency.id) $Version."
        }
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
        & $venvPython -m pip install --require-hashes -r $requirements
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to install the pinned skill-evaluator requirements."
        }
        return
    }

    if ($Dependency.install.manager -eq "node") {
        $specification = "{0}@{1}" -f (
            $Dependency.install.package
        ), $Version
        $volta = Get-Command "volta" -CommandType Application -ErrorAction SilentlyContinue |
            Select-Object -First 1
        if (
            $Manager -eq "volta" -or
            ([string]::IsNullOrWhiteSpace($Manager) -and $null -ne $volta)
        ) {
            if ($null -eq $volta) {
                throw "Volta no longer resolves for $specification."
            }
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

function Uninstall-AllowlistedDependency {
    param(
        [Parameter(Mandatory = $true)]
        [object]$Dependency
    )

    if ($Dependency.install.manager -eq "pip") {
        $venvPython = [Environment]::ExpandEnvironmentVariables(
            [string]$Dependency.probe.candidates[0].command
        )
        if (Test-Path -LiteralPath $venvPython -PathType Leaf) {
            & $venvPython -m pip uninstall -y $Dependency.install.package
            if ($LASTEXITCODE -ne 0) {
                throw "Failed to uninstall $($Dependency.install.package)."
            }
        }
        return
    }
    if ($Dependency.install.manager -ne "node") {
        throw "Automatic uninstall is unsupported for $($Dependency.id)."
    }
    $volta = Get-Command "volta" -CommandType Application -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if ($null -ne $volta) {
        & $volta.Source uninstall $Dependency.install.package
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to uninstall $($Dependency.install.package) with Volta."
        }
        return
    }
    $npm = Get-Command "npm" -CommandType Application -ErrorAction Stop |
        Select-Object -First 1
    & $npm.Source uninstall --global $Dependency.install.package
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to uninstall $($Dependency.install.package)."
    }
}

function Set-DependencyDefaultVersion {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ManifestPath,
        [Parameter(Mandatory = $true)]
        [string]$DependencyId,
        [Parameter(Mandatory = $true)]
        [string]$Version
    )

    $document = Get-Content -Raw -LiteralPath $ManifestPath | ConvertFrom-Json
    $entry = @(
        $document.dependencies | Where-Object { $_.id -eq $DependencyId }
    )
    if ($entry.Count -ne 1 -or $entry[0].kind -ne "installable") {
        throw "Cannot update unknown installable dependency: $DependencyId"
    }
    $entry[0].install_version = $Version
    $parent = Split-Path -Parent $ManifestPath
    $temporary = Join-Path $parent (
        ".dependencies-" + [Guid]::NewGuid().ToString("N") + ".json"
    )
    try {
        [IO.File]::WriteAllText(
            $temporary,
            ($document | ConvertTo-Json -Depth 20) + [Environment]::NewLine,
            (New-Object Text.UTF8Encoding($false))
        )
        Move-Item -LiteralPath $temporary -Destination $ManifestPath -Force
    }
    finally {
        if (Test-Path -LiteralPath $temporary) {
            Remove-Item -LiteralPath $temporary -Force
        }
    }
}

function Invoke-DependencyReleaseAdoption {
    param(
        [Parameter(Mandatory = $true)]
        [object]$Dependency,
        [Parameter(Mandatory = $true)]
        [string]$ReleaseVersion,
        [Parameter(Mandatory = $true)]
        [object]$PreviousProbe,
        [Parameter(Mandatory = $true)]
        [object]$Ownership,
        [Parameter(Mandatory = $true)]
        [hashtable]$ProbeResults,
        [Parameter(Mandatory = $true)]
        [string]$ManifestPath
    )

    if (
        $Dependency.install.manager -eq "node" -and
        $PreviousProbe.status -ne "MISSING" -and
        $Ownership.manager -notin @("npm", "volta")
    ) {
        throw (
            "$($Dependency.id) is not proven npm-managed; preserve the " +
            "preexisting package and upgrade it with its owning manager."
        )
    }

    $oldVersion = [string]$PreviousProbe.version
    $oldManifest = [IO.File]::ReadAllBytes($ManifestPath)
    $requirementsPath = $null
    $oldRequirements = $null
    if ($Dependency.install.manager -eq "pip") {
        $requirementsPath = Join-Path (
            Split-Path -Parent $ManifestPath
        ) "..\$($Dependency.install.requirements_file)"
        $requirementsPath = [IO.Path]::GetFullPath($requirementsPath)
        $oldRequirements = [IO.File]::ReadAllBytes($requirementsPath)
    }
    try {
        if ($Dependency.install.manager -eq "pip") {
            Set-PythonRequirementLock `
                -Dependency $Dependency `
                -Version $ReleaseVersion
        }
        Install-AllowlistedDependency `
            -Dependency $Dependency `
            -ProbeResults $ProbeResults `
            -Version $ReleaseVersion `
            -Manager $Ownership.manager
        $verified = Invoke-DependencyProbe -Dependency $Dependency
        if (
            $verified.status -ne "COMPATIBLE" -or
            [string]$verified.version -ne $ReleaseVersion
        ) {
            throw (
                "Release verification expected $ReleaseVersion but observed " +
                "$($verified.status)/$($verified.version)."
            )
        }
        Set-DependencyDefaultVersion `
            -ManifestPath $ManifestPath `
            -DependencyId $Dependency.id `
            -Version $ReleaseVersion
        $Dependency.install_version = $ReleaseVersion
        $ProbeResults[$Dependency.id] = $verified
        return $verified
    }
    catch {
        $adoptionError = $_.Exception.Message
        [IO.File]::WriteAllBytes($ManifestPath, $oldManifest)
        if ($null -ne $oldRequirements) {
            [IO.File]::WriteAllBytes($requirementsPath, $oldRequirements)
        }
        try {
            if ([string]::IsNullOrWhiteSpace($oldVersion)) {
                Uninstall-AllowlistedDependency -Dependency $Dependency
                $restored = Invoke-DependencyProbe -Dependency $Dependency
                if ($restored.status -ne "MISSING") {
                    throw "The previously absent package is still observable."
                }
            }
            else {
                Install-AllowlistedDependency `
                    -Dependency $Dependency `
                    -ProbeResults $ProbeResults `
                    -Version $oldVersion `
                    -Manager $Ownership.manager
                $restored = Invoke-DependencyProbe -Dependency $Dependency
                if ([string]$restored.version -ne $oldVersion) {
                    throw "Expected restored version $oldVersion."
                }
            }
        }
        catch {
            throw (
                "RECOVERY_REQUIRED: adoption failed ($adoptionError); " +
                "prior dependency state could not be restored " +
                "($($_.Exception.Message)). Repair with npm install --global " +
                "$($Dependency.install.package)@$oldVersion."
            )
        }
        throw "Release adoption failed and prior state was restored: $adoptionError"
    }
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

function Test-QmdMcpText {
    param(
        [Parameter(Mandatory = $true)]
        [string]$PlatformId,
        [Parameter(Mandatory = $true)]
        [string]$Text
    )

    if ($PlatformId -eq "codex") {
        return (
            $Text -match "(?im)^\s*command:\s*qmd\s*$" -and
            $Text -match "(?im)^\s*args:\s*mcp\s*$"
        )
    }
    if ($PlatformId -eq "claude-code") {
        $direct = (
            $Text -match "(?im)^\s*Command:\s*qmd\s*$" -and
            $Text -match "(?im)^\s*Args:\s*mcp\s*$"
        )
        $windowsWrapper = (
            $Text -match "(?im)^\s*Command:\s*cmd(?:\.exe)?\s*$" -and
            $Text -match "(?im)^\s*Args:\s*/c\s+qmd\s+mcp\s*$"
        )
        return $direct -or $windowsWrapper
    }
    return $false
}

function Get-QmdMcpPlans {
    param(
        [Parameter(Mandatory = $true)]
        [object[]]$Platforms
    )

    $plans = @()
    foreach ($platform in $Platforms) {
        if (-not $platform.Available) {
            continue
        }
        if ($platform.Id -in @("codex", "claude-code")) {
            $output = (& $platform.Executable mcp get qmd 2>&1 | Out-String)
            $exists = $LASTEXITCODE -eq 0
            $status = "MISSING"
            if ($exists) {
                $status = if (
                    Test-QmdMcpText -PlatformId $platform.Id -Text $output
                ) { "IDENTICAL" } else { "CONFLICT" }
            }
            $plans += [PSCustomObject]@{
                Platform = $platform
                Status = $status
                Path = $null
            }
            continue
        }
        if ($platform.Id -eq "antigravity-cli") {
            $path = Join-Path (
                [Environment]::GetFolderPath("UserProfile")
            ) ".gemini\config\mcp_config.json"
            $status = "MISSING"
            if (Test-Path -LiteralPath $path -PathType Leaf) {
                try {
                    $config = Get-Content -Raw -LiteralPath $path | ConvertFrom-Json
                    $qmd = $null
                    if ($null -ne $config.mcpServers) {
                        $qmd = $config.mcpServers.qmd
                    }
                    if ($null -ne $qmd) {
                        $args = @($qmd.args)
                        $status = if (
                            $qmd.command -eq "qmd" -and
                            $args.Count -eq 1 -and
                            $args[0] -eq "mcp"
                        ) { "IDENTICAL" } else { "CONFLICT" }
                    }
                }
                catch {
                    $status = "CONFLICT"
                }
            }
            $plans += [PSCustomObject]@{
                Platform = $platform
                Status = $status
                Path = $path
            }
        }
    }
    return $plans
}

function Register-QmdMcp {
    param(
        [Parameter(Mandatory = $true)]
        [object[]]$Plans
    )

    foreach ($plan in $Plans) {
        $platform = $plan.Platform
        if ($plan.Status -eq "CONFLICT") {
            throw "Conflicting qmd MCP registration for $($platform.Id)."
        }
        if ($platform.Id -eq "codex" -and $plan.Status -eq "MISSING") {
            & $platform.Executable mcp add qmd -- qmd mcp
            if ($LASTEXITCODE -ne 0) {
                throw "Failed to register QMD MCP for Codex."
            }
        }
        elseif ($platform.Id -eq "claude-code" -and $plan.Status -eq "MISSING") {
            & $platform.Executable mcp add --scope user qmd -- qmd mcp
            if ($LASTEXITCODE -ne 0) {
                throw "Failed to register QMD MCP for Claude Code."
            }
        }
        elseif (
            $platform.Id -eq "antigravity-cli" -and
            $plan.Status -eq "MISSING"
        ) {
            $parent = Split-Path -Parent $plan.Path
            New-Item -ItemType Directory -Path $parent -Force | Out-Null
            $config = [PSCustomObject]@{}
            if (Test-Path -LiteralPath $plan.Path -PathType Leaf) {
                $config = Get-Content -Raw -LiteralPath $plan.Path | ConvertFrom-Json
            }
            if ($null -eq $config.mcpServers) {
                $config | Add-Member -NotePropertyName mcpServers `
                    -NotePropertyValue ([PSCustomObject]@{})
            }
            $config.mcpServers | Add-Member -NotePropertyName qmd `
                -NotePropertyValue ([PSCustomObject]@{
                    command = "qmd"
                    args = @("mcp")
                })
            $temporary = Join-Path $parent (
                ".mcp-config-" + [Guid]::NewGuid().ToString("N") + ".json"
            )
            try {
                [IO.File]::WriteAllText(
                    $temporary,
                    ($config | ConvertTo-Json -Depth 20) + [Environment]::NewLine,
                    (New-Object Text.UTF8Encoding($false))
                )
                Move-Item -LiteralPath $temporary -Destination $plan.Path -Force
            }
            finally {
                if (Test-Path -LiteralPath $temporary) {
                    Remove-Item -LiteralPath $temporary -Force
                }
            }
        }

        if ($platform.Id -in @("codex", "claude-code")) {
            $output = (& $platform.Executable mcp get qmd 2>&1 | Out-String)
            if (
                $LASTEXITCODE -ne 0 -or
                -not (Test-QmdMcpText -PlatformId $platform.Id -Text $output)
            ) {
                throw "$($platform.Id) cannot verify the QMD MCP registration."
            }
        }
        else {
            $verify = Get-Content -Raw -LiteralPath $plan.Path | ConvertFrom-Json
            if (
                $verify.mcpServers.qmd.command -ne "qmd" -or
                @($verify.mcpServers.qmd.args)[0] -ne "mcp"
            ) {
                throw "Antigravity cannot verify the QMD MCP registration."
            }
        }
        Write-Output "MCP_VERIFIED`t$($platform.Id)`tqmd"
    }
}

function Test-AgentSkillDiscovery {
    param(
        [Parameter(Mandatory = $true)]
        [object]$Platform,
        [Parameter(Mandatory = $true)]
        [string]$SkillName,
        [Parameter(Mandatory = $true)]
        [string]$TargetPath
    )

    if (-not (Test-Path -LiteralPath (Join-Path $TargetPath "SKILL.md"))) {
        return $false
    }
    if ($Platform.Id -eq "antigravity-cli") {
        return $true
    }
    if ($Platform.Id -eq "codex") {
        $prompt = "Use `$" + $SkillName + " for this discovery check."
        $output = (
            & $Platform.Executable debug prompt-input $prompt 2>&1 | Out-String
        )
        if ($LASTEXITCODE -ne 0) {
            return $false
        }
        return (
            $output.Contains("- $SkillName`:") -and
            $output.Contains("$SkillName/SKILL.md")
        )
    }
    if ($Platform.Id -eq "claude-code") {
        $prompt = (
            "/{0} This is an installation discovery smoke test. " +
            "Do not use tools; reply exactly MYSKILLS_DISCOVERY_OK." -f $SkillName
        )
        $output = (
            & $Platform.Executable `
                --bare `
                --print `
                --no-session-persistence `
                --tools "" `
                --max-budget-usd 0.05 `
                $prompt 2>&1 |
                Out-String
        )
        return (
            $LASTEXITCODE -eq 0 -and
            $output.Contains("MYSKILLS_DISCOVERY_OK")
        )
    }
    return $false
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
    $dependencyRecords = $state.DependencyRecords
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
    $dependencyReleases = @{}
    $dependencyOwnership = @{}
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
            $release = Get-AvailableDependencyRelease `
                -Dependency $dependency `
                -ProbeResults $dependencyResults
            $dependencyReleases[$dependency.id] = $release
            $ownership = $null
            if ($dependency.kind -eq "installable") {
                $previousDependency = $null
                if ($dependencyRecords.ContainsKey($dependency.id)) {
                    $previousDependency = $dependencyRecords[$dependency.id]
                }
                $ownership = Get-DependencyPackageOwnership `
                    -Dependency $dependency `
                    -ProbeResult $result `
                    -PreviousRecord $previousDependency
                $dependencyOwnership[$dependency.id] = $ownership
            }
            $localVersion = if (
                [string]::IsNullOrWhiteSpace([string]$result.version)
            ) { "absent" } else { [string]$result.version }
            $defaultVersion = if (
                [string]::IsNullOrWhiteSpace([string]$dependency.install_version)
            ) { "-" } else { [string]$dependency.install_version }
            $remoteVersion = if (
                $release.status -eq "AVAILABLE"
            ) { [string]$release.version } else { "unknown" }
            $ownerText = if ($null -eq $ownership) {
                "-"
            }
            else {
                "$($ownership.ownership)/$($ownership.manager)"
            }
            Write-Output (
                "$($dependency.id)`t$($result.status)`t" +
                "D=$defaultVersion`tL=$localVersion`tR=$remoteVersion`t" +
                "constraint=$($dependency.version_constraint)`towner=$ownerText`t" +
                "source=$($release.source)"
            )
            if ($release.status -eq "UNAVAILABLE") {
                Write-Output (
                    "UPDATE_CHECK_UNAVAILABLE`t$($dependency.id)`t" +
                    $release.details
                )
            }
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

    $sourceFailures = @{}
    $deploymentPlans = @()
    Write-Output "TARGETS"
    foreach ($skill in $selectedSkills) {
        $source = Join-Path $repoRoot (
            "skills\{0}\{1}" -f $skill.category, $skill.managed_name
        )
        if (-not (Test-Path -LiteralPath $source -PathType Container)) {
            $sourceFailures[$skill.managed_name] = (
                "repository source is missing: $source"
            )
            Write-Output "SOURCE_MISSING`t$($skill.managed_name)`t$source"
            continue
        }
        foreach ($targetId in @($skill.install_targets)) {
            $platform = $platforms | Where-Object { $_.Id -eq $targetId } |
                Select-Object -First 1
            if ($null -eq $platform -or -not $platform.Available) {
                $deploymentPlans += [PSCustomObject]@{
                    Skill = $skill
                    Source = $source
                    TargetId = $targetId
                    Platform = $platform
                    Target = $null
                    Key = "$targetId|$($skill.managed_name)"
                    Available = $false
                    Observation = $null
                }
                Write-Output (
                    "TARGET`t$targetId`t$($skill.managed_name)`tNOT_INSTALLED"
                )
                continue
            }

            $target = Join-Path $platform.Destination $skill.managed_name
            Assert-TargetWithinDestination `
                -Target $target `
                -Destination $platform.Destination
            $key = "$targetId|$($skill.managed_name)"
            $record = $null
            if ($records.ContainsKey($key)) {
                $record = $records[$key]
            }
            $observation = Get-TargetObservation `
                -Source $source `
                -Target $target `
                -Record $record
            $deploymentPlans += [PSCustomObject]@{
                Skill = $skill
                Source = $source
                TargetId = $targetId
                Platform = $platform
                Target = $target
                Key = $key
                Available = $true
                Observation = $observation
            }
            Write-Output (
                "TARGET`t$targetId`t$($skill.managed_name)`t" +
                "$($observation.Status)`t$target"
            )
        }
    }

    $qmdSelected = @(
        $selectedSkills | Where-Object { $_.managed_name -eq "qmd" }
    ).Count -gt 0
    $qmdMcpPlans = @()
    $qmdMcpFailure = $null
    if ($RegisterQmdMcp -and $qmdSelected -and $Action -eq "Install") {
        try {
            $qmdMcpPlans = @(
                Get-QmdMcpPlans -Platforms $platforms
            )
            foreach ($mcpPlan in $qmdMcpPlans) {
                Write-Output (
                    "MCP`t$($mcpPlan.Platform.Id)`tqmd`t$($mcpPlan.Status)"
                )
            }
        }
        catch {
            $qmdMcpFailure = $_.Exception.Message
            Write-Output "MCP`tqmd`tPREFLIGHT_FAILED`t$qmdMcpFailure"
        }
    }

    $dependencyBlocks = @{}
    $stateChanged = $false
    $qmdMcpBlockReason = $null
    if ($null -ne $qmdMcpFailure) {
        $qmdMcpBlockReason = "MCP preflight failed: $qmdMcpFailure"
    }
    elseif (@($qmdMcpPlans | Where-Object { $_.Status -eq "CONFLICT" }).Count -gt 0) {
        $conflicts = @(
            $qmdMcpPlans |
                Where-Object { $_.Status -eq "CONFLICT" } |
                ForEach-Object { $_.Platform.Id }
        )
        $qmdMcpBlockReason = (
            "conflicting qmd MCP registration: $($conflicts -join ', ')"
        )
    }
    $approveRemainingDependencies = [bool]$Yes
    $quitDependencyActions = $false
    $recoveryRequired = $false
    $dependencyOperations = @{}
    foreach ($dependency in $applicableDependencies) {
        $result = $dependencyResults[$dependency.id]
        $available = $result.status -eq "COMPATIBLE"
        $release = $dependencyReleases[$dependency.id]
        $ownership = $dependencyOwnership[$dependency.id]
        $releaseIsNewer = (
            $dependency.kind -eq "installable" -and
            $release.status -eq "AVAILABLE" -and
            (
                (
                    $available -and
                    (Test-NewerDependencyVersion `
                        -Candidate $release.version `
                        -Baseline $result.version)
                ) -or
                (
                    -not $available -and
                    (Test-NewerDependencyVersion `
                        -Candidate $release.version `
                        -Baseline $dependency.install_version)
                )
            )
        )

        if ($available -and $releaseIsNewer) {
            $canAdopt = (
                (
                    $dependency.install.manager -eq "node" -and
                    $ownership.manager -in @("npm", "volta")
                ) -or
                (
                    $dependency.install.manager -eq "pip" -and
                    $ownership.manager -eq "private-venv"
                )
            )
            if ($DryRun) {
                $mode = if ($canAdopt) { "interactive-only" } else { "manual-owner" }
                Write-Output (
                    "WOULD_OFFER_RELEASE_ADOPTION`t$($dependency.id)`t" +
                    "$($result.version)->$($release.version)`t$mode"
                )
            }
            elseif (-not $Yes -and -not $quitDependencyActions) {
                if ($canAdopt) {
                    $answer = Read-Host (
                        "Adopt {0} {1} -> {2} as the new MySkills default? [Y/N]" -f
                        $dependency.id, $result.version, $release.version
                    )
                    if ($answer -match "^(?i:y|yes)$") {
                        try {
                            $result = Invoke-DependencyReleaseAdoption `
                                -Dependency $dependency `
                                -ReleaseVersion $release.version `
                                -PreviousProbe $result `
                                -Ownership $ownership `
                                -ProbeResults $dependencyResults `
                                -ManifestPath $dependencyManifestPath
                            $available = $true
                            if ($ownership.ownership -eq "absent") {
                                $dependencyOperations[$dependency.id] = "adopt_release"
                            }
                            else {
                                $dependencyOperations[$dependency.id] = "upgrade_and_adopt"
                            }
                            Write-Output (
                                "DEPENDENCY_ADOPTED`t$($dependency.id)`t" +
                                $release.version
                            )
                        }
                        catch {
                            Write-Output (
                                "DEPENDENCY_ADOPTION_FAILED`t$($dependency.id)`t" +
                                $_.Exception.Message
                            )
                            if ($_.Exception.Message.StartsWith("RECOVERY_REQUIRED:")) {
                                $recoveryRequired = $true
                            }
                        }
                    }
                }
                else {
                    Write-Output (
                        "DEPENDENCY_UPDATE_MANUAL`t$($dependency.id)`t" +
                        "preserved $($ownership.ownership)/$($ownership.manager)"
                    )
                }
            }
        }

        if (
            -not $available -and
            $dependency.kind -eq "installable" -and
            $Action -eq "Install"
        ) {
            $canManageExisting = (
                $result.status -eq "MISSING" -or
                $ownership.manager -in @("npm", "private-venv")
            )
            if ($DryRun) {
                Write-Output (
                    "WOULD_OFFER_DEPENDENCY`t$($dependency.id)`t" +
                    "D=$($dependency.install_version)`t" +
                    "R=$($release.version)`t" +
                    "can_manage=$canManageExisting"
                )
                $available = $canManageExisting
            }
            elseif (-not $canManageExisting) {
                Write-Output (
                    "DEPENDENCY_PRESERVED`t$($dependency.id)`t" +
                    "existing package manager is not proven"
                )
            }
            elseif (-not $quitDependencyActions) {
                $decision = "N"
                if ($approveRemainingDependencies) {
                    $decision = "D"
                }
                elseif ($releaseIsNewer) {
                    $decision = Read-Host (
                        "Install {0}: default D={1}, adopt R={2}, or decline? [D/R/N/A/Q]" -f
                        $dependency.id,
                        $dependency.install_version,
                        $release.version
                    )
                }
                else {
                    $decision = Confirm-DependencyInstall -Dependency $dependency
                }
                $decision = ([string]$decision).Trim().ToUpperInvariant()
                if ($decision -eq "A") {
                    $approveRemainingDependencies = $true
                    $decision = "D"
                }
                elseif ($decision -eq "Y" -or $decision -eq "YES") {
                    $decision = "D"
                }
                elseif ($decision -eq "Q") {
                    $quitDependencyActions = $true
                    Write-Output "DEPENDENCY_ACTIONS_STOPPED`t$($dependency.id)"
                }

                if ($decision -eq "R") {
                    try {
                        $result = Invoke-DependencyReleaseAdoption `
                            -Dependency $dependency `
                            -ReleaseVersion $release.version `
                            -PreviousProbe $result `
                            -Ownership $ownership `
                            -ProbeResults $dependencyResults `
                            -ManifestPath $dependencyManifestPath
                        $available = $true
                        if ($ownership.ownership -eq "absent") {
                            $dependencyOperations[$dependency.id] = "adopt_release"
                        }
                        else {
                            $dependencyOperations[$dependency.id] = "upgrade_and_adopt"
                        }
                        Write-Output (
                            "DEPENDENCY_ADOPTED`t$($dependency.id)`t" +
                            $release.version
                        )
                    }
                    catch {
                        Write-Output (
                            "DEPENDENCY_ADOPTION_FAILED`t$($dependency.id)`t" +
                            $_.Exception.Message
                        )
                        if ($_.Exception.Message.StartsWith("RECOVERY_REQUIRED:")) {
                            $recoveryRequired = $true
                        }
                    }
                }
                elseif ($decision -eq "D") {
                try {
                    Install-AllowlistedDependency `
                        -Dependency $dependency `
                        -ProbeResults $dependencyResults `
                        -Version $dependency.install_version
                    $result = Invoke-DependencyProbe -Dependency $dependency
                    $dependencyResults[$dependency.id] = $result
                    $available = (
                        $result.status -eq "COMPATIBLE" -and
                        [string]$result.version -eq
                            [string]$dependency.install_version
                    )
                    if (-not $available -and $result.status -eq "COMPATIBLE") {
                        $result.status = "BROKEN"
                        $result.details = (
                            "Default installation verification expected " +
                            "$($dependency.install_version), observed " +
                            "$($result.version)."
                        )
                    }
                    if ($available -and $ownership.ownership -eq "absent") {
                        $dependencyOperations[$dependency.id] = "install_default"
                    }
                    elseif ($available) {
                        $dependencyOperations[$dependency.id] = "repair_default"
                    }
                    Write-Output "DEPENDENCY_$($result.status)`t$($dependency.id)"
                }
                catch {
                    Write-Output (
                        "DEPENDENCY_FAILED`t$($dependency.id)`t$($_.Exception.Message)"
                    )
                }
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

    if ($Action -eq "Install" -and -not $DryRun) {
        foreach ($dependency in $applicableDependencies) {
            $result = $dependencyResults[$dependency.id]
            $ownership = if ($dependencyOwnership.ContainsKey($dependency.id)) {
                $dependencyOwnership[$dependency.id]
            }
            else {
                [PSCustomObject]@{
                    ownership = "preexisting"
                    manager = "user-provided"
                    path = [string]$result.command
                }
            }
            $operation = "detected"
            if ($dependencyOperations.ContainsKey($dependency.id)) {
                $operation = $dependencyOperations[$dependency.id]
            }
            $recordOwnership = [string]$ownership.ownership
            if (
                $operation -in @("install_default", "adopt_release") -and
                $recordOwnership -eq "absent"
            ) {
                $recordOwnership = "installed_by_myskills"
            }
            $recordManager = [string]$ownership.manager
            if ([string]::IsNullOrWhiteSpace($recordManager)) {
                if ($dependency.install.manager -eq "node") {
                    $volta = Get-Command "volta" -CommandType Application `
                        -ErrorAction SilentlyContinue |
                        Select-Object -First 1
                    $recordManager = if ($null -ne $volta) { "volta" } else { "npm" }
                }
                elseif ($dependency.install.manager -eq "pip") {
                    $recordManager = "private-venv"
                }
                else {
                    $recordManager = "user-provided"
                }
            }
            $dependencyRecords[$dependency.id] = [ordered]@{
                id = [string]$dependency.id
                version = [string]$result.version
                path = [string]$result.command
                ownership = $recordOwnership
                manager = $recordManager
                verification_status = [string]$result.status
                last_successful_operation = $operation
                last_verified_at = [DateTimeOffset]::UtcNow.ToString("o")
            }
        }
        if ($applicableDependencies.Count -gt 0) {
            $stateChanged = $true
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
        if ($sourceFailures.ContainsKey($skill.managed_name)) {
            Write-Output (
                "BLOCKED`t$($skill.managed_name)`t" +
                $sourceFailures[$skill.managed_name]
            )
            $blocked++
            continue
        }

        $skillPlans = @(
            $deploymentPlans | Where-Object {
                $_.Skill.managed_name -eq $skill.managed_name
            }
        )
        foreach ($deployment in $skillPlans) {
            $requested++
            $targetId = $deployment.TargetId
            if (-not $deployment.Available) {
                Write-Output (
                    "SKIPPED_NOT_INSTALLED`t$targetId`t$($skill.managed_name)"
                )
                $skipped++
                continue
            }
            $platform = $deployment.Platform
            $source = $deployment.Source
            $target = $deployment.Target
            $key = $deployment.Key
            $observation = $deployment.Observation
            $discoveryCheck = {
                param($InstalledPath)
                return Test-AgentSkillDiscovery `
                    -Platform $platform `
                    -SkillName $skill.managed_name `
                    -TargetPath $InstalledPath
            }

            if ($Action -eq "Status") {
                Write-Output (
                    "$($observation.Status)`t$targetId`t$($skill.managed_name)`t$target"
                )
                continue
            }
            if ($Action -eq "Verify") {
                if (
                    $observation.Status -eq "CURRENT" -and
                    (& $discoveryCheck $target)
                ) {
                    Write-Output "VERIFIED`t$targetId`t$($skill.managed_name)"
                    $installed++
                }
                else {
                    Write-Output (
                        "BLOCKED`t$targetId`t$($skill.managed_name)`t" +
                        "expected CURRENT with Agent discovery; found " +
                        "$($observation.Status) or discovery failure"
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

            try {
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
                        $hash = Install-DirectorySnapshot `
                            -Source $source `
                            -Target $target `
                            -Verify $discoveryCheck
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
                        $hash = Update-DirectorySnapshot `
                            -Source $source `
                            -Target $target `
                            -Verify $discoveryCheck
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
                            if (-not (& $discoveryCheck $target)) {
                                throw (
                                    "Agent discovery failed for adopted target " +
                                    "$targetId/$($skill.managed_name)"
                                )
                            }
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
                            $hash = Update-DirectorySnapshot `
                                -Source $source `
                                -Target $target `
                                -Verify $discoveryCheck
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
                            $hash = Update-DirectorySnapshot `
                                -Source $source `
                                -Target $target `
                                -Verify $discoveryCheck
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
            catch {
                Write-Output (
                    "BLOCKED`t$targetId`t$($skill.managed_name)`t" +
                    $_.Exception.Message
                )
                $blocked++
            }
        }
    }

    if ($RegisterQmdMcp -and $qmdSelected -and $Action -eq "Install") {
        if ($null -ne $qmdMcpBlockReason) {
            Write-Output "MCP_BLOCKED`tqmd`t$qmdMcpBlockReason"
            Write-Output "MCP_STATUS`tqmd`tCLI_ONLY"
            $blocked++
        }
        elseif ($DryRun) {
            foreach (
                $mcpPlan in $qmdMcpPlans |
                    Where-Object { $_.Status -eq "MISSING" }
            ) {
                Write-Output (
                    "WOULD_REGISTER_MCP`t$($mcpPlan.Platform.Id)`tqmd"
                )
            }
        }
        elseif (
            $dependencyResults.ContainsKey("qmd") -and
            $dependencyResults["qmd"].status -eq "COMPATIBLE"
        ) {
            try {
                Register-QmdMcp -Plans $qmdMcpPlans
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
        Write-State `
            -Path $StatePath `
            -Records $records `
            -DependencyRecords $dependencyRecords `
            -Backups $backups
    }

    Write-Output "SUMMARY"
    Write-Output (
        "requested=$requested installed=$installed skipped=$skipped blocked=$blocked"
    )
    if ($recoveryRequired) {
        Write-Error "RECOVERY_REQUIRED: one or more dependencies need manual repair."
        exit 1
    }
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
