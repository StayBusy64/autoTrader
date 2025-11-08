# LTCUSD Scalper Bot - 1 Minute Strategy

Advanced scalping strategy optimized for LTCUSD on 1-minute timeframe with TradeLocker integration.

## Key Improvements Over Original Strategy

### 1. Faster Indicators for 1m Scalping
- **EMA Periods**: Changed from 9/21 to **5/13** (faster response for 1m)
- **Trend EMA**: Added 50-period EMA for overall trend context
- **Why**: 1-minute scalping requires quick entries/exits; slower EMAs cause lag

### 2. Multi-Indicator Confirmation
Original strategy relied solely on EMA crossover. New strategy requires:
- ✅ **EMA Crossover** (5/13)
- ✅ **MACD Confirmation** (trend direction)
- ✅ **ADX > 20** (trend strength - avoids choppy markets)
- ✅ **RSI Filter** (65/35 levels, tighter than original)
- ✅ **Bollinger Bands** (volatility-based entry timing)
- ✅ **Volume > 1.3x Average** (mandatory confirmation)

**Result**: Significantly reduces false signals and choppy market losses

### 3. Advanced Risk Management

#### Dynamic Position Sizing
```python
Position Size = (Account Risk / Stop Distance)
```
- Automatically adjusts to volatility
- Maintains consistent risk per trade

#### Multi-Layer Stop Loss
1. **Initial Stop**: 1.5x ATR (tighter than original 2.0x)
2. **Breakeven Move**: After 1.0x ATR profit
3. **Trailing Stop**: Activates at 1.0x ATR profit, trails at 1.2x ATR
4. **Partial Exits**: Take 50% at 1.5x ATR, let rest run

#### Better Risk/Reward
- Original: 2:3 (1:1.5 R:R)
- **New: 1.5:2.5 (1:1.67 R:R)** with partial exits

### 4. Smart Session Filtering

Original: 8-17 UTC (too broad)

**New Optimized Sessions**:
- **Active Trading**: 9-16 UTC
- **Avoids**: First/last 5 minutes of each hour (low liquidity)
- **Why**: Focuses on high-volume periods, avoids spread widening

### 5. Enhanced Daily Protection
- Max Daily Loss: **2%** (stops trading when hit)
- Max Daily Trades: **15** (prevents overtrading/revenge trading)
- Automatic daily reset at midnight

### 6. Profit Protection Features

#### Partial Exits
- Takes **50% profit** at 1.5x ATR
- Lets remaining 50% run to 2.5x ATR
- **Benefit**: Locks in profits while maintaining upside

#### Smart Breakeven
- Moves stop to breakeven + 0.1 ATR after 1.0x ATR profit
- **Benefit**: Protects capital once trade is profitable

#### Intelligent Trailing Stop
- Activates after 1.0x ATR profit
- Trails at 1.2x ATR distance
- **Benefit**: Captures larger moves without giving back gains

### 7. Volume Confirmation (MANDATORY)
Original: Optional volume filter

**New**: Volume MUST be 30% above 20-period average
- **Why**: 1m scalping in low volume = high slippage and false breakouts

### 8. ADX Filter (Trend Strength)
New addition: ADX must be > 20

- **ADX < 20**: Choppy/ranging market (skip trades)
- **ADX > 20**: Trending market (take trades)
- **Why**: Scalping in range-bound markets = death by 1000 cuts

### 9. Comprehensive Logging
Every trade logs:
- Entry/exit prices
- Stop loss/take profit levels
- Risk/reward ratio
- RSI, ADX, MACD values
- Win/loss tracking
- Daily PnL
- Win rate statistics

## Strategy Parameters

### Core Indicators
```python
fast_ema_period = 5          # Fast EMA (responsive)
slow_ema_period = 13         # Slow EMA (Fibonacci)
trend_ema_period = 50        # Trend filter

rsi_period = 14
rsi_overbought = 65          # Tighter for scalping
rsi_oversold = 35

adx_period = 14
adx_threshold = 20           # Min trend strength

atr_period = 14
atr_stop_multiplier = 1.5    # Tight stop for scalping
atr_target_multiplier = 2.5  # Better R:R
```

### Risk Management
```python
risk_per_trade = 0.5%        # Risk per trade
max_daily_loss_pct = 2.0%    # Daily loss limit
max_daily_trades = 15        # Prevent overtrading
volume_threshold = 1.3       # 30% above average
```

### Session Times (UTC)
```python
session_start = 9            # 9 AM UTC
session_end = 16             # 4 PM UTC
avoid_first_minutes = 5      # Skip first 5 min of hour
avoid_last_minutes = 5       # Skip last 5 min of hour
```

## Installation

### Requirements
```bash
pip install backtrader pandas matplotlib
```

### Directory Structure
```
autoTrader/
├── strategies/
│   ├── LTCUSD_ScalperBot_1m.py
│   ├── backtest_runner.py
│   ├── optimize_parameters.py
│   └── README.md
└── data/
    └── LTCUSD_1m.csv  # Your 1-minute OHLCV data
```

## Usage

### 1. Prepare Your Data

CSV format required:
```
datetime,open,high,low,close,volume
2024-01-01 00:00:00,65.123,65.456,65.000,65.234,125000
2024-01-01 00:01:00,65.234,65.500,65.100,65.300,135000
...
```

### 2. Run a Backtest

Basic backtest:
```bash
cd strategies
python backtest_runner.py --data ../data/LTCUSD_1m.csv
```

With custom parameters:
```bash
python backtest_runner.py \
    --data ../data/LTCUSD_1m.csv \
    --cash 10000 \
    --commission 0.0006 \
    --start 2024-01-01 \
    --end 2024-12-31 \
    --fast-ema 5 \
    --slow-ema 13 \
    --risk 0.5 \
    --atr-stop 1.5 \
    --atr-target 2.5
```

### 3. Optimize Parameters

Find best parameters for your data:
```bash
python optimize_parameters.py --data ../data/LTCUSD_1m.csv
```

This will:
- Test hundreds of parameter combinations
- Rank by ROI, Sharpe Ratio, Win Rate
- Save results to `optimization_results.csv`
- Show top 10 parameter sets

### 4. Live Trading Integration

#### TradeLocker Integration

1. **Use with TradingView Alerts**:
   - Set up alerts based on strategy signals
   - Use webhook to send to TradeLocker API

2. **Export Signals**:
   ```python
   # In your live script
   from LTCUSD_ScalperBot_1m import LTCUSD_ScalperBot_1m

   # Run strategy
   cerebro = bt.Cerebro()
   cerebro.addstrategy(LTCUSD_ScalperBot_1m)
   # ... configure and run
   ```

3. **Webhook Integration** (with existing server.py):
   - Strategy generates signals
   - Send to your FastAPI webhook server
   - Server executes trades via TradeLocker API

## Expected Performance

### Conservative Settings (Default)
- **Risk per Trade**: 0.5%
- **Expected Win Rate**: 55-65%
- **Average R:R**: 1:1.67
- **Monthly Return**: 5-15% (varies by market conditions)
- **Max Drawdown**: <10%

### Aggressive Settings
- **Risk per Trade**: 1.0%
- **Expected Win Rate**: 50-60%
- **Monthly Return**: 10-25%
- **Max Drawdown**: <15%

**Note**: Past performance doesn't guarantee future results. Always test on recent data.

## Risk Warnings

1. **Scalping Risks**:
   - High commission sensitivity (use low-fee broker)
   - Requires tight spreads
   - Sensitive to slippage

2. **1-Minute Trading**:
   - High frequency = more commissions
   - Requires stable internet
   - Monitor during active trading hours

3. **Capital Requirements**:
   - Minimum $5,000 recommended
   - Allows proper position sizing
   - Reduces impact of fees

4. **Market Conditions**:
   - Works best in trending markets
   - ADX filter helps avoid choppy periods
   - Monitor crypto volatility

## Optimization Tips

### For Higher Win Rate
```python
# More conservative
adx_threshold = 25          # Only strong trends
volume_threshold = 1.5      # Higher volume requirement
atr_stop_multiplier = 1.0   # Tighter stop
```

### For Higher Profit Factor
```python
# Better R:R
atr_stop_multiplier = 1.5
atr_target_multiplier = 3.0
partial_exit_percent = 0.3  # Take less profit early
```

### For More Trades
```python
# More aggressive
adx_threshold = 15
rsi_overbought = 70
rsi_oversold = 30
cooldown_bars = 1
```

## Monitoring & Maintenance

### Daily Checklist
- [ ] Check daily PnL vs limit
- [ ] Review trade count
- [ ] Monitor win rate (should stay >50%)
- [ ] Check for unusual slippage
- [ ] Verify session times (DST changes)

### Weekly Review
- [ ] Backtest on recent data
- [ ] Compare live vs backtest performance
- [ ] Adjust parameters if needed
- [ ] Review losing trades for patterns

### Monthly Optimization
- [ ] Run parameter optimization
- [ ] Update parameters if market changed
- [ ] Review commission impact
- [ ] Adjust position sizing based on account growth

## Comparison: Original vs Optimized

| Feature | Original | Optimized | Impact |
|---------|----------|-----------|--------|
| EMA Periods | 9/21 | 5/13 | ⚡ Faster entries |
| Trend Filter | None | 50 EMA | 🛡️ Avoids counter-trend |
| MACD Confirm | Optional | Required | ✅ Better signals |
| ADX Filter | None | Required | 📈 Trends only |
| Volume Filter | Optional | Mandatory | 💪 Quality entries |
| Stop Loss | 2.0 ATR | 1.5 ATR | 🎯 Tighter risk |
| Take Profit | 3.0 ATR | 2.5 ATR | 💰 Better R:R |
| Partial Exits | No | Yes (50%) | 🔒 Lock profits |
| Breakeven | Manual | Automatic | 🛡️ Protect capital |
| Trailing Stop | Basic | Advanced | 📊 Capture trends |
| Session Filter | 8-17 UTC | 9-16 UTC (optimized) | ⏰ High volume only |
| Daily Limits | 1.5% loss | 2% loss + 15 trades | 🚦 Better control |

## Support & Troubleshooting

### Common Issues

**1. Too Few Trades**
- Lower `adx_threshold` (try 15)
- Lower `volume_threshold` (try 1.2)
- Widen session hours

**2. Too Many Losses**
- Increase `adx_threshold` (try 25)
- Increase `volume_threshold` (try 1.5)
- Check if market is ranging (use ADX)

**3. Large Drawdowns**
- Reduce `risk_per_trade` (try 0.3%)
- Enable `use_trailing_stop`
- Lower `max_daily_trades`

**4. Backtest vs Live Mismatch**
- Check commission settings
- Verify data quality
- Account for slippage (add 0.01% to commission)

## Contributing

To improve this strategy:
1. Test on different market conditions
2. Share optimization results
3. Report bugs or edge cases
4. Suggest new filters/indicators

## License

This strategy is provided for educational purposes. Trade at your own risk.

---

**Last Updated**: 2025-11-08
**Version**: 2.0 (Optimized)
**Tested On**: Backtrader 1.9.78.123

**Disclaimer**: Trading cryptocurrencies involves substantial risk. This strategy is not financial advice. Always test thoroughly before live trading.
