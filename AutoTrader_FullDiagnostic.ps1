# =====================================================================
# AutoTrader Full Diagnostic + Render Secret Sync (v2)
# Author: StayBusy64  |  Updated: 2025-11-02
# =====================================================================

$baseUrl       = "https://autotrader-lao5.onrender.com"
$serviceId     = "srv-d43nhugdl3ps73a472qg"
$renderApiKey  = "rnd_9CACqjF0HJyiIqyi91Fo3MFlSdfS"  # Replace with your actual Render API key
$ErrorActionPreference = "Continue"

Write-Host "`n🚀 AutoTrader Render + Webhook Diagnostic" -ForegroundColor Cyan
Write-Host "🔗 Endpoint: $baseUrl/webhook" -ForegroundColor Gray

try {
    Write-Host "`n📡 Fetching secret from Render..." -ForegroundColor Yellow
    $headers = @{ "Authorization" = "Bearer $renderApiKey" }
    $response = Invoke-RestMethod -Uri "https://api.render.com/v1/services/$serviceId/env-vars" -Headers $headers -Method Get -TimeoutSec 10
    $webhookSecret = ($response | Where-Object { $_.key -eq "WEBHOOK_SECRET" }).value
    if (-not $webhookSecret) { throw "WEBHOOK_SECRET not found in Render." }
    $env:WEBHOOK_SECRET = $webhookSecret
    Write-Host "✅ Retrieved and set local WEBHOOK_SECRET → $webhookSecret" -ForegroundColor Green
}
catch {
    Write-Host "❌ Failed to fetch secret: $($_.Exception.Message)" -ForegroundColor Red
}

try {
    Write-Host "`n🌐 Checking root endpoint..." -ForegroundColor Yellow
    $root = Invoke-WebRequest -Uri $baseUrl -UseBasicParsing -TimeoutSec 8
    Write-Host "✅ Root OK → $($root.StatusCode) $($root.StatusDescription)" -ForegroundColor Green
}
catch {
    Write-Host "❌ Root check failed: $($_.Exception.Message)" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit
}

Write-Host "`n⚙️  Sending authorized test payload..." -ForegroundColor Yellow
$testTrade = @{
    symbol    = "BTCUSD"
    side      = "buy"
    quantity  = 1
    price     = 35000
    timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
}
$json = $testTrade | ConvertTo-Json -Compress
$headersReq = @{ "X-Webhook-Secret" = $env:WEBHOOK_SECRET }

try {
    $resp = Invoke-WebRequest -Uri "$baseUrl/webhook" -Method POST -Headers $headersReq -Body $json -ContentType "application/json" -TimeoutSec 10
    if ($resp.StatusCode -eq 200) {
        Write-Host "`n✅ Authorized Webhook Success → $($resp.StatusCode) $($resp.StatusDescription)" -ForegroundColor Green
        Write-Host "Response: $($resp.Content)" -ForegroundColor Gray
    } else {
        Write-Host "⚠️ Unexpected response → $($resp.StatusCode): $($resp.StatusDescription)" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
}

Read-Host "`n✅ Diagnostic complete. Press Enter to close"
