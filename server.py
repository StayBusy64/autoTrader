from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from datetime import datetime
import hmac
import hashlib
import logging
import os

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("trades.log"), logging.StreamHandler()]
)

app = FastAPI(title="AutoTrader Webhook")

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "default_secret_change_me")
DAILY_LOSS_CAP = -250.0
ALLOWED_SYMBOLS = ["BTCUSDT", "ETHUSDT", "LTCUSDT"]
session_pnl = 0.0

class TradeWebhook(BaseModel):
    symbol: str
    side: str
    price: float
    quantity: float
    strategy: str = "AutoTrader"

@app.post("/webhook")
async def webhook(request: Request, trade: TradeWebhook):
    signature = request.headers.get("X-Webhook-Signature")
    body = await request.body()
    expected_sig = hmac.new(WEBHOOK_SECRET.encode(), body, hashlib.sha256).hexdigest()

    if signature != expected_sig:
        raise HTTPException(status_code=401, detail="Invalid signature")

    if trade.symbol not in ALLOWED_SYMBOLS:
        raise HTTPException(status_code=400, detail="Symbol not allowed")

    global session_pnl
    pnl = (trade.quantity * trade.price * (1 if trade.side.lower() == "buy" else -1))
    session_pnl += pnl
    logging.info(f"{trade.strategy}: {trade.side.upper()} {trade.symbol} @ {trade.price} qty {trade.quantity}")

    return {"status": "ok", "pnl": session_pnl, "timestamp": datetime.now().isoformat()}

@app.get("/healthz")
async def healthz():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.get("/status")
async def status():
    return {
        "session_pnl": session_pnl,
        "daily_loss_cap": DAILY_LOSS_CAP,
        "allowed_symbols": ALLOWED_SYMBOLS,
        "webhook_secret_configured": WEBHOOK_SECRET != "default_secret_change_me"
    }

@app.get("/")
def home():
    return {"status": "ok", "message": "AutoTrader backend is live ??"}
