# Smoke test: the deployed EventEase must report UP with the database CONNECTED.
$url = "http://localhost:5000/health"
for ($i = 1; $i -le 12; $i++) {
    try {
        $r = Invoke-RestMethod -Uri $url -TimeoutSec 5
        if ($r.status -eq "UP" -and $r.database -eq "CONNECTED") {
            Write-Host "[+] Health probe status: $($r.status) (Database: $($r.database))"
            exit 0
        }
    } catch {
        Write-Host "Attempt $i/12: service not ready yet..."
    }
    Start-Sleep -Seconds 5
}
Write-Host "[-] Smoke test FAILED: $url did not report UP/CONNECTED"
exit 1
