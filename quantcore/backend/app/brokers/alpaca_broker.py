"""
Alpaca broker adapter — stocks and crypto.
"""
from __future__ import annotations
import structlog
from app.brokers.base import BaseBroker
from app.core.config import settings

log = structlog.get_logger()


class AlpacaBroker(BaseBroker):
    name = "Alpaca"

    def __init__(self):
        self._client = None

    async def connect(self):
        from alpaca_trade_api import REST
        self._client = REST(
            settings.ALPACA_API_KEY,
            settings.ALPACA_API_SECRET,
            settings.ALPACA_BASE_URL,
        )
        account = self._client.get_account()
        log.info("alpaca_connected", status=account.status, equity=account.equity)

    async def disconnect(self):
        self._client = None

    async def submit_bracket_order(
        self, instrument, direction, lot_size, entry_price, stop_loss, take_profit
    ) -> str:
        side = "buy" if direction == "LONG" else "sell"
        order = self._client.submit_order(
            symbol=instrument,
            qty=lot_size,
            side=side,
            type="limit",
            limit_price=round(entry_price, 2),
            time_in_force="gtc",
            order_class="bracket",
            stop_loss={"stop_price": round(stop_loss, 2)},
            take_profit={"limit_price": round(take_profit, 2)},
        )
        return order.id

    async def cancel_pending_orders(self, account_id: str):
        if self._client:
            self._client.cancel_all_orders()

    async def close_all_positions(self, account_id: str):
        if self._client:
            self._client.close_all_positions()

    async def tighten_trailing_stops(self, account_id: str, factor: float = 0.80):
        if not self._client:
            return
        positions = self._client.list_positions()
        for pos in positions:
            # Replace existing stop with tightened stop
            # In production: modify existing bracket stop leg
            pass

    async def get_open_position_count(self, account_id: str) -> int:
        if not self._client:
            return 0
        return len(self._client.list_positions())

    async def get_account_equity(self, account_id: str) -> float:
        if not self._client:
            return 0.0
        return float(self._client.get_account().equity)

    async def get_open_positions(self, account_id: str) -> list[dict]:
        if not self._client:
            return []
        positions = self._client.list_positions()
        return [
            {
                "instrument": p.symbol,
                "direction": "LONG" if float(p.qty) > 0 else "SHORT",
                "size": abs(float(p.qty)),
                "entry_price": float(p.avg_entry_price),
                "current_price": float(p.current_price),
                "unrealized_pnl": float(p.unrealized_pl),
            }
            for p in positions
        ]
