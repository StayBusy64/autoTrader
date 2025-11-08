import backtrader as bt
from datetime import datetime, time

class LTCUSD_ScalperBot_1m(bt.Strategy):
    """
    High-Performance Scalping Strategy for LTCUSD on 1-minute timeframe

    Strategy Features:
    - Multi-indicator confirmation (EMA, RSI, MACD, Bollinger Bands)
    - Volume surge detection for high-probability setups
    - Dynamic position sizing based on volatility
    - Multiple exit strategies (fixed SL, trailing, partial profits)
    - Advanced risk management for prop firm trading
    - Optimized for frequent but quality trades
    """

    params = (
        # EMA Trend Detection (Faster for scalping) - Backward compatible
        ('fast_ema', 5),
        ('fast_ema_period', 5),
        ('medium_ema', 13),
        ('slow_ema', 21),
        ('slow_ema_period', 21),

        # RSI Momentum
        ('rsi_period', 14),
        ('rsi_overbought', 70),  # Wider range for scalping
        ('rsi_oversold', 30),
        ('rsi_midline', 50),

        # MACD Trend Strength
        ('macd_fast', 12),
        ('macd_slow', 26),
        ('macd_signal', 9),

        # Bollinger Bands Volatility
        ('bb_period', 20),
        ('bb_dev', 2.0),

        # ATR Position Sizing & Stops - Backward compatible
        ('atr_period', 14),
        ('atr_multiplier', 2.0),
        ('atr_stop_multiplier', 1.5),    # Tight stop for scalping
        ('atr_target_multiplier', 2.5),  # Good R:R ratio

        # Volume Detection
        ('volume_period', 20),
        ('volume_surge_multiplier', 1.5),  # 50% above average
        ('use_volume_filter', False),      # Backward compatible
        ('volume_ma_period', 20),          # Backward compatible
        ('volume_threshold', 1.2),         # Backward compatible

        # Trailing Stop - Backward compatible
        ('use_trailing_stop', True),
        ('trailing_activation_atr', 1.0),  # Activate after 1 ATR profit
        ('trailing_distance_atr', 0.8),    # Trail 0.8 ATR behind
        ('trailing_stop_activation', 1.0), # Backward compatible
        ('trailing_stop_distance', 0.8),   # Backward compatible

        # Partial Profit Taking
        ('use_partial_exit', True),
        ('partial_exit_pct', 0.5),         # Close 50% at first target
        ('partial_target_atr', 1.5),       # First target at 1.5 ATR

        # Risk Management - Backward compatible
        ('risk_per_trade', 1.0),           # 1% risk per trade
        ('max_position_size', 2.0),        # Max 2 lots
        ('max_daily_loss_pct', 3.0),       # Stop trading after 3% daily loss
        ('max_daily_drawdown_pct', 3.0),   # Backward compatible
        ('max_daily_trades', 15),          # Limit overtrading
        ('max_consecutive_losses', 3),     # Cool down after 3 losses
        ('cooldown_after_loss', 2),        # Wait 2 bars after loss
        ('cooldown_bars', 2),              # Backward compatible

        # Session Filter - Backward compatible
        ('trade_24_7', True),              # Crypto trades 24/7
        ('avoid_low_volume_hours', False), # Trade all hours for more signals
        ('low_volume_start', 0),           # Midnight
        ('low_volume_end', 4),             # 4 AM UTC
        ('session_start', 0),              # Backward compatible
        ('session_end', 23),               # Backward compatible

        # Market Condition Filters
        ('min_volatility_percentile', 30), # Avoid dead markets
        ('max_volatility_percentile', 95), # Avoid extreme chaos
        ('require_trend', False),          # More flexible - don't require strong trend
        ('min_trend_strength', 0.15),      # Lower threshold when enabled

        # Entry Confirmation
        ('require_volume_surge', False),   # More trades - volume is secondary
        ('require_macd_agreement', False), # More trades - MACD is secondary
        ('allow_bb_breakout', True),       # Trade BB breakouts

        # Backward compatible unused params
        ('use_momentum_filter', False),
        ('momentum_threshold', 0.0),
        ('avoid_first_minutes', 0),
        ('avoid_last_minutes', 0),
    )

    def _safe_param(self, value, default):
        """Handle TradeLocker's 'undefined' strings"""
        if value == 'undefined' or value is None or value == '':
            return default
        return value

    def __init__(self):
        # Default values for TradeLocker compatibility
        defaults = {
            'fast_ema': 5, 'fast_ema_period': 5, 'medium_ema': 13, 'slow_ema': 21, 'slow_ema_period': 21,
            'rsi_period': 14, 'rsi_overbought': 70, 'rsi_oversold': 30, 'rsi_midline': 50,
            'macd_fast': 12, 'macd_slow': 26, 'macd_signal': 9,
            'bb_period': 20, 'bb_dev': 2.0,
            'atr_period': 14, 'atr_multiplier': 2.0, 'atr_stop_multiplier': 1.5, 'atr_target_multiplier': 2.5,
            'volume_period': 20, 'volume_surge_multiplier': 1.5,
            'use_volume_filter': False, 'volume_ma_period': 20, 'volume_threshold': 1.2,
            'use_trailing_stop': True, 'trailing_activation_atr': 1.0, 'trailing_distance_atr': 0.8,
            'trailing_stop_activation': 1.0, 'trailing_stop_distance': 0.8,
            'use_partial_exit': True, 'partial_exit_pct': 0.5, 'partial_target_atr': 1.5,
            'risk_per_trade': 1.0, 'max_position_size': 2.0, 'max_daily_loss_pct': 3.0, 'max_daily_drawdown_pct': 3.0,
            'max_daily_trades': 15, 'max_consecutive_losses': 3, 'cooldown_after_loss': 2, 'cooldown_bars': 2,
            'trade_24_7': True, 'avoid_low_volume_hours': False, 'low_volume_start': 0, 'low_volume_end': 4,
            'session_start': 0, 'session_end': 23,
            'min_volatility_percentile': 30, 'max_volatility_percentile': 95,
            'require_trend': False, 'min_trend_strength': 0.15,
            'require_volume_surge': False, 'require_macd_agreement': False, 'allow_bb_breakout': True,
            'use_momentum_filter': False, 'momentum_threshold': 0.0,
            'avoid_first_minutes': 0, 'avoid_last_minutes': 0,
        }

        # Extract and validate all parameters
        fast_ema = self._safe_param(self.params.fast_ema, defaults['fast_ema'])
        medium_ema = self._safe_param(self.params.medium_ema, defaults['medium_ema'])
        slow_ema = self._safe_param(self.params.slow_ema, defaults['slow_ema'])
        rsi_period = self._safe_param(self.params.rsi_period, defaults['rsi_period'])
        macd_fast = self._safe_param(self.params.macd_fast, defaults['macd_fast'])
        macd_slow = self._safe_param(self.params.macd_slow, defaults['macd_slow'])
        macd_signal = self._safe_param(self.params.macd_signal, defaults['macd_signal'])
        bb_period = self._safe_param(self.params.bb_period, defaults['bb_period'])
        bb_dev = self._safe_param(self.params.bb_dev, defaults['bb_dev'])
        atr_period = self._safe_param(self.params.atr_period, defaults['atr_period'])
        volume_period = self._safe_param(self.params.volume_period, defaults['volume_period'])

        # Indicators - EMA Trend
        self.ema_fast = bt.indicators.EMA(self.data.close, period=fast_ema)
        self.ema_medium = bt.indicators.EMA(self.data.close, period=medium_ema)
        self.ema_slow = bt.indicators.EMA(self.data.close, period=slow_ema)

        # RSI Momentum
        self.rsi = bt.indicators.RSI(self.data.close, period=rsi_period)

        # MACD Trend Strength
        self.macd = bt.indicators.MACD(self.data.close,
                                        period_me1=macd_fast,
                                        period_me2=macd_slow,
                                        period_signal=macd_signal)

        # Bollinger Bands Volatility
        self.bb = bt.indicators.BollingerBands(self.data.close,
                                                period=bb_period,
                                                devfactor=bb_dev)

        # ATR for stops and position sizing
        self.atr = bt.indicators.ATR(self.data, period=atr_period)

        # Volume analysis
        self.volume_sma = bt.indicators.SMA(self.data.volume, period=volume_period)

        # Crossover signals
        self.fast_medium_cross = bt.indicators.CrossOver(self.ema_fast, self.ema_medium)
        self.macd_cross = bt.indicators.CrossOver(self.macd.macd, self.macd.signal)

        # State tracking
        self.order = None
        self.entry_price = None
        self.stop_loss = None
        self.take_profit = None
        self.partial_target = None
        self.position_closed_partial = False

        # Risk tracking
        self.daily_trades = 0
        self.daily_pnl = 0.0
        self.last_trade_date = None
        self.consecutive_losses = 0
        self.bars_since_trade = 0
        self.starting_cash = None
        self.daily_starting_cash = None

        # Trailing stop tracking
        self.highest_price = None
        self.lowest_price = None
        self.trailing_active = False

        # Store validated parameters as instance variables
        self.rsi_ob = self._safe_param(self.params.rsi_overbought, defaults['rsi_overbought'])
        self.rsi_os = self._safe_param(self.params.rsi_oversold, defaults['rsi_oversold'])
        self.rsi_mid = self._safe_param(self.params.rsi_midline, defaults['rsi_midline'])
        self.atr_stop_mult = self._safe_param(self.params.atr_stop_multiplier, defaults['atr_stop_multiplier'])
        self.atr_target_mult = self._safe_param(self.params.atr_target_multiplier, defaults['atr_target_multiplier'])
        self.vol_surge = self._safe_param(self.params.volume_surge_multiplier, defaults['volume_surge_multiplier'])
        self.use_trailing = self._safe_param(self.params.use_trailing_stop, defaults['use_trailing_stop'])
        self.trail_activation = self._safe_param(self.params.trailing_activation_atr, defaults['trailing_activation_atr'])
        self.trail_distance = self._safe_param(self.params.trailing_distance_atr, defaults['trailing_distance_atr'])
        self.use_partial = self._safe_param(self.params.use_partial_exit, defaults['use_partial_exit'])
        self.partial_pct = self._safe_param(self.params.partial_exit_pct, defaults['partial_exit_pct'])
        self.partial_target_mult = self._safe_param(self.params.partial_target_atr, defaults['partial_target_atr'])
        self.risk_pct = self._safe_param(self.params.risk_per_trade, defaults['risk_per_trade'])
        self.max_size = self._safe_param(self.params.max_position_size, defaults['max_position_size'])
        self.max_daily_loss = self._safe_param(self.params.max_daily_loss_pct, defaults['max_daily_loss_pct'])
        self.max_trades = self._safe_param(self.params.max_daily_trades, defaults['max_daily_trades'])
        self.max_consec_losses = self._safe_param(self.params.max_consecutive_losses, defaults['max_consecutive_losses'])
        self.cooldown_bars = self._safe_param(self.params.cooldown_after_loss, defaults['cooldown_after_loss'])
        self.trade_24h = self._safe_param(self.params.trade_24_7, defaults['trade_24_7'])
        self.avoid_low_vol = self._safe_param(self.params.avoid_low_volume_hours, defaults['avoid_low_volume_hours'])
        self.low_vol_start = self._safe_param(self.params.low_volume_start, defaults['low_volume_start'])
        self.low_vol_end = self._safe_param(self.params.low_volume_end, defaults['low_volume_end'])
        self.req_volume_surge = self._safe_param(self.params.require_volume_surge, defaults['require_volume_surge'])
        self.req_macd = self._safe_param(self.params.require_macd_agreement, defaults['require_macd_agreement'])
        self.allow_bb = self._safe_param(self.params.allow_bb_breakout, defaults['allow_bb_breakout'])
        self.req_trend = self._safe_param(self.params.require_trend, defaults['require_trend'])
        self.min_trend = self._safe_param(self.params.min_trend_strength, defaults['min_trend_strength'])

        # Backward compatible parameters
        self.use_vol_filter_old = self._safe_param(self.params.use_volume_filter, defaults['use_volume_filter'])
        self.use_momentum = self._safe_param(self.params.use_momentum_filter, defaults['use_momentum_filter'])

        # Store periods for min data check
        self.max_period = max(slow_ema, rsi_period, macd_slow, bb_period, atr_period, volume_period)

    def start(self):
        """Called when backtest starts"""
        self.starting_cash = self.broker.getvalue()
        self.daily_starting_cash = self.starting_cash

    def log(self, txt, dt=None):
        """Logging function"""
        dt = dt or self.datas[0].datetime.datetime(0)
        print(f'{dt.isoformat()} {txt}')

    def notify_order(self, order):
        """Handle order notifications"""
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'BUY EXECUTED @ {order.executed.price:.5f}, Size: {order.executed.size:.2f}')
                if not self.entry_price:  # Only set on initial entry, not partial close
                    self.entry_price = order.executed.price
                    self.bars_since_trade = 0
                    self.trailing_active = False
                    self.position_closed_partial = False
                    self.daily_trades += 1

            elif order.issell():
                self.log(f'SELL EXECUTED @ {order.executed.price:.5f}, Size: {order.executed.size:.2f}')
                if not self.entry_price:  # Initial short entry
                    self.entry_price = order.executed.price
                    self.bars_since_trade = 0
                    self.trailing_active = False
                    self.position_closed_partial = False
                    self.daily_trades += 1
                else:  # Closing a position
                    pnl = 0
                    if self.position.size > 0:  # Was long
                        pnl = (order.executed.price - self.entry_price) * abs(order.executed.size)
                    else:  # Was short
                        pnl = (self.entry_price - order.executed.price) * abs(order.executed.size)

                    self.daily_pnl += pnl
                    self.log(f'PNL: ${pnl:.2f}, Daily: ${self.daily_pnl:.2f}')

                    # Track consecutive losses
                    if pnl < 0:
                        self.consecutive_losses += 1
                    else:
                        self.consecutive_losses = 0

                    # Reset if fully closed
                    if not self.position:
                        self.entry_price = None
                        self.stop_loss = None
                        self.take_profit = None
                        self.partial_target = None
                        self.highest_price = None
                        self.lowest_price = None
                        self.trailing_active = False
                        self.position_closed_partial = False

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log(f'Order {order.getstatusname()}')

        self.order = None

    def notify_trade(self, trade):
        """Handle trade notifications"""
        if not trade.isclosed:
            return
        self.log(f'TRADE CLOSED - Gross: ${trade.pnl:.2f}, Net: ${trade.pnlcomm:.2f}')

    def reset_daily_stats(self):
        """Reset daily statistics"""
        current_date = self.datas[0].datetime.date(0)
        if self.last_trade_date != current_date:
            self.daily_pnl = 0.0
            self.daily_trades = 0
            self.daily_starting_cash = self.broker.getvalue()
            self.last_trade_date = current_date

    def check_risk_limits(self):
        """Check if any risk limits are violated"""
        self.reset_daily_stats()

        # Check daily loss limit
        if self.daily_starting_cash and self.daily_starting_cash > 0:
            loss_pct = abs(self.daily_pnl / self.daily_starting_cash) * 100
            if self.daily_pnl < 0 and loss_pct >= self.max_daily_loss:
                return False

        # Check max daily trades
        if self.daily_trades >= self.max_trades:
            return False

        # Check consecutive losses cooldown
        if self.consecutive_losses >= self.max_consec_losses:
            return False

        # Check cooldown after loss
        if self.consecutive_losses > 0 and self.bars_since_trade < self.cooldown_bars:
            return False

        return True

    def is_trading_session(self):
        """Check if within allowed trading hours"""
        if self.trade_24h and not self.avoid_low_vol:
            return True

        try:
            current_hour = self.datas[0].datetime.time(0).hour

            if self.avoid_low_vol:
                # Avoid low volume hours (e.g., midnight to 4 AM)
                if self.low_vol_start <= current_hour < self.low_vol_end:
                    return False

            return True
        except:
            return True

    def check_volume_surge(self):
        """Check for volume surge"""
        if not self.req_volume_surge:
            return True

        try:
            if self.data.volume[0] >= self.volume_sma[0] * self.vol_surge:
                return True
        except:
            pass
        return False

    def check_trend_strength(self):
        """Check if there's a clear trend"""
        if not self.req_trend:
            return True

        try:
            price = self.data.close[0]
            ema_separation = abs(self.ema_fast[0] - self.ema_slow[0]) / price
            return ema_separation >= self.min_trend
        except:
            return False

    def check_macd_agreement(self, direction):
        """Check if MACD agrees with trade direction"""
        if not self.req_macd:
            return True

        try:
            if direction == 'long':
                return self.macd.macd[0] > self.macd.signal[0]
            else:  # short
                return self.macd.macd[0] < self.macd.signal[0]
        except:
            return False

    def calculate_position_size(self):
        """Calculate position size based on ATR and risk"""
        try:
            atr_value = self.atr[0]
            if not atr_value or atr_value <= 0:
                return 0.01

            account_value = self.broker.getvalue()
            if account_value <= 0:
                return 0.01

            risk_amount = account_value * (self.risk_pct / 100.0)
            stop_distance = atr_value * self.atr_stop_mult

            if stop_distance <= 0:
                return 0.01

            position_size = risk_amount / stop_distance
            position_size = min(position_size, self.max_size)
            position_size = max(position_size, 0.01)

            return round(position_size, 2)
        except:
            return 0.01

    def update_trailing_stop(self):
        """Update trailing stop"""
        if not self.use_trailing or not self.position:
            return

        try:
            current_price = self.data.close[0]
            atr_value = self.atr[0]

            if self.position.size > 0:  # Long position
                if self.highest_price is None or current_price > self.highest_price:
                    self.highest_price = current_price

                # Activate trailing stop after sufficient profit
                if not self.trailing_active and self.entry_price:
                    profit_atr = (self.highest_price - self.entry_price) / atr_value
                    if profit_atr >= self.trail_activation:
                        self.trailing_active = True
                        self.log(f'Trailing stop ACTIVATED')

                # Update trailing stop
                if self.trailing_active:
                    new_stop = self.highest_price - (atr_value * self.trail_distance)
                    if self.stop_loss is None or new_stop > self.stop_loss:
                        self.stop_loss = new_stop

            elif self.position.size < 0:  # Short position
                if self.lowest_price is None or current_price < self.lowest_price:
                    self.lowest_price = current_price

                if not self.trailing_active and self.entry_price:
                    profit_atr = (self.entry_price - self.lowest_price) / atr_value
                    if profit_atr >= self.trail_activation:
                        self.trailing_active = True
                        self.log(f'Trailing stop ACTIVATED')

                if self.trailing_active:
                    new_stop = self.lowest_price + (atr_value * self.trail_distance)
                    if self.stop_loss is None or new_stop < self.stop_loss:
                        self.stop_loss = new_stop
        except:
            pass

    def check_partial_profit(self):
        """Check and execute partial profit taking"""
        if not self.use_partial or not self.position or self.position_closed_partial:
            return

        try:
            current_price = self.data.close[0]

            # Check if partial target reached
            if self.position.size > 0 and current_price >= self.partial_target:
                size_to_close = abs(self.position.size) * self.partial_pct
                size_to_close = round(size_to_close, 2)
                if size_to_close >= 0.01:
                    self.log(f'PARTIAL PROFIT @ {current_price:.5f}, Closing {size_to_close} lots')
                    self.order = self.sell(size=size_to_close)
                    self.position_closed_partial = True

            elif self.position.size < 0 and current_price <= self.partial_target:
                size_to_close = abs(self.position.size) * self.partial_pct
                size_to_close = round(size_to_close, 2)
                if size_to_close >= 0.01:
                    self.log(f'PARTIAL PROFIT @ {current_price:.5f}, Closing {size_to_close} lots')
                    self.order = self.buy(size=size_to_close)
                    self.position_closed_partial = True
        except:
            pass

    def next(self):
        """Main strategy logic"""
        # Increment cooldown counter
        if self.bars_since_trade < 100:  # Cap at 100 to avoid overflow
            self.bars_since_trade += 1

        # Don't process if order pending
        if self.order:
            return

        current_price = self.data.close[0]

        # === POSITION MANAGEMENT ===
        if self.position:
            # Update trailing stop
            self.update_trailing_stop()

            # Check partial profit
            self.check_partial_profit()

            # Check stop loss
            if self.stop_loss:
                if self.position.size > 0 and current_price <= self.stop_loss:
                    self.log(f'STOP LOSS HIT @ {current_price:.5f}')
                    self.order = self.close()
                    return
                elif self.position.size < 0 and current_price >= self.stop_loss:
                    self.log(f'STOP LOSS HIT @ {current_price:.5f}')
                    self.order = self.close()
                    return

            # Check take profit
            if self.take_profit:
                if self.position.size > 0 and current_price >= self.take_profit:
                    self.log(f'TAKE PROFIT HIT @ {current_price:.5f}')
                    self.order = self.close()
                    return
                elif self.position.size < 0 and current_price <= self.take_profit:
                    self.log(f'TAKE PROFIT HIT @ {current_price:.5f}')
                    self.order = self.close()
                    return

            return  # Don't look for new entries while in position

        # === ENTRY LOGIC ===

        # Check minimum data
        if len(self.data) < self.max_period:
            return

        # Check risk limits
        if not self.check_risk_limits():
            return

        # Check trading session
        if not self.is_trading_session():
            return

        # Check ATR available
        if not self.atr[0] or self.atr[0] <= 0:
            return

        # Check trend strength
        if not self.check_trend_strength():
            return

        # Check volume surge
        if not self.check_volume_surge():
            return

        # === LONG ENTRY SIGNALS ===
        long_signal = False

        # Primary: Fast EMA crosses above Medium EMA
        if self.fast_medium_cross > 0:
            # Confirmation 1: Price above slow EMA (uptrend)
            if self.data.close[0] > self.ema_slow[0]:
                # Confirmation 2: RSI in bullish zone but not overbought
                if self.rsi_mid < self.rsi[0] < self.rsi_ob:
                    # Confirmation 3: MACD agreement
                    if self.check_macd_agreement('long'):
                        long_signal = True

        # Alternative: MACD crossover with trend
        if not long_signal and self.macd_cross > 0:
            if self.ema_fast[0] > self.ema_medium[0] > self.ema_slow[0]:
                if self.rsi[0] > self.rsi_mid and self.rsi[0] < self.rsi_ob:
                    long_signal = True

        # Alternative: BB breakout with momentum
        if not long_signal and self.allow_bb:
            if self.data.close[0] > self.bb.top[0]:
                if self.ema_fast[0] > self.ema_slow[0]:
                    if self.rsi[0] > self.rsi_mid:
                        if self.check_volume_surge():
                            long_signal = True

        # === SHORT ENTRY SIGNALS ===
        short_signal = False

        # Primary: Fast EMA crosses below Medium EMA
        if self.fast_medium_cross < 0:
            # Confirmation 1: Price below slow EMA (downtrend)
            if self.data.close[0] < self.ema_slow[0]:
                # Confirmation 2: RSI in bearish zone but not oversold
                if self.rsi_os < self.rsi[0] < self.rsi_mid:
                    # Confirmation 3: MACD agreement
                    if self.check_macd_agreement('short'):
                        short_signal = True

        # Alternative: MACD crossover with trend
        if not short_signal and self.macd_cross < 0:
            if self.ema_fast[0] < self.ema_medium[0] < self.ema_slow[0]:
                if self.rsi[0] < self.rsi_mid and self.rsi[0] > self.rsi_os:
                    short_signal = True

        # Alternative: BB breakout with momentum
        if not short_signal and self.allow_bb:
            if self.data.close[0] < self.bb.bot[0]:
                if self.ema_fast[0] < self.ema_slow[0]:
                    if self.rsi[0] < self.rsi_mid:
                        if self.check_volume_surge():
                            short_signal = True

        # === EXECUTE TRADES ===
        if long_signal:
            size = self.calculate_position_size()
            atr_value = self.atr[0]

            self.stop_loss = current_price - (atr_value * self.atr_stop_mult)
            self.take_profit = current_price + (atr_value * self.atr_target_mult)
            self.partial_target = current_price + (atr_value * self.partial_target_mult)

            self.log(f'LONG ENTRY @ {current_price:.5f} | Size: {size} | RSI: {self.rsi[0]:.1f}')
            self.log(f'  SL: {self.stop_loss:.5f} | PT: {self.partial_target:.5f} | TP: {self.take_profit:.5f}')

            self.order = self.buy(size=size)
            self.highest_price = current_price

        elif short_signal:
            size = self.calculate_position_size()
            atr_value = self.atr[0]

            self.stop_loss = current_price + (atr_value * self.atr_stop_mult)
            self.take_profit = current_price - (atr_value * self.atr_target_mult)
            self.partial_target = current_price - (atr_value * self.partial_target_mult)

            self.log(f'SHORT ENTRY @ {current_price:.5f} | Size: {size} | RSI: {self.rsi[0]:.1f}')
            self.log(f'  SL: {self.stop_loss:.5f} | PT: {self.partial_target:.5f} | TP: {self.take_profit:.5f}')

            self.order = self.sell(size=size)
            self.lowest_price = current_price
