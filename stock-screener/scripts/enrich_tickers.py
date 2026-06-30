"""
tickers.csv に Industry/Sector 情報を追加する週次スクリプト。
yfinance ではなく Finviz からスクレイピングして取得。
6754銘柄 × 1.5秒 ≒ 約2.8時間（GitHub Actions無料枠6時間以内）

修正点：
- yfinance → Finviz スクレイピングに切り替え
- キャッシュにあってもindustryが空の銘柄は再取得
- 途中保存で中断時も進捗を保持
"""

import csv, time, json, sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

SCRIPT_DIR  = Path(__file__).parent
INPUT_CSV   = SCRIPT_DIR / "tickers.csv"
OUTPUT_CSV  = SCRIPT_DIR / "tickers_enriched.csv"
CACHE_JSON  = SCRIPT_DIR / "industry_cache.json"

try:
    import requests
    from bs4 import BeautifulSoup
    print("✅ ライブラリ読み込み完了")
except ImportError as e:
    print(f"❌ pip install requests beautifulsoup4")
    sys.exit(1)

FINVIZ_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

def load_existing_cache() -> dict:
    if CACHE_JSON.exists():
        with open(CACHE_JSON, encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_cache(cache: dict):
    with open(CACHE_JSON, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False)

def fetch_finviz(ticker: str) -> tuple[str, dict]:
    """Finvizから1銘柄のSector/Industry/Countryを取得。"""
    try:
        url = f"https://finviz.com/quote.ashx?t={ticker}"
        resp = requests.get(url, headers=FINVIZ_HEADERS, timeout=15)
        if resp.status_code == 404:
            # 上場廃止・存在しない銘柄 → "__not_found__"マークして再試行しない
            return ticker, {"sector": "", "industry": "", "country": "", "_status": "not_found"}
        if resp.status_code != 200:
            return ticker, {"sector": "", "industry": "", "country": ""}

        soup = BeautifulSoup(resp.text, "html.parser")

        # Finvizのquoteページ：snapshot-tableからSector/Industry/Country取得
        result = {"sector": "", "industry": "", "country": ""}
        cells = soup.select("td.snapshot-td2-cp, td.snapshot-td2")
        label = None
        for cell in cells:
            cls = cell.get("class", [])
            if "snapshot-td2-cp" in cls:
                label = cell.get_text(strip=True)
            elif "snapshot-td2" in cls and label:
                val = cell.get_text(strip=True)
                if label == "Sector":
                    result["sector"] = val if val != "-" else ""
                elif label == "Industry":
                    result["industry"] = val if val != "-" else ""
                elif label == "Country":
                    result["country"] = val if val != "-" else ""
                label = None

        result["_status"] = "ok"
        return ticker, result

    except Exception as e:
        return ticker, {"sector": "", "industry": "", "country": ""}


def main():
    # 入力CSV読み込み
    tickers = []
    with open(INPUT_CSV, encoding="utf-8") as f:
        tickers = list(csv.DictReader(f))
    print(f"対象: {len(tickers)} 銘柄")

    # キャッシュ読み込み
    cache = load_existing_cache()
    print(f"キャッシュ: {len(cache)} 銘柄分あり")

    # 取得が必要な銘柄：
    # ① キャッシュにない
    # ② キャッシュにあってもindustryが空（かつnot_foundでない）
    missing = [
        t["symbol"] for t in tickers
        if t["symbol"] not in cache
        or (
            not cache[t["symbol"]].get("industry", "").strip()
            and cache[t["symbol"]].get("_status") != "not_found"
        )
    ]
    print(f"新規取得 or 空欄再取得: {len(missing)} 銘柄")
    print(f"（推定所要時間: {len(missing)*1.5/3600:.1f}時間）")

    if missing:
        done = 0
        # Finvizへの負荷を下げるためシングルスレッドで順番に取得
        # （並列だとBotブロックされる可能性が高い）
        for sym in missing:
            ticker_sym, info = fetch_finviz(sym)
            cache[sym] = info
            done += 1

            status = "✅" if info.get("industry") else ("🚫" if info.get("_status") == "not_found" else "⚠️")
            if done % 100 == 0:
                print(f"  {status} {done}/{len(missing)} 完了... [{sym}: {info.get('industry','空欄')}]")
                save_cache(cache)  # 途中保存

            time.sleep(1.5)  # Finviz Bot対策

        save_cache(cache)
        print(f"✅ キャッシュ保存完了: {len(cache)} 銘柄")

    # 結果集計
    with_industry = sum(1 for v in cache.values() if v.get("industry","").strip())
    not_found     = sum(1 for v in cache.values() if v.get("_status") == "not_found")
    print(f"Industry情報あり: {with_industry}銘柄")
    print(f"存在しない銘柄(404): {not_found}銘柄")
    print(f"Industry空欄: {len(cache)-with_industry-not_found}銘柄")

    # 出力CSV書き出し
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["symbol", "name", "sector", "industry", "country"])
        writer.writeheader()
        for t in tickers:
            sym  = t["symbol"]
            info = cache.get(sym, {})
            writer.writerow({
                "symbol":   sym,
                "name":     t.get("name", ""),
                "sector":   info.get("sector", ""),
                "industry": info.get("industry", ""),
                "country":  info.get("country", "") or t.get("country", "USA"),
            })

    print(f"✅ tickers_enriched.csv 書き出し完了（{len(tickers)}銘柄）")


if __name__ == "__main__":
    main()
