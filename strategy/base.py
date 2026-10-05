# -*- coding: utf-8 -*-
"""
策略层基类 - 参考 freqtrade/strategy/interface.py 架构
所有策略继承 StrategyBase，实现 generate_signal 接口
"""
import abc


class StrategyBase(abc.ABC):
    """策略基类"""

    name = "base"

    def __init__(self, params=None):
        self.params = params or {}
        self.signal_history = []

    @abc.abstractmethod
    def generate_signal(self, df):
        """生成交易信号
        :param df: DataFrame with columns [timestamp, open, high, low, close, volume]
        :return: int: 1=买入, -1=卖出, 0=持有
        """
        raise NotImplementedError

    def on_data(self, df):
        """数据到达回调（记录信号历史）"""
        signal = self.generate_signal(df)
        self.signal_history.append({"time": df.iloc[-1]["timestamp"], "signal": signal})
        return signal

    def describe(self):
        """策略描述"""
        return {
            "name": self.name,
            "params": self.params,
            "signal_count": len(self.signal_history),
        }
