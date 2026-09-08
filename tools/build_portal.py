"""투자 아이디어 샘터 정적 허브 빌더.

data/cases.csv + data/navigation.json + data/taxonomy.json을 합쳐
dist/index.html(홈·탐색)과 dist/macro.html(거시 인과지도)을 만든다.
"""
import csv
import hashlib
import html
import json
import os
import re
import sys
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dist_names import dist_page, is_web_safe
from site_shell import render_nav

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DIST = ROOT / "dist"


def load_json(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def load_cases():
    with (DATA / "cases.csv").open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def dashboard_for_meta(meta_path, meta):
    """메타 파일과 함께 생성된 대시보드를 찾아 포털에 연결한다.

    dist 파일명은 ASCII만 남기므로(`dist_names`) 메타 이름을 같은 규칙으로
    변환해 찾고, 그래도 없으면 종목코드로 시작하는 산출물을 훑는다.
    """
    code = str(meta.get("code", ""))
    candidates = [DIST / dist_page(meta_path.stem)]
    if code:
        candidates.append(DIST / dist_page(f"{code}_dashboard"))
        candidates.extend(sorted(DIST.glob(f"{code}_*.html")))
    return next((path for path in candidates if path.exists()), None)


def source_case_for(code):
    """사례 원문은 선택사항이다. 있으면 포털 데이터에 함께 남긴다."""
    matches = sorted((ROOT / "cases").glob(f"**/*{code}*.md"))
    return matches[0].relative_to(ROOT).as_posix() if matches else ""


def latest_price_date(meta):
    code, name = str(meta.get("code", "")), str(meta.get("name", ""))
    price_path = DATA / "prices" / f"{code}_{name}.csv"
    if not price_path.exists():
        return str(meta.get("event_date") or meta.get("as_of") or "")
    with price_path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    return rows[-1].get("date", "") if rows else ""


def custom_issue_id(label):
    digest = hashlib.sha1(label.encode("utf-8")).hexdigest()[:10]
    return f"custom-{digest}"


def infer_theme_ids(meta, taxonomy):
    """명시값을 우선하고, 없으면 메타의 문구에서 분류어를 찾는다."""
    available = {item["id"] for item in taxonomy["themes"]}
    explicit = [item for item in meta.get("theme_ids", []) if item in available]
    if explicit:
        return explicit
    haystack = json.dumps(meta, ensure_ascii=False).lower()
    hits = []
    for theme in taxonomy["themes"]:
        words = [theme["label"], *theme.get("aliases", [])]
        if any(word.lower() in haystack for word in words):
            hits.append(theme["id"])
    return hits


def discovered_cases(taxonomy, known_pairs):
    """data/meta와 dist의 교집합을 찾아 수동 색인 없이 사례로 등록한다.

    한 종목에 이슈가 둘 이상일 수 있으므로(207940 = 인적분할 + 유상증자)
    제외 기준은 종목코드가 아니라 **(종목코드, 이슈유형)** 쌍이다.
    코드로만 걸러내면 cases.csv에 행이 생기는 순간 같은 종목의 다른 이슈가 포털에서 사라진다.
    """
    entries = []
    seen_codes = set()
    known_issue_labels = {item["label"]: item["id"] for item in taxonomy["issues"]}
    for meta_path in sorted((DATA / "meta").glob("*.json")):
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        code, name = str(meta.get("code", "")), str(meta.get("name", ""))
        issue_type = str(meta.get("issue_type") or "기타 검증")
        if not code or not name or (code, issue_type) in known_pairs:
            continue
        dashboard = dashboard_for_meta(meta_path, meta)
        if not dashboard:
            continue
        issue_label = str(meta.get("issue_type") or "기타 검증")
        issue_id = known_issue_labels.get(issue_label)
        if not issue_id:
            issue_id = custom_issue_id(issue_label)
            if not any(item["id"] == issue_id for item in taxonomy["issues"]):
                taxonomy["issues"].append({"id": issue_id, "label": issue_label, "aliases": [issue_label]})
        theme_ids = infer_theme_ids(meta, taxonomy)
        pattern_ids = [item for item in meta.get("pattern_ids", [])
                       if any(pattern["id"] == item for pattern in taxonomy["patterns"])]
        title = str(meta.get("portal_title") or meta.get("headline") or meta.get("question") or issue_label)
        summary = str(meta.get("portal_summary") or meta.get("question") or meta.get("thesis", ""))
        # 같은 종목의 자동 등록이 둘 이상이면 뒤에 오는 것에 이슈 접미사를 붙여 id 충돌을 막는다.
        slug = code if code not in seen_codes else f"{code}-{issue_id}"
        seen_codes.add(code)
        entries.append({
            "id": f"case-auto-{slug}", "case_id": f"auto-{slug}", "kind": "case",
            "name": name, "code": code, "title": title, "summary": summary,
            "issue_id": issue_id, "issue_label": issue_label,
            "issue_ids": [issue_id], "issue_labels": [issue_label], "theme_ids": theme_ids,
            "pattern_ids": pattern_ids, "featured_pattern_ids": pattern_ids,
            "event_date": str(meta.get("event_date") or latest_price_date(meta)),
            "event_label": str(meta.get("event_label") or "검증"),
            "performance_base_date": str(meta.get("base_date") or ""),
            "aliases": list(meta.get("aliases", [])),
            "dashboard_href": dashboard.name, "source_case_path": source_case_for(code),
            "available": True,
        })
    return entries


def patterns(value):
    return [part.strip() for part in value.split("|") if part.strip()]


def validate(taxonomy, navigation, cases):
    nav_ids = [entry["case_id"] for entry in navigation["cases"]]
    if len(nav_ids) != len(set(nav_ids)):
        raise ValueError("navigation.json에 중복 case_id가 있습니다.")
    case_ids = {row["case_id"] for row in cases}
    unknown_case_ids = set(nav_ids) - case_ids
    if unknown_case_ids:
        raise ValueError(f"navigation.json에 cases.csv에 없는 case_id가 있습니다: {sorted(unknown_case_ids)}")
    theme_ids = {item["id"] for item in taxonomy["themes"]}
    issue_ids = {item["id"] for item in taxonomy["issues"]}
    for entry in navigation["cases"]:
        unknown = set(entry["theme_ids"]) - theme_ids
        if unknown:
            raise ValueError(f"{entry['case_id']}에 알 수 없는 theme_ids: {sorted(unknown)}")
        unknown_issues = set(entry.get("issue_ids", [])) - issue_ids
        if unknown_issues:
            raise ValueError(f"{entry['case_id']}에 알 수 없는 issue_ids: {sorted(unknown_issues)}")
    macro_ids = [entry["id"] for entry in navigation["macro"]]
    if len(macro_ids) != len(set(macro_ids)):
        raise ValueError("navigation.json에 중복 macro id가 있습니다.")


def build_index(taxonomy, navigation, cases):
    editing = {entry["case_id"]: entry for entry in navigation["cases"]}
    issue_map = {"유상증자": "rights", "지수편입": "index-inclusion"}
    issue_labels = {entry["id"]: entry["label"] for entry in taxonomy["issues"]}
    entries = []
    for row in cases:
        edit = editing[row["case_id"]]
        issue_id = issue_map.get(row["이슈유형"])
        if not issue_id:
            raise ValueError(f"아직 ID가 등록되지 않은 이슈 유형: {row['이슈유형']}")
        dashboard = row["대시보드"].replace("\\", "/")
        if dashboard.startswith("dist/"):
            dashboard = dashboard[5:]
        # 한글 경로는 배포 후 404가 되므로 CSV에 옛 이름이 남아 있어도 ASCII로 맞춘다.
        dashboard = dist_page(dashboard)
        case_path = row["케이스파일"].replace("\\", "/")
        if not (ROOT / "dist" / dashboard).exists():
            raise FileNotFoundError(f"대시보드 산출물이 없습니다: {dashboard}")
        if not (ROOT / case_path).exists():
            raise FileNotFoundError(f"케이스 문서가 없습니다: {case_path}")
        # CSV의 이슈유형은 대표 이슈로 유지하고, navigation의 issue_ids로 복수 연결을 덧붙인다.
        entry_issue_ids = list(dict.fromkeys([issue_id, *edit.get("issue_ids", [])]))
        entries.append({
            "id": f"case-{row['case_id']}",
            "case_id": row["case_id"],
            "kind": "case",
            "name": row["종목명"],
            "code": row["종목코드"],
            "title": edit["title"],
            "summary": edit["summary"],
            "issue_id": issue_id,
            "issue_label": issue_labels[issue_id],
            "issue_ids": entry_issue_ids,
            "issue_labels": [issue_labels[item] for item in entry_issue_ids],
            "theme_ids": edit["theme_ids"],
            "pattern_ids": patterns(row["핵심패턴태그"]),
            "featured_pattern_ids": edit["featured_pattern_ids"],
            "event_date": edit["event_date"],
            "event_label": edit["event_label"],
            "performance_base_date": row["기준일"],
            "aliases": edit.get("aliases", []),
            "dashboard_href": dashboard,
            "source_case_path": case_path,
            "available": True,
        })
    entries.extend(discovered_cases(taxonomy, {(row["종목코드"], row["이슈유형"]) for row in cases}))
    payload = {"taxonomy": taxonomy, "cases": entries, "macro": navigation["macro"], "shortcuts": navigation["shortcuts"]}
    template = (ROOT / "tools" / "portal_template.html").read_text(encoding="utf-8")
    safe_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    revision = hashlib.sha256(safe_json.encode("utf-8")).hexdigest()[:16]
    page = template.replace("/*__PORTAL_DATA__*/null", safe_json)
    page = page.replace("<!--__SITE_NAV__-->", render_nav(portal=True))
    page = page.replace("/*__PORTAL_REVISION__*/\"\"", json.dumps(revision))
    live_data = (
        "window.__PORTAL_SNAPSHOT__="
        + json.dumps({"revision": revision, "data": payload}, ensure_ascii=False, separators=(",", ":"))
        .replace("</", "<\\/")
        + ";\n"
    )
    return page, len(entries), live_data, revision


def portal_header(active):
    nav = render_nav(active)
    return f'''<header class="spring-bar"><div class="spring-bar-in"><a class="spring-brand" href="index.html#home">투자 샘터</a><nav aria-label="주요 메뉴">{nav}</nav><form class="spring-search" action="index.html#search" method="get"><input name="q" type="search" aria-label="통합 검색" placeholder="종목·이슈·테마·경제 변수 검색"><button type="submit">검색</button></form></div></header>'''


def macro_styles():
    return '''<style>
      :root{color-scheme:light}
      body{margin:0;background:#fff;color:#18181b;font-family:"Pretendard Variable",Pretendard,-apple-system,BlinkMacSystemFont,system-ui,"Malgun Gothic",sans-serif} .spring-bar{background:#fff;border-bottom:1px solid #e4e4e7}.spring-bar-in{max-width:1180px;margin:auto;padding:13px 22px;display:flex;align-items:center;gap:28px;flex-wrap:wrap}.spring-brand{font-weight:700;font-size:18px;color:#18181b;text-decoration:none}.spring-bar nav{display:flex;gap:4px;flex-wrap:wrap}.spring-bar nav a{color:#71717a;text-decoration:none;padding:8px 10px;border-radius:8px;font-size:14px}.spring-bar nav a[aria-current="page"]{background:#f4f4f5;color:#18181b;font-weight:600}.spring-search{margin-left:auto;display:flex;gap:7px;min-width:min(310px,100%)}.spring-search input,.spring-search button{font:inherit;border:1px solid #e4e4e7;border-radius:8px;padding:8px 10px;background:#fff}.spring-search input{min-width:0;width:100%}.spring-search button{cursor:pointer}.macro-wrap{max-width:1180px;margin:auto;padding:22px}.macro-crumb{font-size:13px;color:#71717a;margin:0 0 10px}.macro-heading{display:flex;gap:12px;align-items:center;justify-content:space-between;flex-wrap:wrap;margin-bottom:12px}.macro-heading h1{font-size:25px;margin:0}.macro-heading p{font-size:14px;color:#71717a;margin:4px 0 0}.scenario-picker{display:flex;gap:8px;flex-wrap:wrap}.scenario-picker button{font:inherit;border:1px solid #e4e4e7;border-radius:8px;background:#fff;padding:8px 12px;cursor:pointer}.scenario-picker button[aria-pressed="true"]{border-color:#18181b;color:#fafafa;background:#18181b}#macro-causal-dashboard{border:1px solid #e4e4e7!important;border-radius:10px!important}#macro-causal-dashboard .cid-topbar,#macro-causal-dashboard .cid-sidebar,#macro-causal-dashboard .cid-horizon{display:none!important}#macro-causal-dashboard .cid-body{grid-template-columns:minmax(0,1fr) 250px!important;min-height:0!important}#macro-causal-dashboard .cid-shell{min-height:0!important}@media(max-width:820px){.macro-wrap{padding:16px}.spring-bar-in{padding:12px 16px;gap:12px}.spring-bar nav{order:3;width:100%}.spring-search{order:4;width:100%;flex-basis:100%;margin-left:0}#macro-causal-dashboard .cid-body{display:block!important}}@media(prefers-color-scheme:dark){body{background:#09090b;color:#fafafa}.spring-bar{background:#18181b;border-color:#27272a}.spring-brand{color:#fafafa}.spring-bar nav a{color:#a1a1aa}.spring-bar nav a[aria-current="page"]{background:#27272a;color:#fafafa}.spring-search input,.spring-search button{background:#18181b;color:#fafafa;border-color:#3f3f46}}
      @media(prefers-color-scheme:dark){.scenario-picker button{background:#18181b;color:#fafafa;border-color:#3f3f46}.scenario-picker button[aria-pressed="true"]{background:#fafafa;color:#18181b;border-color:#fafafa}}
      @media(prefers-color-scheme:dark){:root{color-scheme:dark}}
    </style>'''


def build_macro(navigation):
    source = (ROOT / "design" / "causal-investment-dashboard.html").read_text(encoding="utf-8")
    source = re.sub(r"\s*<header class=\"cid-topbar\">.*?</header>", "", source, count=1, flags=re.S)
    source = re.sub(r"\s*<aside class=\"cid-sidebar\".*?</aside>", "", source, count=1, flags=re.S)
    source = re.sub(r"\s*<div class=\"cid-horizon\".*?</div>", "", source, count=1, flags=re.S)
    source = re.sub(r"\s*const mockStyle = \{.*?if \(globalThis\.Tweak\).*?\n\s*}\n", "\n", source, count=1, flags=re.S)
    # 경로 선택기는 통합 셸에 있으므로 원래 사이드바 범위가 아니라 문서 전체에서 받는다.
    source = source.replace("root.querySelectorAll('[data-scenario]').forEach(button => {", "document.querySelectorAll('[data-scenario]').forEach(button => {")
    source = source.replace("</div>\n", "</div>\n", 1)
    scenarios = navigation["macro"]
    picker = "".join(f'<button type="button" data-scenario="{html.escape(s["id"])}" aria-pressed="{"true" if s["id"] == "energy" else "false"}">{html.escape(s["title"])}</button>' for s in scenarios)
    page = f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>거시 인과지도 | 투자 아이디어 샘터</title><link rel="stylesheet" as="style" crossorigin href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css">{macro_styles()}</head><body>{portal_header("macro")}<main class="macro-wrap"><p class="macro-crumb">홈 / 거시 인과지도</p><div class="macro-heading"><div><h1>거시 인과지도</h1><p>관심 있는 변화의 출발점을 골라 조건과 시차를 따라가 보세요.</p></div><div class="scenario-picker" aria-label="예시 경로">{picker}</div></div><p class="macro-crumb">현재 지도는 예시 경로입니다. 실시간 분석이나 예측 결과를 뜻하지 않습니다.</p>{source}</main><script>document.querySelector('.spring-search').addEventListener('submit',function(e){{e.preventDefault();location.href='index.html#search?q='+encodeURIComponent(this.q.value)}});const macroParams=new URLSearchParams(location.search);const macroScenario=macroParams.get('scenario');if(macroScenario)document.querySelector(`.scenario-picker [data-scenario="${{macroScenario}}"]`)?.click();const macroNode=macroParams.get('node');if(macroNode)document.querySelector(`#macro-causal-dashboard [data-node="${{macroNode}}"]`)?.click();</script></body></html>'''
    page = page.replace('<p class="macro-crumb">현재 지도는', '<p><a href="causal-network.html">통합 인과망 · 시계열 검증실 →</a></p><p class="macro-crumb">현재 지도는')
    return page


def check_web_safe_dist():
    """한글이 들어간 dist 파일명은 배포되면 404가 되므로 빌드 단계에서 막는다."""
    bad = sorted(path.name for path in DIST.iterdir()
                 if path.is_file() and not is_web_safe(path.name))
    if bad:
        raise ValueError(f"dist에 배포할 수 없는(비ASCII) 파일명이 있습니다: {bad}")


def main():
    taxonomy, navigation, cases = load_json("taxonomy.json"), load_json("navigation.json"), load_cases()
    validate(taxonomy, navigation, cases)
    DIST.mkdir(exist_ok=True)
    index_html, case_count, live_data, revision = build_index(taxonomy, navigation, cases)
    (DIST / "index.html").write_text(index_html, encoding="utf-8")
    (DIST / "portal-data.js").write_text(live_data, encoding="utf-8")
    (DIST / "macro.html").write_text(build_macro(navigation), encoding="utf-8")
    check_web_safe_dist()
    print("완료: dist/index.html · dist/portal-data.js · dist/macro.html")
    print(f"  사례 {case_count}건 · 거시 경로 {len(navigation['macro'])}개 · 리비전 {revision}")
    if '--skip-network' not in sys.argv:
        network_python = ROOT / '.venv-network' / 'Scripts' / 'python.exe'
        subprocess.run([str(network_python) if network_python.exists() else sys.executable,
                        str(ROOT / 'tools' / 'build_causal_network.py')], check=True)


if __name__ == "__main__":
    main()
