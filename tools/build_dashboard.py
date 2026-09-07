"""
케이스 대시보드 빌더

    data/prices/<key>.csv  +  data/events/<key>.csv  +  data/meta/<key>.json
        -> dist/<종목코드>_dashboard.html

사용법:
    python tools/build_dashboard.py 007660_이수페타시스

아티팩트는 외부 fetch 가 차단되므로 모든 데이터를 HTML 안에 인라인한다.
파생값(수익률·초과수익·상대강도·거래량배수)은 전부 여기서 계산하고
템플릿은 그리기만 한다 — 계산 로직이 한 곳에만 있도록.
"""
import sys, os, csv, json, io, subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dist_names import dist_page

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read_prices(key):
    rows = []
    with open(f"{ROOT}/data/prices/{key}.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append({
                "date": r["date"],
                "close": float(r["close"]),
                "vol": float(r["volume"]),
                "bm": float(r["bm_close"]),
            })
    return rows


def read_flows(key, dates):
    """투자자별 순매수 금액(억원) 누적. 키움(개인 포함) 우선, 없으면 네이버 폴백."""
    kiwoom = f"{ROOT}/data/investors/{key}.csv"
    naver = f"{ROOT}/data/flows/{key}.csv"
    raw, src = {}, None
    detail, rawclose, prica = {}, {}, {}
    if os.path.exists(kiwoom):                    # 키움 ka10059 — 금액 기준, 개인 포함
        src = "키움 ka10059 (개인 포함 · 금액 기준)"
        with open(kiwoom, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                raw[r["date"]] = (float(r["indiv"] or 0), float(r["frgn"] or 0),
                                  float(r["orgn"] or 0))
                rawclose[r["date"]] = float(r["close"] or 0)
                prica[r["date"]] = float(r["trde_prica"] or 0)
                detail[r["date"]] = {k: float(r.get(k) or 0) for k in
                                     ("fin_invt", "insur", "invtrt", "etc_fin",
                                      "bank", "pension", "pe_fund", "natn")}
    elif os.path.exists(naver):                   # 폴백 — 수량x원주가, 개인 없음
        src = "네이버 (외국인·기관만 · 수량 환산)"
        with open(naver, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                c = float(r["close"] or 0)
                raw[r["date"]] = (0.0, float(r["frgn_net"] or 0) * c / 1e8,
                                  float(r["inst_net"] or 0) * c / 1e8)
    else:
        return None
    ind, frgn, inst = [], [], []
    a = b = c2 = 0.0
    for d in dates:
        x, y, z = raw.get(d, (0.0, 0.0, 0.0))
        a += x; b += y; c2 += z
        ind.append(round(a, 1)); frgn.append(round(b, 1)); inst.append(round(c2, 1))
    return {"cumInd": ind, "cumFrgn": frgn, "cumInst": inst,
            "source": src, "hasIndiv": os.path.exists(kiwoom),
            "raw": raw, "detail": detail, "rawClose": rawclose, "trdePrica": prica}


ORGN_SUB = [("fin_invt", "금융투자"), ("invtrt", "투신"), ("pension", "연기금등"),
            ("pe_fund", "사모펀드"), ("insur", "보험"), ("bank", "은행"),
            ("etc_fin", "기타금융"), ("natn", "국가")]


def read_shares(key):
    """유동주식수 / 유통비율 / 상장주식수 변동 이력."""
    p = f"{ROOT}/data/shares/{key}.json"
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None


def read_events(key):
    with open(f"{ROOT}/data/events/{key}.csv", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def portal_context(meta):
    """통합 포털의 탐색 문구와 같은 이슈 사례 링크를 만든다."""
    nav_path = f"{ROOT}/data/navigation.json"
    cases_path = f"{ROOT}/data/cases.csv"
    if not (os.path.exists(nav_path) and os.path.exists(cases_path)):
        return {"summary": "사건과 이후의 시장 반응을 지수 대비로 확인합니다.", "related": []}
    navigation = json.load(open(nav_path, encoding="utf-8"))
    with open(cases_path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    same_code = [r for r in rows if r["종목코드"] == meta["code"]]
    # 같은 종목에 케이스가 둘 이상이면 이슈유형까지 맞춰야 관련 사례가 뒤바뀌지 않는다.
    current = next((r for r in same_code if r["이슈유형"] == meta.get("issue_type")),
                   same_code[0] if same_code else None)
    if not current:
        return {"summary": "사건과 이후의 시장 반응을 지수 대비로 확인합니다.", "related": []}
    edits = {r["case_id"]: r for r in navigation.get("cases", [])}
    edit = edits.get(current["case_id"], {})
    related = []
    for row in rows:
        if row["case_id"] == current["case_id"] or row["이슈유형"] != current["이슈유형"]:
            continue
        other = edits.get(row["case_id"], {})
        href = row["대시보드"].replace("\\", "/")
        if href.startswith("dist/"):
            href = href[5:]
        related.append({
            "name": row["종목명"],
            "title": other.get("title", row["이슈유형"]),
            "href": href,
            "reason": f"같은 {row['이슈유형']} 사례",
        })
    return {
        "summary": edit.get("summary", "사건과 이후의 시장 반응을 지수 대비로 확인합니다."),
        "related": related,
    }


def main():
    key = sys.argv[1]
    meta = json.load(open(f"{ROOT}/data/meta/{key}.json", encoding="utf-8"))
    # 한 종목에 이슈가 둘 이상이면 시세·수급·유통주식은 공유하고 이벤트만 분리한다.
    # meta의 data_key 가 시세 계열 파일의 키, key 는 이벤트·산출물의 키다.
    dkey = meta.get("data_key", key)
    rows = read_prices(dkey)
    events = read_events(key)
    portal = portal_context(meta)

    dates = [r["date"] for r in rows]
    close = [r["close"] for r in rows]
    bm = [r["bm"] for r in rows]
    vol = [r["vol"] for r in rows]
    n = len(rows)
    avg_vol = sum(vol) / n

    # ---- 자금 유입: 거래대금과 60일 이동평균 ----
    flows = read_flows(dkey, dates)
    shares = read_shares(dkey)
    # 거래대금: 키움 실거래대금(억원) 우선. 없으면 수정주가x거래량 근사
    if flows and flows.get("trdePrica"):
        val = [flows["trdePrica"].get(dates[i], 0.0) * 1e8 or close[i] * vol[i]
               for i in range(n)]
    else:
        val = [close[i] * vol[i] for i in range(n)]
    MA = 60
    val_ma = []
    for i in range(n):
        w = val[max(0, i - MA + 1):i + 1]
        val_ma.append(sum(w) / len(w))
    val_mult = [val[i] / val_ma[i] if val_ma[i] else 0 for i in range(n)]
    avg_val = sum(val) / n

    # ---- 유동시가총액 대비 회전율 ----
    # 총시총이 아니라 **유동시총**으로 나눈다. 최대주주·자사주·보호예수 물량은
    # 거래에 나오지 않으므로 총시총을 쓰면 분모가 부풀고 종목 간 비교가 깨진다.
    turn = None
    if shares:
        fr = shares["float_ratio"]
        steps = sorted(shares["steps"], key=lambda s: s["from"])
        listed = []
        for d in dates:
            cur = steps[0]["listed"]
            for s in steps:
                if d >= s["from"]:
                    cur = s["listed"]
            listed.append(cur)
        rc = flows.get("rawClose", {}) if flows else {}
        fcap = [(rc.get(dates[i]) or close[i]) * listed[i] * fr for i in range(n)]
        turn = [round(val[i] / fcap[i] * 100, 3) if fcap[i] else 0 for i in range(n)]
        fcap_eok = [round(c / 1e8) for c in fcap]

    # D-day -> 첫 거래일로 스냅
    dday = meta["dday"]
    i0 = next(i for i, d in enumerate(dates) if d >= dday)
    b_close, b_bm = close[i0], bm[i0]

    def rs_at(i):
        return (close[i] / b_close) / (bm[i] / b_bm) * 100

    # ---- 이벤트: 거래일 스냅 + 당일 등락/초과/거래량배수 ----
    ev_out = []
    for k, e in enumerate(events):
        idx = next((i for i, d in enumerate(dates) if d >= e["date"]), None)
        if idx is None:
            continue
        prev = idx - 1
        chg = (close[idx] / close[prev] - 1) * 100 if prev >= 0 else 0.0
        bchg = (bm[idx] / bm[prev] - 1) * 100 if prev >= 0 else 0.0
        ev_out.append({
            "n": k + 1,
            "i": idx,
            "date": e["date"],
            "tradingDate": dates[idx],
            "snapped": dates[idx] != e["date"],
            "phase": e["phase"],
            "category": e["category"],
            "impact": e["impact"],
            "title": e["title"],
            "detail": e.get("detail", ""),
            "verified": e.get("verified", ""),
            "source": e.get("source", ""),
            "close": close[idx],
            "chg": round(chg, 2),
            "bmChg": round(bchg, 2),
            "excess": round(chg - bchg, 2),
            "volMult": round(vol[idx] / avg_vol, 1),
            "val": round(val[idx] / 1e8),                 # 억원
            "valMult": round(val_mult[idx], 1),           # 60일 평균 대비
            "rs": round(rs_at(idx), 1),
        })

    # ---- 구간 수익률 ----
    periods = []
    marks = [("D-day", 0), ("D+1", 1), ("D+5", 5), ("D+20", 20), ("D+60", 60),
             ("D+120", 120), ("D+250", 250), ("D+500", 500), ("최근", n - 1 - i0)]
    seen = set()
    for label, off in marks:
        j = i0 + off
        if j >= n or j in seen:
            continue
        seen.add(j)
        sr = (close[j] / b_close - 1) * 100
        br = (bm[j] / b_bm - 1) * 100
        periods.append({
            "label": label, "date": dates[j], "close": close[j],
            "sr": round(sr, 1), "br": round(br, 1),
            "ex": round(sr - br, 1), "rs": round(rs_at(j), 1),
        })

    # ---- 요약 통계 ----
    seg = range(i0, n)
    lo_i = min(seg, key=lambda i: close[i])
    hi_i = max(seg, key=lambda i: close[i])
    rs_lo_i = min(seg, key=rs_at)
    rs_hi_i = max(seg, key=rs_at)
    price_rec = next((i for i in range(i0 + 1, n) if close[i] >= b_close), None)
    rs_rec = next((i for i in range(i0 + 1, n) if rs_at(i) >= 100), None)

    stats = {
        "ddayDate": dates[i0],
        "ddayClose": b_close,
        "lastDate": dates[-1],
        "lastClose": close[-1],
        "srTotal": round((close[-1] / b_close - 1) * 100, 1),
        "brTotal": round((bm[-1] / b_bm - 1) * 100, 1),
        "exTotal": round(((close[-1] / b_close) - (bm[-1] / b_bm)) * 100, 1),
        "rsLast": round(rs_at(n - 1), 1),
        "troughPct": round((close[lo_i] / b_close - 1) * 100, 1),
        "troughDate": dates[lo_i],
        "peakPct": round((close[hi_i] / b_close - 1) * 100, 1),
        "peakDate": dates[hi_i],
        "rsMin": round(rs_at(rs_lo_i), 1), "rsMinDate": dates[rs_lo_i],
        "rsMax": round(rs_at(rs_hi_i), 1), "rsMaxDate": dates[rs_hi_i],
        "priceRecDays": (price_rec - i0) if price_rec else None,
        "priceRecDate": dates[price_rec] if price_rec else None,
        "rsRecDays": (rs_rec - i0) if rs_rec else None,
        "rsRecDate": dates[rs_rec] if rs_rec else None,
        "startDate": dates[0],
        "srFull": round((close[-1] / close[0] - 1) * 100, 1),
        "brFull": round((bm[-1] / bm[0] - 1) * 100, 1),
    }

    # ---- 국면별 성과 (지수편입 등 앵커가 여러 개인 이슈용) ----
    def snap(d):
        return next((i for i, x in enumerate(dates) if x >= d), n - 1)

    phases = []
    for ph in meta.get("phases", []):
        a, b = snap(ph["start"]), snap(ph["end"])
        sr = (close[b] / close[a] - 1) * 100
        br = (bm[b] / bm[a] - 1) * 100
        seg_val = val[a:b + 1] or [0]
        pavg = sum(seg_val) / len(seg_val)
        phases.append({
            "label": ph["label"], "note": ph.get("note", ""),
            "from": dates[a], "to": dates[b], "days": b - a,
            "sr": round(sr, 1), "br": round(br, 1), "ex": round(sr - br, 1),
            "rsEnd": round(rs_at(b), 1),
            "avgVal": round(pavg / 1e8),                  # 구간 평균 일거래대금(억)
            "valVsBase": round(pavg / avg_val, 2),        # 전체 평균 대비
            "turn": round(sum(turn[a:b + 1]) / max(b - a + 1, 1), 3) if turn else None,
        })
    for i, ph in enumerate(phases):                       # 직전 국면 대비
        ph["valVsPrev"] = round(ph["avgVal"] / phases[i-1]["avgVal"], 2) if i else None
    stats["phases"] = phases

    if flows:
        for ph in phases:
            a, b = snap(ph["from"]), snap(ph["to"])
            ph["instNet"] = round(flows["cumInst"][b] - flows["cumInst"][a])
            ph["frgnNet"] = round(flows["cumFrgn"][b] - flows["cumFrgn"][a])
            ph["indNet"] = round(flows["cumInd"][b] - flows["cumInd"][a])
            det = flows.get("detail") or {}
            if det:
                sub = {}
                for src_k, ko in ORGN_SUB:
                    sub[ko] = round(sum(det.get(dates[x], {}).get(src_k, 0.0)
                                        for x in range(a + 1, b + 1)))
                ph["orgnSub"] = sub


    # ---- 자금 유입 요약 ----
    top = sorted(range(n), key=lambda i: -val[i])[:15]
    up = sum(1 for i in top if i > 0 and close[i] > close[i-1])
    stats["shares"] = ({"listed": shares["listed_now"],
                        "floatShares": shares["float_shares_now"],
                        "floatRatio": round(shares["float_ratio"] * 100, 1),
                        "asOf": shares["as_of"], "note": shares["note"]} if shares else None)
    stats["flow"] = {
        "avgTurn": round(sum(turn) / n, 3) if turn else None,
        "recentTurn": round(sum(turn[-20:]) / 20, 3) if turn else None,
        "avgVal": round(avg_val / 1e8),
        "peakVal": round(max(val) / 1e8), "peakDate": dates[val.index(max(val))],
        "topUpRatio": f"{up}/{len(top)}",
        "recentVal": round(sum(val[-20:]) / 20 / 1e8),
        "recentMult": round((sum(val[-20:]) / 20) / avg_val, 2),
        "instTotal": round(flows["cumInst"][-1] - flows["cumInst"][i0]) if flows else None,
        "frgnTotal": round(flows["cumFrgn"][-1] - flows["cumFrgn"][i0]) if flows else None,
        "indTotal": round(flows["cumInd"][-1] - flows["cumInd"][i0]) if flows else None,
        "flowSource": flows["source"] if flows else None,
        "hasIndiv": flows["hasIndiv"] if flows else False,
        "topDays": [{"date": dates[i], "val": round(val[i] / 1e8),
                     "mult": round(val_mult[i], 1),
                     "chg": round((close[i] / close[i-1] - 1) * 100, 1) if i else 0}
                    for i in sorted(top)],
    }

    band = meta.get("band")
    if band:
        stats["band"] = {"i0": snap(band["start"]), "i1": snap(band["end"]),
                         "label": band["label"]}
    elif rs_rec:
        stats["band"] = {"i0": i0, "i1": rs_rec,
                         "label": f"악재 반영 구간 (기준일 → RS 회복 {rs_rec - i0}거래일)"}

    # ---- KPI (이슈 유형에 따라 구성이 달라진다) ----
    nm, bl = meta["name"], meta["benchmark_label"]
    if phases:
        peak = max(range(i0, n), key=rs_at)
        stats["kpis"] = [
            {"k": f"{nm} 수익률", "v": f"{stats['srTotal']:+.0f}%", "tone": stats["srTotal"],
             "n": f"{dates[i0]} → {dates[-1]}"},
            {"k": f"{bl} 동기간", "v": f"{stats['brTotal']:+.0f}%", "tone": stats["brTotal"],
             "n": "같은 기간 지수"},
            {"k": "초과수익", "v": f"{stats['exTotal']:+.0f}%p", "hero": 1,
             "n": f"현재 상대강도 RS {stats['rsLast']}"},
            {"k": "RS 최고", "v": f"{stats['rsMax']:.0f}", "n": stats["rsMaxDate"]},
            {"k": "RS 고점 → 현재", "v": f"{stats['rsMax']:.0f} → {stats['rsLast']:.0f}",
             "tone": stats["rsLast"] - stats["rsMax"],
             "n": f"고점 이후 {rs_at(n-1) - rs_at(peak):+.0f}p"},
            {"k": "RS 최저", "v": f"{stats['rsMin']:.0f}", "n": stats["rsMinDate"]},
        ]
    else:
        stats["kpis"] = [
            {"k": f"{nm} 수익률", "v": f"{stats['srTotal']:+.0f}%", "tone": stats["srTotal"],
             "n": f"{dates[i0]} → {dates[-1]}"},
            {"k": f"{bl} 동기간", "v": f"{stats['brTotal']:+.0f}%", "tone": stats["brTotal"],
             "n": "같은 기간 지수 상승률"},
            {"k": "초과수익", "v": f"{stats['exTotal']:+.0f}%p", "hero": 1,
             "n": f"상대강도 RS {stats['rsLast']}"},
            {"k": "기준일 대비 최저", "v": f"{stats['troughPct']:+.0f}%",
             "tone": stats["troughPct"], "n": stats["troughDate"]},
            {"k": "상대강도 회복",
             "v": (f"{stats['rsRecDays']}일" if stats["rsRecDays"] else "미회복"),
             "n": f"거래일 기준 · {stats['rsRecDate'] or '-'}"},
            {"k": "RS 고점→현재", "v": f"{stats['rsMax']:.0f} → {stats['rsLast']:.0f}",
             "n": f"고점 {stats['rsMaxDate']}"},
        ]

    payload = {
        "meta": meta, "dates": dates,
        "close": [round(c, 1) for c in close],
        "bm": [round(v, 2) for v in bm],
        "vol": [int(v) for v in vol],
        "val": [round(v / 1e8) for v in val],
        "valMa": [round(v / 1e8) for v in val_ma],
        "turn": turn,
        "fcap": fcap_eok if turn else None,
        "cumInst": flows["cumInst"] if flows else None,
        "cumFrgn": flows["cumFrgn"] if flows else None,
        "cumInd": flows["cumInd"] if flows else None,
        "ddayIndex": i0, "events": ev_out,
        "periods": periods, "stats": stats,
    }

    tpl = open(f"{ROOT}/tools/dashboard_template.html", encoding="utf-8").read()
    js = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    portal_js = json.dumps(portal, ensure_ascii=False, separators=(",", ":"))
    from site_shell import render_nav
    html = tpl.replace("/*__DATA__*/null", js)
    html = html.replace("<!--__SITE_NAV__-->", render_nav("cases"))
    html = html.replace("/*__PORTAL__*/null", portal_js)
    html = html.replace("__TITLE__", f'{meta["name"]} {meta["issue_type"]} 해부')

    os.makedirs(f"{ROOT}/dist", exist_ok=True)
    page = dist_page(f"{key}_dashboard")
    out = f"{ROOT}/dist/{page}"
    open(out, "w", encoding="utf-8").write(html)

    print(f"완료: dist/{page}")
    print(f"  거래일 {n}일 · 이벤트 {len(ev_out)}건 · D-day {dates[i0]}")
    print(f"  종목 {stats['srTotal']:+}% / {meta['benchmark_label']} {stats['brTotal']:+}%"
          f" / 초과 {stats['exTotal']:+}%p / RS {stats['rsLast']}")
    print(f"  HTML {len(html)/1024:.0f} KB")
    if "--skip-portal" not in sys.argv:
        subprocess.run([sys.executable, f"{ROOT}/tools/build_portal.py"], check=True)


if __name__ == "__main__":
    main()
