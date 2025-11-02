# =====================================================================
# AutoTrader TOTAL FIX & VALIDATION
# Author: StayBusy64  |  Updated: 2025-11-02
# =====================================================================
# This script will:
#  1. Sync your WEBHOOK_SECRET to Render automatically
#  2. Trigger redeploy and wait until live
#  3. Validate the webhook endpoint end-to-end
# =====================================================================

# -------- CONFIG --------
$baseUrl       = "https://autotrader-lao5.onrender.com"
$serviceId     = "srv-d43nhugdl3ps73a472qg"
$renderApiKey  = "rnd_9CACqjF0HJyiIqyi91Fo3MFlSdfS"   # <- Replace if rotated
$webhookSecret = "qwertyuiopoiuytrewq"                # <- The expected secret
$ErrorActionPreference = "Stop"
# ------------------------

Write-Host "`n🚀 Starting AutoTrader TOTAL FIX" -ForegroundColor Cyan
Write-Host "🔗 Target: $baseUrl/webhook" -ForegroundColor Gray

# STEP 1 ─ Ensure Render connection
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

# STEP 2 ─ Update WEBHOOK_SECRET on Render
try {
    Write-Host "`n🔑 Syncing WEBHOOK_SECRET to Render..." -ForegroundColor Yellow
    $body = @{ key = "WEBHOOK_SECRET"; value = $webhookSecret } | ConvertTo-Json
    Invoke-RestMethod -Uri "https://api.render.com/v1/services/$serviceId/env-vars" -Headers $headers -Method Post -Body $body -ContentType "application/json" | Out-Null
    Write-Host "✅ WEBHOOK_SECRET updated in Render environment" -ForegroundColor Green
}
catch {
    Write-Host "⚠️ Could not update secret via Render API (may be permission-locked for Free tier)" -ForegroundColor Yellow
    Write-Host "👉 If so, open Render → Environment tab → ensure 'WEBHOOK_SECRET' = $webhookSecret" -ForegroundColor Gray
}

# STEP 3 ─ Trigger redeploy
try {
    Write-Host "`n🌀 Triggering redeploy..." -ForegroundColor Yellow
    $deploy = Invoke-RestMethod -Uri "https://api.render.com/v1/services/$serviceId/deploys" -Headers $headers -Method Post
    $deployId = $deploy.id
    Write-Host "🚀 Redeploy started → ID: $deployId" -ForegroundColor Green
}
catch {
    Write-Host "⚠️ Redeploy trigger failed (maybe already building). Continuing check loop..." -ForegroundColor Yellow
}

# STEP 4 ─ Wait until live
Write-Host "`n⏳ Waiting for Render service to reach 'live' status..." -ForegroundColor Yellow
$maxWait = 180
for ($i=0; $i -lt $maxWait; $i+=10) {
    try {
        $status = (Invoke-RestMethod -Uri "https://api.render.com/v1/services/$serviceId" -Headers $headers).serviceDetails.deployment.status
        Write-Host "   → $status"
        if ($status -eq "live" -or $status -eq "succeeded") {
            Write-Host "✅ Service is live!" -ForegroundColor Green
            break
        }
    } catch { }
    Start-Sleep -Seconds 10
}
Write-Host "🛰 Proceeding to validation..." -ForegroundColor Yellow

# STEP 5 ─ Verify root endpoint
try {
    $root = Invoke-WebRequest -Uri $baseUrl -UseBasicParsing -TimeoutSec 8
    if ($root.StatusCode -eq 200) {
        Write-Host "✅ Root OK → 200 OK" -ForegroundColor Green
    } else {
        Write-Host "⚠️ Root returned $($root.StatusCode)" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "❌ Could not reach root endpoint: $($_.Exception.Message)" -ForegroundColor Red
}

# STEP 6 ─ Send signed webhook test
Write-Host "`n⚙️  Sending signed webhook payload..." -ForegroundColor Yellow
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

# STEP 7 ─ Done
Write-Host "`n✅ TOTAL FIX complete." -ForegroundColor Green
Write-Host "🔐 Secret: $webhookSecret" -ForegroundColor Gray
Write-Host "🌐 Endpoint: $baseUrl/webhook" -ForegroundColor Gray
Read-Host "`nPress Enter to close PowerShell"
