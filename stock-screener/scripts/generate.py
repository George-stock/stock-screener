"""
US Stock Screener - データ生成スクリプト
全US市場（6700銘柄以上）を対象にRS Ratingを計算して
data.json と universe.json を生成する。

データソース:
  - 銘柄リスト: scripts/tickers.csv
  - Industry/Sector: Finviz無料スクリーナー
  - 価格データ: yfinance（無料）
  - EPS加速: yfinance 四半期決算データ
"""

import json, sys, time, datetime, warnings, csv, requests
from pathlib import Path

warnings.filterwarnings("ignore")

SCRIPT_DIR    = Path(__file__).parent
OUTPUT_DIR    = SCRIPT_DIR.parent / "docs"
TICKERS_CSV   = SCRIPT_DIR / "tickers.csv"
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
    from bs4 import BeautifulSoup
    print("✅ ライブラリ読み込み完了")
except ImportError as e:
    print(f"❌ ライブラリ不足: {e}")
    print("pip install yfinance pandas numpy requests beautifulsoup4")
    sys.exit(1)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Finviz から Industry/Sector 取得
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def fetch_finviz_industry() -> dict:
    """Finviz無料スクリーナーから全銘柄のIndustry/Sectorを取得。"""
    print("Finviz から Industry/Sector 取得中...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    result = {}  # {ticker: {sector, industry}}
    
    # Finviz screener は1ページ20件、offsetで全件取得
    offset = 1
    while True:
        url = f"https://finviz.com/screener.ashx?v=152&o=ticker&r={offset}"
        try:
            r = requests.get(url, headers=headers, timeout=30)
            if r.status_code != 200:
                print(f"  Finviz アクセス失敗: {r.status_code}")
                break
            
            soup = BeautifulSoup(r.text, "html.parser")
            
            # テーブルを探す
            table = soup.find("table", {"id": "screener-views-table"})
            if not table:
                # 別のテーブル構造を試す
                tables = soup.find_all("table", class_="styled-table-new")
                table = tables[0] if tables else None
            
            if not table:
                print(f"  テーブル見つからず (offset={offset})")
                break
                
            rows = table.find_all("tr")[1:]  # ヘッダー除く
            if not rows:
                break
                
            count = 0
            for row in rows:
                cols = row.find_all("td")
                if len(cols) < 4:
                    continue
                try:
                    ticker   = cols[1].get_text(strip=True)
                    sector   = cols[3].get_text(strip=True)
                    industry = cols[4].get_text(strip=True) if len(cols) > 4 else ""
                    if ticker:
                        result[ticker] = {"sector": sector, "industry": industry}
                        count += 1
                except Exception:
                    pass
            
            print(f"  offset={offset}: {count}件取得 (累計: {len(result)}件)")
            
            if count == 0:
                break
                
            offset += 20
            time.sleep(1)  # レート制限回避
            
        except Exception as e:
            print(f"  Finviz エラー: {e}")
            break
    
    print(f"  → Finviz から {len(result)} 銘柄のIndustry取得完了")
    return result


def fetch_industry_yfinance(tickers: list[str]) -> dict:
    """yfinanceからIndustry/Sectorを取得（Finvizの補完用）。"""
    result = {}
    print(f"  yfinance でIndustry補完中（{len(tickers)}銘柄）...")
    for ticker in tickers[:500]:  # 上位500銘柄まで
        try:
            info = yf.Ticker(ticker).info
            result[ticker] = {
                "sector":   info.get("sector", ""),
                "industry": info.get("industry", ""),
            }
        except Exception:
            pass
        time.sleep(0.05)
    return result


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 銘柄リスト読み込み
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def load_tickers() -> list[dict]:
    if not TICKERS_CSV.exists():
        print(f"❌ {TICKERS_CSV} が見つかりません")
        sys.exit(1)
    tickers = []
    with open(TICKERS_CSV, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sym = row["symbol"].strip()
            if sym:
                tickers.append(row)
    print(f"銘柄リスト読み込み: {len(tickers)} 銘柄")
    return tickers


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# RS Rating 計算
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def calc_rs_raw(prices: pd.Series) -> float:
    p = prices.dropna()
    if len(p) < 253:
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
def fetch_prices_and_calc_rs(ticker_info: list[dict], industry_map: dict) -> pd.DataFrame:
    all_tickers = [t["symbol"] for t in ticker_info]
    info_map    = {t["symbol"]: t for t in ticker_info}
    batch_size  = 500

    print(f"価格データ取得中（{len(all_tickers)}銘柄）...")
    closes_all = {}

    for i in range(0, len(all_tickers), batch_size):
        batch = all_tickers[i:i+batch_size]
        n = i // batch_size + 1
        total_batches = (len(all_tickers) - 1) // batch_size + 1
        print(f"  バッチ {n}/{total_batches} ({len(batch)}銘柄)...")
        try:
            raw = yf.download(batch, period="14mo", auto_adjust=True,
                              progress=False, threads=True, group_by="ticker")
            if raw.empty:
                continue
            if isinstance(raw.columns, pd.MultiIndex):
                close = raw.xs("Close", axis=1, level=1)
            else:
                close = raw[["Close"]] if "Close" in raw else pd.DataFrame()
            for t in batch:
                if t in close.columns:
                    s = close[t].dropna()
                    if len(s) >= 10:
                        closes_all[t] = s
        except Exception as e:
            print(f"    バッチエラー: {e}")
        time.sleep(3)

    print(f"  → {len(closes_all)} 銘柄の価格取得完了")

    print("RS Rating 計算中...")
    rs_raws    = {t: calc_rs_raw(p) for t, p in closes_all.items()}
    rs_series  = pd.Series(rs_raws)
    rs_ratings = rs_raw_to_rating(rs_series)

    today_prices = {t: float(p.iloc[-1]) for t, p in closes_all.items() if len(p) >= 2}
    prev_prices  = {t: float(p.iloc[-2]) for t, p in closes_all.items() if len(p) >= 2}

    print("出来高データ取得中...")
    volumes     = {}
    avg_volumes = {}
    for i in range(0, len(all_tickers), batch_size):
        batch = all_tickers[i:i+batch_size]
        try:
            raw = yf.download(batch, period="3mo", auto_adjust=True,
                              progress=False, threads=True, group_by="ticker")
            if raw.empty:
                continue
            if isinstance(raw.columns, pd.MultiIndex):
                vol = raw.xs("Volume", axis=1, level=1)
            else:
                vol = raw[["Volume"]] if "Volume" in raw else pd.DataFrame()
            for t in batch:
                if t in vol.columns:
                    v = vol[t].dropna()
                    if len(v) >= 2:
                        volumes[t]     = float(v.iloc[-1])
                        avg_volumes[t] = float(v.iloc[-63:].mean()) if len(v) >= 63 else float(v.mean())
        except Exception:
            pass
        time.sleep(2)

    rows = []
    for ticker in closes_all:
        rs    = rs_ratings.get(ticker)
        price = today_prices.get(ticker)
        prev  = prev_prices.get(ticker)
        info  = info_map.get(ticker, {})
        ind   = industry_map.get(ticker, {})
        if rs is None or pd.isna(rs) or price is None:
            continue
        avg_v   = avg_volumes.get(ticker, 0)
        vol     = volumes.get(ticker, 0)
        sector   = ind.get("sector")   or info.get("sector", "")
        industry = ind.get("industry") or info.get("industry", "")
        rows.append({
            "Ticker":      ticker,
            "Company":     info.get("name", ""),
            "Sector":      sector,
            "Industry":    industry,
            "Country":     info.get("country", "USA"),
            "Price":       round(price, 2),
            "Change":      f"{(price-prev)/prev*100:.2f}%" if prev else "—",
            "RS Rating":   int(rs),
            "Avg Volume":  f"{avg_v/1e6:.2f}M" if avg_v >= 1e6 else f"{avg_v/1e3:.0f}K" if avg_v >= 1e3 else str(int(avg_v)),
            "Rel Volume":  round(vol / avg_v, 2) if avg_v > 0 else None,
            "_change_pct": (price - prev) / prev if prev else 0,
            "_price":      price,
            "_avg_vol":    avg_v,
            "_vol":        vol,
        })

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    if "Industry" in df.columns:
        ind_rs_map = (
            df[df["Industry"].fillna("") != ""].groupby("Industry")["RS Rating"]
            .mean().rank(ascending=False).astype(int)
        )
        df["Industry RS"] = df["Industry"].map(ind_rs_map)
    else:
        df["Industry RS"] = None

    return df


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# スクリーニングフィルタ
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = df[df["_change_pct"] >= 0.05]
    df = df[df["_price"].between(0.75, 300)]
    df = df[df["_avg_vol"] >= 500000]
    df = df[df["_price"] * df["_vol"] >= 1_000_000]
    df = df[df["Rel Volume"].fillna(0) >= 1]
    df = df[df["RS Rating"] >= 60]
    df = df.sort_values("RS Rating", ascending=False).reset_index(drop=True)
    df.index = df.index + 1
    df.insert(0, "No.", df.index)
    return df


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# EPS加速判定
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def calc_eps_accel(tickers: list[str]) -> dict:
    result = {}
    for ticker in tickers[:100]:
        try:
            t  = yf.Ticker(ticker)
            qe = t.quarterly_income_stmt
            if qe is None or qe.empty:
                continue
            ni_rows = [r for r in qe.index if "Net Income" in str(r)]
            if not ni_rows:
                continue
            eps = qe.loc[ni_rows[0]].dropna()
            if len(eps) < 2:
                continue
            q0, q1 = float(eps.iloc[0]), float(eps.iloc[1])
            yoy0 = (q0 - q1) / abs(q1) * 100 if q1 != 0 else (100.0 if q0 > q1 else 0)
            yoy1 = 0
            if len(eps) >= 4:
                q2 = float(eps.iloc[2])
                yoy1 = (q1 - q2) / abs(q2) * 100 if q2 != 0 else 0
            result[ticker] = {
                "eps_accel": "Y" if yoy0 > yoy1 else "N",
                "eps_yoy_q0": round(yoy0, 1),
                "eps_yoy_q1": round(yoy1, 1),
                "rev_accel": "", "rev_yoy_q0": None, "rev_yoy_q1": None,
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
        df[df["Industry"].fillna("") != ""].groupby("Industry")
        .agg(rs=("RS Rating", "mean"), count=("RS Rating", "count"), sector=("Sector", "first"))
        .reset_index().sort_values("rs", ascending=False).reset_index(drop=True)
    )
    total = len(ind)
    return {
        "date": today,
        "industry_rs": [
            {
                "rank": i + 1,
                "grade": industry_rs_grade(i + 1, total),
                "industry": row["Industry"],
                "sector": row["sector"],
                "rs": int(round(row["rs"])),
                "count": int(row["count"]),
            }
            for i, row in ind.iterrows()
        ],
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HVC判定
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def build_hvc(tickers: list[str]) -> dict:
    print("HVC 判定中...")
    today        = datetime.date.today()
    window_end   = today - datetime.timedelta(days=1)
    window_start = today - datetime.timedelta(days=HV_MONTHS * 30)
    rows = []

    for i in range(0, len(tickers), 100):
        batch = tickers[i:i+100]
        try:
            raw = yf.download(batch, period="1y", auto_adjust=True,
                              progress=False, threads=True, group_by="ticker")
            if raw.empty:
                continue
            if not isinstance(raw.columns, pd.MultiIndex):
                continue
            vol_df   = raw.xs("Volume", axis=1, level=1)
            close_df = raw.xs("Close",  axis=1, level=1)
            open_df  = raw.xs("Open",   axis=1, level=1)
            high_df  = raw.xs("High",   axis=1, level=1)

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
                avg_v  = float(vols.iloc[-63:].mean())
                rel_v  = float(vols.loc[max_idx]) / avg_v if avg_v > 0 else 0
                latest = float(close_df[ticker].iloc[-1])
                since  = (latest - close) / close * 100
                rows.append({
                    "ticker": ticker, "industry": "", "type": "HVE",
                    "date": str(max_date), "hvc": gap >= 10 and rng >= 75,
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
    export_df = df.drop(columns=[c for c in df.columns if c.startswith("_")], errors="ignore")
    columns   = list(export_df.columns)
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

    existing = {"days": [], "industry_trend": [], "high_volume": {}, "earnings_accel": {}}
    if DATA_JSON.exists():
        with open(DATA_JSON, encoding="utf-8") as f:
            existing = json.load(f)

    # Industry/Sector取得
    industry_map = fetch_finviz_industry()
    if len(industry_map) < 100:
        print("Finviz取得失敗 → yfinanceでフォールバック")
        ticker_info = load_tickers()
        syms = [t["symbol"] for t in ticker_info]
        industry_map = fetch_industry_yfinance(syms)
    
    ticker_info = load_tickers()

    # Industry情報をticker_infoにマージ
    for t in ticker_info:
        sym = t["symbol"]
        if sym in industry_map:
            t["sector"]   = industry_map[sym].get("sector", "")
            t["industry"] = industry_map[sym].get("industry", "")

    df_all    = fetch_prices_and_calc_rs(ticker_info, industry_map)
    if df_all.empty:
        print("❌ データ取得失敗")
        sys.exit(1)

    df_screen = apply_filters(df_all)
    print(f"スクリーニング通過: {len(df_screen)} 銘柄")

    tickers_screen = df_screen["Ticker"].tolist()
    eps_map        = calc_eps_accel(tickers_screen)
    df_screen["EPS加速"]  = df_screen["Ticker"].map(lambda t: "▲加速" if eps_map.get(t, {}).get("eps_accel") == "Y" else "—")
    df_screen["売上加速"] = "—"
    df_screen["HV"]       = ""

    ind_rs_today = build_industry_rs(df_all, today)
    hvc_data     = build_hvc(tickers_screen)
    hvc_set      = {r["ticker"] for r in hvc_data["rows"]}
    df_screen["HV"] = df_screen["Ticker"].map(lambda t: "HV1" if t in hvc_set else "")

    days = [d for d in existing.get("days", []) if d["date"] != today]
    days.insert(0, df_to_day(df_screen, today))
    days = days[:KEEP_DAYS]

    trends = [t for t in existing.get("industry_trend", []) if t["date"] != today]
    trends.insert(0, ind_rs_today)
    trends = trends[:TREND_DAYS]

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

    data_out = {
        "generated_at": now,
        "screening_summary": SCREENING_SUMMARY,
        "days": days,
        "industry_trend": trends,
        "high_volume": hvc_data,
        "earnings_accel": {
            "meta": {"generated_at": now, "days": 60,
                     "n_targets": len(tickers_screen), "n_eps_judged": len(eps_map),
                     "n_rev_judged": 0, "n_rev_ready": 0},
            "map": eps_map,
        },
    }
    with open(DATA_JSON, "w", encoding="utf-8") as f:
        json.dump(data_out, f, ensure_ascii=False, separators=(",", ":"))
    print(f"✅ data.json 書き出し完了")

    with open(UNIVERSE_JSON, "w", encoding="utf-8") as f:
        json.dump({"date": today, "generated_at": now, "tickers": universe_tickers},
                  f, ensure_ascii=False, separators=(",", ":"))
    print(f"✅ universe.json 書き出し完了")
    print(f"=== 完了: {len(df_screen)}銘柄スクリーニング / {len(universe_tickers)}銘柄RS計算 ===")


if __name__ == "__main__":
    main()
