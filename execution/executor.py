# -*- coding: utf-8 -*-
"""
执行层 - 参考 freqtrade/exchange + freqtradebot.py 架构
支持模拟盘（sandbox）/ 实盘下单，仓位管理，订单状态跟踪
"""
import time
import ccxt


class Executor:
    """交易执行器"""

    def __init__(self, exchange=None, symbol="BTC/USDT", dry_run=True, params=None):
        """
        :param exchange: ccxt exchange 实例（来自 MarketData）
        :param symbol: 交易对
        :param dry_run: True=模拟盘, False=实盘
        :param params: 附加参数（仓位比例等）
        """
        self.exchange = exchange
        self.symbol = symbol
        self.dry_run = dry_run
        self.params = params or {}
        self.position = 0.0  # 当前持仓（币数）
        self.cash = self.params.get("initial_cash", 10000.0)  # 可用资金
        self.orders = []  # 订单历史

    def buy(self, amount_pct=1.0):
        """买入（按资金比例）"""
        if self.dry_run:
            return self._dry_run_order("buy", amount_pct)
        return self._live_order("buy", amount_pct)

    def sell(self, amount_pct=1.0):
        """卖出（按持仓比例）"""
        if self.dry_run:
            return self._dry_run_order("sell", amount_pct)
        return self._live_order("sell", amount_pct)

    def _dry_run_order(self, side, amount_pct):
        """模拟下单"""
        ticker = self.exchange.fetch_ticker(self.symbol)
        price = ticker["last"]
        if side == "buy":
            spend = self.cash * amount_pct
            amount = spend / price
            self.position += amount
            self.cash -= spend
        else:
            amount = self.position * amount_pct
            self.position -= amount
            self.cash += amount * price

        order = {
            "id": f"dry_{len(self.orders)+1}",
            "side": side,
            "symbol": self.symbol,
            "price": price,
            "amount": round(amount, 8),
            "time": time.time(),
            "status": "closed",
            "dry_run": True,
        }
        self.orders.append(order)
        return order

    def _live_order(self, side, amount_pct):
        """实盘下单（需 API key + 实盘权限）"""
        # 需要 exchange 配置 API key 才能实盘
        raise NotImplementedError("实盘下单需要配置交易所 API key，请先在 config 中配置")

    def get_balance(self):
        """获取账户余额"""
        return {
            "cash": round(self.cash, 2),
            "position": round(self.position, 8),
            "position_value": round(self.position * self._last_price(), 2),
            "total": round(self.cash + self.position * self._last_price(), 2),
        }

    def _last_price(self):
        ticker = self.exchange.fetch_ticker(self.symbol)
        return ticker["last"]

    def get_orders(self, limit=10):
        """获取最近订单"""
        return self.orders[-limit:][::-1]
