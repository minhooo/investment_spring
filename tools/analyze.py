"""
구간 수익률 / 상대강도 분석기

사용법:
    python tools/analyze.py data/prices/007660_이수페타시스.csv 2024-11-08

출력: 케이스 문서에 그대로 붙여넣을 수 있는 마크다운 표
"""
import sys, csv, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


def load(path):
    with open(path, encoding="utf-8") as f:
        return [
            {"date": r["date"], "close": float(r["close"]),
             "bm": float(r["bm_close"]), "vol": float(r["volume"]),
             "bmn": r.get("bm_name", "지수")}
            for r in csv.DictReader(f)
        ]


def main():
    path, dday = sys.argv[1], sys.argv[2]
    rows = load(path)
    idx = {r["date"]: i for i, r in enumerate(rows)}
    if dday not in idx:
        cands = [d for d in idx if d >= dday]
        dday = min(cands)
        print(f"# D-day 를 다음 거래일 {dday} 로 조정")
    i0 = idx[dday]
    b = rows[i0]

    print(f"\n## 기준일 D-day = {dday}  종목 {b['close']:,.0f}  KOSPI {b['bm']:,.2f}\n")
    BM = rows[0].get("bmn", "지수")
    print(f"| 구간 | 날짜 | 종가 | 종목 | {BM} | **초과수익** | RS(D-day=100) |")
    print("|---|---|---|---|---|---|---|")
    for label, off in [("D-day", 0), ("D+1", 1), ("D+5", 5), ("D+20", 20),
                       ("D+60", 60), ("D+120", 120), ("D+250", 250),
                       ("D+500", 500), ("최근", len(rows) - 1 - i0)]:
        j = i0 + off
        if j >= len(rows):
            continue
        r = rows[j]
        sr = r["close"] / b["close"] - 1
        br = r["bm"] / b["bm"] - 1
        rs = (r["close"] / b["close"]) / (r["bm"] / b["bm"]) * 100
        print(f"| {label} | {r['date']} | {r['close']:,.0f} | {sr*100:+.1f}% | "
              f"{br*100:+.1f}% | **{(sr-br)*100:+.1f}%p** | {rs:.1f} |")

    # 최저점 / 최고점
    seg = rows[i0:]
    lo = min(seg, key=lambda r: r["close"])
    hi = max(seg, key=lambda r: r["close"])
    rslist = [((r["close"]/b["close"])/(r["bm"]/b["bm"])*100, r) for r in seg]
    rslo = min(rslist, key=lambda x: x[0])
    rshi = max(rslist, key=lambda x: x[0])
    print(f"\n- 최저 종가: {lo['close']:,.0f} ({lo['date']}, D-day 대비 {(lo['close']/b['close']-1)*100:+.1f}%)")
    print(f"- 최고 종가: {hi['close']:,.0f} ({hi['date']}, D-day 대비 {(hi['close']/b['close']-1)*100:+.1f}%)")
    print(f"- RS 최저: {rslo[0]:.1f} ({rslo[1]['date']})")
    print(f"- RS 최고: {rshi[0]:.1f} ({rshi[1]['date']})")

    # D-day 주가 회복일
    for r in seg[1:]:
        if r["close"] >= b["close"]:
            print(f"- 명목 주가 회복일: {r['date']} (D+{rows.index(r)-i0} 거래일)")
            break
    for v, r in rslist[1:]:
        if v >= 100:
            print(f"- 상대강도(RS) 회복일: {r['date']} (D+{rows.index(r)-i0} 거래일)")
            break

    # 연초(2024-01-02) 대비
    s0 = rows[0]
    last = rows[-1]
    print(f"\n## 전체 기간 {s0['date']} ~ {last['date']}")
    sr = last["close"]/s0["close"]-1
    br = last["bm"]/s0["bm"]-1
    print(f"- 종목 {sr*100:+.1f}%  |  {BM} {br*100:+.1f}%  |  **초과 {(sr-br)*100:+.1f}%p**  "
          f"| RS {(1+sr)/(1+br)*100:.1f}")

    # 거래량 상위일 (이벤트 탐지용)
    avg = sum(r["vol"] for r in rows)/len(rows)
    top = sorted(rows, key=lambda r: -r["vol"])[:10]
    print(f"\n## 거래량 급증 상위 10일 (평균 대비 배수) — 미기록 이벤트 탐지용")
    print("| 날짜 | 종가 | 전일대비 | 거래량 배수 |")
    print("|---|---|---|---|")
    for r in top:
        k = rows.index(r)
        chg = (r["close"]/rows[k-1]["close"]-1)*100 if k > 0 else 0
        print(f"| {r['date']} | {r['close']:,.0f} | {chg:+.1f}% | {r['vol']/avg:.1f}x |")


if __name__ == "__main__":
    main()
