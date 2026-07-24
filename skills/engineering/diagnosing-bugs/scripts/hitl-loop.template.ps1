[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$captured = [ordered]@{}

function Invoke-HumanStep {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Instruction
    )

    Write-Host ""
    Write-Host ">>> $Instruction"
    Read-Host "    Press Enter when done" | Out-Null
}

function Read-CapturedValue {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,

        [Parameter(Mandatory = $true)]
        [string]$Question
    )

    Write-Host ""
    Write-Host ">>> $Question"
    $captured[$Name] = Read-Host "    >"
}

# Edit the steps below for the current reproduction.
Invoke-HumanStep -Instruction "Open the app at http://localhost:3000 and sign in."
Read-CapturedValue -Name "ERRORED" -Question "Click Export. Did it throw an error? (y/n)"
Read-CapturedValue -Name "ERROR_MSG" -Question "Paste the error message (or 'none'):"

Write-Output ""
Write-Output "--- Captured ---"
foreach ($entry in $captured.GetEnumerator()) {
    Write-Output ("{0}={1}" -f $entry.Key, $entry.Value)
}
