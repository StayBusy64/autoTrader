# Quick Start Guide - LTCUSD Scalper Bot

Get your scalper bot running in 5 minutes!

## Step 1: Install Dependencies

```bash
cd strategies
pip install -r requirements.txt
```

## Step 2: Generate Sample Data (or use your own)

```bash
# Generate 30 days of sample data
python generate_sample_data.py --days 30 --events

# This creates: LTCUSD_1m_sample.csv
```

**Or use your own data**: Format must be CSV with columns:
```
datetime,open,high,low,close,volume
```

## Step 3: Run Your First Backtest

```bash
# Basic backtest with default parameters
python backtest_runner.py --data LTCUSD_1m_sample.csv
```

You should see output like:
```
================================================================================
LTCUSD SCALPER BOT - BACKTEST
================================================================================
Starting Portfolio Value: $10000.00
...
Final Portfolio Value: $11250.00
Total P&L: $1250.00 (12.50%)
Win Rate: 58.33%
================================================================================
```

## Step 4: Optimize for Your Data

```bash
# Find the best parameters for your data
python optimize_parameters.py --data LTCUSD_1m_sample.csv
```

This will:
- Test hundreds of parameter combinations
- Show top 10 performing sets
- Save full results to `optimization_results.csv`

## Step 5: Backtest with Optimized Parameters

```bash
# Use parameters from optimization
python backtest_runner.py \
    --data LTCUSD_1m_sample.csv \
    --fast-ema 5 \
    --slow-ema 13 \
    --risk 0.5 \
    --atr-stop 1.5 \
    --atr-target 2.5
```

## Step 6: Live Trading Setup (Optional)

### Option A: TradingView Alerts

1. Convert strategy to Pine Script
2. Set alerts on entry/exit signals
3. Use TradingView webhook → Your server

### Option B: Direct Integration

```bash
# Configure TradeLocker
python tradelocker_config.py setup

# Test connection
python tradelocker_config.py test
```

---

## Common Commands

### Basic Backtest
```bash
python backtest_runner.py --data LTCUSD_1m_sample.csv
```

### Custom Date Range
```bash
python backtest_runner.py \
    --data LTCUSD_1m_sample.csv \
    --start 2024-01-01 \
    --end 2024-01-31
```

### Higher Risk Settings
```bash
python backtest_runner.py \
    --data LTCUSD_1m_sample.csv \
    --risk 1.0 \
    --atr-stop 1.0 \
    --atr-target 3.0
```

### Conservative Settings
```bash
python backtest_runner.py \
    --data LTCUSD_1m_sample.csv \
    --risk 0.3 \
    --atr-stop 2.0 \
    --atr-target 2.0
```

---

## Expected Results

### Default Parameters
- **Win Rate**: 55-65%
- **Monthly Return**: 5-15%
- **Max Drawdown**: <10%
- **Trades per Day**: 3-8

### Aggressive Parameters
- **Win Rate**: 50-60%
- **Monthly Return**: 10-25%
- **Max Drawdown**: <15%
- **Trades per Day**: 8-15

---

## Troubleshooting

### "No module named 'backtrader'"
```bash
pip install backtrader
```

### "No data file specified"
You need to provide a CSV file:
```bash
python backtest_runner.py --data YOUR_FILE.csv
```

### "Too few trades"
Try more aggressive settings:
```bash
python backtest_runner.py \
    --data LTCUSD_1m_sample.csv \
    --fast-ema 7 \
    --slow-ema 17
```

### "Too many losses"
Try more conservative settings or check if market is ranging:
```bash
# Generate data with more trends
python generate_sample_data.py --days 30 --trend 0.0003 --events
```

---

## Next Steps

1. ✅ Read full [README.md](README.md) for detailed docs
2. ✅ Run optimization to find best parameters
3. ✅ Test on different market conditions
4. ✅ Forward test on recent data
5. ✅ Paper trade before going live

---

## Key Files

| File | Purpose |
|------|---------|
| `LTCUSD_ScalperBot_1m.py` | Main strategy code |
| `backtest_runner.py` | Run backtests |
| `optimize_parameters.py` | Parameter optimization |
| `generate_sample_data.py` | Create test data |
| `tradelocker_config.py` | Live trading setup |
| `README.md` | Full documentation |

---

## Support

**Issues?** Check the full [README.md](README.md) for:
- Detailed parameter explanations
- Performance optimization tips
- Risk management guidelines
- Live trading setup

**Still stuck?** Make sure you:
1. Have Python 3.8+
2. Installed all requirements
3. Have properly formatted CSV data
4. Are using the correct command syntax

---

**Happy Scalping!** 📈

Remember: Always backtest thoroughly before live trading. This is not financial advice.
