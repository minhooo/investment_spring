"""OpenDART 주요사항보고서에서 상장사의 자금조달 결정 데이터를 수집한다.

현재 범위는 유상증자·전환사채(CB)·신주인수권부사채(BW)·교환사채(EB)다.
발행결정 공시를 기준으로 하며 납입 완료나 실제 자금 집행을 뜻하지 않는다.

사용법:
    python tools/fetch_financing_data.py --start 20260101 --end 20260908
"""
from __future__ import annotations

import argparse
import calendar
import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import dart  # noqa: E402

OUT = ROOT / "data" / "financing" / "2026-ytd.json"
TARGETS = {
    "RIGHTS": {"label": "유상증자", "needle": "유상증자결정", "endpoint": "piicDecsn.json"},
    "CB": {"label": "CB", "needle": "전환사채권발행결정", "endpoint": "cvbdIsDecsn.json"},
    "BW": {"label": "BW", "needle": "신주인수권부사채권발행결정", "endpoint": "bdwtIsDecsn.json"},
    "EB": {"label": "EB", "needle": "교환사채권발행결정", "endpoint": "exbdIsDecsn.json"},
}
PROCEEDS = {
    "facility": ("시설투자", "fdpp_fclt"),
    "acquisition": ("타법인증권 취득", "fdpp_bsninh"),
    "operations": ("운영자금", "fdpp_op"),
    "debt": ("채무상환", "fdpp_dtrp"),
    "overseas": ("해외투자", "fdpp_ocsa"),
    "other": ("기타", "fdpp_etc"),
}


def months(start: str, end: str):
    first = datetime.strptime(start, "%Y%m%d").date().replace(day=1)
    last = datetime.strptime(end, "%Y%m%d").date().replace(day=1)
    cur = first
    while cur <= last:
        final_day = calendar.monthrange(cur.year, cur.month)[1]
        bgn = cur.strftime("%Y%m%d")
        fin = min(date(cur.year, cur.month, final_day), datetime.strptime(end, "%Y%m%d").date())
        yield bgn, fin.strftime("%Y%m%d")
        cur = date(cur.year + (cur.month == 12), 1 if cur.month == 12 else cur.month + 1, 1)


def integer(value) -> int:
    text = str(value or "").strip()
    if not text or text == "-":
        return 0
    sign = -1 if text.startswith("-") else 1
    digits = re.sub(r"[^0-9]", "", text)
    return sign * int(digits) if digits else 0


def number(value):
    text = str(value or "").strip().replace(",", "")
    if not text or text == "-":
        return None
    try:
        return float(text)
    except ValueError:
        return None


def iso_date(value) -> str:
    match = re.search(r"(\d{4})\D*(\d{1,2})\D*(\d{1,2})", str(value or ""))
    if not match:
        return ""
    return "-".join(part.zfill(2) for part in match.groups())


def listed_stock_codes() -> dict[str, str]:
    """DART 고유번호 XML의 상장 종목코드만 매핑한다."""
    dart.corp_code("005930")  # cache가 없으면 공식 XML을 내려받는다.
    xml = ROOT / "data" / ".cache" / "corpcode.xml"
    mapping = {}
    for item in ET.parse(xml).getroot().iter("list"):
        corp = (item.findtext("corp_code") or "").strip()
        stock = (item.findtext("stock_code") or "").strip()
        if corp and stock:
            mapping[corp] = stock
    return mapping


def decision_reports(start: str, end: str):
    """월별 주요사항보고서에서 대상 자금조달 공시의 법인을 모은다."""
    found = defaultdict(set)
    for bgn, fin in months(start, end):
        first = dart.get("list.json", bgn_de=bgn, end_de=fin, pblntf_ty="B", page_count=100)
        if first.get("status") not in {"000", "013"}:
            raise RuntimeError(f"DART 목록 조회 실패: {first.get('message')}")
        total = int(first.get("total_page") or 0)
        pages = [first] + [dart.get("list.json", bgn_de=bgn, end_de=fin, pblntf_ty="B", page_no=page, page_count=100)
                           for page in range(2, total + 1)]
        for page in pages:
            for report in page.get("list", []):
                title = report.get("report_nm", "")
                for kind, spec in TARGETS.items():
                    if spec["needle"] in title:
                        found[(report.get("corp_code", ""), kind)].add(report.get("rcept_no", ""))
    return found


def first_value(row: dict, keys: tuple[str, ...]):
    for key in keys:
        value = row.get(key)
        if integer(value):
            return integer(value), key
    return 0, ""


def normalize(kind: str, row: dict, stock_code: str):
    proceeds = {key: integer(row.get(field)) for key, (_, field) in PROCEEDS.items()}
    amount, amount_field = first_value(row, ("bd_fta", "nstk_ostk_ascnt", "nstk_ostk_cnt", "fdpp_op"))
    if sum(proceeds.values()):
        amount, amount_field = sum(proceeds.values()), "use_of_proceeds_total"
    shares, _ = first_value(row, ("cvisstk_cnt", "exstk_cnt", "nstk_ostk_cnt"))
    dilution = number(row.get("cvisstk_tisstk_vs"))
    if dilution is None:
        dilution = number(row.get("exstk_tisstk_vs"))
    price, _ = first_value(row, ("cv_prc", "ex_prc", "nstk_ostk_fv"))
    start = iso_date(row.get("cvrqpd_bgd") or row.get("exrqpd_bgd"))
    end = iso_date(row.get("cvrqpd_edd") or row.get("exrqpd_edd"))
    rcept_no = str(row.get("rcept_no") or "")
    decision_date = iso_date(row.get("bddd") or row.get("decsn_d"))
    date_basis = "이사회 결의일"
    if not decision_date and rcept_no:
        decision_date = iso_date(rcept_no[:8])
        date_basis = "공시 접수일"
    return {
        "id": f"{kind}-{row.get('corp_code')}-{rcept_no}",
        "kind": kind,
        "kind_label": TARGETS[kind]["label"],
        "corp_code": row.get("corp_code", ""),
        "name": row.get("corp_name", ""),
        "stock_code": stock_code,
        "decision_date": decision_date,
        "date_basis": date_basis,
        "amount": amount,
        "amount_field": amount_field,
        "proceeds": proceeds,
        "method": row.get("bdis_mthn") or row.get("ic_mthn") or "",
        "security": row.get("bd_knd") or "",
        "conversion_price": price or None,
        "potential_shares": shares or None,
        "dilution_pct": dilution,
        "conversion_start": start,
        "conversion_end": end,
        "maturity": iso_date(row.get("bd_mtd")),
        "rcept_no": rcept_no,
        "source_url": f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={rcept_no}" if rcept_no else "",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", default="20260101")
    parser.add_argument("--end", default=date.today().strftime("%Y%m%d"))
    args = parser.parse_args()
    source_index = decision_reports(args.start, args.end)
    stocks = listed_stock_codes()
    events = []
    for (corp_code, kind) in sorted(source_index):
        stock_code = stocks.get(corp_code)
        if not stock_code:
            continue
        result = dart.get(TARGETS[kind]["endpoint"], corp_code=corp_code, bgn_de=args.start, end_de=args.end)
        if result.get("status") not in {"000", "013"}:
            raise RuntimeError(f"{kind} {corp_code}: {result.get('message')}")
        for row in result.get("list", []):
            event = normalize(kind, row, stock_code)
            if event["decision_date"] and args.start <= event["decision_date"].replace("-", "") <= args.end:
                events.append(event)
    # 같은 발행결정을 정정한 여러 공시는 접수번호가 가장 큰 최종 항목 하나만 남긴다.
    deduped = {}
    for event in events:
        key = (event["corp_code"], event["kind"], event["decision_date"], event["amount"])
        if key not in deduped or event["rcept_no"] > deduped[key]["rcept_no"]:
            deduped[key] = event
    events = sorted(deduped.values(), key=lambda row: (row["decision_date"], row["rcept_no"]), reverse=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "as_of": f"{args.end[:4]}-{args.end[4:6]}-{args.end[6:]}",
        "scope": "OpenDART 주요사항보고서 기준 상장사 발행결정 공시. 실제 납입·집행·상환 데이터는 포함하지 않음.",
        "instruments": ["RIGHTS", "CB", "BW", "EB"],
        "source": {
            "name": "OpenDART 주요사항보고서 API",
            "url": "https://opendart.fss.or.kr/guide/main.do",
            "classification": "SOURCE DATA",
        },
        "events": events,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"자금조달 결정 {len(events)}건 저장: {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

