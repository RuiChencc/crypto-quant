# -*- coding: utf-8 -*-
"""crypto-quant 冒烟测试：模块导入 + 合成数据回测全链路"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import load_demo_data, generate_signals
from data.market_data import MarketData
from strategy.ma_cross import MACrossStrategy
from backtest.backtest import BacktestEngine
from risk.risk_manager import RiskManager
from report.report import ReportGenerator


def test_imports():
    assert MarketData and MACrossStrategy and BacktestEngine
    assert RiskManager and ReportGenerator
    print("[PASS] 模块导入 OK")


def test_backtest_pipeline():
    df = load_demo_data(limit=200)
    assert len(df) == 200
    assert list(df.columns) == ["timestamp", "open", "high", "low", "close", "volume"]

    strategy = MACrossStrategy()
    signals = generate_signals(strategy, df)
    assert len(signals) == 200

    engine = BacktestEngine(initial_capital=10000)
    result = engine.run(df, signals)
    for key in ["initial_capital", "final_equity", "total_return_pct", "trades",
                "max_drawdown_pct", "sharpe_ratio", "win_rate_pct"]:
        assert key in result, f"缺少字段: {key}"
    assert result["trades"] >= 0
    print(f"[PASS] 回测链路 OK: 收益 {result['total_return_pct']}% / 交易 {result['trades']} 次")


def test_risk():
    risk = RiskManager()
    allowed, reason = risk.check_order("buy", 0.1, 0, 10000)
    assert allowed and reason == "OK"
    # 仓位超限测试
    allowed, reason = risk.check_order("buy", 0.9, 0, 10000)
    assert not allowed
    print("[PASS] 风控检查 OK")


def test_strategy_signal():
    df = load_demo_data(limit=100, seed=7)
    strategy = MACrossStrategy()
    s = strategy.generate_signal(df)
    assert s in (1, -1, 0)
    print(f"[PASS] 策略信号 OK (最后信号: {s})")


if __name__ == "__main__":
    test_imports()
    test_strategy_signal()
    test_risk()
    test_backtest_pipeline()
    print()
    print("全部冒烟测试通过")
