# -*- coding: utf-8 -*-
"""
数据层 - 基于 ccxt 统一交易所 API 获取加密 K 线数据
参考 freqtrade/data 架构（55k stars 开源加密量化框架）

支持: Binance / OKX / Bybit / Gate / Kraken 等 100+ 交易所
"""
import os
import time
import json
import pandas as pd
import ccxt


class MarketData:
    """加密市场数据获取器"""

    EXCHANGES = {
        "binance": ccxt.binance,
        "okx": ccxt.okx,
        "bybit": ccxt.bybit,
        "gate": ccxt.gate,
        "kraken": ccxt.kraken,
        "bitget": ccxt.bitget,
    }

    def __init__(self, exchange="binance", sandbox=True, cache_dir=None):
        """初始化交易所连接"""
        if exchange not in self.EXCHANGES:
            raise ValueError(f"Unsupported exchange: {exchange}, choose from {list(self.EXCHANGES)}")

        ex_class = self.EXCHANGES[exchange]
        kwargs = {"enableRateLimit": True}
        if sandbox:
            kwargs["sandboxMode"] = True
        self.exchange = ex_class(kwargs)
        self.exchange_name = exchange
        self.cache_dir = cache_dir or os.path.join(os.path.dirname(__file__), "..", "data_cache")
        os.makedirs(self.cache_dir, exist_ok=True)

    def fetch_ohlcv(self, symbol="BTC/USDT", timeframe="1h", limit=500):
        """获取 K 线数据（OHLCV）"""
        cache_file = os.path.join(self.cache_dir, f"{self.exchange_name}_{symbol.replace('/', '_')}_{timeframe}.json")
        if os.path.exists(cache_file):
            cached = json.load(open(cache_file, encoding="utf-8"))
            if cached.get("symbol") == symbol and cached.get("timeframe") == timeframe:
                print(f"[data] 命中缓存: {cache_file}")
                df = pd.DataFrame(cached["data"], columns=["timestamp", "open", "high", "low", "close", "volume"])
                df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
                return df

        print(f"[data] 从 {self.exchange_name} 获取 {symbol} {timeframe} K线 x{limit}")
        raw = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        df = pd.DataFrame(raw, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")

        # 缓存
        json.dump({
            "symbol": symbol,
            "timeframe": timeframe,
            "fetched_at": time.time(),
            "data": raw,
        }, open(cache_file, "w", encoding="utf-8"))
        print(f"[data] 已缓存: {cache_file} ({len(df)} 行)")
        return df

    def fetch_ticker(self, symbol="BTC/USDT"):
        """获取实时行情"""
        ticker = self.exchange.fetch_ticker(symbol)
        return {
            "symbol": ticker["symbol"],
            "last": ticker["last"],
            "bid": ticker["bid"],
            "ask": ticker["ask"],
            "volume": ticker["baseVolume"],
            "change_24h_pct": ticker.get("percentage"),
            "timestamp": ticker["timestamp"],
        }

    def list_symbols(self, market_type="spot"):
        """列出交易所支持的交易对"""
        markets = self.exchange.load_markets()
        symbols = [s for s in markets if markets[s].get("type") == market_type]
        return sorted(symbols)[:100]
