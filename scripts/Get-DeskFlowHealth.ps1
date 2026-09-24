<#
.SYNOPSIS
  Operational health check for the DeskFlow service.
  Reports service health, monitor status, and an SLA/stale summary.

.EXAMPLE
  .\Get-DeskFlowHealth.ps1
  .\Get-DeskFlowHealth.ps1 -Credential (Get-Credential)   # also show stats
#>
param(
    [string]$BaseUrl = "http://localhost:8000",
    [pscredential]$Credential
)

. "$PSScriptRoot\DeskFlowClient.ps1"

try {
    $health = Invoke-RestMethod -Uri "$BaseUrl/health" -Method Get
    Write-Host "Service    : UP" -ForegroundColor Green
    Write-Host "Model      : $($health.model)"
}
catch {
    Write-Host "Service    : DOWN ($BaseUrl)" -ForegroundColor Red
    exit 1
}

if (-not $Credential) {
    Write-Host "`n(Re-run with -Credential to include ticket/SLA statistics.)" -ForegroundColor DarkGray
    exit 0
}

$token = Get-DeskFlowToken -BaseUrl $BaseUrl -EmployeeId EMP001 -Credential $Credential
$stats = Get-DeskFlowJson -BaseUrl $BaseUrl -Token $token -Path /stats

Write-Host "`nTickets    : $($stats.totals.tickets) total / $($stats.totals.open) open"
Write-Host "SLA        : $($stats.totals.sla_breached) breached, $($stats.totals.stale) stale" `
    -ForegroundColor ($(if ($stats.totals.sla_breached -gt 0) { "Yellow" } else { "Green" }))
Write-Host "Employees  : $($stats.totals.employees)"
Write-Host "Tool calls : $(($stats.tool_calls.PSObject.Properties.Value | Measure-Object -Sum).Sum)"

if ($stats.totals.sla_breached -gt 0) {
    Write-Host "`nBreached tickets:" -ForegroundColor Yellow
    $stats.sla_breaches | ForEach-Object {
        Write-Host ("  {0}  [{1}]  {2}" -f $_.ticket_id, $_.priority, $_.title)
    }
}
