"""
tickers.csv に Industry/Sector 情報を追加する週次スクリプト。
yfinance の Ticker.info から取得して tickers_enriched.csv として保存。
"""

import csv, time, json, sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

SCRIPT_DIR  = Path(__file__).parent
INPUT_CSV   = SCRIPT_DIR / "tickers.csv"
OUTPUT_CSV  = SCRIPT_DIR / "tickers_enriched.csv"
CACHE_JSON  = SCRIPT_DIR / "industry_cache.json"

try:
    import yfinance as yf
    print("✅ yfinance 読み込み完了")
except ImportError:
    print("❌ pip install yfinance")
    sys.exit(1)


def load_existing_cache() -> dict:
    if CACHE_JSON.exists():
        with open(CACHE_JSON, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_cache(cache: dict):
    with open(CACHE_JSON, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False)


def fetch_info(ticker: str) -> tuple[str, dict]:
    try:
        info = yf.Ticker(ticker).info
        return ticker, {
            "sector":   info.get("sector", "") or "",
            "industry": info.get("industry", "") or "",
        }
    except Exception:
        return ticker, {"sector": "", "industry": ""}


def main():
    # 入力CSV読み込み
    tickers = []
    with open(INPUT_CSV, encoding="utf-8") as f:
        tickers = list(csv.DictReader(f))
    print(f"対象: {len(tickers)} 銘柄")

    # キャッシュ読み込み（前回の結果を再利用）
    cache = load_existing_cache()
    print(f"キャッシュ: {len(cache)} 銘柄分あり")

    # キャッシュにない銘柄だけ取得
    missing = [t["symbol"] for t in tickers if t["symbol"] not in cache]
    print(f"新規取得: {len(missing)} 銘柄")

    if missing:
        # 並列取得（10スレッド）
        done = 0
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(fetch_info, sym): sym for sym in missing}
            for future in as_completed(futures):
                sym, info = future.result()
                cache[sym] = info
                done += 1
                if done % 100 == 0:
                    print(f"  {done}/{len(missing)} 完了...")
                    save_cache(cache)  # 途中保存
                time.sleep(0.02)

        save_cache(cache)
        print(f"✅ キャッシュ保存完了: {len(cache)} 銘柄")

    # 出力CSV書き出し
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["symbol", "name", "sector", "industry", "country"])
        writer.writeheader()
        count_with_industry = 0
        for t in tickers:
            sym  = t["symbol"]
            info = cache.get(sym, {})
            sector   = info.get("sector", "")
            industry = info.get("industry", "")
            if industry:
                count_with_industry += 1
            writer.writerow({
                "symbol":   sym,
                "name":     t.get("name", ""),
                "sector":   sector,
                "industry": industry,
                "country":  t.get("country", "USA"),
            })

    print(f"✅ tickers_enriched.csv 書き出し完了")
    print(f"   Industry情報あり: {count_with_industry}/{len(tickers)} 銘柄")


if __name__ == "__main__":
    main()
