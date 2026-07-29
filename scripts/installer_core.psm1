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

function Read-CodexAppServerResponse {
    param(
        [Parameter(Mandatory = $true)]
        [System.Diagnostics.Process]$Process,

        [Parameter(Mandatory = $true)]
        [int]$RequestId,

        [int]$TimeoutMilliseconds = 10000
    )

    $stopwatch = [Diagnostics.Stopwatch]::StartNew()
    while ($stopwatch.ElapsedMilliseconds -lt $TimeoutMilliseconds) {
        $remaining = [Math]::Max(
            1,
            $TimeoutMilliseconds - [int]$stopwatch.ElapsedMilliseconds
        )
        $lineTask = $Process.StandardOutput.ReadLineAsync()
        if (-not $lineTask.Wait($remaining)) {
            throw "Timed out waiting for Codex app-server response $RequestId."
        }
        $line = $lineTask.Result
        if ($null -eq $line) {
            throw "Codex app-server closed before response $RequestId."
        }
        try {
            $message = $line | ConvertFrom-Json
        }
        catch {
            continue
        }
        $idProperty = $message.PSObject.Properties["id"]
        if ($null -ne $idProperty -and $idProperty.Value -eq $RequestId) {
            return $message
        }
    }
    throw "Timed out waiting for Codex app-server response $RequestId."
}

function Test-CodexSkillDiscovery {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$Executable,

        [Parameter(Mandatory = $true)]
        [string]$SkillName,

        [Parameter(Mandatory = $true)]
        [string]$TargetPath,

        [Parameter(Mandatory = $true)]
        [string]$WorkingDirectory
    )

    $expectedSkillFile = [IO.Path]::GetFullPath(
        (Join-Path $TargetPath "SKILL.md")
    )
    if (-not (Test-Path -LiteralPath $expectedSkillFile -PathType Leaf)) {
        return $false
    }

    $resolvedExecutable = [IO.Path]::GetFullPath($Executable)
    if ([IO.Path]::GetExtension($resolvedExecutable) -ieq ".ps1") {
        $cmdCandidate = [IO.Path]::ChangeExtension($resolvedExecutable, ".cmd")
        if (-not (Test-Path -LiteralPath $cmdCandidate -PathType Leaf)) {
            throw "Codex app-server requires an executable or CMD launcher."
        }
        $resolvedExecutable = $cmdCandidate
    }

    $startInfo = New-Object Diagnostics.ProcessStartInfo
    $extension = [IO.Path]::GetExtension($resolvedExecutable)
    if ($extension -ieq ".cmd" -or $extension -ieq ".bat") {
        if ($resolvedExecutable.Contains('"')) {
            throw "Unsupported quote in Codex launcher path."
        }
        $startInfo.FileName = $env:ComSpec
        $startInfo.Arguments = (
            '/d /c call "{0}" app-server --stdio' -f $resolvedExecutable
        )
    }
    else {
        $startInfo.FileName = $resolvedExecutable
        $startInfo.Arguments = "app-server --stdio"
    }
    $startInfo.UseShellExecute = $false
    $startInfo.CreateNoWindow = $true
    $startInfo.RedirectStandardInput = $true
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true

    $process = New-Object Diagnostics.Process
    $process.StartInfo = $startInfo
    $previousInputEncoding = [Console]::InputEncoding
    try {
        [Console]::InputEncoding = New-Object Text.UTF8Encoding($false)
        if (-not $process.Start()) {
            throw "Codex app-server did not start."
        }
        $standardInput = $process.StandardInput
    }
    finally {
        [Console]::InputEncoding = $previousInputEncoding
    }

    $standardErrorTask = $process.StandardError.ReadToEndAsync()
    try {
        $initialize = @{
            id = 1
            method = "initialize"
            params = @{
                clientInfo = @{
                    name = "myskills-installer"
                    version = "1.0"
                }
            }
        } | ConvertTo-Json -Compress -Depth 8
        $standardInput.WriteLine($initialize)
        $standardInput.Flush()
        $initializeResponse = Read-CodexAppServerResponse `
            -Process $process `
            -RequestId 1
        if ($null -ne $initializeResponse.PSObject.Properties["error"]) {
            throw "Codex app-server initialization failed."
        }

        $initialized = @{
            method = "initialized"
            params = @{}
        } | ConvertTo-Json -Compress -Depth 4
        $listRequest = @{
            id = 2
            method = "skills/list"
            params = @{
                cwds = @([IO.Path]::GetFullPath($WorkingDirectory))
                forceReload = $true
            }
        } | ConvertTo-Json -Compress -Depth 8
        $standardInput.WriteLine($initialized)
        $standardInput.WriteLine($listRequest)
        $standardInput.Flush()

        $listResponse = Read-CodexAppServerResponse `
            -Process $process `
            -RequestId 2
        if ($null -ne $listResponse.PSObject.Properties["error"]) {
            throw "Codex app-server Skill discovery failed."
        }
        foreach ($entry in @($listResponse.result.data)) {
            foreach ($skill in @($entry.skills)) {
                if (
                    $skill.name -eq $SkillName -and
                    [IO.Path]::GetFullPath([string]$skill.path) -ieq
                        $expectedSkillFile -and
                    $skill.enabled -ne $false
                ) {
                    return $true
                }
            }
        }
        return $false
    }
    finally {
        try {
            $standardInput.Close()
        }
        catch {
        }
        if (-not $process.HasExited) {
            $process.Kill()
        }
        $process.WaitForExit()
        $null = $standardErrorTask.GetAwaiter().GetResult()
        $process.Dispose()
    }
}

function Test-ClaudeSkillDiscovery {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$Executable,

        [Parameter(Mandatory = $true)]
        [string]$SkillName,

        [Parameter(Mandatory = $true)]
        [string]$TargetPath
    )

    if (
        -not (
            Test-Path `
                -LiteralPath (Join-Path $TargetPath "SKILL.md") `
                -PathType Leaf
        )
    ) {
        return $false
    }

    $resolvedExecutable = [IO.Path]::GetFullPath($Executable)
    $extension = [IO.Path]::GetExtension($resolvedExecutable)
    if ($extension -ieq ".ps1" -or $extension -ieq ".cmd") {
        $nativeCandidate = Join-Path `
            (Split-Path -Parent $resolvedExecutable) `
            "node_modules\@anthropic-ai\claude-code\bin\claude.exe"
        if (Test-Path -LiteralPath $nativeCandidate -PathType Leaf) {
            $resolvedExecutable = $nativeCandidate
            $extension = ".exe"
        }
        elseif ($extension -ieq ".ps1") {
            $cmdCandidate = [IO.Path]::ChangeExtension(
                $resolvedExecutable,
                ".cmd"
            )
            if (-not (Test-Path -LiteralPath $cmdCandidate -PathType Leaf)) {
                throw "Claude discovery requires an executable or CMD launcher."
            }
            $resolvedExecutable = $cmdCandidate
            $extension = ".cmd"
        }
    }

    $listener = New-Object Net.Sockets.TcpListener(
        [Net.IPAddress]::Loopback,
        0
    )
    $emptyMcpConfig = Join-Path `
        ([IO.Path]::GetTempPath()) `
        ("myskills-empty-mcp-" + [Guid]::NewGuid().ToString("N") + ".json")
    $process = $null
    $standardErrorTask = $null
    try {
        $listener.Start()
        $port = ([Net.IPEndPoint]$listener.LocalEndpoint).Port
        $listener.Stop()
        [IO.File]::WriteAllText(
            $emptyMcpConfig,
            '{"mcpServers":{}}',
            (New-Object Text.UTF8Encoding($false))
        )

        $arguments = @(
            "--print",
            "/$SkillName installation discovery only",
            "--output-format",
            "stream-json",
            "--verbose",
            "--no-session-persistence",
            "--setting-sources=user",
            "--mcp-config",
            $emptyMcpConfig,
            "--strict-mcp-config",
            "--no-chrome",
            "--max-turns",
            "1",
            "--tools",
            ""
        )
        $quotedArguments = @(
            foreach ($argument in $arguments) {
                if ($argument.Contains('"')) {
                    throw "Unsupported quote in Claude discovery argument."
                }
                '"' + $argument + '"'
            }
        )

        $startInfo = New-Object Diagnostics.ProcessStartInfo
        if ($extension -ieq ".cmd" -or $extension -ieq ".bat") {
            if ($resolvedExecutable.Contains('"')) {
                throw "Unsupported quote in Claude launcher path."
            }
            $startInfo.FileName = $env:ComSpec
            $startInfo.Arguments = (
                '/d /c call "{0}" {1}' -f
                    $resolvedExecutable,
                    ($quotedArguments -join " ")
            )
        }
        else {
            $startInfo.FileName = $resolvedExecutable
            $startInfo.Arguments = $quotedArguments -join " "
        }
        $startInfo.UseShellExecute = $false
        $startInfo.CreateNoWindow = $true
        $startInfo.RedirectStandardInput = $true
        $startInfo.RedirectStandardOutput = $true
        $startInfo.RedirectStandardError = $true
        $startInfo.EnvironmentVariables["ANTHROPIC_BASE_URL"] = (
            "http://127.0.0.1:$port"
        )
        $startInfo.EnvironmentVariables["ANTHROPIC_API_KEY"] = (
            "myskills-local-discovery-probe"
        )
        $startInfo.EnvironmentVariables[
            "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC"
        ] = "1"

        $process = New-Object Diagnostics.Process
        $process.StartInfo = $startInfo
        if (-not $process.Start()) {
            throw "Claude discovery process did not start."
        }
        $process.StandardInput.Close()
        $standardErrorTask = $process.StandardError.ReadToEndAsync()
        $stopwatch = [Diagnostics.Stopwatch]::StartNew()
        while ($stopwatch.ElapsedMilliseconds -lt 10000) {
            $remaining = [Math]::Max(
                1,
                10000 - [int]$stopwatch.ElapsedMilliseconds
            )
            $lineTask = $process.StandardOutput.ReadLineAsync()
            if (-not $lineTask.Wait($remaining)) {
                throw "Timed out waiting for Claude discovery evidence."
            }
            $line = $lineTask.Result
            if ($null -eq $line) {
                break
            }
            try {
                $event = $line | ConvertFrom-Json
            }
            catch {
                continue
            }
            $typeProperty = $event.PSObject.Properties["type"]
            $subtypeProperty = $event.PSObject.Properties["subtype"]
            if (
                $null -ne $typeProperty -and
                $typeProperty.Value -eq "system" -and
                $null -ne $subtypeProperty -and
                $subtypeProperty.Value -eq "init"
            ) {
                return (@($event.skills) -contains $SkillName)
            }
        }
        throw "Claude discovery evidence was not emitted."
    }
    finally {
        if ($null -ne $process) {
            try {
                $process.StandardInput.Close()
            }
            catch {
            }
            if (-not $process.HasExited) {
                $process.Kill()
            }
            $process.WaitForExit()
            if ($null -ne $standardErrorTask) {
                $null = $standardErrorTask.GetAwaiter().GetResult()
            }
            $process.Dispose()
        }
        $listener.Stop()
        if (Test-Path -LiteralPath $emptyMcpConfig) {
            Remove-Item -LiteralPath $emptyMcpConfig -Force
        }
    }
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

function Set-ReparsePointDirectorySnapshot {
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
        throw "Reparse-point target does not exist: $resolvedTarget"
    }
    $targetItem = Get-Item -LiteralPath $resolvedTarget -Force
    if (
        ($targetItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -eq 0
    ) {
        throw "Target is not a reparse point: $resolvedTarget"
    }
    $linkTypeProperty = $targetItem.PSObject.Properties["LinkType"]
    $linkType = if ($null -ne $linkTypeProperty) {
        [string]$linkTypeProperty.Value
    }
    else {
        ""
    }
    if ($linkType -notin @("Junction", "SymbolicLink")) {
        throw "Unsupported reparse-point type '$linkType': $resolvedTarget"
    }

    $parent = Split-Path -Parent $resolvedTarget
    $preservedLink = Join-Path $parent (
        ".myskills-previous-link-" + [Guid]::NewGuid().ToString("N")
    )
    $movedLink = $false
    try {
        Move-Item -LiteralPath $resolvedTarget -Destination $preservedLink
        $movedLink = $true
        $sourceHash = Install-DirectorySnapshot `
            -Source $Source `
            -Target $resolvedTarget `
            -Verify $Verify

        $preservedItem = Get-Item -LiteralPath $preservedLink -Force
        if (
            ($preservedItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -eq
                0
        ) {
            throw "Preserved target is not a reparse point: $preservedLink"
        }
        [IO.Directory]::Delete($preservedLink, $false)
        $movedLink = $false
        return $sourceHash
    }
    catch {
        $failure = $_
        if ($movedLink) {
            try {
                $null = Get-Item `
                    -LiteralPath $preservedLink `
                    -Force `
                    -ErrorAction Stop
            }
            catch {
                throw (
                    "Recovery required: original link is unavailable at " +
                    $preservedLink
                )
            }
            if (Test-Path -LiteralPath $resolvedTarget) {
                $replacement = Get-Item -LiteralPath $resolvedTarget -Force
                if (
                    ($replacement.Attributes -band
                        [IO.FileAttributes]::ReparsePoint) -ne 0
                ) {
                    throw (
                        "Recovery required: unexpected reparse point remains at " +
                        $resolvedTarget
                    )
                }
                Remove-Item -LiteralPath $resolvedTarget -Recurse -Force
            }
            Move-Item -LiteralPath $preservedLink -Destination $resolvedTarget
            $movedLink = $false
        }
        throw $failure
    }
    finally {
        if ($movedLink) {
            throw "Recovery required: original link remains at $preservedLink"
        }
    }
}

function Format-SkillTargetPlanLine {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$PlatformId,

        [Parameter(Mandatory = $true)]
        [string]$SkillName,

        [Parameter(Mandatory = $true)]
        [string]$Status,

        [Parameter(Mandatory = $true)]
        [string]$TargetPath,

        [bool]$IsReparsePoint = $false,

        [AllowEmptyString()]
        [string]$LinkType = "",

        [AllowEmptyString()]
        [string]$LinkTarget = ""
    )

    $line = "TARGET`t$PlatformId`t$SkillName`t$Status`t$TargetPath"
    if ($IsReparsePoint) {
        $line += "`tLINK`t$LinkType`t$LinkTarget"
    }
    return $line
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
    "Format-SkillTargetPlanLine",
    "Get-DirectoryDigest",
    "Get-SkillDeploymentState",
    "Install-DirectorySnapshot",
    "Set-ReparsePointDirectorySnapshot",
    "Test-ClaudeSkillDiscovery",
    "Test-CodexSkillDiscovery",
    "Update-DirectorySnapshot"
)
