"""공통 상단 메뉴의 단일 정의를 정적 템플릿에 삽입한다."""
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def navigation():
    return json.loads((ROOT / "data" / "site_navigation.json").read_text(encoding="utf-8"))["items"]


def render_nav(active=None, portal=False):
    """현재 메뉴와 포털 hash 탐색을 함께 지원하는 nav anchor 목록."""
    parts = []
    for item in navigation():
        attrs = [f'href="{html.escape(item["href"], quote=True)}"']
        if portal:
            attrs.append(f'data-nav="{html.escape(item["key"], quote=True)}"')
        if item["key"] == active:
            attrs.append('aria-current="page"')
        parts.append(f'<a {" ".join(attrs)}>{html.escape(item["label"])}</a>')
    return "".join(parts)
