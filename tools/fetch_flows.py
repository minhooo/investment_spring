"""
투자자별 순매매 수집기 (네이버 금융 외국인·기관 매매동향)

    python tools/fetch_flows.py 007660 이수페타시스 700

출력: data/flows/<코드>_<종목명>.csv
    date, close, volume, inst_net, frgn_net, frgn_hold, frgn_rate

왜 필요한가:
  거래대금은 **방향이 없다.** 매수와 매도가 같은 숫자에 잡히므로
  "돈이 몰렸다"와 "돈이 빠져나갔다"를 구분하지 못한다.
  순매매(net)는 방향을 가진 유일한 공개 지표다.

주의: 이 표는 **수량(주)** 기준이다. 금액으로 보려면 종가를 곱한다.
      원주가 기준이므로 수정주가 시계열과 직접 곱하면 어긋난다 — 이 파일의 close 를 쓸 것.
"""
import sys, os, io, re, csv, time, urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HDR = {"User-Agent": "Mozilla/5.0", "Referer": "https://finance.naver.com/"}


def page(code, p):
    url = f"https://finance.naver.com/item/frgn.naver?code={code}&page={p}"
    req = urllib.request.Request(url, headers=HDR)
    raw = urllib.request.urlopen(req, timeout=30).read()
    return raw.decode("euc-kr", "replace")


def parse(html):
    out = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.S):
        if "tah p10" not in tr:
            continue
        cells = [re.sub(r"<[^>]+>", "", c).replace("&nbsp;", " ").strip()
                 for c in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
        cells = [c for c in cells if c != ""]
        if len(cells) < 8 or not re.match(r"^\d{4}\.\d{2}\.\d{2}$", cells[0]):
            continue
        num = lambda x: int(re.sub(r"[^\d\-]", "", x) or 0)
        out.append({
            "date": cells[0].replace(".", "-"),
            "close": num(cells[1]),
            "volume": num(cells[4]),
            "inst_net": num(cells[5]),
            "frgn_net": num(cells[6]),
            "frgn_hold": num(cells[7]),
            "frgn_rate": cells[8] if len(cells) > 8 else "",
        })
    return out


def main():
    code, name = sys.argv[1], sys.argv[2]
    want = int(sys.argv[3]) if len(sys.argv) > 3 else 700
    rows, seen = [], set()
    for p in range(1, want // 20 + 3):
        try:
            got = parse(page(code, p))
        except Exception as e:
            print(f"  page {p} 실패: {e}")
            break
        new = [r for r in got if r["date"] not in seen]
        if not new:
            break
        for r in new:
            seen.add(r["date"])
        rows.extend(new)
        if len(rows) >= want:
            break
        time.sleep(0.25)          # 서버 예의
    rows.sort(key=lambda r: r["date"])

    os.makedirs(f"{ROOT}/data/flows", exist_ok=True)
    path = f"{ROOT}/data/flows/{code}_{name}.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["date", "close", "volume", "inst_net",
                                          "frgn_net", "frgn_hold", "frgn_rate"])
        w.writeheader()
        w.writerows(rows)
    print(f"완료: data/flows/{code}_{name}.csv  ({len(rows)}행, "
          f"{rows[0]['date']} ~ {rows[-1]['date']})")


if __name__ == "__main__":
    main()
