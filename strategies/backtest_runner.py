"""
Backtest Runner for LTCUSD Scalper Bot
Optimized for 1-minute timeframe with comprehensive analytics
"""

import backtrader as bt
from datetime import datetime
from LTCUSD_ScalperBot_1m import LTCUSD_ScalperBot_1m
import sys


class CustomAnalyzer(bt.Analyzer):
    """Custom analyzer for detailed performance metrics"""

    def __init__(self):
        self.trades = []
        self.current_trade = {}

    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                self.current_trade = {
                    'entry_time': self.strategy.datetime.datetime(),
                    'entry_price': order.executed.price,
                    'size': order.executed.size,
                    'type': 'long'
                }
            elif order.issell() and self.current_trade:
                self.current_trade['exit_time'] = self.strategy.datetime.datetime()
                self.current_trade['exit_price'] = order.executed.price
                pnl = (order.executed.price - self.current_trade['entry_price']) * self.current_trade['size']
                self.current_trade['pnl'] = pnl
                self.current_trade['pnl_pct'] = (pnl / (self.current_trade['entry_price'] * self.current_trade['size'])) * 100
                self.current_trade['duration'] = (self.current_trade['exit_time'] - self.current_trade['entry_time']).total_seconds() / 60
                self.trades.append(self.current_trade.copy())
                self.current_trade = {}

    def get_analysis(self):
        return {
            'trades': self.trades,
            'total_trades': len(self.trades),
            'winning_trades': len([t for t in self.trades if t['pnl'] > 0]),
            'losing_trades': len([t for t in self.trades if t['pnl'] < 0]),
            'avg_trade_duration': sum([t['duration'] for t in self.trades]) / len(self.trades) if self.trades else 0,
            'avg_win': sum([t['pnl'] for t in self.trades if t['pnl'] > 0]) / len([t for t in self.trades if t['pnl'] > 0]) if [t for t in self.trades if t['pnl'] > 0] else 0,
            'avg_loss': sum([t['pnl'] for t in self.trades if t['pnl'] < 0]) / len([t for t in self.trades if t['pnl'] < 0]) if [t for t in self.trades if t['pnl'] < 0] else 0,
        }


def run_backtest(
    data_file=None,
    initial_cash=10000,
    commission=0.0006,  # 0.06% per trade (typical for crypto)
    start_date=None,
    end_date=None,
    **strategy_params
):
    """
    Run backtest with specified parameters

    Args:
        data_file: Path to CSV file with OHLCV data (datetime, open, high, low, close, volume)
        initial_cash: Starting capital
        commission: Commission rate (0.0006 = 0.06%)
        start_date: Start date for backtest (YYYY-MM-DD)
        end_date: End date for backtest (YYYY-MM-DD)
        **strategy_params: Override default strategy parameters
    """

    # Initialize Cerebro
    cerebro = bt.Cerebro()

    # Add strategy
    cerebro.addstrategy(LTCUSD_ScalperBot_1m, **strategy_params)

    # Load data
    if data_file:
        dataformat = 'datetime,open,high,low,close,volume'

        data = bt.feeds.GenericCSVData(
            dataname=data_file,
            dtformat='%Y-%m-%d %H:%M:%S',
            datetime=0,
            open=1,
            high=2,
            low=3,
            close=4,
            volume=5,
            openinterest=-1,
            fromdate=datetime.strptime(start_date, '%Y-%m-%d') if start_date else None,
            todate=datetime.strptime(end_date, '%Y-%m-%d') if end_date else None,
        )
        cerebro.adddata(data)
    else:
        print("ERROR: No data file specified")
        print("Please provide a CSV file with format: datetime,open,high,low,close,volume")
        print("Example: python backtest_runner.py --data LTCUSD_1m.csv")
        sys.exit(1)

    # Set broker parameters
    cerebro.broker.setcash(initial_cash)
    cerebro.broker.setcommission(commission=commission)

    # Add analyzers
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe', riskfreerate=0.0)
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
    cerebro.addanalyzer(CustomAnalyzer, _name='custom')

    # Print starting conditions
    print('=' * 80)
    print('LTCUSD SCALPER BOT - BACKTEST')
    print('=' * 80)
    print(f'Starting Portfolio Value: ${cerebro.broker.getvalue():.2f}')
    print(f'Commission: {commission*100:.3f}%')

    if strategy_params:
        print('\nStrategy Parameters:')
        for key, value in strategy_params.items():
            print(f'  {key}: {value}')

    print('=' * 80)
    print()

    # Run backtest
    results = cerebro.run()
    strat = results[0]

    # Print results
    print()
    print('=' * 80)
    print('BACKTEST RESULTS')
    print('=' * 80)

    final_value = cerebro.broker.getvalue()
    pnl = final_value - initial_cash
    pnl_pct = (pnl / initial_cash) * 100

    print(f'Final Portfolio Value: ${final_value:.2f}')
    print(f'Total P&L: ${pnl:.2f} ({pnl_pct:.2f}%)')

    # Sharpe Ratio
    sharpe = strat.analyzers.sharpe.get_analysis()
    if 'sharperatio' in sharpe and sharpe['sharperatio'] is not None:
        print(f'Sharpe Ratio: {sharpe["sharperatio"]:.3f}')

    # Drawdown
    drawdown = strat.analyzers.drawdown.get_analysis()
    print(f'Max Drawdown: {drawdown.max.drawdown:.2f}%')
    print(f'Max Drawdown Money: ${drawdown.max.moneydown:.2f}')

    # Returns
    returns = strat.analyzers.returns.get_analysis()
    if 'rtot' in returns:
        print(f'Total Return: {returns["rtot"]*100:.2f}%')
    if 'rnorm' in returns:
        print(f'Normalized Return: {returns["rnorm"]*100:.2f}%')

    # Trade Analysis
    trades = strat.analyzers.trades.get_analysis()
    print()
    print('TRADE STATISTICS')
    print('-' * 80)

    total_trades = trades.total.closed if hasattr(trades, 'total') and hasattr(trades.total, 'closed') else 0
    print(f'Total Trades: {total_trades}')

    if hasattr(trades, 'won'):
        won = trades.won.total if hasattr(trades.won, 'total') else 0
        lost = trades.lost.total if hasattr(trades.lost, 'total') else 0
        win_rate = (won / total_trades * 100) if total_trades > 0 else 0

        print(f'Winning Trades: {won}')
        print(f'Losing Trades: {lost}')
        print(f'Win Rate: {win_rate:.2f}%')

        if hasattr(trades.won, 'pnl'):
            avg_win = trades.won.pnl.average if hasattr(trades.won.pnl, 'average') else 0
            print(f'Average Win: ${avg_win:.2f}')

        if hasattr(trades.lost, 'pnl'):
            avg_loss = trades.lost.pnl.average if hasattr(trades.lost.pnl, 'average') else 0
            print(f'Average Loss: ${avg_loss:.2f}')

            if avg_loss != 0:
                profit_factor = abs(avg_win / avg_loss)
                print(f'Profit Factor: {profit_factor:.2f}')

    # Custom Analysis
    custom = strat.analyzers.custom.get_analysis()
    if custom['total_trades'] > 0:
        print()
        print('CUSTOM METRICS')
        print('-' * 80)
        print(f'Average Trade Duration: {custom["avg_trade_duration"]:.1f} minutes')
        print(f'Average Win: ${custom["avg_win"]:.2f}')
        print(f'Average Loss: ${custom["avg_loss"]:.2f}')

    print('=' * 80)

    # Plot if matplotlib available
    try:
        cerebro.plot(style='candlestick', barup='green', bardown='red')
    except:
        print('\nNote: Plotting requires matplotlib. Install with: pip install matplotlib')

    return {
        'final_value': final_value,
        'pnl': pnl,
        'pnl_pct': pnl_pct,
        'max_drawdown': drawdown.max.drawdown,
        'total_trades': total_trades,
        'win_rate': win_rate if 'win_rate' in locals() else 0,
    }


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Run LTCUSD Scalper Bot Backtest')
    parser.add_argument('--data', type=str, help='Path to CSV data file')
    parser.add_argument('--cash', type=float, default=10000, help='Initial cash (default: 10000)')
    parser.add_argument('--commission', type=float, default=0.0006, help='Commission rate (default: 0.0006)')
    parser.add_argument('--start', type=str, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', type=str, help='End date (YYYY-MM-DD)')

    # Strategy parameters
    parser.add_argument('--fast-ema', type=int, default=5, help='Fast EMA period (default: 5)')
    parser.add_argument('--slow-ema', type=int, default=13, help='Slow EMA period (default: 13)')
    parser.add_argument('--risk', type=float, default=0.5, help='Risk per trade % (default: 0.5)')
    parser.add_argument('--atr-stop', type=float, default=1.5, help='ATR stop multiplier (default: 1.5)')
    parser.add_argument('--atr-target', type=float, default=2.5, help='ATR target multiplier (default: 2.5)')

    args = parser.parse_args()

    strategy_params = {
        'fast_ema_period': args.fast_ema,
        'slow_ema_period': args.slow_ema,
        'risk_per_trade': args.risk,
        'atr_stop_multiplier': args.atr_stop,
        'atr_target_multiplier': args.atr_target,
    }

    run_backtest(
        data_file=args.data,
        initial_cash=args.cash,
        commission=args.commission,
        start_date=args.start,
        end_date=args.end,
        **strategy_params
    )
