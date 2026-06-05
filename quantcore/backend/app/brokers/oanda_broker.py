"""
OANDA broker adapter — forex demo + live.
"""
from __future__ import annotations
import structlog
from app.brokers.base import BaseBroker
from app.core.config import settings

log = structlog.get_logger()


class OandaBroker(BaseBroker):
    name = "OANDA"

    def __init__(self):
        self._api = None
        self._account_id = settings.OANDA_ACCOUNT_ID

    async def connect(self):
        import oandapyV20
        import oandapyV20.endpoints.accounts as accounts
        env = "practice" if settings.OANDA_ENVIRONMENT == "practice" else "live"
        self._api = oandapyV20.API(access_token=settings.OANDA_ACCESS_TOKEN, environment=env)
        r = accounts.AccountSummary(self._account_id)
        self._api.request(r)
        log.info("oanda_connected", env=env, account=self._account_id)

    async def disconnect(self):
        self._api = None

    async def submit_bracket_order(
        self, instrument, direction, lot_size, entry_price, stop_loss, take_profit
    ) -> str:
        import oandapyV20.endpoints.orders as orders
        side_units = lot_size if direction == "LONG" else -lot_size
        data = {
            "order": {
                "type": "LIMIT",
                "instrument": instrument.replace("/", "_"),
                "units": str(side_units),
                "price": str(round(entry_price, 5)),
                "takeProfitOnFill": {"price": str(round(take_profit, 5))},
                "stopLossOnFill": {"price": str(round(stop_loss, 5))},
                "timeInForce": "GTC",
            }
        }
        r = orders.OrderCreate(self._account_id, data=data)
        self._api.request(r)
        return r.response["orderCreateTransaction"]["id"]

    async def cancel_pending_orders(self, account_id: str):
        import oandapyV20.endpoints.orders as orders
        r = orders.OrderList(self._account_id)
        self._api.request(r)
        for order in r.response.get("orders", []):
            cancel_r = orders.OrderCancel(self._account_id, orderID=order["id"])
            self._api.request(cancel_r)

    async def close_all_positions(self, account_id: str):
        import oandapyV20.endpoints.positions as positions
        r = positions.PositionList(self._account_id)
        self._api.request(r)
        for pos in r.response.get("positions", []):
            instrument = pos["instrument"]
            long_units = int(pos["long"]["units"])
            short_units = int(pos["short"]["units"])
            if long_units != 0:
                close_r = positions.PositionClose(
                    self._account_id, instrument, data={"longUnits": "ALL"}
                )
                self._api.request(close_r)
            if short_units != 0:
                close_r = positions.PositionClose(
                    self._account_id, instrument, data={"shortUnits": "ALL"}
                )
                self._api.request(close_r)

    async def tighten_trailing_stops(self, account_id: str, factor: float = 0.80):
        pass  # OANDA: modify trades with trailing stop distance

    async def get_open_position_count(self, account_id: str) -> int:
        import oandapyV20.endpoints.positions as positions
        if not self._api:
            return 0
        r = positions.PositionList(self._account_id)
        self._api.request(r)
        return len([p for p in r.response.get("positions", []) if
                     int(p["long"]["units"]) != 0 or int(p["short"]["units"]) != 0])

    async def get_account_equity(self, account_id: str) -> float:
        import oandapyV20.endpoints.accounts as accounts
        if not self._api:
            return 0.0
        r = accounts.AccountSummary(self._account_id)
        self._api.request(r)
        return float(r.response["account"]["NAV"])

    async def get_open_positions(self, account_id: str) -> list[dict]:
        import oandapyV20.endpoints.positions as positions
        if not self._api:
            return []
        r = positions.PositionList(self._account_id)
        self._api.request(r)
        result = []
        for pos in r.response.get("positions", []):
            for side, sign in (("long", 1), ("short", -1)):
                units = int(pos[side]["units"])
                if units != 0:
                    result.append({
                        "instrument": pos["instrument"],
                        "direction": "LONG" if sign == 1 else "SHORT",
                        "size": abs(units),
                        "entry_price": float(pos[side]["averagePrice"]),
                        "unrealized_pnl": float(pos[side]["unrealizedPL"]),
                    })
        return result
