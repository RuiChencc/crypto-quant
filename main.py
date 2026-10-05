# -*- coding: utf-8 -*-
"""
crypto-quant 主入口
数据获取 -> 策略信号 -> 回测 -> 风控 -> 报告（复用 visualization-mcp）

用法:
  python main.py                      # 实盘数据 + 回测
  python main.py --demo               # 离线演示（合成数据，无需网络）
  python main.py --symbol ETH/USDT --timeframe 4h --limit 1000
"""
import os
import sys
import argparse
import numpy as np
import pandas as pd

from data.market_data import MarketData
from strategy.ma_cross import MACrossStrategy
from backtest.backtest import BacktestEngine
from risk.risk_manager import RiskManager
from report.report import ReportGenerator


def load_demo_data(symbol="BTC/USDT", timeframe="1h", limit=500, seed=42):
    """生成合成 K 线数据（离线演示用，带趋势 + 波动）"""
    rng = np.random.default_rng(seed)
    n = limit
    # 随机游走 + 趋势
    drift = 0.0002
    returns = rng.normal(drift, 0.02, n)
    price = 30000 * np.exp(np.cumsum(returns))
    volume = rng.uniform(100, 1000, n)
    timestamps = pd.date_range(end=pd.Timestamp.now(), periods=n, freq="1h")

    df = pd.DataFrame({
        "timestamp": timestamps,
        "open": price * (1 + rng.normal(0, 0.005, n)),
        "high": price * (1 + np.abs(rng.normal(0.01, 0.005, n))),
        "low": price * (1 - np.abs(rng.normal(0.01, 0.005, n))),
        "close": price,
        "volume": volume,
    })
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    print(f"[demo] 合成数据: {symbol} {timeframe} x{len(df)} 行")
    return df


def generate_signals(strategy, df):
    """对每个 K 线生成信号（滚动窗口）"""
    signals = []
    for i in range(len(df)):
        signals.append(strategy.generate_signal(df.iloc[: i + 1]))
    return signals


def main():
    parser = argparse.ArgumentParser(description="crypto-quant")
    parser.add_argument("--demo", action="store_true", help="离线演示（合成数据）")
    parser.add_argument("--exchange", default="binance")
    parser.add_argument("--symbol", default="BTC/USDT")
    parser.add_argument("--timeframe", default="1h")
    parser.add_argument("--limit", type=int, default=500)
    args = parser.parse_args()

    print("=" * 50)
    print("crypto-quant v0.1.0")
    print("=" * 50)

    # 1. 数据层
    if args.demo:
        df = load_demo_data(args.symbol, args.timeframe, args.limit)
    else:
        md = MarketData(exchange=args.exchange, sandbox=True)
        df = md.fetch_ohlcv(args.symbol, args.timeframe, args.limit)
    print(f"[1/5] 数据就绪: {len(df)} 行 K 线")

    # 2. 策略层
    strategy = MACrossStrategy(params={"short_window": 10, "long_window": 30})
    signals = generate_signals(strategy, df)
    buy = signals.count(1)
    sell = signals.count(-1)
    print(f"[2/5] 策略 {strategy.name}: 买入信号 {buy} 次 / 卖出信号 {sell} 次")

    # 3. 回测层
    engine = BacktestEngine(initial_capital=10000)
    result = engine.run(df, signals)
    print(f"[3/5] 回测完成: 收益 {result['total_return_pct']}% / 交易 {result['trades']} 次 / 夏普 {result['sharpe_ratio']}")

    # 4. 风控层
    risk = RiskManager()
    allowed, reason = risk.check_order("buy", 0.1, 0, result["final_equity"])
    print(f"[4/5] 风控检查(模拟): {reason}")

    # 5. 报告层（复用 visualization-mcp v0.2.0）
    reporter = ReportGenerator()
    reporter.generate_summary_report(result)
    if not args.demo:
        reporter.generate_kline(df, title=f"{args.symbol} {args.timeframe} K线")
    reporter.generate_equity_curve(result, title=f"{args.symbol} 回测净值")
    print("[5/5] 报告生成完成")

    print()
    print("回测明细:")
    print(f"  初始资金 : {result['initial_capital']}")
    print(f"  最终权益 : {result['final_equity']}")
    print(f"  总收益率 : {result['total_return_pct']}%")
    print(f"  交易次数 : {result['trades']}")
    print(f"  最大回撤 : {result['max_drawdown_pct']}%")
    print(f"  夏普比率 : {result['sharpe_ratio']}")
    print(f"  胜率     : {result['win_rate_pct']}%")
    print()
    print("输出目录: output/")


if __name__ == "__main__":
    main()
