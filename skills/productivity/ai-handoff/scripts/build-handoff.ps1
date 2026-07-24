[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Objective,

    [Parameter(Mandatory = $true)]
    [string]$Target,

    [Parameter(Mandatory = $true)]
    [string[]]$Deliverable,

    [ValidateSet("agent", "human")]
    [string]$Audience = "agent",

    [ValidateSet("agent", "human")]
    [string]$FinalAudience,

    [string[]]$ContextFile = @(),

    [string[]]$Constraint = @(),

    [switch]$AllowExtendedBudget,

    [string]$Output
)

$ErrorActionPreference = "Stop"
$DefaultBudget = 6000
$HardCeiling = 10000

function Assert-Ascii {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Value
    )

    foreach ($character in $Value.ToCharArray()) {
        if ([int]$character -gt 127) {
            throw "Terminal transport payload must contain ASCII characters only."
        }
    }
}

$lines = New-Object System.Collections.Generic.List[string]
$lines.Add("OBJECTIVE: $Objective")
$lines.Add("TARGET: $Target")
$lines.Add("AUDIENCE: $Audience")

if ($FinalAudience) {
    $lines.Add("FINAL_AUDIENCE: $FinalAudience")
}

if ($ContextFile.Count -gt 0) {
    $lines.Add("AUTHORITATIVE_CONTEXT:")
    foreach ($path in $ContextFile) {
        $lines.Add("- $path")
    }
}

$lines.Add("CONSTRAINTS:")
if ($Constraint.Count -eq 0) {
    $lines.Add("- Do not expand authority beyond the objective.")
} else {
    foreach ($item in $Constraint) {
        $lines.Add("- $item")
    }
}

$lines.Add("DELIVERABLES:")
foreach ($item in $Deliverable) {
    $lines.Add("- $item")
}

$lines.Add("VERIFICATION:")
$lines.Add("- Treat destination files and runtime state as authoritative.")
$lines.Add("- Distinguish observed facts from assumptions.")
$lines.Add("- Report blockers instead of inventing missing information.")

if ($Audience -eq "human" -or $FinalAudience -eq "human") {
    $lines.Add("Answer in Traditional Chinese (zh-TW).")
}

$payload = [string]::Join("`n", $lines)

try {
    Assert-Ascii -Value $payload
} catch {
    [Console]::Error.WriteLine($_.Exception.Message)
    exit 2
}

if ($payload.Length -gt $HardCeiling) {
    [Console]::Error.WriteLine(
        "Payload length {0:N0} exceeds the 10,000 character hard ceiling." -f $payload.Length
    )
    exit 3
}

if ($payload.Length -gt $DefaultBudget -and -not $AllowExtendedBudget) {
    [Console]::Error.WriteLine(
        "Payload length {0:N0} exceeds the 6,000 character default budget. Reduce it, or use -AllowExtendedBudget only when every remaining field is required." -f $payload.Length
    )
    exit 4
}

if ($payload.Length -gt $DefaultBudget) {
    [Console]::Error.WriteLine(
        "WARNING: Extended payload length is {0:N0} characters." -f $payload.Length
    )
}

if ($Output) {
    $resolvedOutput = [System.IO.Path]::GetFullPath($Output)
    $parent = [System.IO.Path]::GetDirectoryName($resolvedOutput)
    if ($parent -and -not [System.IO.Directory]::Exists($parent)) {
        [System.IO.Directory]::CreateDirectory($parent) | Out-Null
    }

    $ascii = New-Object System.Text.ASCIIEncoding($false)
    [System.IO.File]::WriteAllText($resolvedOutput, $payload, $ascii)
    Write-Output $resolvedOutput
} else {
    Write-Output $payload
}
