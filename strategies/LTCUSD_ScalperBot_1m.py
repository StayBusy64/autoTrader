import backtrader as bt
from datetime import datetime, time

class LTCUSD_ScalperBot_1m(bt.Strategy):
    """
    Advanced Scalping Strategy for LTCUSD on 1-minute timeframe

    Strategy Components:
    - Fast EMA crossover (5/13) for quick entries
    - MACD for trend confirmation
    - ADX for trend strength filtering (avoid choppy markets)
    - RSI for overbought/oversold conditions
    - Bollinger Bands for volatility-based entries
    - Volume confirmation (mandatory for 1m)
    - ATR-based dynamic stops and targets
    - Smart trailing stop with profit protection
    - Multi-layered risk management

    Optimized for TradeLocker with high ROI potential
    """

    params = (
        # EMA Parameters (optimized for 1m scalping)
        ('fast_ema_period', 5),      # Faster for 1m
        ('slow_ema_period', 13),     # Fibonacci number
        ('trend_ema_period', 50),    # Overall trend filter

        # MACD Parameters
        ('macd_fast', 12),
        ('macd_slow', 26),
        ('macd_signal', 9),

        # RSI Parameters
        ('rsi_period', 14),
        ('rsi_overbought', 65),      # Tighter for scalping
        ('rsi_oversold', 35),
        ('rsi_neutral_high', 55),
        ('rsi_neutral_low', 45),

        # ADX Parameters (trend strength)
        ('adx_period', 14),
        ('adx_threshold', 20),       # Min trend strength

        # Bollinger Bands
        ('bb_period', 20),
        ('bb_dev', 2.0),

        # ATR Parameters
        ('atr_period', 14),
        ('atr_stop_multiplier', 1.5),     # Tighter stop for scalping
        ('atr_target_multiplier', 2.5),   # Better R:R ratio
        ('atr_breakeven_multiplier', 1.0), # Move to breakeven faster

        # Volume Filter (MANDATORY for 1m)
        ('volume_ma_period', 20),
        ('volume_threshold', 1.3),   # Volume must be 30% above average

        # Trailing Stop
        ('use_trailing_stop', True),
        ('trailing_activation_atr', 1.0),  # Activate after 1x ATR profit
        ('trailing_distance_atr', 1.2),    # Trail at 1.2x ATR

        # Smart Profit Taking
        ('use_partial_exits', True),
        ('partial_exit_percent', 0.5),     # Take 50% at first target
        ('partial_exit_atr', 1.5),         # First target at 1.5x ATR

        # Risk Management
        ('risk_per_trade', 0.5),          # 0.5% per trade
        ('max_position_size', 1.0),
        ('max_daily_loss_pct', 2.0),      # Stop trading if -2%
        ('max_daily_trades', 15),         # Limit overtrading
        ('cooldown_bars', 2),             # Minimum bars between trades

        # Session Filters (UTC) - Focus on high-volume periods
        ('session_start', 9),      # After Asian close
        ('session_end', 16),       # Before US close
        ('avoid_first_minutes', 5), # Skip first 5 mins of hour
        ('avoid_last_minutes', 5),  # Skip last 5 mins of hour

        # Market Structure
        ('min_price_movement', 0.0001),  # Minimum price movement to consider
        ('max_spread_atr', 0.3),         # Max spread as % of ATR

        # Advanced Filters
        ('use_ema_trend_filter', True),   # Only trade with trend
        ('use_macd_confirmation', True),  # Require MACD agreement
        ('use_bb_filter', True),          # Use BB for entry timing
        ('require_volume_spike', True),   # Volume must exceed threshold
    )

    def __init__(self):
        # Primary Indicators
        self.fast_ema = bt.indicators.EMA(self.data.close, period=self.params.fast_ema_period)
        self.slow_ema = bt.indicators.EMA(self.data.close, period=self.params.slow_ema_period)
        self.trend_ema = bt.indicators.EMA(self.data.close, period=self.params.trend_ema_period)

        # MACD
        self.macd = bt.indicators.MACD(
            self.data.close,
            period_me1=self.params.macd_fast,
            period_me2=self.params.macd_slow,
            period_signal=self.params.macd_signal
        )

        # RSI
        self.rsi = bt.indicators.RSI(self.data.close, period=self.params.rsi_period)

        # ADX (Trend Strength)
        self.adx = bt.indicators.ADX(self.data, period=self.params.adx_period)

        # Bollinger Bands
        self.bb = bt.indicators.BollingerBands(
            self.data.close,
            period=self.params.bb_period,
            devfactor=self.params.bb_dev
        )

        # ATR
        self.atr = bt.indicators.ATR(self.data, period=self.params.atr_period)

        # Volume
        self.volume_ma = bt.indicators.SMA(self.data.volume, period=self.params.volume_ma_period)

        # Crossovers
        self.ema_crossover = bt.indicators.CrossOver(self.fast_ema, self.slow_ema)
        self.macd_crossover = bt.indicators.CrossOver(self.macd.macd, self.macd.signal)

        # State Management
        self.order = None
        self.entry_price = None
        self.stop_loss = None
        self.take_profit = None
        self.breakeven_moved = False
        self.partial_exit_done = False
        self.trailing_active = False

        # Position tracking
        self.highest_price = None
        self.lowest_price = None
        self.entry_bar = 0
        self.bars_since_trade = 999

        # Daily tracking
        self.daily_pnl = 0.0
        self.daily_trades = 0
        self.last_trade_date = None
        self.starting_cash = None
        self.daily_starting_cash = None

        # Performance tracking
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0

    def start(self):
        """Called when backtest starts"""
        self.starting_cash = self.broker.getvalue()
        self.daily_starting_cash = self.starting_cash
        self.log('=' * 60)
        self.log(f'STRATEGY STARTED - Initial Capital: ${self.starting_cash:.2f}')
        self.log('=' * 60)

    def log(self, txt, dt=None):
        """Enhanced logging"""
        dt = dt or self.datas[0].datetime.datetime(0)
        print(f'{dt.isoformat()} | {txt}')

    def notify_order(self, order):
        """Handle order notifications"""
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'✓ BUY EXECUTED | Price: ${order.executed.price:.5f} | Size: {order.executed.size:.3f} | Cost: ${order.executed.value:.2f}')
                self.entry_price = order.executed.price
                self.entry_bar = len(self.data)
                self.bars_since_trade = 0
                self.breakeven_moved = False
                self.partial_exit_done = False
                self.trailing_active = False
                self.total_trades += 1
                self.daily_trades += 1

            elif order.issell():
                self.log(f'✓ SELL EXECUTED | Price: ${order.executed.price:.5f} | Size: {order.executed.size:.3f} | Value: ${order.executed.value:.2f}')

                # Calculate PnL for position closes
                if self.entry_price and abs(order.executed.size) > 0.001:
                    pnl = (order.executed.price - self.entry_price) * abs(order.executed.size)
                    pnl_pct = (pnl / (self.entry_price * abs(order.executed.size))) * 100

                    self.daily_pnl += pnl

                    if pnl > 0:
                        self.winning_trades += 1
                        self.log(f'✓ WIN | PNL: ${pnl:.2f} ({pnl_pct:.2f}%) | Daily: ${self.daily_pnl:.2f}')
                    else:
                        self.losing_trades += 1
                        self.log(f'✗ LOSS | PNL: ${pnl:.2f} ({pnl_pct:.2f}%) | Daily: ${self.daily_pnl:.2f}')

                    # Win rate
                    if self.total_trades > 0:
                        win_rate = (self.winning_trades / self.total_trades) * 100
                        self.log(f'Win Rate: {win_rate:.1f}% ({self.winning_trades}W/{self.losing_trades}L)')

                # Reset for full exit
                if not self.position:
                    self.entry_price = None
                    self.stop_loss = None
                    self.take_profit = None
                    self.highest_price = None
                    self.lowest_price = None
                    self.breakeven_moved = False
                    self.partial_exit_done = False
                    self.trailing_active = False

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log(f'✗ ORDER {order.getstatusname()}')

        self.order = None

    def notify_trade(self, trade):
        """Handle trade notifications"""
        if not trade.isclosed:
            return
        self.log(f'TRADE CLOSED | Gross PNL: ${trade.pnl:.2f} | Net PNL: ${trade.pnlcomm:.2f}')

    def reset_daily_stats(self):
        """Reset daily statistics"""
        current_date = self.datas[0].datetime.date(0)

        if self.last_trade_date != current_date:
            if self.last_trade_date is not None:
                self.log('-' * 60)
                self.log(f'DAY END | Total PNL: ${self.daily_pnl:.2f} | Trades: {self.daily_trades}')
                self.log('-' * 60)

            self.daily_pnl = 0.0
            self.daily_trades = 0
            self.daily_starting_cash = self.broker.getvalue()
            self.last_trade_date = current_date

    def is_trading_session(self):
        """Check if within optimal trading session"""
        try:
            current_time = self.datas[0].datetime.time(0)
            current_minute = current_time.minute

            # Check hour range
            start = time(int(self.params.session_start), 0)
            end = time(int(self.params.session_end), 0)

            if not (start <= current_time <= end):
                return False

            # Avoid first/last minutes of hour (low liquidity)
            if current_minute < self.params.avoid_first_minutes:
                return False
            if current_minute >= (60 - self.params.avoid_last_minutes):
                return False

            return True
        except:
            return True

    def check_daily_limits(self):
        """Check if daily limits exceeded"""
        # Max daily loss
        if self.daily_starting_cash and self.daily_starting_cash > 0:
            loss_pct = abs(self.daily_pnl / self.daily_starting_cash) * 100

            if self.daily_pnl < 0 and loss_pct >= self.params.max_daily_loss_pct:
                if self.daily_trades > 0:  # Only log once
                    self.log(f'⚠ DAILY LOSS LIMIT HIT | {loss_pct:.2f}% | Stopping trades')
                return True

        # Max daily trades
        if self.daily_trades >= self.params.max_daily_trades:
            return True

        return False

    def calculate_position_size(self):
        """Calculate optimal position size based on volatility and risk"""
        try:
            if not self.atr[0] or self.atr[0] <= 0:
                return 0.01

            account_value = self.broker.getvalue()
            if account_value <= 0:
                return 0.01

            # Risk amount
            risk_amount = account_value * (self.params.risk_per_trade / 100.0)

            # Stop distance
            stop_distance = self.atr[0] * self.params.atr_stop_multiplier

            if stop_distance <= 0:
                return 0.01

            # Position size
            position_size = risk_amount / stop_distance

            # Apply limits
            position_size = min(position_size, self.params.max_position_size)
            position_size = max(position_size, 0.01)

            return round(position_size, 3)
        except Exception as e:
            self.log(f'Error calculating position size: {e}')
            return 0.01

    def check_volume_condition(self):
        """Check if volume confirms the move"""
        try:
            if not self.params.require_volume_spike:
                return True

            current_volume = self.data.volume[0]
            avg_volume = self.volume_ma[0]

            if avg_volume <= 0:
                return False

            volume_ratio = current_volume / avg_volume

            return volume_ratio >= self.params.volume_threshold
        except:
            return False

    def check_trend_alignment(self, direction):
        """Check if trend aligns with trade direction"""
        try:
            if not self.params.use_ema_trend_filter:
                return True

            price = self.data.close[0]

            if direction == 'long':
                # For long: price above trend EMA, fast > slow
                return price > self.trend_ema[0] and self.fast_ema[0] > self.slow_ema[0]
            else:
                # For short: price below trend EMA, fast < slow
                return price < self.trend_ema[0] and self.fast_ema[0] < self.slow_ema[0]
        except:
            return False

    def check_macd_confirmation(self, direction):
        """Check MACD confirms the direction"""
        try:
            if not self.params.use_macd_confirmation:
                return True

            if direction == 'long':
                return self.macd.macd[0] > self.macd.signal[0] and self.macd.macd[0] > 0
            else:
                return self.macd.macd[0] < self.macd.signal[0] and self.macd.macd[0] < 0
        except:
            return False

    def check_bb_entry(self, direction):
        """Check Bollinger Band entry conditions"""
        try:
            if not self.params.use_bb_filter:
                return True

            price = self.data.close[0]

            if direction == 'long':
                # Enter long near lower BB but not below
                return self.bb.bot[0] <= price <= self.bb.mid[0]
            else:
                # Enter short near upper BB but not above
                return self.bb.mid[0] <= price <= self.bb.top[0]
        except:
            return False

    def update_stop_and_target(self):
        """Advanced stop loss and take profit management"""
        if not self.position or not self.entry_price:
            return

        try:
            current_price = self.data.close[0]
            atr = self.atr[0]

            if self.position.size > 0:  # Long position
                # Update highest price
                if self.highest_price is None or current_price > self.highest_price:
                    self.highest_price = current_price

                # Move to breakeven
                if not self.breakeven_moved:
                    profit_atr = (current_price - self.entry_price) / atr
                    if profit_atr >= self.params.atr_breakeven_multiplier:
                        self.stop_loss = self.entry_price + (atr * 0.1)  # Breakeven + small buffer
                        self.breakeven_moved = True
                        self.log(f'→ BREAKEVEN | SL moved to ${self.stop_loss:.5f}')

                # Partial exit
                if self.params.use_partial_exits and not self.partial_exit_done:
                    profit_atr = (current_price - self.entry_price) / atr
                    if profit_atr >= self.params.partial_exit_atr:
                        partial_size = self.position.size * self.params.partial_exit_percent
                        if partial_size >= 0.01:
                            self.log(f'→ PARTIAL EXIT | Taking {self.params.partial_exit_percent*100}% at ${current_price:.5f}')
                            self.order = self.sell(size=partial_size)
                            self.partial_exit_done = True
                            return

                # Activate trailing stop
                if self.params.use_trailing_stop:
                    profit_atr = (self.highest_price - self.entry_price) / atr

                    if profit_atr >= self.params.trailing_activation_atr:
                        if not self.trailing_active:
                            self.trailing_active = True
                            self.log(f'→ TRAILING ACTIVATED | Profit: {profit_atr:.2f} ATR')

                        # Update trailing stop
                        trail_distance = atr * self.params.trailing_distance_atr
                        new_stop = self.highest_price - trail_distance

                        if self.stop_loss is None or new_stop > self.stop_loss:
                            self.stop_loss = new_stop

                # Check stop loss
                if self.stop_loss and current_price <= self.stop_loss:
                    self.log(f'✗ STOP LOSS HIT | Price: ${current_price:.5f} | SL: ${self.stop_loss:.5f}')
                    self.order = self.close()
                    return

                # Check take profit
                if self.take_profit and current_price >= self.take_profit:
                    self.log(f'✓ TAKE PROFIT HIT | Price: ${current_price:.5f} | TP: ${self.take_profit:.5f}')
                    self.order = self.close()
                    return

            elif self.position.size < 0:  # Short position
                # Update lowest price
                if self.lowest_price is None or current_price < self.lowest_price:
                    self.lowest_price = current_price

                # Move to breakeven
                if not self.breakeven_moved:
                    profit_atr = (self.entry_price - current_price) / atr
                    if profit_atr >= self.params.atr_breakeven_multiplier:
                        self.stop_loss = self.entry_price - (atr * 0.1)
                        self.breakeven_moved = True
                        self.log(f'→ BREAKEVEN | SL moved to ${self.stop_loss:.5f}')

                # Partial exit
                if self.params.use_partial_exits and not self.partial_exit_done:
                    profit_atr = (self.entry_price - current_price) / atr
                    if profit_atr >= self.params.partial_exit_atr:
                        partial_size = abs(self.position.size) * self.params.partial_exit_percent
                        if partial_size >= 0.01:
                            self.log(f'→ PARTIAL EXIT | Taking {self.params.partial_exit_percent*100}% at ${current_price:.5f}')
                            self.order = self.buy(size=partial_size)
                            self.partial_exit_done = True
                            return

                # Activate trailing stop
                if self.params.use_trailing_stop:
                    profit_atr = (self.entry_price - self.lowest_price) / atr

                    if profit_atr >= self.params.trailing_activation_atr:
                        if not self.trailing_active:
                            self.trailing_active = True
                            self.log(f'→ TRAILING ACTIVATED | Profit: {profit_atr:.2f} ATR')

                        # Update trailing stop
                        trail_distance = atr * self.params.trailing_distance_atr
                        new_stop = self.lowest_price + trail_distance

                        if self.stop_loss is None or new_stop < self.stop_loss:
                            self.stop_loss = new_stop

                # Check stop loss
                if self.stop_loss and current_price >= self.stop_loss:
                    self.log(f'✗ STOP LOSS HIT | Price: ${current_price:.5f} | SL: ${self.stop_loss:.5f}')
                    self.order = self.close()
                    return

                # Check take profit
                if self.take_profit and current_price <= self.take_profit:
                    self.log(f'✓ TAKE PROFIT HIT | Price: ${current_price:.5f} | TP: ${self.take_profit:.5f}')
                    self.order = self.close()
                    return

        except Exception as e:
            self.log(f'Error in update_stop_and_target: {e}')

    def next(self):
        """Main strategy logic - executed on each bar"""
        # Increment bars counter
        if self.bars_since_trade < 999:
            self.bars_since_trade += 1

        # Reset daily stats
        self.reset_daily_stats()

        # Wait for pending orders
        if self.order:
            return

        # Manage existing position
        if self.position:
            self.update_stop_and_target()
            return

        # Check minimum data requirement
        min_period = max(
            self.params.slow_ema_period,
            self.params.trend_ema_period,
            self.params.rsi_period,
            self.params.atr_period,
            self.params.adx_period,
            self.params.bb_period,
            self.params.volume_ma_period
        )

        if len(self.data) < min_period + 1:
            return

        # Pre-flight checks
        if not self.is_trading_session():
            return

        if self.check_daily_limits():
            return

        if self.bars_since_trade < self.params.cooldown_bars:
            return

        if not self.atr[0] or self.atr[0] <= 0:
            return

        # Check ADX - need trending market
        if self.adx[0] < self.params.adx_threshold:
            return

        # Check volume
        if not self.check_volume_condition():
            return

        # Get current values
        current_price = self.data.close[0]
        atr = self.atr[0]

        # =================================================================
        # LONG ENTRY CONDITIONS
        # =================================================================
        if self.ema_crossover > 0:  # Fast EMA crossed above Slow EMA

            # Multi-filter confirmation
            if (self.check_trend_alignment('long') and
                self.check_macd_confirmation('long') and
                self.check_bb_entry('long') and
                self.rsi[0] < self.params.rsi_overbought and
                self.rsi[0] > self.params.rsi_neutral_low):

                size = self.calculate_position_size()

                # Calculate stops and targets
                stop_distance = atr * self.params.atr_stop_multiplier
                target_distance = atr * self.params.atr_target_multiplier

                self.stop_loss = current_price - stop_distance
                self.take_profit = current_price + target_distance

                risk_reward = target_distance / stop_distance

                self.log('=' * 60)
                self.log(f'⬆ LONG SIGNAL')
                self.log(f'  Entry: ${current_price:.5f}')
                self.log(f'  Size: {size} | R:R: 1:{risk_reward:.2f}')
                self.log(f'  Stop: ${self.stop_loss:.5f} (-{stop_distance:.5f})')
                self.log(f'  Target: ${self.take_profit:.5f} (+{target_distance:.5f})')
                self.log(f'  RSI: {self.rsi[0]:.1f} | ADX: {self.adx[0]:.1f}')
                self.log(f'  MACD: {self.macd.macd[0]:.5f}')
                self.log('=' * 60)

                self.order = self.buy(size=size)
                self.highest_price = current_price

        # =================================================================
        # SHORT ENTRY CONDITIONS
        # =================================================================
        elif self.ema_crossover < 0:  # Fast EMA crossed below Slow EMA

            # Multi-filter confirmation
            if (self.check_trend_alignment('short') and
                self.check_macd_confirmation('short') and
                self.check_bb_entry('short') and
                self.rsi[0] > self.params.rsi_oversold and
                self.rsi[0] < self.params.rsi_neutral_high):

                size = self.calculate_position_size()

                # Calculate stops and targets
                stop_distance = atr * self.params.atr_stop_multiplier
                target_distance = atr * self.params.atr_target_multiplier

                self.stop_loss = current_price + stop_distance
                self.take_profit = current_price - target_distance

                risk_reward = target_distance / stop_distance

                self.log('=' * 60)
                self.log(f'⬇ SHORT SIGNAL')
                self.log(f'  Entry: ${current_price:.5f}')
                self.log(f'  Size: {size} | R:R: 1:{risk_reward:.2f}')
                self.log(f'  Stop: ${self.stop_loss:.5f} (+{stop_distance:.5f})')
                self.log(f'  Target: ${self.take_profit:.5f} (-{target_distance:.5f})')
                self.log(f'  RSI: {self.rsi[0]:.1f} | ADX: {self.adx[0]:.1f}')
                self.log(f'  MACD: {self.macd.macd[0]:.5f}')
                self.log('=' * 60)

                self.order = self.sell(size=size)
                self.lowest_price = current_price

    def stop(self):
        """Called when backtest ends"""
        self.log('=' * 60)
        self.log('STRATEGY STOPPED')
        self.log(f'Final Portfolio Value: ${self.broker.getvalue():.2f}')
        self.log(f'Starting Capital: ${self.starting_cash:.2f}')

        if self.starting_cash:
            total_return = ((self.broker.getvalue() - self.starting_cash) / self.starting_cash) * 100
            self.log(f'Total Return: {total_return:.2f}%')

        self.log(f'Total Trades: {self.total_trades}')

        if self.total_trades > 0:
            win_rate = (self.winning_trades / self.total_trades) * 100
            self.log(f'Winning Trades: {self.winning_trades}')
            self.log(f'Losing Trades: {self.losing_trades}')
            self.log(f'Win Rate: {win_rate:.2f}%')

        self.log('=' * 60)
