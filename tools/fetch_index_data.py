"""KOSPI 200 현재 구성 스냅샷 수집기.

네이버 증권의 KOSPI200 편입종목 화면을 정규화한다. KRX 원본 수집 경로가
연결되기 전의 보조 출처이므로 결과에 source/quality flag를 보존한다.
"""
import argparse
import csv
import datetime as dt
import json
import re
import time
import urllib.request
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "indexes" / "kospi200"
HEADERS = {"User-Agent": "Mozilla/5.0", "Referer": "https://finance.naver.com/"}
URL = "https://finance.naver.com/sise/entryJongmok.naver?type=KPI200&page={}"


def number(value):
    value = re.sub(r"<.*?>", "", value)
    return int(re.sub(r"[^0-9]", "", unescape(value)) or 0)


def fetch_page(page):
    request = urllib.request.Request(URL.format(page), headers=HEADERS)
    raw = urllib.request.urlopen(request, timeout=30).read().decode("euc-kr", "replace")
    rows = re.findall(r"<tr>\s*<td class=\"ctg\"><a href=\"/item/main\.naver\?code=([A-Za-z0-9]+)\"[^>]*>(.*?)</a></td>(.*?)</tr>", raw, re.S)
    result = []
    for code, name, cells in rows:
        values = re.findall(r"<td[^>]*>(.*?)</td>", cells, re.S)
        if len(values) < 6:
            continue
        result.append({
            "security_id": f"KRX:{code}", "ticker": code, "name": unescape(re.sub(r"<.*?>", "", name)).strip(),
            "price": number(values[0]), "market_cap_eok": number(values[5]), "sector": "업종 원천 미연결",
        })
    return result


def signed_number(value):
    return int(re.sub(r"[^0-9]", "", str(value)) or 0)


def enrich_with_kiwoom(members):
    """ka10001로 가격·시총·유통주식수 현재 스냅샷을 보강한다.

    구성목록 자체를 키움 데이터라고 오인하지 않도록, 목록 수집과 보강을 분리한다.
    """
    import sys
    sys.path.insert(0, str(ROOT / "tools"))
    from fetch_investors import token
    access_token = token()
    failures = []
    targets = [row for row in members if not row.get("float_market_cap_eok")]
    for position, row in enumerate(targets, start=1):
        request = urllib.request.Request(
            "https://api.kiwoom.com/api/dostk/stkinfo",
            data=json.dumps({"stk_cd": row["ticker"]}).encode(),
            headers={"Content-Type": "application/json;charset=UTF-8", "authorization": f"Bearer {access_token}",
                     "api-id": "ka10001", "cont-yn": "N", "next-key": ""},
        )
        try:
            response = json.loads(urllib.request.urlopen(request, timeout=25).read().decode())
            if response.get("return_code") != 0:
                raise RuntimeError(response.get("return_msg") or "unknown API error")
            row["price"] = signed_number(response.get("cur_prc"))
            row["market_cap_eok"] = signed_number(response.get("mac"))
            row["listed_shares"] = signed_number(response.get("flo_stk")) * 1000
            row["float_shares"] = signed_number(response.get("dstr_stk")) * 1000
            row["float_ratio"] = float(str(response.get("dstr_rt") or "0").replace(",", ""))
            row["float_market_cap_eok"] = round(row["market_cap_eok"] * row["float_ratio"] / 100, 3)
        except Exception as exc:
            failures.append({"ticker": row["ticker"], "reason": str(exc)[:120]})
        if position % 25 == 0 or position == len(targets):
            print(f"  키움 보강 {position}/{len(targets)}", flush=True)
        time.sleep(0.08)
    return failures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", default="kospi200", choices=["kospi200"])
    parser.add_argument("--as-of", help="기준일 YYYY-MM-DD; 생략하면 수집일")
    parser.add_argument("--market-provider", choices=["kiwoom", "naver"], default="kiwoom",
                        help="가격·시가총액·유통주식수 보강 원천 (기본: kiwoom)")
    parser.add_argument("--resume", action="store_true", help="이전 키움 보강 실패 종목만 재시도")
    args = parser.parse_args()
    previous = OUT / "constituents_latest.csv"
    if args.resume and previous.exists():
        with previous.open(encoding="utf-8", newline="") as f:
            members = list(csv.DictReader(f))
    else:
        members = []
        for page in range(1, 22):
            members.extend(fetch_page(page))
        members = list({row["ticker"]: row for row in members}.values())
    if not 195 <= len(members) <= 205:
        raise RuntimeError(f"KOSPI 200 구성종목 수가 허용 범위를 벗어났습니다: {len(members)}")
    members.sort(key=lambda row: int(row["market_cap_eok"]), reverse=True)
    failures = enrich_with_kiwoom(members) if args.market_provider == "kiwoom" else []
    members.sort(key=lambda row: int(row["market_cap_eok"]), reverse=True)
    as_of = args.as_of or dt.date.today().isoformat()
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "constituents_latest.csv").open("w", encoding="utf-8", newline="") as f:
        fields = ["security_id", "ticker", "name", "sector", "price", "market_cap_eok", "listed_shares", "float_shares", "float_ratio", "float_market_cap_eok"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader(); writer.writerows(members)
    master = ROOT / "data" / "indexes" / "security_master.csv"
    with master.open("w", encoding="utf-8", newline="") as f:
        fields = ["security_id", "ticker", "name", "sector"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader(); writer.writerows([{key: row[key] for key in fields} for row in members])
    (OUT / "source_latest.json").write_text(json.dumps({
        "index_id": "kospi200", "as_of": as_of, "collected_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "source": {"name": "네이버 증권 KOSPI200 구성목록 · 키움증권 ka10001 보강", "url": "https://finance.naver.com/sise/sise_index.naver?code=KPI200", "kind": "constituent_list_plus_kiwoom_current_snapshot", "market_data_source": "키움증권 REST ka10001 (현재가·시가총액·유통주식수·유통비율)"},
        "quality_flags": ["non_krx_constituent_source", "official_weight_unavailable", "index_shares_unavailable", "sector_source_unavailable"]
        + (["kiwoom_enrichment_partial"] if failures else [])
        + (["unexpected_constituent_count"] if len(members) != 200 else []),
        "enrichment_failures": failures,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"저장: {OUT.relative_to(ROOT)} · 구성종목 {len(members)}개 · 기준일 {as_of}")


if __name__ == "__main__":
    main()
