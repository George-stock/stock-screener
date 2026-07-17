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
KEEP_DAYS  = 130
TREND_DAYS = 130
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


YF_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
}

def fetch_yahoo_profile(ticker: str) -> dict:
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


def load_industry_cache() -> dict:
    cache = {}
    cache_path = SCRIPT_DIR / "industry_cache.json"
    if cache_path.exists():
        try:
            with open(cache_path, encoding="utf-8") as f:
                cache = json.load(f)
            with_ind = sum(1 for v in cache.values() if v.get("industry"))
            print(f"industry_cache.json: {len(cache)}銘柄 (Industry付き: {with_ind})")
            return cache
        except Exception as e:
            print(f"  industry_cache.json読み込みエラー: {e}")
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


def calc_rs_raw(prices: pd.Series) -> float:
    p = prices.dropna()
    if len(p) < 253:
        return float("nan")
    try:
        current = p.iloc[-1]
        perf1 = current / p.iloc[-64]  - 1
        perf2 = current / p.iloc[-127] - 1
        perf3 = current / p.iloc[-190] - 1
        perf4 = current / p.iloc[-253] - 1
        return 0.4 * perf1 + 0.2 * perf2 + 0.2 * perf3 + 0.2 * perf4
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


def fetch_prices_and_calc_rs(ticker_info: list[dict]) -> pd.DataFrame:
    all_tickers = [t["symbol"] for t in ticker_info]
    info_map    = {t["symbol"]: t for t in ticker_info}
    batch_size  = 200

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
            raw = yf.download(batch, period="2y", auto_adjust=True,
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
        time.sleep(8)

    print(f"  → {len(closes_all)} 銘柄取得完了 [{elapsed():.0f}s]")

    short_tickers = [t for t, p in closes_all.items() if len(p.dropna()) < 253]
    if short_tickers and time_ok():
        print(f"  データ不足{len(short_tickers)}銘柄をリトライ中...")
        retry_batch_size = 50
        recovered = 0
        for i in range(0, len(short_tickers), retry_batch_size):
            if not time_ok():
                print(f"  ⚠️ タイムアウト接近、リトライ中断")
                break
            batch = short_tickers[i:i+retry_batch_size]
            try:
                raw = yf.download(batch, period="2y", auto_adjust=True,
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
                        if len(s) > len(closes_all.get(t, pd.Series(dtype=float))):
                            closes_all[t] = s
                            if t in high.columns:  highs_all[t] = high[t].dropna()
                            if t in low.columns:   lows_all[t]  = low[t].dropna()
                            if t in open_.columns: opens_all[t] = open_[t].dropna()
                            if len(s) >= 253:
                                recovered += 1
            except Exception as e:
                print(f"    リトライエラー: {e}")
            time.sleep(8)
        print(f"  → リトライで{recovered}銘柄が253日分のデータを回復")

    print("RS Rating 計算中...")
    rs_raws    = {t: calc_rs_raw(p) for t, p in closes_all.items()}
    rs_series  = pd.Series(rs_raws)
    rs_ratings = rs_raw_to_rating(rs_series)

    today_prices = {t: float(p.iloc[-1]) for t, p in closes_all.items() if len(p) >= 2}
    prev_prices  = {t: float(p.iloc[-2]) for t, p in closes_all.items() if len(p) >= 2}

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

        ytd_prices = prices[prices.index.date >= year_start]
        if len(ytd_prices) >= 2:
            perf_ytd[t] = (cur - float(ytd_prices.iloc[0])) / float(ytd_prices.iloc[0])

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

        if n >= 5:  vol_w[t] = float(prices.iloc[-5:].pct_change().std() * 100)
        if n >= 21: vol_m[t] = float(prices.iloc[-21:].pct_change().std() * 100)

        if n >= 15:
            delta = prices.iloc[-15:].diff().dropna()
            gain  = delta.clip(lower=0).mean()
            loss  = (-delta.clip(upper=0)).mean()
            if loss > 0: rsi14[t] = round(100 - 100/(1+gain/loss), 2)
            else:        rsi14[t] = 100.0

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
            "Industry RS": None,
            "Perf Week":   fmt_pct(perf_week.get(ticker)),
            "Perf Month":  fmt_pct(perf_month.get(ticker)),
            "Perf Quart":  fmt_pct(perf_quart.get(ticker)),
            "Perf Half":   fmt_pct(perf_half.get(ticker)),
            "Perf Year":   fmt_pct(perf_year.get(ticker)),
            "Perf YTD":    fmt_pct(perf_ytd.get(ticker)),
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
            "Market Cap":  None, "P/E": None, "Fwd P/E": None, "PEG": None,
            "P/S": None, "P/B": None, "EPS": None, "EPS this Y": None,
            "EPS next Y": None, "EPS past 5Y": None, "EPS next 5Y": None,
            "Sales past 5Y": None, "EPS Q/Q": None, "Sales Q/Q": None,
            "Float Short": None, "Short Ratio": None, "Insider Own": None,
            "Inst Own": None, "ROA": None, "ROE": None, "ROI": None,
            "Gross M": None, "Oper M": None, "Profit M": None,
            "Recom": None, "Target Price": None, "Earnings": None, "IPO Date": None,
            "HV": "", "EPS加速": "—", "売上加速": "—",
            "_change_pct": chg, "_price": price, "_avg_vol": avg_v,
            "_vol": vol, "_lo52": lo52,
        })

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    _recalc_industry_rs(df)

    last_dates = [p.index[-1] for p in closes_all.values() if len(p) > 0]
    if last_dates:
        latest = max(last_dates)
        df.attrs["last_trading_date"] = pd.Timestamp(latest).date().isoformat()

    return df


def _recalc_industry_rs(df: pd.DataFrame):
    valid = df[df["Industry"].fillna("") != ""]
    if len(valid) > 0:
        ind_rs_map = (
            valid.groupby("Industry")["RS Rating"]
            .mean().round().astype(int)
        )
        df["Industry RS"] = df["Industry"].map(ind_rs_map)
    else:
        df["Industry RS"] = None


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


def enrich_with_finviz(df_screen: pd.DataFrame, df_all: pd.DataFrame) -> pd.DataFrame:
    cache_path = SCRIPT_DIR / "industry_cache.json"
    cache = {}
    if cache_path.exists():
        try:
            with open(cache_path, encoding="utf-8") as f:
                cache = json.load(f)
        except Exception:
            pass

    col_map = {
        "market_cap": "Market Cap", "pe": "P/E", "fwd_pe": "Fwd P/E",
        "eps_qoq": "EPS Q/Q", "eps_past5y": "EPS past 5Y",
        "sales_past5y": "Sales past 5Y", "insider_own": "Insider Own",
        "inst_own": "Inst Own", "float_short": "Float Short",
        "short_ratio": "Short Ratio", "roa": "ROA", "roe": "ROE",
        "roi": "ROI", "gross_m": "Gross M", "oper_m": "Oper M",
        "profit_m": "Profit M", "beta": "Beta", "recom": "Recom",
    }

    for idx in df_screen.index:
        ticker = df_screen.at[idx, "Ticker"]
        cdata  = cache.get(ticker, {})
        if not cdata:
            continue
        mask = df_screen["Ticker"] == ticker
        if not df_screen.at[idx, "Industry"] and cdata.get("industry"):
            df_screen.loc[mask, "Industry"] = cdata["industry"]
            df_screen.loc[mask, "Sector"]   = cdata.get("sector", "")
            mask_all = df_all["Ticker"] == ticker
            df_all.loc[mask_all, "Industry"] = cdata["industry"]
            df_all.loc[mask_all, "Sector"]   = cdata.get("sector", "")
        for cache_key, df_col in col_map.items():
            val = cdata.get(cache_key)
            if val and df_col in df_screen.columns:
                df_screen.loc[mask, df_col] = val

    all_tickers = df_screen["Ticker"].tolist()
    if all_tickers and time_ok():
        wait_sec = 90
        print(f"  Rate Limit回避のため{wait_sec}秒待機...")
        time.sleep(wait_sec)

        print(f"  yfinanceで最新ファンダメンタル取得中（{len(all_tickers)}銘柄）...")
        ok_count = 0
        for ticker in all_tickers:
            if not time_ok():
                break
            info = {}
            for attempt in range(2):
                try:
                    info = yf.Ticker(ticker).info
                    if info:
                        break
                except Exception as e:
                    if attempt == 0:
                        time.sleep(10)
                    else:
                        print(f"    ⚠️ {ticker}: {e}")
            if not info:
                time.sleep(4)
                continue
            industry = info.get("industry", "") or ""
            sector   = info.get("sector", "")   or ""
            mask     = df_screen["Ticker"] == ticker
            mask_all = df_all["Ticker"] == ticker
            if industry:
                df_screen.loc[mask, "Industry"] = industry
                df_screen.loc[mask, "Sector"]   = sector
                df_all.loc[mask_all, "Industry"] = industry
                df_all.loc[mask_all, "Sector"]   = sector
            def fmt_p(v):
                if v is None: return None
                return f"{v*100:.2f}%"
            yf_vals = {
                "Float Short":  fmt_p(info.get("shortPercentOfFloat")),
                "Short Ratio":  info.get("shortRatio"),
                "Insider Own":  fmt_p(info.get("heldPercentInsiders")),
                "Inst Own":     fmt_p(info.get("heldPercentInstitutions")),
                "Beta":         info.get("beta"),
                "ROA":          fmt_p(info.get("returnOnAssets")),
                "ROE":          fmt_p(info.get("returnOnEquity")),
                "Gross M":      fmt_p(info.get("grossMargins")),
                "Oper M":       fmt_p(info.get("operatingMargins")),
                "Profit M":     fmt_p(info.get("profitMargins")),
                "Recom":        info.get("recommendationMean"),
                "Target Price": info.get("targetMeanPrice"),
                "P/E":          info.get("trailingPE"),
                "Fwd P/E":      info.get("forwardPE"),
                "EPS past 5Y":  fmt_p(info.get("earningsGrowth")),
                "Sales past 5Y":fmt_p(info.get("revenueGrowth")),
            }
            for col, val in yf_vals.items():
                if val is not None and col in df_screen.columns:
                    df_screen.loc[mask, col] = val
            ok_count += 1
            time.sleep(4)
        print(f"    → {ok_count}/{len(all_tickers)}銘柄 最新化完了 [{elapsed():.0f}s]")

    _recalc_industry_rs(df_all)
    valid_ind = df_all[df_all["Industry"].fillna("") != ""]
    if len(valid_ind) > 0:
        ind_rs_map = valid_ind.groupby("Industry")["RS Rating"].mean().round().astype(int)
        df_screen["Industry RS"] = df_screen["Industry"].map(ind_rs_map)

    print(f"  → 補完完了 [{elapsed():.0f}s]")
    return df_screen


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
            ni_rows  = [r for r in qe.index if "Net Income" in str(r) and "Minority" not in str(r)]
            rev_rows = [r for r in qe.index if r in ("Total Revenue", "Revenue")]
            eps_accel = ""
            eps_yoy0 = None
            eps_yoy1 = None
            if ni_rows:
                ni = qe.loc[ni_rows[0]].dropna()
                if len(ni) >= 3:
                    q0 = float(ni.iloc[0])
                    q1 = float(ni.iloc[1])
                    q2 = float(ni.iloc[2])
                    q3 = float(ni.iloc[3]) if len(ni) >= 4 else None
                    def yoy(cur, prev):
                        if prev == 0: return 100.0 if cur > 0 else -100.0
                        return (cur - prev) / abs(prev) * 100
                    yoy0 = yoy(q0, q2)
                    eps_yoy0 = round(yoy0, 1)
                    if q3 is not None:
                        yoy1 = yoy(q1, q3)
                        eps_yoy1 = round(yoy1, 1)
                        eps_accel = "Y" if yoy0 > yoy1 else "N"
                    else:
                        eps_accel = "Y" if yoy0 > 0 else "N"
            rev_accel = ""
            rev_yoy0 = None
            rev_yoy1 = None
            if rev_rows:
                rv = qe.loc[rev_rows[0]].dropna()
                if len(rv) >= 3:
                    r0 = float(rv.iloc[0])
                    r1 = float(rv.iloc[1])
                    r2 = float(rv.iloc[2])
                    r3 = float(rv.iloc[3]) if len(rv) >= 4 else None
                    ryoy0 = yoy(r0, r2)
                    rev_yoy0 = round(ryoy0, 1)
                    if r3 is not None:
                        ryoy1 = yoy(r1, r3)
                        rev_yoy1 = round(ryoy1, 1)
                        rev_accel = "Y" if ryoy0 > ryoy1 else "N"
                    else:
                        rev_accel = "Y" if ryoy0 > 0 else "N"
            if eps_accel:
                result[ticker] = {
                    "eps_accel":  eps_accel,
                    "eps_yoy_q0": eps_yoy0,
                    "eps_yoy_q1": eps_yoy1,
                    "rev_accel":  "",
                    "rev_yoy_q0": rev_yoy0,
                    "rev_yoy_q1": None,
                }
        except Exception:
            pass
        time.sleep(0.05)
    print(f"  → {len(result)} 銘柄完了")
    return result


def build_industry_rs(df: pd.DataFrame, today: str) -> dict:
    valid = df[df["Industry"].fillna("") != ""] if "Industry" in df.columns else pd.DataFrame()
    if len(valid) == 0:
        return {"date": today, "industry_rs": []}
    ind = (
        valid.groupby("Industry")
        .agg(rs=("RS Rating","mean"), count=("RS Rating","count"), sector=("Sector","first"))
        .reset_index()
    )
    ind = ind[ind["count"] >= 5].sort_values("rs", ascending=False).reset_index(drop=True)
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
                since  = (latest - close) / close * 100 if close != 0 else None
                rows.append({
                    "ticker":      ticker,
                    "industry":    industry_map.get(ticker, ""),
                    "type":        "HVE",
                    "date":        str(max_date),
                    "hvc":         gap_ >= 10 and rng >= 75,
                    "gap":         round(gap_, 2),
                    "close_range": round(rng, 1),
                    "relvol":      round(rel_v, 1),
                    "since":       round(since, 2) if since is not None else None,
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


def build_insights(df: pd.DataFrame, ind_rs_today: dict) -> dict:
    import numpy as np
    rs_ge_80 = int((df["RS Rating"] >= 80).sum())
    rs_ge_90 = int((df["RS Rating"] >= 90).sum())
    top_industries = []
    for r in (ind_rs_today.get("industry_rs") or [])[:5]:
        top_industries.append({"name": r["industry"], "rank": r["rank"]})
    EXCLUDE_INDUSTRIES = {
        "Exchange Traded Fund", "ETF", "Shell Companies", "シェルカンパニー",
        "Closed-End Fund - Debt", "Closed-End Fund - Equity", "Closed-End Fund - Foreign",
    }
    concentrated = []
    if "Industry" in df.columns:
        ind_counts = df[
            (df["Industry"].fillna("") != "") &
            (~df["Industry"].isin(EXCLUDE_INDUSTRIES))
        ]["Industry"].value_counts()
        for ind, cnt in ind_counts.items():
            if cnt >= 3:
                concentrated.append([ind, int(cnt)])
    divergent = []
    if "Industry RS" in df.columns and "Industry" in df.columns:
        for _, row in df.iterrows():
            rs  = row.get("RS Rating", 0) or 0
            irs = row.get("Industry RS")
            ind = row.get("Industry", "") or ""
            try:
                irs_int = int(irs) if irs is not None and str(irs) != "nan" else None
            except (ValueError, TypeError):
                irs_int = None
            if rs >= 85 and irs_int is not None and irs_int < 50 and ind:
                divergent.append({
                    "ticker":   row.get("Ticker", ""),
                    "rs":       int(rs),
                    "industry": ind,
                    "ind_rank": irs_int,
                })
    return {
        "rs_ge_80":         rs_ge_80,
        "rs_ge_90":         rs_ge_90,
        "top_industries":   top_industries,
        "total_industries": len(ind_rs_today.get("industry_rs") or []),
        "concentrated":     concentrated,
        "divergent":        divergent,
    }


def df_to_day(df: pd.DataFrame, today: str, insights: dict = None) -> dict:
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
    day = {"date": today, "count": len(rows), "columns": columns, "rows": rows}
    if insights:
        day["insights"] = insights
    return day


def sanitize_for_json(obj):
    """NaN/Infinity/-InfinityをNoneに再帰変換する。"""
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize_for_json(v) for v in obj]
    if isinstance(obj, float):
        if obj != obj or obj in (float("inf"), float("-inf")):
            return None
        return obj
    return obj


def fetch_sentiment() -> dict:
    """VIX, VIX3M, VTS, PCRをサーバーサイドで取得してdictで返す。"""
    result = {"vix": None, "vix3m": None, "vts": None, "pcr": None, "generated_at": None}
    try:
        def get_last_close(ticker):
            try:
                hist = yf.Ticker(ticker).history(period="5d")
                if hist.empty: return None
                return round(float(hist["Close"].dropna().iloc[-1]), 2)
            except Exception:
                return None
        result["vix"]   = get_last_close("^VIX")
        result["vix3m"] = get_last_close("^VIX3M")
        if result["vix"] and result["vix3m"] and result["vix3m"] > 0:
            result["vts"] = round(result["vix"] / result["vix3m"], 3)
        print(f"  VIX={result['vix']}  VIX3M={result['vix3m']}  VTS={result['vts']}")
    except Exception as e:
        print(f"  ⚠️ VIX取得エラー: {e}")

    try:
        # PCR → stooq経由でCBOE Total Put/Call Ratioを取得
        # yfinanceのCBOE PCRティッカー(^CPC等)はデータなし
        # CBOE公式CSVはBot検出でブロックされるためstooqを使用
        time.sleep(10)
        end   = datetime.date.today()
        start = end - datetime.timedelta(days=10)
        pcr_url = (
            f"https://stooq.com/q/d/l/?s=^cpc"
            f"&d1={start.strftime('%Y%m%d')}"
            f"&d2={end.strftime('%Y%m%d')}&i=d"
        )
        resp = requests.get(pcr_url, timeout=15,
                            headers={"User-Agent": "Mozilla/5.0"})
        print(f"  PCR stooq status: {resp.status_code}")
        if resp.status_code == 200:
            raw_lines = resp.text.strip().splitlines()
            print(f"  PCR stooq lines: {len(raw_lines)}, last: {raw_lines[-1] if raw_lines else 'none'}")
            # 1行目はヘッダー(Date,Open,High,Low,Close,Volume)、2行目以降がデータ
            data_lines = [l for l in raw_lines[1:] if l.strip()]
            if data_lines:
                last = data_lines[-1].split(",")
                # Close列は5番目(index=4)
                if len(last) >= 5:
                    try:
                        result["pcr"] = round(float(last[4]), 2)
                        print(f"  PCR={result['pcr']} (via stooq)")
                    except ValueError as e:
                        print(f"  ⚠️ PCR値変換失敗: {last[4]} / {e}")
            else:
                print("  ⚠️ PCR stooq: データ行なし")
        else:
            print(f"  ⚠️ PCR stooq: HTTP {resp.status_code}")
        if result["pcr"] is None:
            print("  ⚠️ PCR: 取得失敗")
    except Exception as e:
        print(f"  ⚠️ PCR取得エラー: {e}")

    result["generated_at"] = datetime.datetime.now().astimezone().isoformat()
    return result


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

    df_all = fetch_prices_and_calc_rs(ticker_info)
    if df_all.empty:
        print("❌ データ取得失敗")
        sys.exit(1)

    actual_date = df_all.attrs.get("last_trading_date")
    if actual_date:
        if actual_date != today:
            print(f"  📅 日付補正: サーバー日付{today} → 実際の最終取引日{actual_date}")
        today = actual_date

    df_screen = apply_filters(df_all)
    print(f"スクリーニング通過: {len(df_screen)} 銘柄 [{elapsed():.0f}s]")

    df_screen = enrich_with_finviz(df_screen, df_all)

    tickers_screen = df_screen["Ticker"].tolist()
    industry_map   = {t["symbol"]: t.get("industry", "") for t in ticker_info}

    eps_map = calc_eps_accel(tickers_screen)
    df_screen["EPS加速"] = df_screen["Ticker"].map(
        lambda t: "▲加速" if eps_map.get(t, {}).get("eps_accel") == "Y" else "—"
    )
    df_screen["売上加速"] = df_screen["Ticker"].map(
        lambda t: "▲加速" if eps_map.get(t, {}).get("rev_accel") == "Y" else "—"
    )

    ind_rs_today = build_industry_rs(df_all, today)
    tickers_hvc  = df_all[df_all["RS Rating"] >= 60]["Ticker"].tolist()
    print(f"HVC対象: {len(tickers_hvc)}銘柄（RS≥60全銘柄）")
    hvc_data = build_hvc(tickers_hvc, industry_map)
    hvc_set  = {r["ticker"] for r in hvc_data["rows"]}
    df_screen["HV"] = df_screen["Ticker"].map(lambda t: "HV1" if t in hvc_set else "")

    insights = build_insights(df_screen, ind_rs_today)
    days = [d for d in existing.get("days", []) if d["date"] != today]
    days.insert(0, df_to_day(df_screen, today, insights))
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
        ind = row.get("Industry", "") or ""
        if not ind and t in industry_map:
            ind = industry_map[t] or ""
        if t:
            universe_tickers[str(t)] = [
                int(rs)  if pd.notna(rs)  else None,
                int(irs) if pd.notna(irs) else None,
                ind,
            ]
    with_ind = sum(1 for v in universe_tickers.values() if v[2])
    print(f"universe.json: {len(universe_tickers)}銘柄 (Industry付き: {with_ind})")

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
        "sentiment": fetch_sentiment(),
    }
    data_out = sanitize_for_json(data_out)
    with open(DATA_JSON, "w", encoding="utf-8") as f:
        json.dump(data_out, f, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    print(f"✅ data.json 書き出し完了 [{elapsed():.0f}s]")

    universe_out = sanitize_for_json({"date": today, "generated_at": now, "tickers": universe_tickers})
    with open(UNIVERSE_JSON, "w", encoding="utf-8") as f:
        json.dump(universe_out, f, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    print(f"✅ universe.json 書き出し完了")
    print(f"=== 完了: {len(df_screen)}銘柄 / {len(universe_tickers)}銘柄RS [{elapsed():.0f}s] ===")


if __name__ == "__main__":
    main()
