"""
T2 — Mean Reversion Pairs (Forex)
Profits from statistical reversion in cointegrated currency pairs.
"""
from __future__ import annotations
from typing import Any
import structlog
from app.strategies.base import BaseStrategy, StrategySignal

log = structlog.get_logger()

ZSCORE_ENTRY = 2.0
ZSCORE_PARTIAL_EXIT = 0.5
COINTEGRATION_MAX_PVAL = 0.05
VIX_MAX = 30


PAIR_UNIVERSE = [
    ("EURUSD", "GBPUSD"),
    ("AUDUSD", "NZDUSD"),
    ("USDCAD", "USDCHF"),
]


class MeanReversionPairsStrategy(BaseStrategy):
    name = "MeanReversionPairs"
    strategy_type = "TECHNICAL"

    async def scan(self, instruments: list[str], market_data: Any) -> list[StrategySignal]:
        signals: list[StrategySignal] = []

        vix = await market_data.get_vix()
        if vix > VIX_MAX:
            log.info("t2_skipped_high_vix", vix=vix)
            return signals

        for asset_a, asset_b in PAIR_UNIVERSE:
            try:
                sigs = await self._evaluate_pair(asset_a, asset_b, market_data)
                signals.extend(sigs)
            except Exception as e:
                log.warning("t2_eval_error", pair=f"{asset_a}/{asset_b}", error=str(e))
        return signals

    async def _evaluate_pair(
        self, asset_a: str, asset_b: str, market_data: Any
    ) -> list[StrategySignal]:
        coint_pval = await market_data.get_cointegration_pvalue(asset_a, asset_b)
        if coint_pval > COINTEGRATION_MAX_PVAL:
            return []

        zscore = await market_data.get_spread_zscore(asset_a, asset_b)
        if abs(zscore) < ZSCORE_ENTRY:
            return []

        price_a = await market_data.get_current_price(asset_a)
        price_b = await market_data.get_current_price(asset_b)
        atr_a = await market_data.get_atr(asset_a, period=14)
        atr_b = await market_data.get_atr(asset_b, period=14)

        signals = []
        if zscore > ZSCORE_ENTRY:
            # Spread too wide: short A, long B
            signals.append(StrategySignal(
                instrument=asset_a, direction="SHORT",
                entry_price=price_a, stop_loss=price_a + atr_a * 2,
                take_profit=price_a - atr_a * 2,
                lot_size=0.0, confidence_score=min(1.0, zscore / 3),
                strategy=self.name, strategy_type=self.strategy_type,
                filters_passed=["COINTEGRATION", "ZSCORE", "VIX"],
                notes=f"z={zscore:.2f}, pair={asset_a}/{asset_b}",
            ))
            signals.append(StrategySignal(
                instrument=asset_b, direction="LONG",
                entry_price=price_b, stop_loss=price_b - atr_b * 2,
                take_profit=price_b + atr_b * 2,
                lot_size=0.0, confidence_score=min(1.0, zscore / 3),
                strategy=self.name, strategy_type=self.strategy_type,
                filters_passed=["COINTEGRATION", "ZSCORE", "VIX"],
                notes=f"z={zscore:.2f}, pair={asset_a}/{asset_b}",
            ))
        elif zscore < -ZSCORE_ENTRY:
            # Spread too tight: long A, short B
            signals.append(StrategySignal(
                instrument=asset_a, direction="LONG",
                entry_price=price_a, stop_loss=price_a - atr_a * 2,
                take_profit=price_a + atr_a * 2,
                lot_size=0.0, confidence_score=min(1.0, abs(zscore) / 3),
                strategy=self.name, strategy_type=self.strategy_type,
                filters_passed=["COINTEGRATION", "ZSCORE", "VIX"],
                notes=f"z={zscore:.2f}, pair={asset_a}/{asset_b}",
            ))
            signals.append(StrategySignal(
                instrument=asset_b, direction="SHORT",
                entry_price=price_b, stop_loss=price_b + atr_b * 2,
                take_profit=price_b - atr_b * 2,
                lot_size=0.0, confidence_score=min(1.0, abs(zscore) / 3),
                strategy=self.name, strategy_type=self.strategy_type,
                filters_passed=["COINTEGRATION", "ZSCORE", "VIX"],
                notes=f"z={zscore:.2f}, pair={asset_a}/{asset_b}",
            ))
        return signals
