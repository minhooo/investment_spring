"""KOSPI 200 정기변경 History 페이지와 공개 payload를 생성한다."""
import csv
import datetime as dt
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from site_shell import render_nav

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "data" / "indexes" / "kospi200"
DIST = ROOT / "dist"
REVIEW_ID = "2026-h1"
INVESTOR_FILES = {
    "267270": ROOT / "data" / "investors" / "267270_HD건설기계.csv",
    "000990": ROOT / "data" / "investors" / "000990_DB하이텍.csv",
    "483650": ROOT / "data" / "investors" / "483650_달바글로벌.csv",
    "456040": ROOT / "data" / "investors" / "456040_OCI.csv",
}


def number(row, key):
    return float(row.get(key) or 0)


def pct(start, end):
    return round((end / start - 1) * 100, 1) if start else None


def load_market(member, review):
    path = INVESTOR_FILES[member["ticker"]]
    with path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    rows = [row for row in rows if row["date"] <= "2026-07-10"]
    by_date = {row["date"]: row for row in rows}
    required = [review["data_cutoff_at"], review["announcement_at"], review["rebalance_at"], review["effective_at"]]
    missing = [date for date in required if date not in by_date]
    if missing:
        raise ValueError(f"{member['ticker']} 필수 거래일 누락: {', '.join(missing)}")

    signal_start = member["signal_start"]
    review_rows = [row for row in rows if signal_start <= row["date"] <= review["data_cutoff_at"]]
    if not review_rows:
        raise ValueError(f"{member['ticker']} 심사구간 데이터 없음")
    event_rows = [row for row in rows if review["announcement_at"] <= row["date"] <= review["effective_at"]]
    post_rows = [row for row in rows if row["date"] > review["effective_at"]]
    if len(post_rows) < 20:
        raise ValueError(f"{member['ticker']} 편입 후 20거래일 데이터 부족")

    start_close = number(review_rows[0], "close")
    cutoff_close = number(by_date[review["data_cutoff_at"]], "close")
    announcement_close = number(by_date[review["announcement_at"]], "close")
    rebalance_close = number(by_date[review["rebalance_at"]], "close")
    effective_close = number(by_date[review["effective_at"]], "close")
    avg_turnover = sum(number(row, "trde_prica") for row in review_rows) / len(review_rows)
    last20 = review_rows[-20:]
    avg_turnover_20d = sum(number(row, "trde_prica") for row in last20) / len(last20)

    observed = {
        "signal_start": review_rows[0]["date"],
        "signal_end": review_rows[-1]["date"],
        "trading_days": len(review_rows),
        "start_close": round(start_close),
        "cutoff_close": round(cutoff_close),
        "review_return_pct": pct(start_close, cutoff_close),
        "avg_trading_value_eok": round(avg_turnover, 1),
        "last20_avg_trading_value_eok": round(avg_turnover_20d, 1),
        "turnover_acceleration_pct": pct(avg_turnover, avg_turnover_20d),
        "review_flow_eok": {
            "individual": round(sum(number(row, "indiv") for row in review_rows), 1),
            "foreign": round(sum(number(row, "frgn") for row in review_rows), 1),
            "institution": round(sum(number(row, "orgn") for row in review_rows), 1),
        },
        "cutoff_to_announcement_pct": pct(cutoff_close, announcement_close),
        "announcement_to_rebalance_pct": pct(announcement_close, rebalance_close),
        "announcement_to_effective_pct": pct(announcement_close, effective_close),
        "event_flow_eok": {
            "individual": round(sum(number(row, "indiv") for row in event_rows), 1),
            "foreign": round(sum(number(row, "frgn") for row in event_rows), 1),
            "institution": round(sum(number(row, "orgn") for row in event_rows), 1),
        },
        "post_5d_return_pct": pct(effective_close, number(post_rows[4], "close")),
        "post_20d_return_pct": pct(effective_close, number(post_rows[19], "close")),
    }
    series = [
        {
            "date": row["date"],
            "value": round(number(row, "close") / start_close * 100, 2),
        }
        for row in rows
        if review_rows[0]["date"] <= row["date"] <= review["effective_at"]
    ]
    return observed, series


def main():
    review = json.loads((BASE / "reviews" / f"{REVIEW_ID}.json").read_text(encoding="utf-8"))
    for member in review["members"]:
        member["observed"], member["series"] = load_market(member, review)
    now_kst = dt.datetime.now(dt.timezone(dt.timedelta(hours=9))).isoformat(timespec="seconds")
    review["generated_at_kst"] = now_kst
    review["observed_source"] = {
        "provider": "키움증권 REST API",
        "endpoint": "ka10059 종목별투자자기관별",
        "fields": "일별 종가·거래대금·투자자별 순매수",
        "unit": "거래대금·순매수 억원",
    }
    out_dir = DIST / "index-radar-data" / "indexes" / "kospi200" / "reviews"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{REVIEW_ID}.json").write_text(
        json.dumps(review, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )
    template = (ROOT / "tools" / "index_radar_history_template.html").read_text(encoding="utf-8")
    page = template.replace("<!--__SITE_NAV__-->", render_nav("radar"))
    page = page.replace("__REVIEW_DATA__", json.dumps(review, ensure_ascii=False).replace("</", "<\\/"))
    (DIST / "index-radar-history.html").write_text(page, encoding="utf-8")
    print(f"완료: dist/index-radar-history.html · {len(review['members'])}종목 · {review['review_id']}")


if __name__ == "__main__":
    main()
