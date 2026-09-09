"""정규화된 지수 스냅샷에서 지수 레이더 HTML·웹 payload를 만든다."""
import csv
import datetime as dt
import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
from site_shell import render_nav

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "data" / "indexes" / "kospi200"
DIST = ROOT / "dist"


def write_text_retry(path, text, attempts=4):
    """Retry brief Windows file-indexer/share races during consecutive full builds."""
    for attempt in range(attempts):
        try:
            path.write_text(text, encoding="utf-8")
            return
        except OSError:
            if attempt == attempts - 1:
                raise
            time.sleep(0.25 * (attempt + 1))


def main():
    with (BASE / "constituents_latest.csv").open(encoding="utf-8", newline="") as f:
        members = list(csv.DictReader(f))
    source = json.loads((BASE / "source_latest.json").read_text(encoding="utf-8"))
    total = sum(float(row["float_market_cap_eok"]) for row in members)
    for row in members:
        row["weight"] = round(float(row["float_market_cap_eok"]) / total * 100, 6)
    now_kst = dt.datetime.now(dt.timezone(dt.timedelta(hours=9))).isoformat(timespec="seconds")
    payload = {"schema_version":"1.0","index_id":"kospi200","as_of":source["as_of"],"collected_at_kst":now_kst,"source":source["source"],"quality_flags":source["quality_flags"],"weight_kind":"float_market_cap_reference","constituents":members}
    out_data = DIST / "index-radar-data" / "indexes" / "kospi200"
    out_data.mkdir(parents=True, exist_ok=True)
    write_text_retry(out_data / "latest.json", json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    manifest = {"schema_version":"1.1","generated_at_kst":now_kst,"indexes":{"kospi200":{"latest":"index-radar-data/indexes/kospi200/latest.json","as_of":source["as_of"],"history_latest":"index-radar-data/indexes/kospi200/reviews/2026-h1.json","history_page":"index-radar-history.html"}}}
    write_text_retry(DIST / "index-radar-data" / "manifest.json", json.dumps(manifest, ensure_ascii=False, separators=(",", ":")))
    template = (ROOT / "tools" / "index_radar_template.html").read_text(encoding="utf-8")
    (DIST / "index-radar.html").write_text(template.replace("<!--__SITE_NAV__-->", render_nav("radar")), encoding="utf-8")
    print(f"완료: dist/index-radar.html · 구성종목 {len(members)}개 · 기준일 {source['as_of']}")


if __name__ == "__main__":
    main()
