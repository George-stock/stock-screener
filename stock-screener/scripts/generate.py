"""
US Stock Screener - データ生成スクリプト
全US市場（NASDAQ/NYSE上場銘柄）を対象にRS Ratingを計算して
data.json と universe.json を生成する。

データソース:
  - 銘柄リスト: NASDAQ API（無料・全市場）
  - 価格データ: yfinance（無料）
  - EPS加速: yfinance 四半期決算データ
"""

import json, os, sys, time, datetime, warnings, requests
from pathlib import Path

warnings.filterwarnings("ignore")

OUTPUT_DIR    = Path(__file__).parent.parent / "docs"
DATA_JSON     = OUTPUT_DIR / "data.json"
UNIVERSE_JSON = OUTPUT_DIR / "universe.json"

SCREENING_SUMMARY = "前日比≥+5% | 株価$0.75〜300 | 平均出来高≥50万株 | 売買代金≥$1M | 出来高≥平均(RelVol≥1) | 銘柄RS≥60 | 52W安値≥+30%"
KEEP_DAYS  = 14
TREND_DAYS = 28
HV_MONTHS  = 3

try:
    import pandas as pd
    import numpy as np
    import yfinance as yf
    print("✅ ライブラリ読み込み完了")
except ImportError as e:
    print(f"❌ ライブラリ不足: {e}")
    print("pip install yfinance pandas numpy requests")
    sys.exit(1)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 全US市場銘柄リスト取得
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def fetch_all_tickers() -> list[dict]:
    """NASDAQ APIから全上場銘柄を取得する。"""
    print("全US市場銘柄リスト取得中...")
    url = "https://api.nasdaq.com/api/screener/stocks?tableonly=true&limit=10000&exchange=nasdaq|nyse|amex"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers, timeout=30)
        data = r.json()
        rows = data["data"]["table"]["rows"]
        tickers = []
        for row in rows:
            sym = row.get("symbol", "").strip()
            if not sym or "/" in sym or "^" in sym:
                continue
            tickers.append({
                "ticker": sym,
                "company": row.get("name", ""),
                "sector": row.get("sector", ""),
                "industry": row.get("industry", ""),
                "country": "USA",
                "market_cap": row.get("marketCap", ""),
            })
        print(f"  → {len(tickers)} 銘柄取得")
        return tickers
    except Exception as e:
        print(f"  NASDAQ API失敗: {e} → フォールバック使用")
        return fetch_fallback_tickers()


def fetch_fallback_tickers() -> list[dict]:
    """フォールバック: Wikipedia からS&P500+NASDAQ100を取得。"""
    tickers = []
    try:
        sp500 = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")[0]
        for _, r in sp500.iterrows():
            tickers.append({"ticker": r["Symbol"].replace(".", "-"), "company": r["Security"],
                            "sector": r["GICS Sector"], "industry": r["GICS Sub-Industry"],
                            "country": "USA", "market_cap": ""})
    except Exception:
        pass
    try:
        ndx = pd.read_html("https://en.wikipedia.org/wiki/Nasdaq-100")[4]
        existing = {t["ticker"] for t in tickers}
        for _, r in ndx.iterrows():
            sym = str(r.get("Ticker", r.get("Symbol", ""))).replace(".", "-")
            if sym and sym not in existing:
                tickers.append({"ticker": sym, "company": r.get("Company", ""),
                                "sector": "", "industry": "", "country": "USA", "market_cap": ""})
    except Exception:
        pass
    print(f"  → フォールバック: {len(tickers)} 銘柄")
    return tickers


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# RS Rating 計算
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def calc_rs_raw(prices: pd.Series) -> float:
    if len(prices) < 252:
        return float("nan")
    p = prices.dropna()
    if len(p) < 252:
        return float("nan")
    try:
        q1 = p.iloc[-1]   / p.iloc[-64]  - 1
        q2 = p.iloc[-64]  / p.iloc[-127] - 1
        q3 = p.iloc[-127] / p.iloc[-190] - 1
        q4 = p.iloc[-190] / p.iloc[-253] - 1
        return 0.4 * q1 + 0.2 * q2 + 0.2 * q3 + 0.2 * q4
    except Exception:
        return float("nan")


def rs_raw_to_rating(series: pd.Series) -> pd.Series:
    rank = series.rank(pct=True, na_option="keep")
    return (rank * 98 + 1).clip(1, 99).round().astype("Int64")


def industry_rs_grade(rank: int, total: int) -> str:
    pct = rank / total
    if pct <= 0.21: return "A"
    if pct <= 0.42: return "B"
    if pct <= 0.63: return "C"
    if pct <= 0.84: return "D"
    return "E"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 価格データ一括取得 + RS計算
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def fetch_prices_and_calc_rs(ticker_info: list[dict]) -> pd.DataFrame:
    """全銘柄の価格を取得してRS Ratingを計算する。"""
    all_tickers = [t["ticker"] for t in ticker_info]
    info_map = {t["ticker"]: t for t in ticker_info}

    print(f"価格データ取得中（{len(all_tickers)}銘柄）...")
    batch_size = 500
    closes_all = {}

    for i in range(0, len(all_tickers), batch_size):
        batch = all_tickers[i:i+batch_size]
        print(f"  バッチ {i//batch_size+1}/{(len(all_tickers)-1)//batch_size+1} ({len(batch)}銘柄)...")
        try:
            raw = yf.download(batch, period="14mo", auto_adjust=True,
                              progress=False, threads=True)
            if raw.empty:
                continue
            if isinstance(raw.columns, pd.MultiIndex):
                close = raw["Close"]
            else:
                close = raw[["Close"]] if "Close" in raw else raw
            for t in batch:
                if t in close.columns:
                    closes_all[t] = close[t].dropna()
        except Exception as e:
            print(f"    バッチエラー: {e}")
        time.sleep(2)

    print(f"  → {len(closes_all)} 銘柄の価格取得完了")

    # RS計算
    print("RS Rating 計算中...")
    rs_raws = {}
    today_prices = {}
    prev_prices = {}
    volumes = {}
    avg_volumes = {}

    for ticker, prices in closes_all.items():
        rs_raws[ticker] = calc_rs_raw(prices)
        if len(prices) >= 2:
            today_prices[ticker] = float(prices.iloc[-1])
            prev_prices[ticker]  = float(prices.iloc[-2])

    rs_series  = pd.Series(rs_raws)
    rs_ratings = rs_raw_to_rating(rs_series)

    # 出来高データ取得（スクリーニング用）
    print("出来高データ取得中...")
    for i in range(0, len(all_tickers), batch_size):
        batch = all_tickers[i:i+batch_size]
        try:
            raw = yf.download(batch, period="3mo", auto_adjust=True,
                              progress=False, threads=True)
            if raw.empty:
                continue
            if isinstance(raw.columns, pd.MultiIndex):
                vol = raw["Volume"]
            else:
                vol = raw[["Volume"]] if "Volume" in raw else None
            if vol is None:
                continue
            for t in batch:
                if t in vol.columns:
                    v = vol[t].dropna()
                    if len(v) >= 2:
                        volumes[t]     = float(v.iloc[-1])
                        avg_volumes[t] = float(v.iloc[-63:].mean()) if len(v) >= 63 else float(v.mean())
        except Exception:
            pass
        time.sleep(1)

    # Industry RS計算
    print("Industry RS 計算中...")
    rows = []
    for ticker, info in info_map.items():
        rs = rs_ratings.get(ticker)
        price = today_prices.get(ticker)
        prev  = prev_prices.get(ticker)
        if rs is None or pd.isna(rs) or price is None:
            continue
        rows.append({
            "Ticker":    ticker,
            "Company":   info.get("company", ""),
            "Sector":    info.get("sector", ""),
            "Industry":  info.get("industry", ""),
            "Country":   info.get("country", "USA"),
            "Price":     round(price, 2),
            "Change":    f"{(price-prev)/prev*100:.2f}%" if prev else "—",
            "RS Rating": int(rs),
            "Avg Volume": avg_volumes.get(ticker),
            "Rel Volume": round(volumes.get(ticker, 0) / avg_volumes.get(ticker, 1), 2) if avg_volumes.get(ticker) else None,
            "_change_pct": (price - prev) / prev if prev else 0,
            "_price": price,
            "_avg_vol": avg_volumes.get(ticker, 0),
            "_vol": volumes.get(ticker, 0),
        })

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    # Industry RSを計算
    if "Industry" in df.columns and "RS Rating" in df.columns:
        ind_rs_map = (
            df[df["Industry"] != ""].groupby("Industry")["RS Rating"]
            .mean().rank(ascending=False).astype(int)
        )
        df["Industry RS"] = df["Industry"].map(ind_rs_map)

    return df


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# スクリーニングフィルタ
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    """スクリーニング条件を適用する。"""
    df = df.copy()
    df = df[df["_change_pct"] >= 0.05]           # 前日比+5%以上
    df = df[df["_price"].between(0.75, 300)]      # 株価$0.75-300
    df = df[df["_avg_vol"] >= 500000]             # 平均出来高50万株以上
    df = df[df["_price"] * df["_vol"] >= 1000000] # 売買代金$1M以上
    df = df[df["Rel Volume"].fillna(0) >= 1]       # RelVol >= 1
    df = df[df["RS Rating"] >= 60]                # RS >= 60
    df = df.sort_values("RS Rating", ascending=False).reset_index(drop=True)
    df.index = df.index + 1
    df.insert(0, "No.", df.index)
    return df


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# EPS加速判定
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def calc_eps_accel(tickers: list[str]) -> dict:
    result = {}
    for ticker in tickers[:100]:  # 上位100銘柄のみ
        try:
            t = yf.Ticker(ticker)
            qe = t.quarterly_income_stmt
            if qe is None or qe.empty:
                continue
            eps_rows = [r for r in qe.index if "Net Income" in str(r)]
            if not eps_rows:
                continue
            eps = qe.loc[eps_rows[0]].dropna()
            if len(eps) < 2:
                continue
            q0 = float(eps.iloc[0])
            q1 = float(eps.iloc[1])
            if q1 != 0:
                yoy0 = (q0 - q1) / abs(q1) * 100
            elif q1 < 0 and q0 > q1:
                yoy0 = 100.0
            else:
                yoy0 = 0
            if len(eps) >= 4:
                q2 = float(eps.iloc[2])
                q3 = float(eps.iloc[3])
                yoy1 = (q1 - q2) / abs(q2) * 100 if q2 != 0 else 0
            else:
                yoy1 = 0
            accel = "Y" if yoy0 > yoy1 else "N"
            result[ticker] = {
                "eps_accel": accel,
                "eps_yoy_q0": round(yoy0, 1),
                "eps_yoy_q1": round(yoy1, 1),
                "rev_accel": "",
                "rev_yoy_q0": None,
                "rev_yoy_q1": None,
            }
        except Exception:
            pass
        time.sleep(0.05)
    return result


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Industry RS トレンド
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def build_industry_rs(df: pd.DataFrame, today: str) -> dict:
    if "RS Rating" not in df.columns or "Industry" not in df.columns:
        return {"date": today, "industry_rs": []}
    ind = (
        df[df["Industry"] != ""].groupby("Industry")
        .agg(rs=("RS Rating", "mean"), count=("RS Rating", "count"), sector=("Sector", "first"))
        .reset_index()
        .sort_values("rs", ascending=False)
        .reset_index(drop=True)
    )
    total = len(ind)
    rows = []
    for i, row in ind.iterrows():
        rank = i + 1
        rows.append({
            "rank": rank,
            "grade": industry_rs_grade(rank, total),
            "industry": row["Industry"],
            "sector": row["sector"],
            "rs": int(round(row["rs"])),
            "count": int(row["count"]),
        })
    return {"date": today, "industry_rs": rows}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HVC判定
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def build_hvc(tickers: list[str]) -> dict:
    print("HVC 判定中...")
    today = datetime.date.today()
    window_end   = today - datetime.timedelta(days=1)
    window_start = today - datetime.timedelta(days=HV_MONTHS * 30)
    rows = []

    for i in range(0, len(tickers), 100):
        batch = tickers[i:i+100]
        try:
            raw = yf.download(batch, period="1y", auto_adjust=True, progress=False, threads=True)
            if raw.empty:
                continue
            vol_df   = raw["Volume"] if isinstance(raw.columns, pd.MultiIndex) else raw[["Volume"]]
            close_df = raw["Close"]  if isinstance(raw.columns, pd.MultiIndex) else raw[["Close"]]
            open_df  = raw["Open"]   if isinstance(raw.columns, pd.MultiIndex) else raw[["Open"]]
            high_df  = raw["High"]   if isinstance(raw.columns, pd.MultiIndex) else raw[["High"]]

            for ticker in batch:
                if ticker not in vol_df.columns:
                    continue
                vols = vol_df[ticker].dropna()
                if len(vols) < 63:
                    continue
                max_idx  = vols.idxmax()
                max_date = max_idx.date() if hasattr(max_idx, "date") else max_idx
                if not (window_start <= max_date <= window_end):
                    continue
                pos = vols.index.get_loc(max_idx)
                if pos == 0:
                    continue
                close  = float(close_df[ticker].loc[max_idx])
                open_  = float(open_df[ticker].loc[max_idx])
                high   = float(high_df[ticker].loc[max_idx])
                prev_c = float(close_df[ticker].iloc[pos - 1])
                gap    = (open_ - prev_c) / prev_c * 100
                rng    = (close - open_) / (high - open_ + 0.0001) * 100
                hvc    = gap >= 10 and rng >= 75
                avg_v  = float(vols.iloc[-63:].mean())
                rel_v  = float(vols.loc[max_idx]) / avg_v if avg_v > 0 else 0
                latest = float(close_df[ticker].iloc[-1])
                since  = (latest - close) / close * 100
                rows.append({
                    "ticker": ticker, "industry": "", "type": "HVE",
                    "date": str(max_date), "hvc": hvc,
                    "gap": round(gap, 2), "close_range": round(rng, 1),
                    "relvol": round(rel_v, 1), "since": round(since, 2),
                    "volume": int(vols.loc[max_idx]), "market_cap": None,
                })
        except Exception:
            pass
        time.sleep(1)

    rows.sort(key=lambda r: r["date"], reverse=True)
    return {
        "meta": {
            "generated_at": datetime.datetime.now().astimezone().isoformat(),
            "window_start": str(window_start), "window_end": str(window_end),
            "months": HV_MONTHS, "count": len(rows),
            "count_hvc": sum(1 for r in rows if r["hvc"]),
        },
        "rows": rows,
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DataFrame → days形式
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def df_to_day(df: pd.DataFrame, today: str) -> dict:
    # 内部用カラムを除外
    export_df = df.drop(columns=[c for c in df.columns if c.startswith("_")], errors="ignore")
    columns = list(export_df.columns)
    rows = []
    for _, row in export_df.iterrows():
        r = []
        for col in columns:
            val = row[col]
            if isinstance(val, float) and pd.isna(val):
                r.append(None)
            elif hasattr(val, "item"):
                r.append(val.item())
            else:
                r.append(val)
        rows.append(r)
    return {"date": today, "columns": columns, "rows": rows}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# メイン
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def main():
    today = datetime.date.today().isoformat()
    now   = datetime.datetime.now().astimezone().isoformat()
    print(f"=== 生成開始: {now} ===")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 既存データ読み込み
    existing = {"days": [], "industry_trend": [], "high_volume": {}, "earnings_accel": {}}
    if DATA_JSON.exists():
        with open(DATA_JSON, encoding="utf-8") as f:
            existing = json.load(f)

    # 銘柄リスト取得
    ticker_info = fetch_all_tickers()

    # 価格取得 + RS計算
    df_all = fetch_prices_and_calc_rs(ticker_info)
    if df_all.empty:
        print("❌ データ取得失敗")
        sys.exit(1)

    # スクリーニング
    df_screen = apply_filters(df_all)
    print(f"スクリーニング通過: {len(df_screen)} 銘柄")

    # EPS加速
    tickers_screen = df_screen["Ticker"].tolist()
    print("EPS加速判定中...")
    eps_map = calc_eps_accel(tickers_screen)
    df_screen["EPS加速"] = df_screen["Ticker"].map(
        lambda t: "▲加速" if eps_map.get(t, {}).get("eps_accel") == "Y" else "—"
    )
    df_screen["売上加速"] = "—"
    df_screen["HV"] = ""

    # Industry RS トレンド
    ind_rs_today = build_industry_rs(df_all, today)

    # HVC判定
    hvc_data = build_hvc(tickers_screen)
    hvc_set  = {r["ticker"] for r in hvc_data["rows"]}
    df_screen["HV"] = df_screen["Ticker"].map(lambda t: "HV1" if t in hvc_set else "")

    # days更新
    days = [d for d in existing.get("days", []) if d["date"] != today]
    days.insert(0, df_to_day(df_screen, today))
    days = days[:KEEP_DAYS]

    trends = [t for t in existing.get("industry_trend", []) if t["date"] != today]
    trends.insert(0, ind_rs_today)
    trends = trends[:TREND_DAYS]

    # universe.json用（全銘柄RS）
    universe_tickers = {}
    for _, row in df_all.iterrows():
        t   = row.get("Ticker")
        rs  = row.get("RS Rating")
        irs = row.get("Industry RS")
        if t:
            universe_tickers[str(t)] = [
                int(rs)  if pd.notna(rs)  else None,
                int(irs) if pd.notna(irs) else None,
            ]

    # data.json書き出し
    data_out = {
        "generated_at": now,
        "screening_summary": SCREENING_SUMMARY,
        "days": days,
        "industry_trend": trends,
        "high_volume": hvc_data,
        "earnings_accel": {
            "meta": {
                "generated_at": now, "days": 60,
                "n_targets": len(tickers_screen), "n_eps_judged": len(eps_map),
                "n_rev_judged": 0, "n_rev_ready": 0,
            },
            "map": eps_map,
        },
    }
    with open(DATA_JSON, "w", encoding="utf-8") as f:
        json.dump(data_out, f, ensure_ascii=False, separators=(",", ":"))
    print(f"✅ data.json 書き出し完了")

    # universe.json書き出し
    uni_out = {"date": today, "generated_at": now, "tickers": universe_tickers}
    with open(UNIVERSE_JSON, "w", encoding="utf-8") as f:
        json.dump(uni_out, f, ensure_ascii=False, separators=(",", ":"))
    print(f"✅ universe.json 書き出し完了")
    print(f"=== 完了: {len(df_screen)}銘柄スクリーニング / {len(universe_tickers)}銘柄RS計算 ===")


if __name__ == "__main__":
    main()
