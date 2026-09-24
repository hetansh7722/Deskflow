<#
.SYNOPSIS
  Export every ticket (with SLA/stale flags) to CSV for offline review.

.EXAMPLE
  .\Export-DeskFlowTickets.ps1 -OutFile tickets.csv
#>
param(
    [string]$BaseUrl = "http://localhost:8000",
    [string]$OutFile = "tickets.csv",
    [string]$EmployeeId = "EMP001",
    [pscredential]$Credential
)

. "$PSScriptRoot\DeskFlowClient.ps1"

$token = Get-DeskFlowToken -BaseUrl $BaseUrl -EmployeeId $EmployeeId -Credential $Credential
$data = Get-DeskFlowJson -BaseUrl $BaseUrl -Token $token -Path /tickets

$rows = foreach ($t in $data.tickets) {
    [pscustomobject]@{
        TicketId     = $t.ticket_id
        EmployeeId   = $t.employee_id
        Title        = $t.title
        Priority     = $t.priority
        Status       = $t.status
        Category     = $t.category
        AssignedTo   = $t.assigned_to
        CreatedAt    = $t.created_at
        UpdatedAt    = $t.updated_at
        SlaBreached  = [bool]$t.sla_breached
        Stale        = [bool]$t.stale
        Resolution   = $t.resolution
    }
}

$rows | Sort-Object TicketId | Export-Csv -Path $OutFile -NoTypeInformation -Encoding UTF8

Write-Host "Exported $($rows.Count) tickets to $((Resolve-Path $OutFile).Path)" -ForegroundColor Green
$breaches = @($rows | Where-Object SlaBreached).Count
if ($breaches -gt 0) {
    Write-Host "  ⚠ $breaches ticket(s) past SLA — see the admin dashboard" -ForegroundColor Yellow
}
