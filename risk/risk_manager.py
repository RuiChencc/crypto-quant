# -*- coding: utf-8 -*-
"""
风控层 - 参考 freqtrade/leverage + wallets.py 架构
止损 / 止盈 / 仓位限制 / 最大回撤保护
"""
import time


class RiskManager:
    """风险管理器"""

    def __init__(self, params=None):
        self.params = params or {}
        self.params.setdefault("max_position_pct", 0.3)     # 单笔最大仓位 30%
        self.params.setdefault("stop_loss_pct", 0.05)       # 止损 5%
        self.params.setdefault("take_profit_pct", 0.10)     # 止盈 10%
        self.params.setdefault("max_daily_loss_pct", 0.03)  # 日最大亏损 3%
        self.params.setdefault("max_open_trades", 5)        # 最大同时持仓数

        self.daily_pnl = 0.0
        self.day_start_time = time.time()
        self.open_trades = 0

    def check_order(self, side, amount_pct, position_value, total_equity):
        """
        下单前风控检查
        :return: (allowed: bool, reason: str)
        """
        # 仓位限制
        if side == "buy":
            new_position_value = position_value + amount_pct * total_equity
            if new_position_value / total_equity > self.params["max_position_pct"]:
                return False, f"仓位超限: {new_position_value/total_equity:.1%} > {self.params['max_position_pct']:.0%}"
        else:
            if position_value <= 0:
                return False, "无持仓可卖"

        # 持仓数限制
        if side == "buy" and self.open_trades >= self.params["max_open_trades"]:
            return False, f"持仓数超限: {self.open_trades} >= {self.params['max_open_trades']}"

        return True, "OK"

    def check_exit(self, entry_price, current_price):
        """
        持仓退出检查（止损 / 止盈）
        :return: (exit: bool, reason: str)
        """
        change = (current_price - entry_price) / entry_price

        if change <= -self.params["stop_loss_pct"]:
            return True, f"止损触发: {change:.1%}"
        if change >= self.params["take_profit_pct"]:
            return True, f"止盈触发: {change:.1%}"
        return False, "持有"

    def update_daily_pnl(self, pnl):
        """更新每日盈亏（日亏损保护）"""
        # 每日重置
        if time.time() - self.day_start_time > 86400:
            self.day_start_time = time.time()
            self.daily_pnl = 0.0
        self.daily_pnl += pnl

        if self.daily_pnl / 10000 <= -self.params["max_daily_loss_pct"]:
            return False, f"日亏损超限: {self.daily_pnl:.2f}"
        return True, "OK"

    def describe(self):
        """风控参数描述"""
        return dict(self.params)
