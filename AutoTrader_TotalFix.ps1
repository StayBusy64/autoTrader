# =====================================================================
# AutoTrader TOTAL FIX & VALIDATION (Final)
# Author: StayBusy64 | Updated: 2025-11-02
# =====================================================================
# Performs full Render + webhook fix in one run
# =====================================================================

$baseUrl       = "https://autotrader-lao5.onrender.com"
$serviceId     = "srv-d43nhugdl3ps73a472qg"
$renderApiKey  = "rnd_9CACqjF0HJyiIqyi91Fo3MFlSdfS"
$webhookSecret = "qwertyuiopoiuytrewq"
$ErrorActionPreference = "Stop"

Write-Host "`n🚀 Starting AutoTrader TOTAL FIX" -ForegroundColor Cyan
Write-Host "🔗 Target: $baseUrl/webhook" -ForegroundColor Gray

# Ensure connectivity
$headers = @{ "Authorization" = "Bearer $renderApiKey" }

try {
    Write-Host "`n🔍 Verifying Render service..." -ForegroundColor Yellow
    $service = Invoke-RestMethod -Uri "https://api.render.com/v1/services/$serviceId" -Headers $headers
    Write-Host "✅ Service found → $($service.name)" -ForegroundColor Green
}
catch {
    Write-Host "❌ Could not reach Render API: $($_.Exception.Message)" -ForegroundColor Red
    Read-Host "Press Enter to close"
    exit
}

# Attempt to sync WEBHOOK_SECRET
try {
    Write-Host "`n🔑 Updating WEBHOOK_SECRET..." -ForegroundColor Yellow
    $body = @{ key = "WEBHOOK_SECRET"; value = $webhookSecret } | ConvertTo-Json
    Invoke-RestMethod -Uri "https://api.render.com/v1/services/$serviceId/env-vars" -Headers $headers -Method Post -Body $body -ContentType "application/json" | Out-Null
    Write-Host "✅ Secret updated successfully in Render environment" -ForegroundColor Green
}
catch {
    Write-Host "⚠️ Could not update secret via Render API (likely free plan restriction)" -ForegroundColor Yellow
    Write-Host "👉 Ensure manually in Render Dashboard → Environment → WEBHOOK_SECRET = $webhookSecret" -ForegroundColor Gray
}

# Trigger redeploy
try {
    Write-Host "`n🌀 Triggering redeploy..." -ForegroundColor Yellow
    $deploy = Invoke-RestMethod -Uri "https://api.render.com/v1/services/$serviceId/deploys" -Headers $headers -Method Post
    Write-Host "🚀 Redeploy started: $($deploy.id)" -ForegroundColor Green
}
catch {
    Write-Host "⚠️ Redeploy trigger may be restricted — continuing check loop..." -ForegroundColor Yellow
}

# Wait for service to go live
Write-Host "`n⏳ Waiting for service to reach 'live'..." -ForegroundColor Yellow
for ($i=0; $i -lt 180; $i+=10) {
    try {
        $status = (Invoke-RestMethod -Uri "https://api.render.com/v1/services/$serviceId" -Headers $headers).serviceDetails.deployment.status
        Write-Host "   → $status"
        if ($status -eq "live" -or $status -eq "succeeded") { Write-Host "✅ Service is live!" -ForegroundColor Green; break }
    } catch {}
    Start-Sleep -Seconds 10
}

# Root check
try {
    $root = Invoke-WebRequest -Uri $baseUrl -UseBasicParsing -TimeoutSec 8
    Write-Host "`n🌐 Root OK → $($root.StatusCode) $($root.StatusDescription)" -ForegroundColor Green
}
catch {
    Write-Host "❌ Root check failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test webhook
Write-Host "`n⚙️ Sending signed webhook payload..." -ForegroundColor Yellow
$env:WEBHOOK_SECRET = $webhookSecret
$testTrade = @{
    symbol    = "BTCUSD"
    side      = "buy"
    quantity  = 1
    price     = 35000
    timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
}
$json = $testTrade | ConvertTo-Json -Compress
$headersReq = @{ "X-Webhook-Secret" = $webhookSecret }

try {
    $resp = Invoke-WebRequest -Uri "$baseUrl/webhook" -Method POST -Headers $headersReq -Body $json -ContentType "application/json" -TimeoutSec 10
    if ($resp.StatusCode -eq 200) {
        Write-Host "`n✅ Authorized Webhook Success → $($resp.StatusCode) $($resp.StatusDescription)" -ForegroundColor Green
        Write-Host "Response: $($resp.Content)" -ForegroundColor Gray
    } else {
        Write-Host "⚠️ Unexpected response → $($resp.StatusCode): $($resp.StatusDescription)" -ForegroundColor Yellow
        Write-Host "Response: $($resp.Content)" -ForegroundColor Gray
    }
}
catch {
    $msg = $_.Exception.Message
    if ($msg -match "401") {
        Write-Host "❌ 401 Unauthorized — Secret mismatch!" -ForegroundColor Red
        Write-Host "🧩 Verify both backend and Render secret values match '$webhookSecret'" -ForegroundColor Yellow
    } elseif ($msg -match "422") {
        Write-Host "⚠️ 422 Validation Error — Check JSON body format." -ForegroundColor Yellow
    } else {
        Write-Host "⚠️ Error: $msg" -ForegroundColor Yellow
    }
}

Write-Host "`n✅ TOTAL FIX complete." -ForegroundColor Green
Write-Host "🔐 Secret: $webhookSecret" -ForegroundColor Gray
Write-Host "🌐 Endpoint: $baseUrl/webhook" -ForegroundColor Gray
Read-Host "`nPress Enter to close PowerShell"
