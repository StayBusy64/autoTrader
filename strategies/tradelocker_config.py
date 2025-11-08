"""
TradeLocker Configuration & Webhook Integration
Configure this file to connect your strategy signals to TradeLocker
"""

import os
import requests
import json
from typing import Dict, Optional


class TradeLockerConfig:
    """
    TradeLocker API Configuration

    Set these environment variables:
    - TRADELOCKER_API_KEY
    - TRADELOCKER_API_SECRET
    - TRADELOCKER_ACCOUNT_ID
    - WEBHOOK_URL (your AutoTrader webhook endpoint)
    """

    def __init__(self):
        self.api_key = os.getenv('TRADELOCKER_API_KEY', '')
        self.api_secret = os.getenv('TRADELOCKER_API_SECRET', '')
        self.account_id = os.getenv('TRADELOCKER_ACCOUNT_ID', '')
        self.webhook_url = os.getenv('WEBHOOK_URL', 'https://your-server.com/webhook')

        # Trading parameters
        self.symbol = 'LTCUSD'
        self.default_size = 0.1  # Default position size in lots
        self.max_slippage = 0.0005  # 0.05% max slippage

    def send_signal(
        self,
        action: str,
        price: float,
        stop_loss: float,
        take_profit: float,
        size: float = None,
        metadata: Dict = None
    ) -> bool:
        """
        Send trading signal to webhook

        Args:
            action: 'BUY' or 'SELL'
            price: Entry price
            stop_loss: Stop loss price
            take_profit: Take profit price
            size: Position size (uses default if None)
            metadata: Additional info (RSI, ADX, etc.)

        Returns:
            bool: True if signal sent successfully
        """

        if not self.webhook_url:
            print("ERROR: WEBHOOK_URL not configured")
            return False

        payload = {
            'symbol': self.symbol,
            'action': action.upper(),
            'price': price,
            'size': size or self.default_size,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'timestamp': None,  # Will be set by server
            'metadata': metadata or {}
        }

        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=5
            )

            if response.status_code == 200:
                print(f"✓ Signal sent: {action} {self.symbol} @ {price}")
                return True
            else:
                print(f"✗ Signal failed: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            print(f"✗ Error sending signal: {e}")
            return False


class LiveTradingBot:
    """
    Live trading bot that connects strategy to TradeLocker

    Usage:
        bot = LiveTradingBot()
        bot.run()
    """

    def __init__(self):
        self.config = TradeLockerConfig()
        self.position = None  # Current position
        self.last_signal_time = None

    def on_buy_signal(
        self,
        price: float,
        stop_loss: float,
        take_profit: float,
        size: float,
        indicators: Dict
    ):
        """Called when strategy generates BUY signal"""

        print(f"\n{'='*60}")
        print(f"🟢 LONG SIGNAL DETECTED")
        print(f"{'='*60}")
        print(f"Entry Price: ${price:.5f}")
        print(f"Stop Loss:   ${stop_loss:.5f} ({((stop_loss-price)/price*100):.2f}%)")
        print(f"Take Profit: ${take_profit:.5f} ({((take_profit-price)/price*100):.2f}%)")
        print(f"Position Size: {size}")
        print(f"RSI: {indicators.get('rsi', 'N/A')}")
        print(f"ADX: {indicators.get('adx', 'N/A')}")
        print(f"MACD: {indicators.get('macd', 'N/A')}")
        print(f"{'='*60}\n")

        # Send to TradeLocker
        success = self.config.send_signal(
            action='BUY',
            price=price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            size=size,
            metadata=indicators
        )

        if success:
            self.position = {
                'type': 'LONG',
                'entry': price,
                'sl': stop_loss,
                'tp': take_profit,
                'size': size
            }

    def on_sell_signal(
        self,
        price: float,
        stop_loss: float,
        take_profit: float,
        size: float,
        indicators: Dict
    ):
        """Called when strategy generates SELL signal"""

        print(f"\n{'='*60}")
        print(f"🔴 SHORT SIGNAL DETECTED")
        print(f"{'='*60}")
        print(f"Entry Price: ${price:.5f}")
        print(f"Stop Loss:   ${stop_loss:.5f} ({((price-stop_loss)/price*100):.2f}%)")
        print(f"Take Profit: ${take_profit:.5f} ({((price-take_profit)/price*100):.2f}%)")
        print(f"Position Size: {size}")
        print(f"RSI: {indicators.get('rsi', 'N/A')}")
        print(f"ADX: {indicators.get('adx', 'N/A')}")
        print(f"MACD: {indicators.get('macd', 'N/A')}")
        print(f"{'='*60}\n")

        # Send to TradeLocker
        success = self.config.send_signal(
            action='SELL',
            price=price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            size=size,
            metadata=indicators
        )

        if success:
            self.position = {
                'type': 'SHORT',
                'entry': price,
                'sl': stop_loss,
                'tp': take_profit,
                'size': size
            }

    def on_exit_signal(self, price: float, reason: str):
        """Called when position is closed"""

        if not self.position:
            return

        pnl = 0
        if self.position['type'] == 'LONG':
            pnl = (price - self.position['entry']) * self.position['size']
        else:
            pnl = (self.position['entry'] - price) * self.position['size']

        pnl_pct = (pnl / (self.position['entry'] * self.position['size'])) * 100

        print(f"\n{'='*60}")
        print(f"⚫ POSITION CLOSED - {reason}")
        print(f"{'='*60}")
        print(f"Exit Price: ${price:.5f}")
        print(f"PNL: ${pnl:.2f} ({pnl_pct:.2f}%)")
        print(f"{'='*60}\n")

        self.position = None


# Example: Modify strategy to send signals
class LTCUSD_ScalperBot_Live:
    """
    Extended strategy class with live trading hooks

    Add to your strategy:

    from tradelocker_config import LiveTradingBot

    def __init__(self):
        # ... existing code ...
        self.live_bot = LiveTradingBot()

    def notify_order(self, order):
        if order.status == order.Completed:
            if order.isbuy():
                indicators = {
                    'rsi': self.rsi[0],
                    'adx': self.adx[0],
                    'macd': self.macd.macd[0]
                }
                self.live_bot.on_buy_signal(
                    price=order.executed.price,
                    stop_loss=self.stop_loss,
                    take_profit=self.take_profit,
                    size=order.executed.size,
                    indicators=indicators
                )
    """
    pass


# Environment setup helper
def setup_environment():
    """
    Interactive setup for TradeLocker configuration
    Run this once to configure your environment
    """

    print("="*60)
    print("TradeLocker Configuration Setup")
    print("="*60)
    print()

    api_key = input("Enter TradeLocker API Key: ").strip()
    api_secret = input("Enter TradeLocker API Secret: ").strip()
    account_id = input("Enter TradeLocker Account ID: ").strip()
    webhook_url = input("Enter Webhook URL (e.g., https://your-server.com/webhook): ").strip()

    # Create .env file
    env_content = f"""# TradeLocker Configuration
TRADELOCKER_API_KEY={api_key}
TRADELOCKER_API_SECRET={api_secret}
TRADELOCKER_ACCOUNT_ID={account_id}
WEBHOOK_URL={webhook_url}

# Trading Parameters
SYMBOL=LTCUSD
DEFAULT_SIZE=0.1
MAX_SLIPPAGE=0.0005
"""

    with open('.env', 'w') as f:
        f.write(env_content)

    print()
    print("✓ Configuration saved to .env file")
    print()
    print("Next steps:")
    print("1. Review .env file")
    print("2. Install: pip install python-dotenv requests")
    print("3. Load in your script: from dotenv import load_dotenv; load_dotenv()")
    print()


# Quick test
def test_webhook():
    """Test webhook connection"""

    config = TradeLockerConfig()

    print("Testing webhook connection...")
    print(f"Webhook URL: {config.webhook_url}")

    # Send test signal
    success = config.send_signal(
        action='BUY',
        price=65.123,
        stop_loss=65.000,
        take_profit=65.300,
        size=0.1,
        metadata={'test': True}
    )

    if success:
        print("✓ Webhook test successful!")
    else:
        print("✗ Webhook test failed. Check your configuration.")


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == 'setup':
            setup_environment()
        elif sys.argv[1] == 'test':
            test_webhook()
    else:
        print("Usage:")
        print("  python tradelocker_config.py setup  # Configure environment")
        print("  python tradelocker_config.py test   # Test webhook connection")
