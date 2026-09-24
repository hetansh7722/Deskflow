<#
.SYNOPSIS
  Shared REST client helpers for DeskFlow admin scripts.

.DESCRIPTION
  Dot-source this file from a script:
      . "$PSScriptRoot\DeskFlowClient.ps1"
  All calls authenticate with an HMAC session token obtained from POST /login.
#>

function ConvertFrom-SecureStringPlain {
    param([Parameter(Mandatory)][securestring]$SecureString)
    $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($SecureString)
    try {
        [Runtime.InteropServices.Marshal]::PtrToStringAuto($bstr)
    }
    finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
    }
}

function Get-DeskFlowToken {
    <#.Gets a session token from POST /login.#>
    param(
        [string]$BaseUrl = "http://localhost:8000",
        [Parameter(Mandatory)][string]$EmployeeId,
        [pscredential]$Credential
    )

    if ($Credential) {
        $userId = $Credential.UserName
        $password = ConvertFrom-SecureStringPlain $Credential.Password
    }
    else {
        $userId = $EmployeeId
        $password = Read-Host -Prompt "Password for $EmployeeId" -AsSecureString |
            ConvertFrom-SecureStringPlain
    }

    $body = @{ employee_id = $userId; password = $password } | ConvertTo-Json
    try {
        $resp = Invoke-RestMethod -Uri "$BaseUrl/login" -Method Post `
            -ContentType "application/json" -Body $body
    }
    catch {
        throw "Sign-in failed for '$userId' at $BaseUrl — check the ID, password, and that the server is running."
    }
    return $resp.token
}

function Invoke-DeskFlowTool {
    <#.Calls POST /tools/{name} with the given arguments hashtable.#>
    param(
        [Parameter(Mandatory)][string]$BaseUrl,
        [Parameter(Mandatory)][string]$Token,
        [Parameter(Mandatory)][string]$Tool,
        [Parameter(Mandatory)][hashtable]$Arguments
    )
    $body = @{ arguments = $Arguments } | ConvertTo-Json -Depth 6
    Invoke-RestMethod -Uri "$BaseUrl/tools/$Tool" -Method Post `
        -ContentType "application/json" `
        -Headers @{ Authorization = "Bearer $Token" } `
        -Body $body
}

function Get-DeskFlowJson {
    <#.Authenticated GET helper.#>
    param(
        [Parameter(Mandatory)][string]$BaseUrl,
        [Parameter(Mandatory)][string]$Token,
        [Parameter(Mandatory)][string]$Path
    )
    Invoke-RestMethod -Uri "$BaseUrl$Path" -Method Get `
        -Headers @{ Authorization = "Bearer $Token" }
}
