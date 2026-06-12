"""
US Stock Screener - データ生成スクリプト
本家kiri_traderに近いカラム構成で生成。
"""

import json, sys, time, datetime, warnings, csv
from pathlib import Path

warnings.filterwarnings("ignore")

SCRIPT_DIR    = Path(__file__).parent
OUTPUT_DIR    = SCRIPT_DIR.parent / "docs"
TICKERS_CSV   = SCRIPT_DIR / "tickers_enriched.csv"
TICKERS_CSV_B = SCRIPT_DIR / "tickers.csv"
DATA_JSON     = OUTPUT_DIR / "data.json"
UNIVERSE_JSON = OUTPUT_DIR / "universe.json"

SCREENING_SUMMARY = "前日比≥+5% | 株価$0.75〜300 | 平均出来高≥50万株 | 売買代金≥$1M | 出来高≥平均(RelVol≥1) | 銘柄RS≥60 | 52W安値≥+30%"
KEEP_DAYS  = 14
TREND_DAYS = 28
HV_MONTHS  = 3
MAX_SECONDS = 300 * 60

try:
    import pandas as pd
    import numpy as np
    import yfinance as yf
    import requests
    print("✅ ライブラリ読み込み完了")
except ImportError as e:
    print(f"❌ ライブラリ不足: {e}")
    sys.exit(1)

START_TIME = datetime.datetime.now()
def elapsed() -> float:
    return (datetime.datetime.now() - START_TIME).total_seconds()
def time_ok() -> bool:
    return elapsed() < MAX_SECONDS


def fmt_pct(v):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return None
    return f"{v*100:.2f}%"

def fmt_num(v, decimals=2):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return None
    return round(float(v), decimals)

def fmt_market_cap(v):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return None
    if v >= 1e12: return f"{v/1e12:.2f}T"
    if v >= 1e9:  return f"{v/1e9:.2f}B"
    if v >= 1e6:  return f"{v/1e6:.2f}M"
    return str(int(v))

def fmt_vol(v):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return None
    if v >= 1e6: return f"{v/1e6:.2f}M"
    if v >= 1e3: return f"{v/1e3:.0f}K"
    return str(int(v))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Yahoo Finance APIでスクリーニング通過銘柄のIndustry補完
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
YF_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
}

def fetch_yahoo_profile(ticker: str) -> dict:
    """Yahoo Finance APIから1銘柄のSector/Industryを取得。"""
    try:
        url = f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{ticker}?modules=assetProfile,summaryDetail,defaultKeyStatistics,financialData"
        resp = requests.get(url, headers=YF_HEADERS, timeout=10)
        if resp.status_code != 200:
            return {}
        data = resp.json()
        result_list = data.get("quoteSummary", {}).get("result", [])
        if not result_list:
            return {}
        result = result_list[0]

        profile  = result.get("assetProfile", {})
        summary  = result.get("summaryDetail", {})
        keystats = result.get("defaultKeyStatistics", {})
        findata  = result.get("financialData", {})

        def raw(obj, key):
            v = obj.get(key, {})
            if isinstance(v, dict): return v.get("raw")
            return v

        def fmt_pct_val(v):
            if v is None: return None
            return f"{v*100:.2f}%"

        return {
            "Sector":       profile.get("sector", "") or "",
            "Industry":     profile.get("industry", "") or "",
            "Country":      profile.get("country", "") or "",
            "Float Short":  fmt_pct_val(raw(keystats, "shortPercentOfFloat")),
            "Short Ratio":  raw(keystats, "shortRatio"),
            "Insider Own":  fmt_pct_val(raw(keystats, "heldPercentInsiders")),
            "Inst Own":     fmt_pct_val(raw(keystats, "heldPercentInstitutions")),
            "Beta":         raw(summary, "beta"),
            "Recom":        raw(findata, "recommendationMean"),
            "Target Price": raw(findata, "targetMeanPrice"),
            "ROA":          fmt_pct_val(raw(findata, "returnOnAssets")),
            "ROE":          fmt_pct_val(raw(findata, "returnOnEquity")),
            "Gross M":      fmt_pct_val(raw(findata, "grossMargins")),
            "Oper M":       fmt_pct_val(raw(findata, "operatingMargins")),
            "Profit M":     fmt_pct_val(raw(findata, "profitMargins")),
            "Curr R":       raw(findata, "currentRatio"),
            "Quick R":      raw(findata, "quickRatio"),
            "Debt/Eq":      raw(findata, "debtToEquity"),
        }
    except Exception as e:
        print(f"  Yahoo取得エラー {ticker}: {e}")
        return {}


def fetch_yahoo_batch(tickers: list[str]) -> dict:
    """複数銘柄をYahoo Finance APIから取得。{ticker: {col: val}} を返す。"""
    results = {}
    total = len(tickers)
    for i, ticker in enumerate(tickers):
        if not time_ok():
            break
        data = fetch_yahoo_profile(ticker)
        results[ticker] = data
        status = "✅" if data.get("Industry") else "⚠️"
        print(f"  {status} Yahoo {ticker} ({i+1}/{total}): {data.get('Industry','取得失敗')}")
        time.sleep(0.5)
    return results


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 既存data.jsonからIndustryキャッシュ
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def load_industry_cache() -> dict:
    cache = {}
    if not DATA_JSON.exists():
        return cache
    try:
        with open(DATA_JSON, encoding="utf-8") as f:
            data = json.load(f)
        for day in data.get("days", []):
            cols = day.get("columns", [])
            idx  = {c: i for i, c in enumerate(cols)}
            for row in day.get("rows", []):
                t = row[idx["Ticker"]] if "Ticker" in idx else None
                if not t:
                    continue
                industry = row[idx["Industry"]] if "Industry" in idx else ""
                sector   = row[idx["Sector"]]   if "Sector"   in idx else ""
                if industry and t not in cache:
                    cache[t] = {"industry": industry or "", "sector": sector or ""}
        print(f"data.jsonキャッシュ: {len(cache)} 銘柄")
    except Exception as e:
        print(f"  キャッシュ読み込みエラー: {e}")
    return cache


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 銘柄リスト読み込み
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def load_tickers(industry_cache: dict) -> list[dict]:
    csv_path = TICKERS_CSV if TICKERS_CSV.exists() else TICKERS_CSV_B
    tickers = []
    with open(csv_path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sym = row["symbol"].strip()
            if not sym:
                continue
            if not row.get("industry") and sym in industry_cache:
                row["industry"] = industry_cache[sym].get("industry", "")
                row["sector"]   = industry_cache[sym].get("sector", "")
            tickers.append(row)
    has_ind = sum(1 for t in tickers if t.get("industry", ""))
    print(f"銘柄リスト: {len(tickers)} 銘柄 (Industry付き: {has_ind})")
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
def fetch_prices_and_calc_rs(ticker_info: list[dict]) -> pd.DataFrame:
    all_tickers = [t["symbol"] for t in ticker_info]
    info_map    = {t["symbol"]: t for t in ticker_info}
    batch_size  = 500

    print(f"価格データ取得中（{len(all_tickers)}銘柄）...")
    closes_all = {}
    highs_all  = {}
    lows_all   = {}
    opens_all  = {}

    for i in range(0, len(all_tickers), batch_size):
        if not time_ok():
            print(f"  ⚠️ タイムアウト接近")
            break
        batch = all_tickers[i:i+batch_size]
        n = i // batch_size + 1
        tb = (len(all_tickers) - 1) // batch_size + 1
        print(f"  バッチ {n}/{tb} ({len(batch)}銘柄)... [{elapsed():.0f}s]")
        try:
            raw = yf.download(batch, period="14mo", auto_adjust=True,
                              progress=False, threads=True, group_by="ticker")
            if raw.empty:
                continue
            if isinstance(raw.columns, pd.MultiIndex):
                close = raw.xs("Close", axis=1, level=1)
                high  = raw.xs("High",  axis=1, level=1)
                low   = raw.xs("Low",   axis=1, level=1)
                open_ = raw.xs("Open",  axis=1, level=1)
            else:
                close = raw[["Close"]] if "Close" in raw else pd.DataFrame()
                high  = raw[["High"]]  if "High"  in raw else pd.DataFrame()
                low   = raw[["Low"]]   if "Low"   in raw else pd.DataFrame()
                open_ = raw[["Open"]]  if "Open"  in raw else pd.DataFrame()
            for t in batch:
                if t in close.columns:
                    s = close[t].dropna()
                    if len(s) >= 10:
                        closes_all[t] = s
                        if t in high.columns:  highs_all[t] = high[t].dropna()
                        if t in low.columns:   lows_all[t]  = low[t].dropna()
                        if t in open_.columns: opens_all[t] = open_[t].dropna()
        except Exception as e:
            print(f"    エラー: {e}")
        time.sleep(2)

    print(f"  → {len(closes_all)} 銘柄取得完了 [{elapsed():.0f}s]")

    print("RS Rating 計算中...")
    rs_raws    = {t: calc_rs_raw(p) for t, p in closes_all.items()}
    rs_series  = pd.Series(rs_raws)
    rs_ratings = rs_raw_to_rating(rs_series)

    today_prices = {t: float(p.iloc[-1]) for t, p in closes_all.items() if len(p) >= 2}
    prev_prices  = {t: float(p.iloc[-2]) for t, p in closes_all.items() if len(p) >= 2}

    # 各種指標計算（価格データから）
    w52_high = {}; w52_low = {}
    d50_high = {}; d50_low = {}
    sma20 = {}; sma50 = {}; sma200 = {}
    perf_week = {}; perf_month = {}; perf_quart = {}
    perf_half = {}; perf_year = {}; perf_ytd = {}
    atr14 = {}; vol_w = {}; vol_m = {}
    rsi14 = {}; gap = {}; from_open = {}

    year_start = datetime.date(datetime.date.today().year, 1, 1)

    for t, prices in closes_all.items():
        cur = float(prices.iloc[-1])
        n   = len(prices)

        if n >= 252: w52_high[t] = float(prices.iloc[-252:].max()); w52_low[t] = float(prices.iloc[-252:].min())
        elif n >= 1: w52_high[t] = float(prices.max()); w52_low[t] = float(prices.min())

        if n >= 50: d50_high[t] = float(prices.iloc[-50:].max()); d50_low[t] = float(prices.iloc[-50:].min())

        if n >= 20:  sma20[t]  = float(prices.iloc[-20:].mean())
        if n >= 50:  sma50[t]  = float(prices.iloc[-50:].mean())
        if n >= 200: sma200[t] = float(prices.iloc[-200:].mean())

        if n >= 6:   perf_week[t]  = (cur - float(prices.iloc[-6]))  / float(prices.iloc[-6])
        if n >= 21:  perf_month[t] = (cur - float(prices.iloc[-21])) / float(prices.iloc[-21])
        if n >= 63:  perf_quart[t] = (cur - float(prices.iloc[-63])) / float(prices.iloc[-63])
        if n >= 126: perf_half[t]  = (cur - float(prices.iloc[-126]))/ float(prices.iloc[-126])
        if n >= 252: perf_year[t]  = (cur - float(prices.iloc[-252]))/ float(prices.iloc[-252])

        # YTD
        ytd_prices = prices[prices.index.date >= year_start]
        if len(ytd_prices) >= 2:
            perf_ytd[t] = (cur - float(ytd_prices.iloc[0])) / float(ytd_prices.iloc[0])

        # ATR(14)
        if t in highs_all and t in lows_all and n >= 14:
            hi = highs_all[t].iloc[-14:]
            lo = lows_all[t].iloc[-14:]
            pr = prices.iloc[-15:-1] if n >= 15 else prices.iloc[:-1]
            tr_list = []
            for j in range(min(14, len(hi))):
                try:
                    h = float(hi.iloc[j]); l = float(lo.iloc[j])
                    pc = float(pr.iloc[j]) if j < len(pr) else h
                    tr_list.append(max(h-l, abs(h-pc), abs(l-pc)))
                except: pass
            if tr_list: atr14[t] = round(sum(tr_list)/len(tr_list), 2)

        # Volatility W/M (標準偏差)
        if n >= 5:  vol_w[t] = float(prices.iloc[-5:].pct_change().std() * 100)
        if n >= 21: vol_m[t] = float(prices.iloc[-21:].pct_change().std() * 100)

        # RSI(14)
        if n >= 15:
            delta = prices.iloc[-15:].diff().dropna()
            gain  = delta.clip(lower=0).mean()
            loss  = (-delta.clip(upper=0)).mean()
            if loss > 0: rsi14[t] = round(100 - 100/(1+gain/loss), 2)
            else:        rsi14[t] = 100.0

        # Gap / from Open
        if t in opens_all and n >= 2:
            op = float(opens_all[t].iloc[-1])
            pc = float(prices.iloc[-2])
            if pc > 0: gap[t]       = (op - pc) / pc
            if op > 0: from_open[t] = (cur - op) / op

    print("出来高データ取得中...")
    volumes = {}; avg_volumes = {}
    for i in range(0, len(all_tickers), batch_size):
        if not time_ok(): break
        batch = all_tickers[i:i+batch_size]
        try:
            raw = yf.download(batch, period="3mo", auto_adjust=True,
                              progress=False, threads=True, group_by="ticker")
            if raw.empty: continue
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
        except Exception: pass
        time.sleep(2)

    rows = []
    for ticker in closes_all:
        rs    = rs_ratings.get(ticker)
        price = today_prices.get(ticker)
        prev  = prev_prices.get(ticker)
        info  = info_map.get(ticker, {})
        if rs is None or pd.isna(rs) or price is None: continue

        avg_v = avg_volumes.get(ticker, 0)
        vol   = volumes.get(ticker, 0)
        hi52  = w52_high.get(ticker)
        lo52  = w52_low.get(ticker)
        hi50  = d50_high.get(ticker)
        lo50  = d50_low.get(ticker)
        s20   = sma20.get(ticker)
        s50   = sma50.get(ticker)
        s200  = sma200.get(ticker)
        chg   = (price - prev) / prev if prev else 0

        rows.append({
            "Ticker":      ticker,
            "Company":     info.get("name", ""),
            "Sector":      info.get("sector", "") or "",
            "Industry":    info.get("industry", "") or "",
            "Country":     info.get("country", "USA") or "USA",
            "Price":       round(price, 2),
            "Change":      f"{chg*100:.2f}%",
            "Volume":      fmt_vol(vol),
            "Avg Volume":  fmt_vol(avg_v),
            "Rel Volume":  fmt_num(vol / avg_v if avg_v > 0 else None, 2),
            "RS Rating":   int(rs),
            "Industry RS": None,  # 後で計算
            # パフォーマンス
            "Perf Week":   fmt_pct(perf_week.get(ticker)),
            "Perf Month":  fmt_pct(perf_month.get(ticker)),
            "Perf Quart":  fmt_pct(perf_quart.get(ticker)),
            "Perf Half":   fmt_pct(perf_half.get(ticker)),
            "Perf Year":   fmt_pct(perf_year.get(ticker)),
            "Perf YTD":    fmt_pct(perf_ytd.get(ticker)),
            # テクニカル
            "Beta":        None,
            "ATR":         atr14.get(ticker),
            "Volatility W": f"{vol_w[ticker]:.2f}%" if ticker in vol_w else None,
            "Volatility M": f"{vol_m[ticker]:.2f}%" if ticker in vol_m else None,
            "SMA20":       fmt_pct((price - s20)  / s20  if s20  else None),
            "SMA50":       fmt_pct((price - s50)  / s50  if s50  else None),
            "SMA200":      fmt_pct((price - s200) / s200 if s200 else None),
            "50D High":    fmt_pct((price - hi50) / hi50 if hi50 else None),
            "50D Low":     fmt_pct((price - lo50) / lo50 if lo50 else None),
            "52W High":    fmt_pct((price - hi52) / hi52 if hi52 else None),
            "52W Low":     fmt_pct((price - lo52) / lo52 if lo52 else None),
            "RSI":         rsi14.get(ticker),
            "from Open":   fmt_pct(from_open.get(ticker)),
            "Gap":         fmt_pct(gap.get(ticker)),
            # Finvizで補完予定（初期値None）
            "Market Cap":  None,
            "P/E":         None,
            "Fwd P/E":     None,
            "PEG":         None,
            "P/S":         None,
            "P/B":         None,
            "EPS":         None,
            "EPS this Y":  None,
            "EPS next Y":  None,
            "EPS past 5Y": None,
            "EPS next 5Y": None,
            "Sales past 5Y": None,
            "EPS Q/Q":     None,
            "Sales Q/Q":   None,
            "Float Short": None,
            "Short Ratio": None,
            "Insider Own": None,
            "Inst Own":    None,
            "ROA":         None,
            "ROE":         None,
            "ROI":         None,
            "Gross M":     None,
            "Oper M":      None,
            "Profit M":    None,
            "Recom":       None,
            "Target Price":None,
            "Earnings":    None,
            "IPO Date":    None,
            "HV":          "",
            "EPS加速":     "—",
            "売上加速":    "—",
            # 内部計算用（出力しない）
            "_change_pct": chg,
            "_price":      price,
            "_avg_vol":    avg_v,
            "_vol":        vol,
            "_lo52":       lo52,
        })

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    # Industry RS計算（この時点での暫定値）
    _recalc_industry_rs(df)
    return df


def _recalc_industry_rs(df: pd.DataFrame):
    """Industry RSをDataFrame内で再計算（in-place）。"""
    valid = df[df["Industry"].fillna("") != ""]
    if len(valid) > 0:
        ind_rs_map = (
            valid.groupby("Industry")["RS Rating"]
            .mean().rank(ascending=False).astype(int)
        )
        df["Industry RS"] = df["Industry"].map(ind_rs_map)
    else:
        df["Industry RS"] = None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# スクリーニングフィルタ
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = df[df["_change_pct"] >= 0.05]
    df = df[df["_price"].between(0.75, 300)]
    df = df[df["_avg_vol"] >= 500000]
    df = df[df["_price"] * df["_vol"] >= 1_000_000]
    df = df[df["Rel Volume"].fillna(0).astype(float) >= 1]
    df = df[df["RS Rating"] >= 60]
    def check_52w(row):
        lo = row.get("_lo52")
        if lo and lo > 0:
            return row["_price"] >= lo * 1.30
        return True
    df = df[df.apply(check_52w, axis=1)]
    df = df.sort_values("RS Rating", ascending=False).reset_index(drop=True)
    df.index = df.index + 1
    df.insert(0, "No.", df.index)
    return df


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Yahoo Finance APIでスクリーニング通過銘柄を補完
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def enrich_with_finviz(df_screen: pd.DataFrame, df_all: pd.DataFrame) -> pd.DataFrame:
    """スクリーニング通過銘柄をYahoo Finance APIで補完（Industry含む各種カラム）。"""
    if not time_ok():
        return df_screen

    # Industry空欄の銘柄だけを取得対象にする
    tickers_need = df_screen[df_screen["Industry"].fillna("") == ""]["Ticker"].tolist()
    tickers_all  = df_screen["Ticker"].tolist()

    print(f"Yahoo Finance APIからデータ取得中（{len(tickers_all)}銘柄）... [{elapsed():.0f}s]")

    yahoo_data = fetch_yahoo_batch(tickers_all)

    for ticker, ydata in yahoo_data.items():
        if not ydata:
            continue
        mask     = df_screen["Ticker"] == ticker
        mask_all = df_all["Ticker"] == ticker

        for col, val in ydata.items():
            if col in df_screen.columns and val is not None:
                # 既存値がある場合は上書きしない（Industry以外）
                if col in ("Sector", "Industry"):
                    if not df_screen.loc[mask, col].values[0]:
                        df_screen.loc[mask, col] = val
                    if not df_all.loc[mask_all, col].values[0]:
                        df_all.loc[mask_all, col] = val
                else:
                    df_screen.loc[mask, col] = val

    # Industry RS再計算（Yahoo補完後）
    _recalc_industry_rs(df_all)
    valid_ind = df_all[df_all["Industry"].fillna("") != ""]
    if len(valid_ind) > 0:
        ind_rank = valid_ind.groupby("Industry")["RS Rating"].mean().rank(ascending=False).astype(int)
        df_screen["Industry RS"] = df_screen["Industry"].map(ind_rank)

    print(f"  → Yahoo補完完了 [{elapsed():.0f}s]")
    return df_screen


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# EPS加速判定
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def calc_eps_accel(tickers: list[str]) -> dict:
    if not time_ok():
        return {}
    result = {}
    print(f"EPS加速判定中（{min(len(tickers),100)}銘柄）...")
    for ticker in tickers[:100]:
        if not time_ok(): break
        try:
            t  = yf.Ticker(ticker)
            qe = t.quarterly_income_stmt
            if qe is None or qe.empty: continue
            ni_rows = [r for r in qe.index if "Net Income" in str(r)]
            if not ni_rows: continue
            eps = qe.loc[ni_rows[0]].dropna()
            if len(eps) < 2: continue
            q0, q1 = float(eps.iloc[0]), float(eps.iloc[1])
            yoy0 = (q0 - q1) / abs(q1) * 100 if q1 != 0 else (100.0 if q0 > q1 else 0)
            yoy1 = 0
            if len(eps) >= 4:
                q2 = float(eps.iloc[2])
                yoy1 = (q1 - q2) / abs(q2) * 100 if q2 != 0 else 0
            result[ticker] = {
                "eps_accel":  "Y" if yoy0 > yoy1 else "N",
                "eps_yoy_q0": round(yoy0, 1),
                "eps_yoy_q1": round(yoy1, 1),
                "rev_accel": "", "rev_yoy_q0": None, "rev_yoy_q1": None,
            }
        except Exception: pass
        time.sleep(0.05)
    print(f"  → {len(result)} 銘柄完了")
    return result


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Industry RS トレンド
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def build_industry_rs(df: pd.DataFrame, today: str) -> dict:
    valid = df[df["Industry"].fillna("") != ""] if "Industry" in df.columns else pd.DataFrame()
    if len(valid) == 0:
        return {"date": today, "industry_rs": []}
    ind = (
        valid.groupby("Industry")
        .agg(rs=("RS Rating","mean"), count=("RS Rating","count"), sector=("Sector","first"))
        .reset_index().sort_values("rs", ascending=False).reset_index(drop=True)
    )
    total = len(ind)
    return {
        "date": today,
        "industry_rs": [
            {
                "rank":     i + 1,
                "grade":    industry_rs_grade(i+1, total),
                "industry": row["Industry"],
                "sector":   row["sector"],
                "rs":       int(round(row["rs"])),
                "count":    int(row["count"]),
            }
            for i, row in ind.iterrows()
        ],
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HVC判定
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def build_hvc(tickers: list[str], industry_map: dict) -> dict:
    if not time_ok():
        return {"meta": {"generated_at": datetime.datetime.now().astimezone().isoformat(),
                         "count": 0, "count_hvc": 0}, "rows": []}
    print("HVC 判定中...")
    today        = datetime.date.today()
    window_end   = today - datetime.timedelta(days=1)
    window_start = today - datetime.timedelta(days=HV_MONTHS * 30)
    rows = []

    for i in range(0, len(tickers), 100):
        if not time_ok(): break
        batch = tickers[i:i+100]
        try:
            raw = yf.download(batch, period="1y", auto_adjust=True,
                              progress=False, threads=True, group_by="ticker")
            if raw.empty or not isinstance(raw.columns, pd.MultiIndex): continue
            vol_df   = raw.xs("Volume", axis=1, level=1)
            close_df = raw.xs("Close",  axis=1, level=1)
            open_df  = raw.xs("Open",   axis=1, level=1)
            high_df  = raw.xs("High",   axis=1, level=1)

            for ticker in batch:
                if ticker not in vol_df.columns: continue
                vols = vol_df[ticker].dropna()
                if len(vols) < 63: continue
                max_idx  = vols.idxmax()
                max_date = max_idx.date() if hasattr(max_idx, "date") else max_idx
                if not (window_start <= max_date <= window_end): continue
                pos = vols.index.get_loc(max_idx)
                if pos == 0: continue
                close  = float(close_df[ticker].loc[max_idx])
                open_  = float(open_df[ticker].loc[max_idx])
                high   = float(high_df[ticker].loc[max_idx])
                prev_c = float(close_df[ticker].iloc[pos - 1])
                gap_   = (open_ - prev_c) / prev_c * 100
                rng    = (close - open_) / (high - open_ + 0.0001) * 100
                avg_v  = float(vols.iloc[-63:].mean())
                rel_v  = float(vols.loc[max_idx]) / avg_v if avg_v > 0 else 0
                latest = float(close_df[ticker].iloc[-1])
                since  = (latest - close) / close * 100
                rows.append({
                    "ticker":      ticker,
                    "industry":    industry_map.get(ticker, ""),
                    "type":        "HVE",
                    "date":        str(max_date),
                    "hvc":         gap_ >= 10 and rng >= 75,
                    "gap":         round(gap_, 2),
                    "close_range": round(rng, 1),
                    "relvol":      round(rel_v, 1),
                    "since":       round(since, 2),
                    "volume":      int(vols.loc[max_idx]),
                    "market_cap":  None,
                })
        except Exception: pass
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
            if isinstance(val, float) and pd.isna(val): r.append(None)
            elif hasattr(val, "item"): r.append(val.item())
            else: r.append(val)
        rows.append(r)
    return {"date": today, "count": len(rows), "columns": columns, "rows": rows}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# メイン
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def main():
    today = datetime.date.today().isoformat()
    now   = datetime.datetime.now().astimezone().isoformat()
    print(f"=== 生成開始: {now} ===")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    industry_cache = load_industry_cache()

    existing = {"days": [], "industry_trend": [], "high_volume": {}, "earnings_accel": {}}
    if DATA_JSON.exists():
        with open(DATA_JSON, encoding="utf-8") as f:
            existing = json.load(f)

    ticker_info  = load_tickers(industry_cache)
    industry_map = {t["symbol"]: t.get("industry", "") for t in ticker_info}

    df_all    = fetch_prices_and_calc_rs(ticker_info)
    if df_all.empty:
        print("❌ データ取得失敗")
        sys.exit(1)

    df_screen = apply_filters(df_all)
    print(f"スクリーニング通過: {len(df_screen)} 銘柄 [{elapsed():.0f}s]")

    # ★ Finvizで補完（Industry・各種ファンダメンタル）
    df_screen = enrich_with_finviz(df_screen, df_all)

    tickers_screen = df_screen["Ticker"].tolist()
    industry_map   = {t["symbol"]: t.get("industry", "") for t in ticker_info}

    eps_map = calc_eps_accel(tickers_screen)
    df_screen["EPS加速"] = df_screen["Ticker"].map(
        lambda t: "▲加速" if eps_map.get(t, {}).get("eps_accel") == "Y" else "—"
    )
    df_screen["売上加速"] = "—"

    ind_rs_today = build_industry_rs(df_all, today)
    hvc_data     = build_hvc(tickers_screen, industry_map)
    hvc_set      = {r["ticker"] for r in hvc_data["rows"]}
    df_screen["HV"] = df_screen["Ticker"].map(lambda t: "HV1" if t in hvc_set else "")

    days = [d for d in existing.get("days", []) if d["date"] != today]
    days.insert(0, df_to_day(df_screen, today))
    days = days[:KEEP_DAYS]

    trends = [t for t in existing.get("industry_trend", []) if t["date"] != today]
    if ind_rs_today.get("industry_rs"):
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
        "generated_at":      now,
        "screening_summary": SCREENING_SUMMARY,
        "days":              days,
        "industry_trend":    trends,
        "high_volume":       hvc_data,
        "earnings_accel": {
            "meta": {"generated_at": now, "days": 60,
                     "n_targets": len(tickers_screen), "n_eps_judged": len(eps_map),
                     "n_rev_judged": 0, "n_rev_ready": 0},
            "map": eps_map,
        },
    }
    with open(DATA_JSON, "w", encoding="utf-8") as f:
        json.dump(data_out, f, ensure_ascii=False, separators=(",", ":"))
    print(f"✅ data.json 書き出し完了 [{elapsed():.0f}s]")

    with open(UNIVERSE_JSON, "w", encoding="utf-8") as f:
        json.dump({"date": today, "generated_at": now, "tickers": universe_tickers},
                  f, ensure_ascii=False, separators=(",", ":"))
    print(f"✅ universe.json 書き出し完了")
    print(f"=== 完了: {len(df_screen)}銘柄 / {len(universe_tickers)}銘柄RS [{elapsed():.0f}s] ===")


if __name__ == "__main__":
    main()
