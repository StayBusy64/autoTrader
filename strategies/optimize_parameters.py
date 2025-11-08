"""
Parameter Optimization for LTCUSD Scalper Bot
Uses grid search to find optimal parameters for maximum ROI
"""

import backtrader as bt
from LTCUSD_ScalperBot_1m import LTCUSD_ScalperBot_1m
from datetime import datetime
import itertools
import pandas as pd


def optimize_strategy(
    data_file,
    initial_cash=10000,
    commission=0.0006,
    param_grid=None
):
    """
    Optimize strategy parameters using grid search

    Args:
        data_file: Path to CSV file with OHLCV data
        initial_cash: Starting capital
        commission: Commission rate
        param_grid: Dictionary of parameters to test
    """

    if param_grid is None:
        # Default parameter grid
        param_grid = {
            'fast_ema_period': [5, 7, 9],
            'slow_ema_period': [13, 17, 21],
            'rsi_period': [14],
            'atr_stop_multiplier': [1.0, 1.5, 2.0],
            'atr_target_multiplier': [2.0, 2.5, 3.0],
            'adx_threshold': [15, 20, 25],
            'risk_per_trade': [0.5, 1.0],
            'volume_threshold': [1.2, 1.3, 1.5],
        }

    # Generate all combinations
    keys = param_grid.keys()
    values = param_grid.values()
    combinations = [dict(zip(keys, v)) for v in itertools.product(*values)]

    print('=' * 80)
    print('PARAMETER OPTIMIZATION')
    print('=' * 80)
    print(f'Total combinations to test: {len(combinations)}')
    print()

    results = []

    for i, params in enumerate(combinations, 1):
        print(f'Testing combination {i}/{len(combinations)}...')

        # Initialize Cerebro
        cerebro = bt.Cerebro()

        # Add strategy with current parameters
        cerebro.addstrategy(LTCUSD_ScalperBot_1m, **params)

        # Load data
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
        )
        cerebro.adddata(data)

        # Set broker
        cerebro.broker.setcash(initial_cash)
        cerebro.broker.setcommission(commission=commission)

        # Add analyzers
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')

        # Run
        try:
            strats = cerebro.run(stdstats=False)
            strat = strats[0]

            final_value = cerebro.broker.getvalue()
            pnl = final_value - initial_cash
            pnl_pct = (pnl / initial_cash) * 100

            # Get analysis
            sharpe = strat.analyzers.sharpe.get_analysis()
            sharpe_ratio = sharpe.get('sharperatio', 0) or 0

            drawdown = strat.analyzers.drawdown.get_analysis()
            max_dd = drawdown.max.drawdown

            trades = strat.analyzers.trades.get_analysis()
            total_trades = trades.total.closed if hasattr(trades, 'total') and hasattr(trades.total, 'closed') else 0

            won = 0
            win_rate = 0
            if hasattr(trades, 'won') and hasattr(trades.won, 'total'):
                won = trades.won.total
                win_rate = (won / total_trades * 100) if total_trades > 0 else 0

            # Store results
            result = {
                'final_value': final_value,
                'pnl': pnl,
                'pnl_pct': pnl_pct,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_dd,
                'total_trades': total_trades,
                'win_rate': win_rate,
                **params
            }

            results.append(result)

            print(f'  PNL: {pnl_pct:.2f}% | Sharpe: {sharpe_ratio:.3f} | DD: {max_dd:.2f}% | Trades: {total_trades} | WR: {win_rate:.1f}%')

        except Exception as e:
            print(f'  ERROR: {e}')
            continue

    # Convert to DataFrame
    df = pd.DataFrame(results)

    # Sort by PNL%
    df = df.sort_values('pnl_pct', ascending=False)

    print()
    print('=' * 80)
    print('OPTIMIZATION RESULTS (Top 10)')
    print('=' * 80)
    print()

    # Display top 10
    top_10 = df.head(10)

    for i, row in top_10.iterrows():
        print(f"Rank #{top_10.index.get_loc(i) + 1}")
        print(f"  ROI: {row['pnl_pct']:.2f}%")
        print(f"  Sharpe Ratio: {row['sharpe_ratio']:.3f}")
        print(f"  Max DD: {row['max_drawdown']:.2f}%")
        print(f"  Total Trades: {int(row['total_trades'])}")
        print(f"  Win Rate: {row['win_rate']:.2f}%")
        print(f"  Parameters:")
        for key in param_grid.keys():
            print(f"    {key}: {row[key]}")
        print()

    # Save results
    output_file = 'optimization_results.csv'
    df.to_csv(output_file, index=False)
    print(f"Full results saved to: {output_file}")

    # Best by different metrics
    print()
    print('=' * 80)
    print('BEST PARAMETERS BY METRIC')
    print('=' * 80)
    print()

    best_roi = df.loc[df['pnl_pct'].idxmax()]
    print("Best ROI:")
    print(f"  ROI: {best_roi['pnl_pct']:.2f}%")
    for key in param_grid.keys():
        print(f"  {key}: {best_roi[key]}")
    print()

    best_sharpe = df.loc[df['sharpe_ratio'].idxmax()]
    print("Best Sharpe Ratio:")
    print(f"  Sharpe: {best_sharpe['sharpe_ratio']:.3f}")
    print(f"  ROI: {best_sharpe['pnl_pct']:.2f}%")
    for key in param_grid.keys():
        print(f"  {key}: {best_sharpe[key]}")
    print()

    best_winrate = df.loc[df['win_rate'].idxmax()]
    print("Best Win Rate:")
    print(f"  Win Rate: {best_winrate['win_rate']:.2f}%")
    print(f"  ROI: {best_winrate['pnl_pct']:.2f}%")
    for key in param_grid.keys():
        print(f"  {key}: {best_winrate[key]}")
    print()

    return df


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Optimize LTCUSD Scalper Bot Parameters')
    parser.add_argument('--data', type=str, required=True, help='Path to CSV data file')
    parser.add_argument('--cash', type=float, default=10000, help='Initial cash')
    parser.add_argument('--commission', type=float, default=0.0006, help='Commission rate')

    args = parser.parse_args()

    # Custom parameter grid (modify as needed)
    param_grid = {
        'fast_ema_period': [5, 7, 9],
        'slow_ema_period': [13, 17, 21],
        'atr_stop_multiplier': [1.0, 1.5, 2.0],
        'atr_target_multiplier': [2.0, 2.5, 3.0],
        'adx_threshold': [15, 20, 25],
        'risk_per_trade': [0.5, 1.0],
        'volume_threshold': [1.2, 1.3, 1.5],
    }

    optimize_strategy(
        data_file=args.data,
        initial_cash=args.cash,
        commission=args.commission,
        param_grid=param_grid
    )
