# -*- coding: utf-8 -*-
"""
回测引擎 - 参考 freqtrade/optimize/backtesting.py 架构
向量化回测：支持买卖信号、手续费、滑点、仓位管理
"""
import pandas as pd
import numpy as np


class BacktestEngine:
    """向量化回测引擎"""

    def __init__(self, initial_capital=10000, fee_rate=0.001, slippage=0.0005):
        """
        :param initial_capital: 初始资金 (USD)
        :param fee_rate: 手续费率 (默认 0.1%)
        :param slippage: 滑点 (默认 0.05%)
        """
        self.initial_capital = initial_capital
        self.fee_rate = fee_rate
        self.slippage = slippage

    def run(self, df, signals):
        """
        执行回测
        :param df: DataFrame with [timestamp, open, high, low, close, volume]
        :param signals: list[int], 与 df 等长
        :return: 回测结果 dict
        """
        df = df.copy()
        df["signal"] = signals
        df["position"] = df["signal"].shift(1).fillna(0).cumsum().clip(-1, 1)  # 简化: 只做多

        # 计算收益（含手续费 + 滑点）
        df["returns"] = df["close"].pct_change().fillna(0)
        df["trade_cost"] = (df["signal"] != df["signal"].shift(1)).astype(float) * (self.fee_rate + self.slippage)
        df["strategy_returns"] = df["position"] * df["returns"] - df["trade_cost"]
        df["equity"] = self.initial_capital * (1 + df["strategy_returns"]).cumprod()

        # 绩效指标
        final_equity = df["equity"].iloc[-1]
        total_return = (final_equity / self.initial_capital - 1) * 100
        trades = int((df["signal"] != 0).sum())
        max_drawdown = self._calc_max_drawdown(df["equity"])
        sharpe = self._calc_sharpe(df["strategy_returns"])
        win_rate = self._calc_win_rate(df)

        return {
            "initial_capital": self.initial_capital,
            "final_equity": round(final_equity, 2),
            "total_return_pct": round(total_return, 2),
            "trades": trades,
            "max_drawdown_pct": round(max_drawdown, 2),
            "sharpe_ratio": round(sharpe, 2),
            "win_rate_pct": round(win_rate, 2),
            "equity_curve": df[["timestamp", "equity"]].to_dict(orient="records"),
        }

    @staticmethod
    def _calc_max_drawdown(equity):
        peak = equity.cummax()
        drawdown = (equity - peak) / peak
        return drawdown.min() * -100

    @staticmethod
    def _calc_sharpe(returns, annualization=365):
        if returns.std() == 0:
            return 0
        return returns.mean() / returns.std() * np.sqrt(annualization)

    @staticmethod
    def _calc_win_rate(df):
        trades = df[df["signal"] != 0]
        if trades.empty:
            return 0
        wins = trades[trades["returns"] > 0]
        return len(wins) / len(trades) * 100
