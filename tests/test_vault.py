"""Tests for vault utility functions."""

import math

from axonfi.vault import operator_max_drain_per_day


class TestOperatorMaxDrainPerDay:
    def test_capped_by_aggregate(self):
        # 5 bots × $5k = $25k theoretical, capped by $10k aggregate
        assert operator_max_drain_per_day(5, 5_000, 10_000) == 10_000

    def test_theoretical_when_no_aggregate(self):
        # 5 bots × $5k = $25k, no aggregate cap
        assert operator_max_drain_per_day(5, 5_000, 0) == 25_000

    def test_zero_when_no_bots(self):
        assert operator_max_drain_per_day(0, 5_000, 10_000) == 0

    def test_infinity_when_daily_limit_unlimited_no_aggregate(self):
        # daily_limit=0 means unlimited, no aggregate → infinite drain
        assert operator_max_drain_per_day(5, 0, 0) == math.inf

    def test_aggregate_when_daily_limit_unlimited_but_aggregate_set(self):
        # daily_limit=0 means unlimited, but aggregate caps at $10k
        assert operator_max_drain_per_day(5, 0, 10_000) == 10_000

    def test_theoretical_equals_aggregate(self):
        # 2 bots × $5k = $10k = aggregate → returns $10k
        assert operator_max_drain_per_day(2, 5_000, 10_000) == 10_000
