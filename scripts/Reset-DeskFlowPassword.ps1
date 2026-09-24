<#
.SYNOPSIS
  Reset an employee's password through the DeskFlow automation API.

.EXAMPLE
  .\Reset-DeskFlowPassword.ps1 -EmployeeId EMP001
  .\Reset-DeskFlowPassword.ps1 -EmployeeId EMP002 -Credential (Get-Credential)
#>
param(
    [string]$BaseUrl = "http://localhost:8000",
    [Parameter(Mandatory = $true)]
    [string]$EmployeeId,
    [pscredential]$Credential
)

. "$PSScriptRoot\DeskFlowClient.ps1"

$token = Get-DeskFlowToken -BaseUrl $BaseUrl -EmployeeId $EmployeeId -Credential $Credential
$result = Invoke-DeskFlowTool -BaseUrl $BaseUrl -Token $token -Tool reset_password `
    -Arguments @{ employee_id = $EmployeeId }

if ($result.result.status -eq "success") {
    Write-Host "Password reset OK for $($result.result.name) ($EmployeeId)" -ForegroundColor Green
    Write-Host "  Temporary password : $($result.result.temporary_password)" -ForegroundColor Yellow
    Write-Host "  Note               : $($result.result.note)"
}
else {
    Write-Warning "Reset failed: $($result.result | ConvertTo-Json -Compress)"
    exit 1
}
