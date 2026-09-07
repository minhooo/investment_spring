"""
원주가(무수정) 일별 종가 수집기 — 키움 ka10081 (주식일봉차트조회)

    python tools/fetch_prices_raw.py 207940 삼성바이오로직스 KOSPI 20250102 20260906

출력: data/prices/<코드>_<종목명>.csv  (date, close, volume, bm_close, bm_name)

왜 원주가인가 (인적분할 케이스 한정):
  유상증자·액면분할 케이스는 수정주가가 맞다. 그러나 **인적분할**은 다르다.
  네이버 siseJson 은 존속회사(207940)의 분할 전 주가를
  재상장 첫날 시초가에 이어붙이려고 1.4717배로 일괄 상향한다.
  이렇게 하면 "분할 전 1주 = 분할 후 존속회사 1주" 라는 잘못된 가정이 들어가고,
  주주가 함께 받은 신설회사 주식이 사라진다.
  인적분할의 합산가치는 원주가에 분할비율을 곱해서 직접 계산해야 한다.

벤치마크 지수 종가는 네이버 siseJson 을 그대로 쓴다(지수는 수정 대상이 아니다).
"""
import sys, os, csv, json, re, time, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch_investors import token  # noqa: E402


def kiwoom_daily(code, base_dt, until):
    """base_dt 에서 과거로 거슬러 until 까지 원주가 일봉을 모은다."""
    tok, out, cont, nk = token(), {}, "N", ""
    while True:
        body = json.dumps({"stk_cd": code, "base_dt": base_dt,
                           "upd_stkpc_tp": "0"}).encode()
        req = urllib.request.Request(
            "https://api.kiwoom.com/api/dostk/chart", data=body,
            headers={"Content-Type": "application/json;charset=UTF-8",
                     "authorization": f"Bearer {tok}", "api-id": "ka10081",
                     "cont-yn": cont, "next-key": nk})
        with urllib.request.urlopen(req, timeout=30) as r:
            cont, nk = r.headers.get("cont-yn", "N"), r.headers.get("next-key", "")
            data = json.loads(r.read().decode())
        rows = data.get("stk_dt_pole_chart_qry") or []
        if not rows:
            break
        for row in rows:
            d = row["dt"]
            if d < until:
                return out
            out[d] = {"close": abs(int(row["cur_prc"])),
                      "volume": int(row.get("trde_qty") or 0)}
        if cont != "Y":
            break
        time.sleep(0.25)
    return out


def naver_index(symbol, start, end):
    url = ("https://api.finance.naver.com/siseJson.naver"
           f"?symbol={symbol}&requestType=1&startTime={start}&endTime={end}&timeframe=day")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0",
                                               "Referer": "https://finance.naver.com/"})
    raw = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
    rows = json.loads(re.sub(r"\s+", " ", raw.replace("'", '"')).strip())
    return {str(r[0]): float(r[4]) for r in rows[1:]}


def main():
    code, name, bm, start, end = sys.argv[1:6]
    print(f"[1/2] {name}({code}) 원주가 수집 중...")
    stock = kiwoom_daily(code, end, start)
    print(f"      {len(stock)}일")
    print(f"[2/2] 벤치마크 {bm} 수집 중...")
    index = naver_index(bm, start, end)

    os.makedirs(f"{ROOT}/data/prices", exist_ok=True)
    path = f"{ROOT}/data/prices/{code}_{name}.csv"
    n = 0
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["date", "close", "volume", "bm_close", "bm_name"])
        for d in sorted(stock):
            if d not in index or stock[d]["volume"] == 0:
                continue  # 거래정지일(거래량 0)은 버린다
            w.writerow([f"{d[:4]}-{d[4:6]}-{d[6:]}", float(stock[d]["close"]),
                        stock[d]["volume"], index[d], bm])
            n += 1
    print(f"완료: {path}  ({n}행, 원주가)")


if __name__ == "__main__":
    main()
