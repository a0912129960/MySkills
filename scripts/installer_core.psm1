Set-StrictMode -Version 2.0

function Get-DirectoryDigest {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    $resolvedRoot = [IO.Path]::GetFullPath((Resolve-Path -LiteralPath $Path).Path)
    if (-not (Test-Path -LiteralPath $resolvedRoot -PathType Container)) {
        throw "Directory does not exist: $resolvedRoot"
    }

    $files = @(
        Get-ChildItem -LiteralPath $resolvedRoot -Recurse -File |
            ForEach-Object {
                [PSCustomObject]@{
                    File = $_
                    Relative = $_.FullName.Substring($resolvedRoot.Length).TrimStart(
                        [IO.Path]::DirectorySeparatorChar,
                        [IO.Path]::AltDirectorySeparatorChar
                    ).Replace([IO.Path]::DirectorySeparatorChar, "/")
                }
            } |
            Sort-Object -Property Relative
    )

    $stream = New-Object IO.MemoryStream
    $writer = New-Object IO.BinaryWriter(
        $stream,
        (New-Object Text.UTF8Encoding($false)),
        $true
    )
    try {
        foreach ($entry in $files) {
            $pathBytes = [Text.Encoding]::UTF8.GetBytes([string]$entry.Relative)
            $content = [IO.File]::ReadAllBytes($entry.File.FullName)
            $writer.Write([int]$pathBytes.Length)
            $writer.Write([byte[]]$pathBytes)
            $writer.Write([long]$content.Length)
            $writer.Write([byte[]]$content)
        }
        $writer.Flush()
        $stream.Position = 0
        $sha256 = [Security.Cryptography.SHA256]::Create()
        try {
            $digest = $sha256.ComputeHash($stream)
        }
        finally {
            $sha256.Dispose()
        }
        return ([BitConverter]::ToString($digest)).Replace("-", "").ToLowerInvariant()
    }
    finally {
        $writer.Dispose()
        $stream.Dispose()
    }
}

function Get-SkillDeploymentState {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [bool]$TargetExists,

        [Parameter(Mandatory = $true)]
        [string]$SourceHash,

        [AllowNull()]
        [string]$RecordedHash,

        [AllowNull()]
        [string]$ActualHash
    )

    if (-not $TargetExists) {
        return "MISSING"
    }
    if ([string]::IsNullOrEmpty($RecordedHash)) {
        return "UNOWNED"
    }
    if ($ActualHash -ne $RecordedHash) {
        return "DRIFTED"
    }
    if ($SourceHash -ne $RecordedHash) {
        return "UPDATE_AVAILABLE"
    }
    return "CURRENT"
}

function Install-DirectorySnapshot {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$Source,

        [Parameter(Mandatory = $true)]
        [string]$Target,

        [scriptblock]$Verify
    )

    $resolvedSource = [IO.Path]::GetFullPath((Resolve-Path -LiteralPath $Source).Path)
    if (-not (Test-Path -LiteralPath $resolvedSource -PathType Container)) {
        throw "Source directory does not exist: $resolvedSource"
    }

    $resolvedTarget = [IO.Path]::GetFullPath($Target)
    if (Test-Path -LiteralPath $resolvedTarget) {
        throw "Target already exists: $resolvedTarget"
    }

    $parent = Split-Path -Parent $resolvedTarget
    if ([string]::IsNullOrWhiteSpace($parent)) {
        throw "Target must have a parent directory: $resolvedTarget"
    }
    New-Item -ItemType Directory -Path $parent -Force | Out-Null

    $staging = Join-Path $parent (".myskills-stage-" + [Guid]::NewGuid().ToString("N"))
    $installedTarget = $false
    try {
        Copy-Item -LiteralPath $resolvedSource -Destination $staging -Recurse
        $sourceHash = Get-DirectoryDigest -Path $resolvedSource
        $stagingHash = Get-DirectoryDigest -Path $staging
        if ($stagingHash -ne $sourceHash) {
            throw "Copied snapshot digest mismatch for $resolvedTarget"
        }
        Move-Item -LiteralPath $staging -Destination $resolvedTarget
        $installedTarget = $true
        if ($null -ne $Verify -and -not (& $Verify $resolvedTarget)) {
            Remove-Item -LiteralPath $resolvedTarget -Recurse -Force
            $installedTarget = $false
            throw "Post-copy verification failed for $resolvedTarget"
        }
        return $sourceHash
    }
    catch {
        if ($installedTarget -and (Test-Path -LiteralPath $resolvedTarget)) {
            Remove-Item -LiteralPath $resolvedTarget -Recurse -Force
        }
        throw
    }
    finally {
        if (Test-Path -LiteralPath $staging) {
            Remove-Item -LiteralPath $staging -Recurse -Force
        }
    }
}

function Update-DirectorySnapshot {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$Source,

        [Parameter(Mandatory = $true)]
        [string]$Target,

        [scriptblock]$Verify
    )

    $resolvedTarget = [IO.Path]::GetFullPath($Target)
    if (-not (Test-Path -LiteralPath $resolvedTarget -PathType Container)) {
        throw "Target directory does not exist: $resolvedTarget"
    }
    $parent = Split-Path -Parent $resolvedTarget
    $token = [Guid]::NewGuid().ToString("N")
    $replacement = Join-Path $parent (".myskills-replacement-" + $token)
    $previous = Join-Path $parent (".myskills-previous-" + $token)
    $movedPrevious = $false
    try {
        $sourceHash = Install-DirectorySnapshot -Source $Source -Target $replacement
        Move-Item -LiteralPath $resolvedTarget -Destination $previous
        $movedPrevious = $true
        Move-Item -LiteralPath $replacement -Destination $resolvedTarget
        if ($null -ne $Verify -and -not (& $Verify $resolvedTarget)) {
            throw "Post-copy verification failed for $resolvedTarget"
        }
        Remove-Item -LiteralPath $previous -Recurse -Force
        $movedPrevious = $false
        return $sourceHash
    }
    catch {
        if ($movedPrevious -and (Test-Path -LiteralPath $previous)) {
            if (Test-Path -LiteralPath $resolvedTarget) {
                Remove-Item -LiteralPath $resolvedTarget -Recurse -Force
            }
            Move-Item -LiteralPath $previous -Destination $resolvedTarget
            $movedPrevious = $false
        }
        throw
    }
    finally {
        if (Test-Path -LiteralPath $replacement) {
            Remove-Item -LiteralPath $replacement -Recurse -Force
        }
        if ($movedPrevious -and (Test-Path -LiteralPath $previous)) {
            throw "Recovery required: previous snapshot remains at $previous"
        }
    }
}

function Backup-DirectorySnapshot {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$Source,

        [Parameter(Mandatory = $true)]
        [string]$Backup
    )

    $sourceHash = Get-DirectoryDigest -Path $Source
    $backupHash = Install-DirectorySnapshot -Source $Source -Target $Backup
    if ($backupHash -ne $sourceHash) {
        throw "Backup digest mismatch for $Backup"
    }
    return $backupHash
}

Export-ModuleMember -Function @(
    "Backup-DirectorySnapshot",
    "Get-DirectoryDigest",
    "Get-SkillDeploymentState",
    "Install-DirectorySnapshot",
    "Update-DirectorySnapshot"
)
