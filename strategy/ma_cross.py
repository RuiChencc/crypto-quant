# -*- coding: utf-8 -*-
"""
示例策略：双均线交叉（MA Cross）
- 短期均线上穿长期均线 -> 买入信号
- 短期均线下穿长期均线 -> 卖出信号
"""
import pandas as pd
from strategy.base import StrategyBase


class MACrossStrategy(StrategyBase):
    """双均线交叉策略"""

    name = "ma_cross"

    def __init__(self, params=None):
        super().__init__(params)
        self.params.setdefault("short_window", 10)
        self.params.setdefault("long_window", 30)

    def generate_signal(self, df):
        short_win = self.params["short_window"]
        long_win = self.params["long_window"]

        if len(df) < long_win + 1:
            return 0  # 数据不足

        # 计算均线
        df = df.copy()
        df["ma_short"] = df["close"].rolling(short_win).mean()
        df["ma_long"] = df["close"].rolling(long_win).mean()

        prev_short = df["ma_short"].iloc[-2]
        prev_long = df["ma_long"].iloc[-2]
        curr_short = df["ma_short"].iloc[-1]
        curr_long = df["ma_long"].iloc[-1]

        # 金叉 / 死叉
        if prev_short <= prev_long and curr_short > curr_long:
            return 1  # 买入
        if prev_short >= prev_long and curr_short < curr_long:
            return -1  # 卖出
        return 0  # 持有
