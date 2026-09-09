"""일반 사례 제목·요약의 개행 정규화 회귀 검사."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from build_dashboard import inline_text as dashboard_inline_text  # noqa: E402
from build_dashboard import normalize_header_copy  # noqa: E402
from build_portal import inline_text as portal_inline_text  # noqa: E402


def main():
    source = "제목 앞\n\n본문\u2028마지막"
    expected = "제목 앞 본문 마지막"
    assert dashboard_inline_text(source) == expected
    assert portal_inline_text(source) == expected

    meta = normalize_header_copy({"name": "HLB\n제약", "headline": source, "thesis": source})
    assert meta["name"] == "HLB 제약"
    assert meta["headline"] == expected
    assert meta["thesis"] == expected
    print("case copy normalization: OK")


if __name__ == "__main__":
    main()
