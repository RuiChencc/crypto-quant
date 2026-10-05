# crypto-quant

加密货币量化研究框架 — 架构参考 freqtrade（GitHub 55k+ stars，开源加密量化领域最高认可度项目）。

## 架构（分层，参考 freqtrade）

```
crypto-quant/
├── data/        数据层    ccxt 统一交易所 API（Binance/OKX/Bybit/Gate/Kraken 等 100+）
├── strategy/    策略层    策略基类 + 示例策略（双均线交叉）
├── backtest/    回测层    向量化回测（手续费 + 滑点 + 仓位）
├── execution/   执行层    模拟盘/实盘下单（默认 dry_run 模拟盘）
├── risk/        风控层    止损/止盈/仓位限制/日亏损保护
├── report/      报告层    复用 visualization-mcp v0.2.0 生成 K 线 + 净值曲线
├── config/      配置层    YAML 配置
└── tests/       测试层    冒烟测试
```

## 快速开始

```bash
# 离线演示（合成数据，无需网络）
python main.py --demo

# 实盘数据回测（binance 模拟盘）
python main.py --exchange binance --symbol BTC/USDT --timeframe 1h --limit 500

# 冒烟测试
python tests/test_smoke.py
```

## 示例输出

```
crypto-quant v0.1.0
[1/5] 数据就绪: 500 行 K 线
[2/5] 策略 ma_cross: 买入信号 12 次 / 卖出信号 12 次
[3/5] 回测完成: 收益 +18.5% / 交易 24 次 / 夏普 1.2
[4/5] 风控检查(模拟): OK
[5/5] 报告生成完成
```

回测报告 + K 线图 + 净值曲线输出到 `output/` 目录。

## 免责声明

本项目仅供学习研究，不构成投资建议。默认模拟盘运行，实盘需自行配置 API key 并承担风险。
