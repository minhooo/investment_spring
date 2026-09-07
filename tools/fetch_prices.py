"""
종목 + 벤치마크 지수 일별 종가 수집기 (네이버 금융, 수정주가 기준)

사용법:
    python tools/fetch_prices.py 007660 이수페타시스 KOSPI 20240102 20260906

출력:
    data/prices/<코드>_<종목명>.csv
    컬럼: date, close, volume, bm_close, bm_name

주의:
- 네이버 siseJson 은 수정주가(액면분할·유무상증자 반영)를 반환한다.
  유상증자 케이스에서는 수정주가를 쓰는 것이 맞다. 권리락 하락이
  주가 하락으로 잘못 잡히는 것을 방지하기 위함.
- 종목과 지수의 거래일이 다를 수 있으므로 종목 거래일 기준으로 inner join 한다.
"""
import sys, json, re, csv, os, urllib.request

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://finance.naver.com/",
}


def fetch(symbol, start, end):
    url = (
        "https://api.finance.naver.com/siseJson.naver"
        f"?symbol={symbol}&requestType=1&startTime={start}&endTime={end}&timeframe=day"
    )
    req = urllib.request.Request(url, headers=HEADERS)
    raw = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
    # 네이버는 홑따옴표 + 개행이 섞인 유사 JSON 을 반환한다
    txt = raw.replace("'", '"')
    txt = re.sub(r"\s+", " ", txt).strip()
    rows = json.loads(txt)
    out = {}
    for r in rows[1:]:
        d = str(r[0])
        out[d] = {"close": float(r[4]), "volume": float(r[5])}
    return out


def main():
    if len(sys.argv) < 6:
        print(__doc__)
        sys.exit(1)
    code, name, bm, start, end = sys.argv[1:6]

    print(f"[1/2] {name}({code}) 수집 중...")
    stock = fetch(code, start, end)
    print(f"      {len(stock)}일")

    print(f"[2/2] 벤치마크 {bm} 수집 중...")
    index = fetch(bm, start, end)
    print(f"      {len(index)}일")

    os.makedirs("data/prices", exist_ok=True)
    path = f"data/prices/{code}_{name}.csv"
    n = 0
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["date", "close", "volume", "bm_close", "bm_name"])
        for d in sorted(stock):
            if d not in index:
                continue  # 거래일 불일치 행은 버린다
            iso = f"{d[:4]}-{d[4:6]}-{d[6:]}"
            w.writerow([iso, stock[d]["close"], int(stock[d]["volume"]),
                        index[d]["close"], bm])
            n += 1
    print(f"완료: {path}  ({n}행)")


if __name__ == "__main__":
    main()
