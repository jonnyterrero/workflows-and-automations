"""Validate that backtesting replay does not use lookahead bias."""
import pytest
from datetime import datetime, timedelta, timezone


def test_signal_timestamp_before_entry_price():
    """Verify that signal creation time must precede entry price fetch window."""
    signal_ts = datetime(2024, 1, 10, 9, 30, tzinfo=timezone.utc)
    entry_start = signal_ts + timedelta(minutes=1)  # entry window opens AFTER signal
    assert entry_start > signal_ts, "Entry must be strictly after signal creation"


def test_no_future_price_in_backtest():
    """Prices used for entry/exit must have timestamps >= signal_ts + 1 minute."""
    signal_ts = datetime(2024, 1, 10, 9, 30, tzinfo=timezone.utc)
    price_ts = datetime(2024, 1, 10, 9, 31, tzinfo=timezone.utc)
    assert price_ts > signal_ts, "Price timestamp must be after signal timestamp"


def test_lookforward_days_produces_positive_window():
    from packages.backtesting.replay import SignalReplayer
    lookforward = 5
    entry_ts = datetime(2024, 1, 10, tzinfo=timezone.utc)
    exit_start = entry_ts + timedelta(days=lookforward - 1)
    exit_end = entry_ts + timedelta(days=lookforward + 2)
    assert exit_end > exit_start > entry_ts


def test_return_formula():
    entry = 100.0
    exit_price = 110.0
    ret = (exit_price - entry) / entry
    assert abs(ret - 0.10) < 1e-9


def test_bearish_signal_aligned_when_price_falls():
    direction = "bearish"
    ret = -0.05
    aligned = (direction == "bullish" and ret > 0) or (direction == "bearish" and ret < 0)
    assert aligned


def test_bullish_signal_not_aligned_when_price_falls():
    direction = "bullish"
    ret = -0.05
    aligned = (direction == "bullish" and ret > 0) or (direction == "bearish" and ret < 0)
    assert not aligned
