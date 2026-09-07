"""
에쓰오일 ↔ 브렌트유 연동 검증 대시보드 빌더

    data/prices/010950_에쓰오일.csv
  + data/macro/DCOILBRENTEU.csv · DDFUELUSGULF.csv · DEXKOUS.csv
  + data/meta/010950_에쓰오일_브렌트연동.json
        -> dist/010950_brent.html
        -> (--md 옵션) 케이스 문서에 붙일 마크다운 표를 stdout 으로

사용법:
    python tools/build_oil_link.py
    python tools/build_oil_link.py --md

계산은 전부 여기서 한다. 템플릿은 그리기만 한다.

시차 정렬 규약 (중요):
    브렌트 결제는 런던 16:30(=KST 익일 01:30)이므로 KRX 종가 시점에
    알려진 최신 브렌트는 '직전 영업일 결제가'다. 따라서 KRX 거래일 t 의
    수익률은 (t 직전 브렌트) / (t-1 직전 브렌트) - 1 과 짝지운다.
    동일자로 붙이면 아직 나오지도 않은 값을 쓰게 된다.
"""
import bisect, csv, io, json, math, os, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dist_names import dist_page

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEY = "010950_에쓰오일"
META = f"{KEY}_브렌트연동"
PAGE = dist_page(f"{META}_brent")
START = "2021-01-04"


# ---------- 입력 ----------
def read_fred(sid):
    out = {}
    with open(f"{ROOT}/data/macro/{sid}.csv", encoding="utf-8") as f:
        for r in list(csv.reader(f))[1:]:
            try:
                out[r[0]] = float(r[1])
            except (ValueError, IndexError):
                pass                      # FRED 는 결측을 '.' 로 준다
    return out


def read_prices():
    px = []
    with open(f"{ROOT}/data/prices/{KEY}.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["date"] >= START:
                px.append((r["date"], float(r["close"]), float(r["bm_close"]),
                           float(r["volume"])))
    return px


# ---------- 통계 ----------
def corr(x, y):
    n = len(x)
    if n < 3:
        return float("nan")
    mx, my = sum(x) / n, sum(y) / n
    sx = math.sqrt(sum((a - mx) ** 2 for a in x))
    sy = math.sqrt(sum((b - my) ** 2 for b in y))
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / (sx * sy) if sx and sy else float("nan")


def slope(y, x):
    n = len(x)
    if n < 3:
        return float("nan")
    mx, my = sum(x) / n, sum(y) / n
    den = sum((a - mx) ** 2 for a in x)
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / den if den else float("nan")


def tstat(r, n):
    """상관계수의 t 통계량 (귀무가설 r=0). |t|>2 면 통상 유의."""
    if n < 4 or abs(r) >= 1:
        return float("nan")
    return r * math.sqrt((n - 2) / (1 - r * r))


def main():
    meta = json.load(open(f"{ROOT}/data/meta/{META}.json", encoding="utf-8"))
    px = read_prices()
    brent = read_fred("DCOILBRENTEU")
    ulsd = read_fred("DDFUELUSGULF")
    fx = read_fred("DEXKOUS")
    bdates = sorted(brent)
    cdates = sorted(d for d in ulsd if d in brent)
    fdates = sorted(fx)

    def last_before(arr, d):
        """d 시점에 이미 알려져 있는 마지막 관측일 (d 당일은 제외)."""
        i = bisect.bisect_left(arr, d)
        return arr[i - 1] if i > 0 else None

    def crack(d):
        return ulsd[d] * 42 - brent[d]

    # ---- KRX 거래일 축에 시차 정렬해 붙인다 ----
    dates, close, bm, vol = [], [], [], []
    bser, cser, fser = [], [], []
    for d, c, b, v in px:
        bd = last_before(bdates, d)
        cd = last_before(cdates, d)
        fd = last_before(fdates, d)
        if not (bd and cd and fd):
            continue
        dates.append(d); close.append(c); bm.append(b); vol.append(v)
        bser.append(brent[bd]); cser.append(crack(cd)); fser.append(fx[fd])
    n = len(dates)

    # ---- 일간 변화 ----
    sr = [0.0] * n      # 주가 수익률
    kr = [0.0] * n      # KOSPI 수익률
    ex = [0.0] * n      # 초과수익 (주가 - 지수)
    br = [0.0] * n      # 브렌트 변화율 (이미 1일 시차 반영됨)
    ck = [0.0] * n      # 디젤크랙 변화 (달러)
    for i in range(1, n):
        sr[i] = close[i] / close[i - 1] - 1
        kr[i] = bm[i] / bm[i - 1] - 1
        ex[i] = (close[i] / close[i - 1]) - (bm[i] / bm[i - 1])
        br[i] = bser[i] / bser[i - 1] - 1
        ck[i] = cser[i] - cser[i - 1]

    idx = {d: i for i, d in enumerate(dates)}

    def snap(d):
        """날짜를 실제 거래일 인덱스로 스냅."""
        if d in idx:
            return idx[d]
        cand = [i for i, x in enumerate(dates) if x >= d]
        return cand[0] if cand else n - 1

    # ---- 국면별 집계 ----
    phases = []
    for p in meta["phases"]:
        i0, i1 = snap(p["start"]), snap(p["end"])
        if i1 <= i0:
            continue
        ex_ = [ex[i] for i in range(i0 + 1, i1 + 1)]
        br_ = [br[i] for i in range(i0 + 1, i1 + 1)]
        ck_ = [ck[i] for i in range(i0 + 1, i1 + 1)]
        r_daily = corr(ex_, br_)
        phases.append({
            "label": p["label"], "note": p["note"],
            "start": dates[i0], "end": dates[i1], "i0": i0, "i1": i1, "n": i1 - i0,
            "stock": (close[i1] / close[i0] - 1) * 100,
            "kospi": (bm[i1] / bm[i0] - 1) * 100,
            "excess": ((close[i1] / close[i0]) - (bm[i1] / bm[i0])) * 100,
            "brent": (bser[i1] / bser[i0] - 1) * 100,
            "brentFrom": bser[i0], "brentTo": bser[i1],
            "crackFrom": cser[i0], "crackTo": cser[i1],
            "closeFrom": close[i0], "closeTo": close[i1],
            "levelBrent": corr(close[i0:i1 + 1], bser[i0:i1 + 1]),
            "levelCrack": corr(close[i0:i1 + 1], cser[i0:i1 + 1]),
            "dailyBrent": r_daily,
            "dailyCrack": corr(ex_, ck_),
            "beta": slope(ex_, br_),
            "t": tstat(r_daily, len(ex_)),
        })

    # ---- 전체 구간 ----
    allr = {
        "n": n - 1,
        "levelBrent": corr(close, bser), "levelCrack": corr(close, cser),
        "dailyBrentPrice": corr(sr[1:], br[1:]),
        "dailyBrent": corr(ex[1:], br[1:]),
        "dailyCrack": corr(ex[1:], ck[1:]),
        "beta": slope(ex[1:], br[1:]),
        "t": tstat(corr(ex[1:], br[1:]), n - 1),
    }

    # ---- 롤링 120거래일 상관 ----
    W = 120
    roll_b, roll_c = [None] * n, [None] * n
    for i in range(W, n):
        roll_b[i] = round(corr(ex[i - W + 1:i + 1], br[i - W + 1:i + 1]), 3)
        roll_c[i] = round(corr(ex[i - W + 1:i + 1], ck[i - W + 1:i + 1]), 3)

    # ---- 충격일 이벤트 스터디 ----
    def shock(th):
        up = [i for i in range(1, n) if br[i] > th]
        dn = [i for i in range(1, n) if br[i] < -th]

        def agg(ii, sign):
            if not ii:
                return None
            hit = sum(1 for i in ii if ex[i] * sign > 0)
            return {"n": len(ii), "hit": hit, "rate": hit / len(ii) * 100,
                    "avgStock": sum(sr[i] for i in ii) / len(ii) * 100,
                    "avgExcess": sum(ex[i] for i in ii) / len(ii) * 100}

        quiet = [i for i in range(1, n) if abs(br[i]) <= 0.01]
        return {"th": th * 100, "up": agg(up, 1), "dn": agg(dn, -1),
                "quiet": {"n": len(quiet),
                          "corr": corr([ex[i] for i in quiet], [br[i] for i in quiet])}}

    shocks = [shock(0.03), shock(0.05)]

    # ---- 충격일 상위 목록 ----
    top = sorted(range(1, n), key=lambda i: -abs(br[i]))[:12]
    topshocks = [{"date": dates[i], "brent": br[i] * 100, "stock": sr[i] * 100,
                  "excess": ex[i] * 100, "close": close[i],
                  "brentLevel": bser[i], "crack": cser[i]} for i in top]

    # ---- 산점도 (국면별) ----
    scatter = []
    for pi, p in enumerate(phases):
        for i in range(p["i0"] + 1, p["i1"] + 1):
            scatter.append([round(br[i] * 100, 2), round(ex[i] * 100, 2), pi])

    # ---- 정규화 궤적 ----
    def norm(a):
        return [round(v / a[0] * 100, 2) for v in a]

    # ---- 브렌트 베타로 재구성한 가상 궤적 (설명력 시각화) ----
    beta_all = allr["beta"]
    fit, acc = [], 1.0
    for i in range(n):
        if i:
            acc *= (1 + kr[i] + beta_all * br[i])
        fit.append(round(acc * 100, 2))

    payload = {
        "meta": meta, "dates": dates,
        "close": [round(c) for c in close],
        "bm": [round(v, 2) for v in bm],
        "brent": [round(v, 2) for v in bser],
        "crack": [round(v, 2) for v in cser],
        "fx": [round(v, 1) for v in fser],
        "nClose": norm(close), "nBm": norm(bm), "nBrent": norm(bser),
        "nCrack": norm(cser), "fit": fit,
        "rollBrent": roll_b, "rollCrack": roll_c, "rollWindow": W,
        "phases": phases, "all": allr, "shocks": shocks,
        "topShocks": topshocks, "scatter": scatter,
    }

    if "--md" in sys.argv:
        print_md(payload)
        return

    tpl = open(f"{ROOT}/tools/oil_link_template.html", encoding="utf-8").read()
    js = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    from site_shell import render_nav
    html = tpl.replace("/*__DATA__*/null", js).replace("<!--__SITE_NAV__-->", render_nav("cases"))
    os.makedirs(f"{ROOT}/dist", exist_ok=True)
    out = f"{ROOT}/dist/{PAGE}"
    open(out, "w", encoding="utf-8").write(html)
    print(f"완료: dist/{PAGE}")
    print(f"  거래일 {n}일 ({dates[0]} ~ {dates[-1]}) · 국면 {len(phases)}개")
    print(f"  전체 일간 상관(초과~브렌트) {allr['dailyBrent']:.2f} "
          f"(t={allr['t']:.1f}) · 초과베타 {allr['beta']:.2f}")
    print(f"  HTML {len(html)/1024:.0f} KB")
    if "--skip-portal" not in sys.argv:
        subprocess.run([sys.executable, f"{ROOT}/tools/build_portal.py"], check=True)


def print_md(p):
    a = p["all"]
    print(f"\n## 전체 구간 {p['dates'][0]} ~ {p['dates'][-1]} (거래일 {a['n']+1}일)\n")
    print("| 검정 | 값 | 읽는 법 |")
    print("|---|---|---|")
    print(f"| 레벨 상관 (주가~브렌트) | {a['levelBrent']:.2f} | 추세 공유만으로도 오르는 값 — 보조지표 |")
    print(f"| 레벨 상관 (주가~디젤크랙) | {a['levelCrack']:.2f} | |")
    print(f"| 일간 상관 (주가~브렌트) | {a['dailyBrentPrice']:.2f} | 시장 전체 움직임이 섞여 있음 |")
    print(f"| **일간 상관 (초과수익~브렌트)** | **{a['dailyBrent']:.2f}** | t={a['t']:.1f} · 지수 효과를 뺀 순수 연동 |")
    print(f"| 일간 상관 (초과수익~디젤크랙) | {a['dailyCrack']:.2f} | 크랙은 일 단위로는 잡히지 않는다 |")
    print(f"| **초과베타** | **{a['beta']:.2f}** | 브렌트 +10% → 초과수익 {a['beta']*10:+.1f}%p |")

    print("\n## 국면별 분해\n")
    print("| 국면 | 기간 | 주가 | KOSPI | 초과 | 브렌트 | 디젤크랙 | 레벨상관(브렌트) | 레벨상관(크랙) | 일간상관 |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for x in p["phases"]:
        print(f"| {x['label']} | {x['start']}~{x['end']} | {x['stock']:+.1f}% | {x['kospi']:+.1f}% | "
              f"**{x['excess']:+.1f}%p** | {x['brentFrom']:.0f}→{x['brentTo']:.0f} ({x['brent']:+.0f}%) | "
              f"{x['crackFrom']:.0f}→{x['crackTo']:.0f} | {x['levelBrent']:+.2f} | "
              f"{x['levelCrack']:+.2f} | {x['dailyBrent']:+.2f} |")

    print("\n## 브렌트 충격일 이벤트 스터디\n")
    print("| 임계 | 방향 | 표본 | 초과수익 평균 | 방향일치율 |")
    print("|---|---|---|---|---|")
    for s in p["shocks"]:
        for k, lab in (("up", "상승충격"), ("dn", "하락충격")):
            v = s[k]
            print(f"| \\|Δ\\|>{s['th']:.0f}% | {lab} | {v['n']}회 | {v['avgExcess']:+.2f}%p | "
                  f"{v['rate']:.0f}% ({v['hit']}/{v['n']}) |")
    q = p["shocks"][0]["quiet"]
    print(f"\n- 평시일(\\|Δ\\|≤1%, {q['n']}일)의 초과수익~브렌트 상관: **{q['corr']:.2f}** — 사실상 무관")


if __name__ == "__main__":
    main()
