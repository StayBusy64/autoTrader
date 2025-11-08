"""
Generate Sample LTCUSD Data for Testing
Creates realistic 1-minute crypto data with trends and volatility
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def generate_crypto_data(
    start_date='2024-01-01',
    days=30,
    initial_price=65.0,
    volatility=0.02,
    trend=0.0001,
    output_file='LTCUSD_1m_sample.csv'
):
    """
    Generate realistic 1-minute crypto data

    Args:
        start_date: Start date (YYYY-MM-DD)
        days: Number of days to generate
        initial_price: Starting price
        volatility: Daily volatility (0.02 = 2%)
        trend: Upward/downward bias
        output_file: Output CSV filename
    """

    print(f"Generating {days} days of 1-minute LTCUSD data...")

    # Calculate number of 1-minute bars
    # 24 hours * 60 minutes = 1440 bars per day
    total_bars = days * 24 * 60

    # Generate timestamps
    start = datetime.strptime(start_date, '%Y-%m-%d')
    timestamps = [start + timedelta(minutes=i) for i in range(total_bars)]

    # Initialize arrays
    prices = np.zeros(total_bars)
    opens = np.zeros(total_bars)
    highs = np.zeros(total_bars)
    lows = np.zeros(total_bars)
    closes = np.zeros(total_bars)
    volumes = np.zeros(total_bars)

    # Set initial price
    current_price = initial_price

    # Volatility per minute
    minute_volatility = volatility / np.sqrt(1440)

    # Generate realistic price action
    for i in range(total_bars):
        # Random walk with trend
        change = np.random.normal(trend, minute_volatility)
        current_price = current_price * (1 + change)

        # Generate OHLC for this minute
        open_price = current_price

        # Intrabar volatility (smaller than daily)
        intrabar_vol = minute_volatility * 0.5
        high_price = open_price * (1 + abs(np.random.normal(0, intrabar_vol)))
        low_price = open_price * (1 - abs(np.random.normal(0, intrabar_vol)))

        # Close could be anywhere between high and low
        close_price = np.random.uniform(low_price, high_price)

        # Volume (higher during certain hours)
        hour = timestamps[i].hour
        base_volume = 100000

        # Higher volume during active hours (9-17 UTC)
        if 9 <= hour <= 17:
            volume_multiplier = np.random.uniform(1.2, 2.0)
        else:
            volume_multiplier = np.random.uniform(0.5, 1.0)

        volume = int(base_volume * volume_multiplier * np.random.uniform(0.8, 1.2))

        # Store values
        opens[i] = open_price
        highs[i] = high_price
        lows[i] = low_price
        closes[i] = close_price
        volumes[i] = volume

        # Update current price for next bar
        current_price = close_price

        # Add some trending periods
        if i % 720 == 0:  # Every 12 hours, potentially change trend
            if np.random.random() > 0.5:
                trend = np.random.uniform(-0.0002, 0.0003)

    # Create DataFrame
    df = pd.DataFrame({
        'datetime': timestamps,
        'open': opens,
        'high': highs,
        'low': lows,
        'close': closes,
        'volume': volumes.astype(int)
    })

    # Round prices to 3 decimals (realistic for LTC)
    for col in ['open', 'high', 'low', 'close']:
        df[col] = df[col].round(3)

    # Save to CSV
    df.to_csv(output_file, index=False)

    print(f"✓ Generated {len(df):,} bars of data")
    print(f"✓ Date range: {df['datetime'].min()} to {df['datetime'].max()}")
    print(f"✓ Price range: ${df['low'].min():.3f} - ${df['high'].max():.3f}")
    print(f"✓ Saved to: {output_file}")

    # Show sample
    print("\nFirst 5 rows:")
    print(df.head())

    print("\nLast 5 rows:")
    print(df.tail())

    return df


def add_market_events(df, events=None):
    """
    Add specific market events (pumps, dumps, consolidation)

    Args:
        df: DataFrame with OHLCV data
        events: List of events to add
    """

    if events is None:
        events = [
            {'type': 'pump', 'start': 0.2, 'duration': 0.05, 'magnitude': 0.15},
            {'type': 'dump', 'start': 0.5, 'duration': 0.03, 'magnitude': -0.12},
            {'type': 'consolidation', 'start': 0.7, 'duration': 0.1},
        ]

    total_bars = len(df)

    for event in events:
        start_idx = int(total_bars * event['start'])
        duration = int(total_bars * event['duration'])
        end_idx = min(start_idx + duration, total_bars)

        if event['type'] == 'pump':
            # Gradual price increase
            magnitude = event['magnitude']
            for i in range(start_idx, end_idx):
                progress = (i - start_idx) / duration
                multiplier = 1 + (magnitude * progress)
                df.loc[i, 'close'] *= multiplier
                df.loc[i, 'high'] *= multiplier * 1.01
                df.loc[i, 'low'] *= multiplier * 0.99
                df.loc[i, 'open'] = df.loc[i-1, 'close'] if i > 0 else df.loc[i, 'open']
                df.loc[i, 'volume'] *= np.random.uniform(1.5, 2.5)

        elif event['type'] == 'dump':
            # Quick price decrease
            magnitude = event['magnitude']
            for i in range(start_idx, end_idx):
                progress = (i - start_idx) / duration
                multiplier = 1 + (magnitude * progress)
                df.loc[i, 'close'] *= multiplier
                df.loc[i, 'high'] *= multiplier * 1.01
                df.loc[i, 'low'] *= multiplier * 0.99
                df.loc[i, 'open'] = df.loc[i-1, 'close'] if i > 0 else df.loc[i, 'open']
                df.loc[i, 'volume'] *= np.random.uniform(2.0, 3.0)

        elif event['type'] == 'consolidation':
            # Low volatility range
            avg_price = df.loc[start_idx:end_idx, 'close'].mean()
            for i in range(start_idx, end_idx):
                df.loc[i, 'close'] = avg_price * np.random.uniform(0.995, 1.005)
                df.loc[i, 'high'] = df.loc[i, 'close'] * 1.002
                df.loc[i, 'low'] = df.loc[i, 'close'] * 0.998
                df.loc[i, 'volume'] *= np.random.uniform(0.3, 0.7)

    return df


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Generate sample LTCUSD data')
    parser.add_argument('--days', type=int, default=30, help='Number of days (default: 30)')
    parser.add_argument('--start', type=str, default='2024-01-01', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--price', type=float, default=65.0, help='Initial price (default: 65.0)')
    parser.add_argument('--volatility', type=float, default=0.02, help='Daily volatility (default: 0.02)')
    parser.add_argument('--trend', type=float, default=0.0001, help='Price trend (default: 0.0001)')
    parser.add_argument('--output', type=str, default='LTCUSD_1m_sample.csv', help='Output filename')
    parser.add_argument('--events', action='store_true', help='Add market events (pumps/dumps)')

    args = parser.parse_args()

    # Generate data
    df = generate_crypto_data(
        start_date=args.start,
        days=args.days,
        initial_price=args.price,
        volatility=args.volatility,
        trend=args.trend,
        output_file=args.output
    )

    # Add events if requested
    if args.events:
        print("\nAdding market events...")
        df = add_market_events(df)
        df.to_csv(args.output, index=False)
        print("✓ Events added")

    print(f"\nReady to backtest!")
    print(f"Run: python backtest_runner.py --data {args.output}")
