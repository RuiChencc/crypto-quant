# -*- coding: utf-8 -*-
"""
报告层 - 复用 visualization-mcp v0.2.0 生成图表
K 线图 + 组合图（净值曲线 + 信号）+ 回测报告
"""
import os
import sys
import json
import base64
import datetime

# 引用 visualization-mcp（复用已升级的图表库）
VIZ_PATH = "D:/OpenCode/.opencode-skills/visualization-mcp"
if VIZ_PATH not in sys.path:
    sys.path.insert(0, VIZ_PATH)


class ReportGenerator:
    """报告生成器（复用 visualization-mcp）"""

    def __init__(self, output_dir=None):
        self.output_dir = output_dir or os.path.join(os.path.dirname(__file__), "..", "output")
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_kline(self, df, title="K线图", save=True):
        """生成 K 线图（复用 visualization-mcp kline 类型）"""
        from visualization_server import visualize

        # 转换为 candles 格式
        candles = []
        for _, row in df.tail(100).iterrows():
            candles.append({
                "o": float(row["open"]),
                "h": float(row["high"]),
                "l": float(row["low"]),
                "c": float(row["close"]),
                "v": float(row["volume"]),
                "t": row["timestamp"].strftime("%Y-%m-%d"),
            })

        data = json.dumps({
            "candles": candles,
            "ma_periods": [5, 10, 20],
            "show_volume": True,
        }, ensure_ascii=False)
        result = visualize(data_str=data, chart_type="kline", title=title, style="dark")
        parsed = json.loads(result)
        b64 = parsed["image_base64"]

        if save:
            filename = f"kline_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            filepath = os.path.join(self.output_dir, filename)
            with open(filepath, "wb") as f:
                f.write(base64.b64decode(b64))
            print(f"[report] K线图已保存: {filepath}")
            return filepath
        return b64

    def generate_equity_curve(self, backtest_result, title="净值曲线", save=True):
        """生成净值曲线（复用 visualization-mcp combo 类型）"""
        from visualization_server import visualize

        equity_curve = backtest_result.get("equity_curve", [])
        dates = [p["timestamp"].strftime("%Y-%m-%d") if hasattr(p["timestamp"], "strftime") else str(p["timestamp"]) for p in equity_curve]
        values = [round(p["equity"], 2) for p in equity_curve]

        data = json.dumps({
            "series": [{"name": "净值", "data": values}],
            "x_labels": dates,
        }, ensure_ascii=False)
        result = visualize(data_str=data, chart_type="line", title=title, style="dark")
        parsed = json.loads(result)
        b64 = parsed["image_base64"]

        if save:
            filename = f"equity_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            filepath = os.path.join(self.output_dir, filename)
            with open(filepath, "wb") as f:
                f.write(base64.b64decode(b64))
            print(f"[report] 净值曲线已保存: {filepath}")
            return filepath
        return b64

    def generate_summary_report(self, backtest_result, save=True):
        """生成回测摘要报告"""
        report = {
            "生成时间": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "初始资金": backtest_result["initial_capital"],
            "最终权益": backtest_result["final_equity"],
            "总收益率": f"{backtest_result['total_return_pct']}%",
            "交易次数": backtest_result["trades"],
            "最大回撤": f"{backtest_result['max_drawdown_pct']}%",
            "夏普比率": backtest_result["sharpe_ratio"],
            "胜率": f"{backtest_result['win_rate_pct']}%",
        }
        text = "\n".join([f"{k}: {v}" for k, v in report.items()])
        print("[report] 回测摘要:")
        print(text)

        if save:
            filename = f"summary_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            filepath = os.path.join(self.output_dir, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(text)
            print(f"[report] 摘要已保存: {filepath}")
            return filepath
        return report
