"""자금 레이더 원본의 최소 데이터 계약을 검사한다."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "data" / "financing" / "2026-ytd.json"
REQUIRED = {"id", "kind", "name", "stock_code", "decision_date", "amount", "proceeds", "rcept_no", "source_url"}
KINDS = {"RIGHTS", "CB", "BW", "EB"}


def main():
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    events = data.get("events", [])
    if not events:
        raise ValueError("자금조달 이벤트가 비어 있습니다.")
    ids = set()
    for index, event in enumerate(events, 1):
        missing = REQUIRED - event.keys()
        if missing:
            raise ValueError(f"{index}행 필수값 누락: {sorted(missing)}")
        if event["id"] in ids:
            raise ValueError(f"중복 이벤트 ID: {event['id']}")
        if event["kind"] not in KINDS:
            raise ValueError(f"알 수 없는 조달수단: {event['kind']}")
        if not re.fullmatch(r"[0-9A-Z]{6}", event["stock_code"]):
            raise ValueError(f"상장 종목코드가 아닙니다: {event['stock_code']}")
        if event["amount"] < 0:
            raise ValueError(f"음수 결정액: {event['id']}")
        if not event["source_url"].startswith("https://dart.fss.or.kr/"):
            raise ValueError(f"DART 원문 경로가 아닙니다: {event['id']}")
        ids.add(event["id"])
    print(f"자금조달 데이터 검증 통과: {len(events)}건 · 기준일 {data.get('as_of')}")


if __name__ == "__main__":
    main()

