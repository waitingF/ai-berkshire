#!/usr/bin/env python3
"""常总战术数据工具 — 量价/均线/板块趋势，供 changzong-ask skill 调用。

零外部依赖（仅 stdlib），通过 Yahoo Finance 获取日线数据。

用法：
    python3 tools/changzong_data.py scan NVDA                    # 个股战术扫描
    python3 tools/changzong_data.py scan NVDA --sector SMH       # 附带板块ETF
    python3 tools/changzong_data.py sector SMH SOXX QQQ           # 批量板块扫描
    python3 tools/changzong_data.py macro                        # 宏观情绪指标
    python3 tools/changzong_data.py scan 600519 --market cn      # A股（600519.SS）
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timedelta
from typing import Any


def _fetch_chart(ticker: str, days: int = 280) -> list[dict] | None:
    """Yahoo Finance 日线 OHLCV。"""
    end_ts = int(datetime.now().timestamp())
    start_ts = int((datetime.now() - timedelta(days=days)).timestamp())
    url = (
        f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
        f"?period1={start_ts}&period2={end_ts}&interval=1d"
    )
    try:
        result = subprocess.run(
            ["/usr/bin/curl", "-s", "-H", "User-Agent: Mozilla/5.0", url],
            capture_output=True,
            text=True,
            timeout=20,
        )
        if result.returncode != 0 or not result.stdout.strip():
            return None
        data = json.loads(result.stdout)
        chart = data.get("chart", {}).get("result", [{}])[0]
        timestamps = chart.get("timestamp") or []
        quote = chart.get("indicators", {}).get("quote", [{}])[0]
        rows: list[dict] = []
        for i, ts in enumerate(timestamps):
            c = _at(quote.get("close"), i)
            o = _at(quote.get("open"), i)
            h = _at(quote.get("high"), i)
            l = _at(quote.get("low"), i)
            v = _at(quote.get("volume"), i)
            if c is None or v is None:
                continue
            rows.append(
                {
                    "date": datetime.fromtimestamp(ts).strftime("%Y-%m-%d"),
                    "open": float(o or c),
                    "high": float(h or c),
                    "low": float(l or c),
                    "close": float(c),
                    "volume": float(v),
                }
            )
        return rows if len(rows) >= 30 else None
    except (json.JSONDecodeError, KeyError, IndexError, ValueError):
        return None


def _at(arr: list | None, i: int):
    if not arr or i >= len(arr):
        return None
    return arr[i]


def _ma(values: list[float], period: int) -> float | None:
    if len(values) < period:
        return None
    return sum(values[-period:]) / period


def _normalize_cn_ticker(code: str) -> str:
    code = code.strip().upper().replace(".SH", "").replace(".SZ", "")
    if code.endswith(".SS") or code.endswith(".HK"):
        return code
    if code.startswith(("6", "9", "5")):
        return f"{code}.SS"
    if code.startswith(("0", "3", "2", "1")):
        return f"{code}.SZ"
    return code


def _pct(a: float, b: float) -> float:
    if b == 0:
        return 0.0
    return (a - b) / b * 100


def analyze_prices(ticker: str, prices: list[dict]) -> dict[str, Any]:
    """常总框架所需的技术信号。"""
    closes = [p["close"] for p in prices]
    volumes = [p["volume"] for p in prices]
    latest = prices[-1]
    close = latest["close"]

    ma5 = _ma(closes, 5)
    ma20 = _ma(closes, 20)
    ma60 = _ma(closes, 60)
    ma120 = _ma(closes, 120) if len(closes) >= 120 else None

    vol_5 = sum(volumes[-5:]) / 5
    vol_20 = sum(volumes[-20:]) / 20
    vol_ratio = vol_5 / vol_20 if vol_20 else 0

    # 近7日最大量（五日线战法：巨量 ≥ 均量1.45倍，这里用20日均量基准）
    peak_vol_7d = max(volumes[-7:])
    mega_vol = peak_vol_7d >= vol_20 * 1.45 if vol_20 else False

    # 连续3日放量（相对20日均量 > 1.0）
    vol_surge_3d = all(v > vol_20 for v in volumes[-3:]) if vol_20 else False

    # 55% 法则：最近量 / 近20日峰值量
    peak_vol_20 = max(volumes[-20:])
    vol_55_ratio = latest["volume"] / peak_vol_20 if peak_vol_20 else 0
    vol_55_ok = vol_55_ratio >= 0.55

    # 52周高低（用可用窗口）
    window = prices[-252:] if len(prices) >= 252 else prices
    high_52w = max(p["high"] for p in window)
    low_52w = min(p["low"] for p in window)
    dist_from_low = _pct(close, low_52w)
    dist_from_high = _pct(close, high_52w)

    # 五日线持有底线：收盘 >= MA5 * (1 - 7.5%)
    ma5_floor = ma5 * 0.925 if ma5 else None
    above_ma5_floor = close >= ma5_floor if ma5_floor else None

    # 120日线趋势
    above_ma120 = close > ma120 if ma120 else None
    ma120_slope = None
    if ma120 and len(closes) >= 130:
        ma120_prev = sum(closes[-130:-10]) / 120
        ma120_slope = _pct(ma120, ma120_prev)

    # 板块/个股30日涨跌
    pct_5d = _pct(close, closes[-6]) if len(closes) >= 6 else None
    pct_20d = _pct(close, closes[-21]) if len(closes) >= 21 else None
    pct_60d = _pct(close, closes[-61]) if len(closes) >= 61 else None

    # 五日线战法入场三条件
    above_ma5 = close > ma5 if ma5 else False
    wuxian_entry = above_ma5 and vol_surge_3d and mega_vol

    # 低量势：地量判断（近5日均量 < 近60日均量 * 0.7）
    vol_60 = sum(volumes[-60:]) / 60 if len(volumes) >= 60 else vol_20
    low_volume = vol_5 < vol_60 * 0.7 if vol_60 else False

    # 势：高低点抬升（近20日低点 > 前20日低点）
    if len(prices) >= 40:
        low_recent = min(p["low"] for p in prices[-20:])
        low_prior = min(p["low"] for p in prices[-40:-20])
        trend_up = low_recent > low_prior
    else:
        trend_up = None

    signals = {
        "五日线战法": {
            "站上5日线": above_ma5,
            "连续3日放量": vol_surge_3d,
            "7日内巨量(≥20日均量1.45x)": mega_vol,
            "三条件齐备": wuxian_entry,
            "持有底线(MA5×92.5%)": round(ma5_floor, 2) if ma5_floor else None,
            "在持有底线之上": above_ma5_floor,
        },
        "120日线生命线": {
            "当前价": round(close, 2),
            "MA120": round(ma120, 2) if ma120 else None,
            "站上120日线": above_ma120,
            "MA120斜率(60日)": round(ma120_slope, 2) if ma120_slope is not None else None,
        },
        "55%量能法则": {
            "今日量/20日峰值": round(vol_55_ratio, 2),
            "趋势仍在(≥55%)": vol_55_ok,
        },
        "行业-低-势-量": {
            "距52周低点": f"+{dist_from_low:.1f}%",
            "距52周高点": f"{dist_from_high:.1f}%",
            "地量(5日均<60日均70%)": low_volume,
            "势-高低点抬升": trend_up,
            "站稳60日线": close > ma60 if ma60 else None,
        },
        "3221参考": {
            "5日/20日量比": round(vol_ratio, 2),
            "20日涨幅": round(pct_20d, 1) if pct_20d is not None else None,
            "60日涨幅": round(pct_60d, 1) if pct_60d is not None else None,
        },
    }

    return {
        "ticker": ticker,
        "as_of": latest["date"],
        "close": round(close, 2),
        "ma5": round(ma5, 2) if ma5 else None,
        "ma20": round(ma20, 2) if ma20 else None,
        "ma60": round(ma60, 2) if ma60 else None,
        "ma120": round(ma120, 2) if ma120 else None,
        "pct_5d": round(pct_5d, 2) if pct_5d is not None else None,
        "pct_20d": round(pct_20d, 2) if pct_20d is not None else None,
        "signals": signals,
        "data_points": len(prices),
    }


def cmd_scan(ticker: str, sector: str | None, market: str, json_out: bool):
    yf_ticker = _normalize_cn_ticker(ticker) if market == "cn" else ticker.upper()
    prices = _fetch_chart(yf_ticker)
    if not prices:
        print(f"❌ 无法获取 {yf_ticker} 价格数据（Yahoo Finance）")
        print("   提示：A股请用 --market cn；港股用 0700.HK；检查代码是否正确")
        sys.exit(1)

    result = analyze_prices(yf_ticker, prices)

    if sector:
        sec_ticker = sector.upper()
        sec_prices = _fetch_chart(sec_ticker)
        if sec_prices:
            sec = analyze_prices(sec_ticker, sec_prices)
            result["sector"] = {
                "ticker": sec_ticker,
                "as_of": sec["as_of"],
                "close": sec["close"],
                "pct_20d": sec["pct_20d"],
                "above_ma120": sec["signals"]["120日线生命线"]["站上120日线"],
                "trend_up": sec["signals"]["行业-低-势-量"]["势-高低点抬升"],
                "板块服从": _sector_obey(sec),
            }
        else:
            result["sector"] = {"ticker": sec_ticker, "error": "无法获取板块数据"}

    if json_out:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    _print_scan(result)


def _sector_obey(sec: dict) -> str:
    above = sec["signals"]["120日线生命线"]["站上120日线"]
    trend = sec["signals"]["行业-低-势-量"]["势-高低点抬升"]
    pct = sec.get("pct_20d") or 0
    if above and trend and pct > 0:
        return "✅ 板块上升趋势，可谈个股"
    if not above or (pct is not None and pct < -5):
        return "❌ 板块走弱/破120日线，个股难独善其身"
    return "⚠️ 板块震荡，宜观察或小仓试探"


def _print_scan(result: dict):
    print("=" * 64)
    print(f"常总战术扫描: {result['ticker']}  数据截止: {result['as_of']}")
    print("=" * 64)
    print(f"  收盘价: {result['close']}")
    print(f"  均线: MA5={result['ma5']}  MA20={result['ma20']}  "
          f"MA60={result['ma60']}  MA120={result['ma120']}")
    print(f"  涨跌: 5日{result['pct_5d']:+.1f}%  20日{result['pct_20d']:+.1f}%")
    print()

    if "sector" in result and "error" not in result["sector"]:
        s = result["sector"]
        print(f"  【板块】{s['ticker']}  20日{s['pct_20d']:+.1f}%  "
              f"120日线上={'是' if s['above_ma120'] else '否'}  → {s['板块服从']}")
        print()

    for block, items in result["signals"].items():
        print(f"  --- {block} ---")
        for k, v in items.items():
            mark = ""
            if isinstance(v, bool):
                mark = " ✅" if v else " ❌"
                v = "是" if v else "否"
            print(f"    {k}: {v}{mark}")
        print()

    print("  数据来源: Yahoo Finance 日线")
    print("  ⚠️ 分析须结合 WebSearch 获取最新宏观/新闻/财报")


def cmd_sector(tickers: list[str], json_out: bool):
    rows = []
    for t in tickers:
        yf = t.upper()
        prices = _fetch_chart(yf)
        if not prices:
            rows.append({"ticker": yf, "error": "无数据"})
            continue
        a = analyze_prices(yf, prices)
        rows.append(
            {
                "ticker": yf,
                "close": a["close"],
                "pct_20d": a["pct_20d"],
                "above_ma120": a["signals"]["120日线生命线"]["站上120日线"],
                "vol_55_ok": a["signals"]["55%量能法则"]["趋势仍在(≥55%)"],
                "trend_up": a["signals"]["行业-低-势-量"]["势-高低点抬升"],
            }
        )

    if json_out:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return

    print("=" * 64)
    print(f"板块/指数扫描  数据截止: {datetime.now().strftime('%Y-%m-%d')}")
    print("=" * 64)
    for r in rows:
        if "error" in r:
            print(f"  {r['ticker']:<8} ❌ {r['error']}")
            continue
        ma = "120上" if r["above_ma120"] else "120下"
        trend = "势↑" if r["trend_up"] else "势↓"
        vol = "量✓" if r["vol_55_ok"] else "量弱"
        print(f"  {r['ticker']:<8} {r['close']:<10} 20日{r['pct_20d']:+6.1f}%  {ma} {trend} {vol}")


def cmd_macro(json_out: bool):
    """宏观情绪快照：VIX、主要指数、利率代理。"""
    macro_tickers = {
        "^VIX": "VIX恐慌指数",
        "SPY": "标普500",
        "QQQ": "纳斯达克100",
        "IWM": "罗素2000",
        "TLT": "20年美债ETF(利率反向)",
        "UUP": "美元指数",
        "GLD": "黄金",
        "CL=F": "WTI原油",
    }
    rows = []
    for sym, label in macro_tickers.items():
        prices = _fetch_chart(sym, days=60)
        if not prices:
            rows.append({"symbol": sym, "label": label, "error": "无数据"})
            continue
        a = analyze_prices(sym, prices)
        vix_note = ""
        if sym == "^VIX" and a["close"]:
            if a["close"] > 30:
                vix_note = "极端恐慌区"
            elif a["close"] > 20:
                vix_note = "恐慌升温"
            elif a["close"] < 15:
                vix_note = "低波动/偏贪婪"
            else:
                vix_note = "中性"
        rows.append(
            {
                "symbol": sym,
                "label": label,
                "close": a["close"],
                "pct_5d": a["pct_5d"],
                "pct_20d": a["pct_20d"],
                "note": vix_note,
            }
        )

    if json_out:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return

    print("=" * 64)
    print(f"宏观情绪快照  数据截止: {datetime.now().strftime('%Y-%m-%d')}")
    print("=" * 64)
    for r in rows:
        if "error" in r:
            print(f"  {r['label']:<20} ❌")
            continue
        extra = f"  ({r['note']})" if r.get("note") else ""
        print(f"  {r['label']:<20} {r['close']:<10} 5日{r['pct_5d']:+5.1f}%  "
              f"20日{r['pct_20d']:+5.1f}%{extra}")
    print()
    print("  ⚠️ 利率/流动性/政策须 WebSearch 补充最新信息")


def main():
    parser = argparse.ArgumentParser(description="常总战术数据工具")
    parser.add_argument("--json", action="store_true", help="JSON 输出")
    sub = parser.add_subparsers(dest="command")

    p_scan = sub.add_parser("scan", help="个股战术扫描")
    p_scan.add_argument("ticker", help="股票代码，如 NVDA / 600519 / 0700.HK")
    p_scan.add_argument("--sector", help="板块ETF，如 SMH / SOXX / KWEB")
    p_scan.add_argument("--market", choices=["us", "cn", "hk"], default="us",
                        help="市场类型，A股用 cn")

    p_sec = sub.add_parser("sector", help="批量板块/指数扫描")
    p_sec.add_argument("tickers", nargs="+", help="代码列表")

    sub.add_parser("macro", help="宏观情绪快照")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "scan":
        cmd_scan(args.ticker, args.sector, args.market, args.json)
    elif args.command == "sector":
        cmd_sector(args.tickers, args.json)
    elif args.command == "macro":
        cmd_macro(args.json)


if __name__ == "__main__":
    main()
