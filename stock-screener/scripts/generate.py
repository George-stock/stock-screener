"""
US Stock Screener - データ生成スクリプト
毎日NYクローズ後に実行して data.json と universe.json を生成する。

データソース: finviz (finvizfinance ライブラリ) + yfinance
"""

import json
import os
import sys
import time
import datetime
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

# ── 出力先 ──────────────────────────────────────────────────
OUTPUT_DIR = Path(__file__).parent.parent / "docs"
DATA_JSON    = OUTPUT_DIR / "data.json"
UNIVERSE_JSON = OUTPUT_DIR / "universe.json"

# ── スクリーニング条件 ────────────────────────────────────
SCREENING_SUMMARY = "前日比≥+5% | 株価$0.75〜300 | 平均出来高≥50万株 | 売買代金≥$1M | 出来高≥平均(RelVol≥1) | 銘柄RS≥60 | 52W安値≥+30%"

KEEP_DAYS      = 14   # 抽出リストを何日分保持するか
TREND_DAYS     = 28   # Industry RSトレンドを何日分保持するか
HV_MONTHS      = 3    # HVC判定ウィンドウ（月）

# ── Finviz スクリーニング用パラメータ ───────────────────────
# finvizfinance の screener に渡すフィルタ
FINVIZ_FILTERS = {
    "Change":         "5to100",       # 前日比 +5%以上
    "Price":          "0.75to300",    # 株価
    "Average Volume": "500000to",     # 平均出来高50万株以上
    "Relative Volume":"1to",          # RelVol 1以上
    "20-Day Simple Moving Average": "SMA20pb",  # 52W安値+30%以上の近似
}

# ── ライブラリインポート ──────────────────────────────────
try:
    import pandas as pd
    import numpy as np
    import yfinance as yf
    from finvizfinance.screener.overview import Overview
    from finvizfinance.screener.performance import Performance
    from finvizfinance.screener.financial import Financial
    from finvizfinance.screener.valuation import Valuation
    print("✅ 全ライブラリ読み込み完了")
except ImportError as e:
    print(f"❌ ライブラリが不足しています: {e}")
    print("以下を実行してください:")
    print("  pip install finvizfinance yfinance pandas numpy")
    sys.exit(1)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# RS Rating 計算
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def calc_rs_raw(prices: pd.Series) -> float:
    """IBD近似式でRS生スコアを計算。データ不足時は NaN を返す。"""
    if len(prices) < 252:
        return float("nan")
    p = prices.dropna()
    if len(p) < 252:
        return float("nan")
    try:
        q1 = p.iloc[-1]  / p.iloc[-63]  - 1  # 直近63日
        q2 = p.iloc[-63] / p.iloc[-126] - 1
        q3 = p.iloc[-126]/ p.iloc[-189] - 1
        q4 = p.iloc[-189]/ p.iloc[-252] - 1
        return 0.4 * q1 + 0.2 * q2 + 0.2 * q3 + 0.2 * q4
    except Exception:
        return float("nan")


def rs_raw_to_rating(series: pd.Series) -> pd.Series:
    """RS生スコア → 1〜99のパーセンタイルに変換。"""
    valid = series.dropna()
    if len(valid) == 0:
        return series.map(lambda _: None)
    rank = series.rank(pct=True, na_option="keep")
    return (rank * 98 + 1).clip(1, 99).round().astype("Int64")


def industry_rs_grade(rank: int, total: int) -> str:
    """ランク → グレード A〜E"""
    pct = rank / total
    if pct <= 0.21: return "A"
    if pct <= 0.42: return "B"
    if pct <= 0.63: return "C"
    if pct <= 0.84: return "D"
    return "E"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# EPS 加速判定
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def calc_eps_accel(ticker_list: list[str]) -> dict:
    """yfinance でEPS前年同期比を取得してEPS加速判定。"""
    result = {}
    for ticker in ticker_list:
        try:
            info = yf.Ticker(ticker)
            earnings = info.quarterly_earnings
            if earnings is None or len(earnings) < 2:
                continue
            # YoYを計算
            yoy = []
            for i in range(min(4, len(earnings))):
                row = earnings.iloc[i]
                if row.get("Earnings") and row.get("Year Ago EPS"):
                    ya = row["Year Ago EPS"]
                    cur = row["Earnings"]
                    if ya != 0:
                        yoy.append((cur - ya) / abs(ya) * 100)
                    elif ya < 0 and cur > ya:
                        yoy.append(100.0)  # 赤字縮小
                    else:
                        yoy.append(None)
            if len(yoy) >= 2 and yoy[0] is not None and yoy[1] is not None:
                accel = "Y" if yoy[0] > yoy[1] else "N"
                result[ticker] = {
                    "eps_accel": accel,
                    "eps_yoy_q0": round(yoy[0], 1),
                    "eps_yoy_q1": round(yoy[1], 1),
                    "rev_accel": "",
                    "rev_yoy_q0": None,
                    "rev_yoy_q1": None,
                }
        except Exception:
            pass
        time.sleep(0.1)
    return result


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Finviz から全銘柄データ取得
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def fetch_finviz_all() -> pd.DataFrame:
    """Finviz から USA+Canada の全銘柄（基本情報）を取得。"""
    print("Finviz 全銘柄取得中...")
    foverview = Overview()
    foverview.set_filter(filters_dict={"Country": "USA"})
    df_usa = foverview.screener_view(columns=[0,1,2,3,4,5,6,65,66,67], verbose=0)

    foverview2 = Overview()
    foverview2.set_filter(filters_dict={"Country": "Canada"})
    df_can = foverview2.screener_view(columns=[0,1,2,3,4,5,6,65,66,67], verbose=0)

    df = pd.concat([df_usa, df_can], ignore_index=True)
    print(f"  → {len(df)} 銘柄取得")
    return df


def fetch_finviz_screened() -> pd.DataFrame:
    """スクリーニング条件に合った銘柄を取得（全カラム）。"""
    print("Finviz スクリーニング実行中...")
    fscreen = Overview()
    fscreen.set_filter(filters_dict={
        "Change":          "5to100",
        "Price":           "0.75to300",
        "Average Volume":  "500000to",
        "Relative Volume": "1to",
        "Country":         "USA,Canada",
    })
    # 複数カラムビューを結合
    views = []
    for ViewClass in [Overview, Performance, Financial, Valuation]:
        try:
            v = ViewClass()
            v.set_filter(filters_dict={
                "Change":         "5to100",
                "Price":          "0.75to300",
                "Average Volume": "500000to",
                "Relative Volume":"1to",
                "Country":        "USA,Canada",
            })
            df_v = v.screener_view(verbose=0)
            views.append(df_v)
            time.sleep(1)
        except Exception as e:
            print(f"  警告: {ViewClass.__name__} 取得失敗: {e}")

    if not views:
        return pd.DataFrame()

    df = views[0]
    for v in views[1:]:
        overlap = set(df.columns) & set(v.columns)
        merge_on = [c for c in ["No.", "Ticker"] if c in overlap]
        if merge_on:
            df = df.merge(v.drop(columns=[c for c in overlap if c not in merge_on]), on=merge_on, how="left")

    print(f"  → {len(df)} 銘柄スクリーニング通過")
    return df


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# yfinance フォールバック（Finviz が使えない場合）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def fetch_yfinance_screened() -> pd.DataFrame:
    """
    yfinance でスクリーニングの近似版。
    S&P500 + NASDAQ100 + Russell2000 の銘柄に絞る（全市場は無理なため）。
    本番環境では Finviz Elite を推奨。
    """
    print("yfinance フォールバックでデータ取得中...")

    # 代表的なインデックス構成銘柄リストを取得
    sp500 = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")[0]["Symbol"].tolist()
    ndx100 = pd.read_html("https://en.wikipedia.org/wiki/Nasdaq-100")[4]["Ticker"].tolist()
    tickers = list(set(sp500 + ndx100))
    print(f"  対象: {len(tickers)} 銘柄")

    # 日次データ取得（過去1年）
    raw = yf.download(tickers, period="1y", auto_adjust=True, progress=False)
    closes = raw["Close"] if "Close" in raw else raw.xs("Close", axis=1, level=0)

    today_data = []
    for ticker in tickers:
        try:
            if ticker not in closes.columns:
                continue
            s = closes[ticker].dropna()
            if len(s) < 2:
                continue
            price  = float(s.iloc[-1])
            prev   = float(s.iloc[-2])
            change = (price - prev) / prev

            # フィルタ
            if not (0.75 <= price <= 300):
                continue
            if change < 0.05:
                continue

            rs_raw = calc_rs_raw(s)
            today_data.append({
                "Ticker": ticker,
                "Company": ticker,
                "Price": round(price, 2),
                "Change": f"{change*100:.2f}%",
                "_rs_raw": rs_raw,
                "Industry": "N/A",
                "Sector": "N/A",
                "Country": "USA",
                "Market Cap": "-",
                "Avg Volume": "-",
                "Rel Volume": "-",
                "Float Short": "-",
                "Perf Month": "-",
                "Perf Quart": "-",
            })
        except Exception:
            pass

    df = pd.DataFrame(today_data)
    if df.empty:
        return df

    # RS計算
    rs_series = pd.Series({r["Ticker"]: r["_rs_raw"] for _, r in df.iterrows()})
    rs_ratings = rs_raw_to_rating(rs_series)
    df["RS Rating"] = df["Ticker"].map(rs_ratings)
    df = df[df["RS Rating"] >= 60].copy()
    df = df.sort_values("RS Rating", ascending=False)
    print(f"  → {len(df)} 銘柄スクリーニング通過")
    return df


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# RS 全銘柄計算（universe.json 用）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def build_universe(screened_df: pd.DataFrame) -> dict:
    """スクリーニング済み銘柄のRS/Industry RSマップを返す。"""
    result = {}
    for _, row in screened_df.iterrows():
        ticker = row.get("Ticker")
        rs = row.get("RS Rating")
        irs = row.get("Industry RS")
        if ticker:
            result[str(ticker)] = [
                int(rs) if pd.notna(rs) else None,
                int(irs) if pd.notna(irs) else None,
            ]
    return result


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Industry RS 集計
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def build_industry_rs(df: pd.DataFrame, today: str) -> dict:
    """銘柄RSの業種平均 → ランキング → gradeを付けて返す。"""
    if "RS Rating" not in df.columns or "Industry" not in df.columns:
        return {"date": today, "industry_rs": []}

    ind_rs = (
        df.groupby("Industry")["RS Rating"]
        .agg(["mean", "count"])
        .rename(columns={"mean": "rs", "count": "count"})
        .reset_index()
    )
    ind_rs = ind_rs[ind_rs["count"] >= 1].copy()
    ind_rs = ind_rs.sort_values("rs", ascending=False).reset_index(drop=True)
    total = len(ind_rs)

    rows = []
    for i, row in ind_rs.iterrows():
        rank = i + 1
        rows.append({
            "rank": rank,
            "grade": industry_rs_grade(rank, total),
            "industry": row["Industry"],
            "sector": df[df["Industry"] == row["Industry"]]["Sector"].iloc[0] if "Sector" in df.columns else "",
            "rs": int(round(row["rs"])),
            "count": int(row["count"]),
        })
    return {"date": today, "industry_rs": rows}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HVC 判定（簡易版）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def build_hvc(tickers: list[str]) -> dict:
    """過去1年で最大出来高日が直近3ヶ月以内の銘柄を検出。"""
    print("HVC 判定中...")
    today = datetime.date.today()
    window_end = today - datetime.timedelta(days=1)
    window_start = today - datetime.timedelta(days=HV_MONTHS * 30)
    rows = []

    batch_size = 50
    for i in range(0, len(tickers), batch_size):
        batch = tickers[i:i+batch_size]
        try:
            raw = yf.download(batch, period="1y", auto_adjust=True, progress=False)
            if raw.empty:
                continue

            vol_df  = raw["Volume"] if "Volume" in raw else raw.xs("Volume", axis=1, level=0)
            close_df = raw["Close"] if "Close" in raw else raw.xs("Close", axis=1, level=0)
            open_df  = raw["Open"]  if "Open"  in raw else raw.xs("Open",  axis=1, level=0)
            high_df  = raw["High"]  if "High"  in raw else raw.xs("High",  axis=1, level=0)

            for ticker in batch:
                if ticker not in vol_df.columns:
                    continue
                vols = vol_df[ticker].dropna()
                if len(vols) < 63:
                    continue
                max_idx = vols.idxmax()
                max_date = max_idx.date() if hasattr(max_idx, "date") else max_idx
                if not (window_start <= max_date <= window_end):
                    continue

                close = float(close_df[ticker].loc[max_idx])
                open_ = float(open_df[ticker].loc[max_idx])
                high  = float(high_df[ticker].loc[max_idx])
                gap   = (open_ - float(close_df[ticker].iloc[vols.index.get_loc(max_idx) - 1])) / float(close_df[ticker].iloc[vols.index.get_loc(max_idx) - 1]) * 100
                close_range = (close - open_) / (high - open_ + 0.0001) * 100

                hvc = gap >= 10 and close_range >= 75
                avg_vol = float(vols.iloc[-63:].mean())
                rel_vol = float(vols.loc[max_idx]) / avg_vol if avg_vol > 0 else 0

                # 最新終値から当日終値までのリターン
                latest_close = float(close_df[ticker].iloc[-1])
                since = (latest_close - close) / close * 100

                rows.append({
                    "ticker": ticker,
                    "industry": "",
                    "type": "HVE",
                    "date": str(max_date),
                    "hvc": hvc,
                    "gap": round(gap, 2),
                    "close_range": round(close_range, 1),
                    "relvol": round(rel_vol, 1),
                    "since": round(since, 2),
                    "volume": int(vols.loc[max_idx]),
                    "market_cap": None,
                })
        except Exception as e:
            print(f"  警告: HVC batch {i} エラー: {e}")
        time.sleep(0.5)

    rows.sort(key=lambda r: r["date"], reverse=True)
    return {
        "meta": {
            "generated_at": datetime.datetime.now().astimezone().isoformat(),
            "window_start": str(window_start),
            "window_end": str(window_end),
            "months": HV_MONTHS,
            "count": len(rows),
            "count_hvc": sum(1 for r in rows if r["hvc"]),
        },
        "rows": rows,
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# data.json 更新（既存に追記してKEEP_DAYS分だけ保持）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def load_existing_data() -> dict:
    if DATA_JSON.exists():
        with open(DATA_JSON, encoding="utf-8") as f:
            return json.load(f)
    return {"days": [], "industry_trend": [], "high_volume": {}, "earnings_accel": {}}


def df_to_day(df: pd.DataFrame, today: str) -> dict:
    """DataFrame → days[i] 形式に変換。"""
    columns = list(df.columns)
    rows = []
    for _, row in df.iterrows():
        r = []
        for col in columns:
            val = row[col]
            if pd.isna(val) if not isinstance(val, str) else False:
                r.append(None)
            else:
                r.append(val if isinstance(val, (str, int, float)) else str(val))
        rows.append(r)
    return {"date": today, "columns": columns, "rows": rows}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# メイン処理
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def main():
    today = datetime.date.today().isoformat()
    now   = datetime.datetime.now().astimezone().isoformat()
    print(f"=== 生成開始: {now} ===")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # ── 既存データ読み込み ──
    existing = load_existing_data()

    # ── スクリーニング実行 ──
    try:
        df = fetch_finviz_screened()
        if df.empty:
            raise ValueError("Finviz 結果が空")
    except Exception as e:
        print(f"Finviz 失敗: {e} → yfinance フォールバック")
        df = fetch_yfinance_screened()

    if df.empty:
        print("❌ データ取得失敗。終了します。")
        sys.exit(1)

    # RS Rating / Industry RS が無ければ計算
    if "RS Rating" not in df.columns:
        print("RS Rating を計算中（yfinance 価格履歴が必要）...")
        tickers = df["Ticker"].tolist()
        prices_raw = yf.download(tickers, period="1y", auto_adjust=True, progress=False)
        closes = prices_raw["Close"] if "Close" in prices_raw else prices_raw.xs("Close", axis=1, level=0)
        rs_raws = {t: calc_rs_raw(closes[t]) for t in tickers if t in closes.columns}
        rs_series = pd.Series(rs_raws)
        rs_ratings = rs_raw_to_rating(rs_series)
        df["RS Rating"] = df["Ticker"].map(rs_ratings)

    if "Industry RS" not in df.columns:
        ind_rs_data = build_industry_rs(df, today)
        ind_map = {r["industry"]: r["rank"] for r in ind_rs_data["industry_rs"]}
        df["Industry RS"] = df["Industry"].map(ind_map)

    # EPS加速
    tickers = df["Ticker"].tolist()
    print("EPS加速を判定中（時間がかかります）...")
    eps_map = calc_eps_accel(tickers[:50])  # 最初の50銘柄のみ（時間節約）
    df["EPS加速"] = df["Ticker"].map(lambda t: "▲加速" if eps_map.get(t, {}).get("eps_accel") == "Y" else "—")
    df["売上加速"] = "—"

    # HV判定
    print("HV判定中...")
    hvc_data = build_hvc(tickers)
    hvc_tickers = {r["ticker"] for r in hvc_data["rows"]}
    df["HV"] = df["Ticker"].map(lambda t: "HV1" if t in hvc_tickers else "")

    # 52W安値フィルタ
    if "52W Low" in df.columns:
        def check_52w(row):
            try:
                price = float(str(row["Price"]).replace(",", ""))
                low52 = float(str(row["52W Low"]).replace(",", "").replace("%", ""))
                return (price - low52) / low52 >= 0.30
            except Exception:
                return True
        df = df[df.apply(check_52w, axis=1)].copy()

    # RS ≥ 60 フィルタ
    df = df[df["RS Rating"] >= 60].copy()
    df = df.sort_values("RS Rating", ascending=False).reset_index(drop=True)
    df.index = df.index + 1
    df.insert(0, "No.", df.index)

    print(f"最終銘柄数: {len(df)}")

    # ── Industry RS トレンド ──
    ind_rs_today = build_industry_rs(df, today)

    # ── 既存データに今日分を追記・古いものを削除 ──
    days = existing.get("days", [])
    days = [d for d in days if d["date"] != today]  # 今日分を上書き
    days.insert(0, df_to_day(df, today))
    days = days[:KEEP_DAYS]

    trends = existing.get("industry_trend", [])
    trends = [t for t in trends if t["date"] != today]
    trends.insert(0, ind_rs_today)
    trends = trends[:TREND_DAYS]

    # ── data.json 書き出し ──
    data_out = {
        "generated_at": now,
        "screening_summary": SCREENING_SUMMARY,
        "days": days,
        "industry_trend": trends,
        "high_volume": hvc_data,
        "earnings_accel": {
            "meta": {
                "generated_at": now,
                "days": 60,
                "n_targets": len(tickers),
                "n_eps_judged": len(eps_map),
                "n_rev_judged": 0,
                "n_rev_ready": 0,
            },
            "map": eps_map,
        },
    }
    with open(DATA_JSON, "w", encoding="utf-8") as f:
        json.dump(data_out, f, ensure_ascii=False, separators=(",", ":"))
    print(f"✅ data.json 書き出し完了: {DATA_JSON}")

    # ── universe.json 書き出し ──
    uni_out = {
        "date": today,
        "generated_at": now,
        "tickers": build_universe(df),
    }
    with open(UNIVERSE_JSON, "w", encoding="utf-8") as f:
        json.dump(uni_out, f, ensure_ascii=False, separators=(",", ":"))
    print(f"✅ universe.json 書き出し完了: {UNIVERSE_JSON}")

    print(f"=== 完了 ===")


if __name__ == "__main__":
    main()
