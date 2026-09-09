"""자금 레이더 정적 화면을 생성한다."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from site_shell import render_nav  # noqa: E402


def main():
    source = ROOT / "data" / "financing" / "2026-ytd.json"
    if not source.exists():
        raise FileNotFoundError(
            "자금조달 원본이 없습니다. python tools/fetch_financing_data.py 를 먼저 실행하세요."
        )
    data = json.loads(source.read_text(encoding="utf-8"))
    template = (ROOT / "tools" / "funding_radar_template.html").read_text(encoding="utf-8")
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    page = template.replace("/*__FUNDING_DATA__*/null", payload)
    page = page.replace("<!--__SITE_NAV__-->", render_nav("funding"))
    output = ROOT / "dist" / "funding-radar.html"
    output.write_text(page, encoding="utf-8")
    print(f"자금 레이더 생성: {output.relative_to(ROOT)} · {len(data['events'])}건")


if __name__ == "__main__":
    main()
