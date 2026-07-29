Set-StrictMode -Version 2.0

function ConvertTo-DependencyVersion {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$Value
    )

    $match = [regex]::Match($Value, '\d+(?:\.\d+){1,3}')
    if (-not $match.Success) {
        return $null
    }

    try {
        return [version]$match.Value
    }
    catch {
        return $null
    }
}

function Test-DependencyVersion {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [version]$Version,

        [AllowNull()]
        [string]$Constraint
    )

    if ([string]::IsNullOrWhiteSpace($Constraint)) {
        return $true
    }

    foreach ($alternative in ($Constraint -split '\s*\|\|\s*')) {
        $candidate = $alternative.Trim()
        if ($candidate -match '^>=\s*(\d+(?:\.\d+){1,3})$') {
            if ($Version -ge [version]$Matches[1]) {
                return $true
            }
            continue
        }

        if ($candidate -match '^\^(\d+)\.(\d+)\.(\d+)$') {
            $minimum = [version]::new(
                [int]$Matches[1],
                [int]$Matches[2],
                [int]$Matches[3]
            )
            $maximum = [version]::new($minimum.Major + 1, 0, 0)
            if ($Version -ge $minimum -and $Version -lt $maximum) {
                return $true
            }
            continue
        }

        throw "Unsupported dependency version constraint: $candidate"
    }

    return $false
}

function Resolve-DependencyCommand {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$Command
    )

    $expanded = [Environment]::ExpandEnvironmentVariables($Command)
    if ([System.IO.Path]::IsPathRooted($expanded)) {
        if (Test-Path -LiteralPath $expanded -PathType Leaf) {
            return (Get-Item -LiteralPath $expanded).FullName
        }
        return $null
    }

    $resolved = Get-Command -Name $expanded -CommandType Application -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if ($null -eq $resolved) {
        return $null
    }
    return $resolved.Source
}

function Invoke-DependencyCommand {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$Command,

        [Parameter(Mandatory = $true)]
        [object[]]$Arguments
    )

    $previousErrorActionPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        $output = @(& $Command @Arguments 2>&1)
        $exitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }
    if ($null -eq $exitCode) {
        $exitCode = 0
    }

    return [pscustomobject]@{
        exit_code = [int]$exitCode
        output = (($output | ForEach-Object { [string]$_ }) -join [Environment]::NewLine).Trim()
    }
}

function Invoke-DependencyProbe {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [psobject]$Dependency,

        [switch]$DryRun
    )

    $plannedCommand = [string]$Dependency.probe.candidates[0].command
    $result = [ordered]@{
        dependency_id = [string]$Dependency.id
        status = 'MISSING'
        command = $plannedCommand
        version = $null
        minimum_version = $Dependency.minimum_version
        version_constraint = $Dependency.version_constraint
        exit_code = $null
        details = $null
    }

    if ($DryRun) {
        $result.status = 'PLANNED'
        $result.details = 'Read-only version and smoke probes would run.'
        return [pscustomobject]$result
    }

    foreach ($candidate in $Dependency.probe.candidates) {
        $resolved = Resolve-DependencyCommand -Command ([string]$candidate.command)
        if ($null -eq $resolved) {
            continue
        }

        $result.command = $resolved
        $versionProbe = Invoke-DependencyCommand `
            -Command $resolved `
            -Arguments @($candidate.arguments)
        $result.exit_code = $versionProbe.exit_code
        if ($versionProbe.exit_code -ne 0) {
            $result.status = 'BROKEN'
            $result.details = $versionProbe.output
            return [pscustomobject]$result
        }

        $version = $null
        if ($null -ne $Dependency.probe.version_pattern) {
            $versionMatch = [regex]::Match(
                $versionProbe.output,
                [string]$Dependency.probe.version_pattern
            )
            if (-not $versionMatch.Success) {
                $result.status = 'BROKEN'
                $result.details = 'Version probe output did not match the allowlisted pattern.'
                return [pscustomobject]$result
            }
            $version = ConvertTo-DependencyVersion -Value $versionMatch.Groups['version'].Value
            if ($null -eq $version) {
                $result.status = 'BROKEN'
                $result.details = 'Version probe output did not contain a parseable version.'
                return [pscustomobject]$result
            }
            $result.version = $version.ToString()

            try {
                $compatible = Test-DependencyVersion `
                    -Version $version `
                    -Constraint ([string]$Dependency.version_constraint)
            }
            catch {
                $result.status = 'BROKEN'
                $result.details = $_.Exception.Message
                return [pscustomobject]$result
            }
            if (-not $compatible) {
                $result.status = 'INCOMPATIBLE'
                $result.details = "Detected version does not satisfy $($Dependency.version_constraint)."
                return [pscustomobject]$result
            }
        }

        if ($null -ne $Dependency.probe.smoke_arguments) {
            $smokeArguments = @($Dependency.probe.smoke_arguments)
            if (
                [string]$candidate.command -eq 'py' -and
                @($candidate.arguments).Count -gt 0 -and
                [string]$candidate.arguments[0] -match '^-\d'
            ) {
                $smokeArguments = @([string]$candidate.arguments[0]) + $smokeArguments
            }

            $smokeProbe = Invoke-DependencyCommand `
                -Command $resolved `
                -Arguments $smokeArguments
            $result.exit_code = $smokeProbe.exit_code
            if ($smokeProbe.exit_code -ne 0) {
                $result.status = 'BROKEN'
                $result.details = $smokeProbe.output
                return [pscustomobject]$result
            }
        }

        $result.status = 'COMPATIBLE'
        $result.details = 'Version and smoke probes passed.'
        return [pscustomobject]$result
    }

    $result.details = 'No allowlisted command candidate was found.'
    return [pscustomobject]$result
}

Export-ModuleMember -Function `
    ConvertTo-DependencyVersion, `
    Test-DependencyVersion, `
    Resolve-DependencyCommand, `
    Invoke-DependencyProbe
