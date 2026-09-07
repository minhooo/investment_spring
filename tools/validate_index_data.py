"""지수 레이더 원본 스냅샷의 최소 무결성 검사."""
import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", default="kospi200", choices=["kospi200"])
    args = parser.parse_args()
    base = ROOT / "data" / "indexes" / args.index
    with (base / "constituents_latest.csv").open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    source = json.loads((base / "source_latest.json").read_text(encoding="utf-8"))
    if not 195 <= len(rows) <= 205:
        raise ValueError(f"구성종목 수 오류: {len(rows)}")
    if len({row["security_id"] for row in rows}) != len(rows):
        raise ValueError("security_id 중복")
    if any(int(row["price"]) <= 0 or int(row["market_cap_eok"]) <= 0 for row in rows):
        raise ValueError("음수 또는 0 가격/시가총액")
    if any(not row.get("float_market_cap_eok") or float(row["float_market_cap_eok"]) <= 0 for row in rows):
        raise ValueError("유동시가총액 누락 또는 0")
    if not source.get("as_of") or not source.get("source", {}).get("url"):
        raise ValueError("기준일 또는 출처 URL 누락")
    review_path = base / "reviews" / "2026-h1.json"
    review = json.loads(review_path.read_text(encoding="utf-8"))
    required_dates = ["observation_start", "data_cutoff_at", "announcement_at", "rebalance_at", "effective_at"]
    if any(not review.get(key) for key in required_dates):
        raise ValueError("History 필수 기준일 누락")
    if [review[key] for key in required_dates] != sorted(review[key] for key in required_dates):
        raise ValueError("History 기준일 순서 오류")
    review_tickers = [member["ticker"] for member in review.get("members", [])]
    if len(review_tickers) != 4 or len(set(review_tickers)) != 4:
        raise ValueError("2026 상반기 History 편입종목은 고유 4종목이어야 함")
    current_tickers = {row["ticker"] for row in rows}
    if missing := sorted(set(review_tickers) - current_tickers):
        raise ValueError(f"현재 구성목록에 History 편입종목 누락: {', '.join(missing)}")
    for member in review["members"]:
        if not member.get("evidence") or not member.get("research_estimate"):
            raise ValueError(f"History 분석 필드 누락: {member['ticker']}")
    print(f"검증 통과: {args.index} · {len(rows)}종목 · {source['as_of']} · History {len(review_tickers)}종목")


if __name__ == "__main__":
    main()
