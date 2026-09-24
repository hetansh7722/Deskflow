<#
.SYNOPSIS
  Bulk software-entitlement report: checks every active employee against one
  application and exports the result to CSV.

.EXAMPLE
  .\Get-DeskFlowEntitlementReport.ps1 -SoftwareName "Adobe Creative Suite" -OutFile adobe.csv
#>
param(
    [string]$BaseUrl = "http://localhost:8000",
    [Parameter(Mandatory = $true)]
    [string]$SoftwareName,
    [string]$OutFile = "entitlement-report.csv",
    [pscredential]$Credential
)

. "$PSScriptRoot\DeskFlowClient.ps1"

$token = Get-DeskFlowToken -BaseUrl $BaseUrl -EmployeeId EMP001 -Credential $Credential
$employees = (Get-DeskFlowJson -BaseUrl $BaseUrl -Token $token -Path /employees).employees

$report = foreach ($emp in $employees) {
    $r = Invoke-DeskFlowTool -BaseUrl $BaseUrl -Token $token -Tool check_software_entitlement `
        -Arguments @{ employee_id = $emp.employee_id; software_name = $SoftwareName }
    $x = $r.result
    [pscustomobject]@{
        EmployeeId   = $emp.employee_id
        Name         = $emp.name
        Department   = $emp.department
        Software     = $x.software
        Entitled     = $x.entitled
        ApprovalReq  = $x.approval_required
        ApproverRole = $x.approver_role
        LicensesLeft = $x.available_licenses
        Error        = $x.error
    }
}

$report | Export-Csv -Path $OutFile -NoTypeInformation -Encoding UTF8

$entitled = @($report | Where-Object Entitled).Count
Write-Host "Checked $($report.Count) employees against '$SoftwareName'" -ForegroundColor Green
Write-Host "  Entitled    : $entitled"
Write-Host "  Not entitled: $($report.Count - $entitled)"
Write-Host "  CSV written : $((Resolve-Path $OutFile).Path)"
