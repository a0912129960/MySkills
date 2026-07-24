[CmdletBinding()]
param(
    [ValidateSet("Copy", "Junction")]
    [string]$Mode = "Copy",
    [string[]]$Destinations = @(
        (Join-Path $HOME ".agents\skills"),
        (Join-Path $HOME ".claude\skills")
    )
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$skillFiles = Get-ChildItem -LiteralPath (Join-Path $repoRoot "skills") -Filter "SKILL.md" -Recurse

foreach ($destination in $Destinations) {
    New-Item -ItemType Directory -Path $destination -Force | Out-Null

    foreach ($skillFile in $skillFiles) {
        $source = $skillFile.Directory.FullName
        $name = $skillFile.Directory.Name
        $target = Join-Path $destination $name

        if (Test-Path -LiteralPath $target) {
            $resolvedDestination = [IO.Path]::GetFullPath($destination)
            $resolvedTarget = [IO.Path]::GetFullPath($target)
            if (-not $resolvedTarget.StartsWith($resolvedDestination + [IO.Path]::DirectorySeparatorChar)) {
                throw "Refusing to replace target outside destination: $resolvedTarget"
            }
            $existing = Get-Item -LiteralPath $target -Force
            if (($existing.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
                [IO.Directory]::Delete($target)
            }
            else {
                Remove-Item -LiteralPath $target -Recurse -Force
            }
        }

        if ($Mode -eq "Junction") {
            New-Item -ItemType Junction -Path $target -Target $source | Out-Null
        }
        else {
            Copy-Item -LiteralPath $source -Destination $target -Recurse
        }

        Write-Output "$Mode $name -> $target"
    }
}
