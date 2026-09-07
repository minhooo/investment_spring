"""
OpenDART 조회 도구 — 공시 원문에서 케이스 데이터를 뽑는다.

사용법:
    python tools/dart.py corp 006400                      # 고유번호 조회
    python tools/dart.py list 006400 20250101 20251231    # 공시 목록 (정기·주요사항·발행)
    python tools/dart.py piic 006400 20250101 20251231    # 주요사항보고서(유상증자결정)
    python tools/dart.py shares 006400 2025 11013         # 주식 총수 현황 (희석률 분모)
    python tools/dart.py doc 20250411800196               # 공시 원문 본문 (태그 제거)

API 키는 프로젝트 루트 .env 의 DART_API_KEY 에서 읽는다. (.gitignore 처리됨)
corpCode 목록은 data/.cache/corpcode.xml 에 캐시한다.
"""
import sys, os, io, json, zipfile, urllib.request, xml.etree.ElementTree as ET

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://opendart.fss.or.kr/api"


def key():
    for line in open(f"{ROOT}/.env", encoding="utf-8"):
        if line.startswith("DART_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise SystemExit(".env 에 DART_API_KEY 가 없습니다")


def get(path, **params):
    params["crtfc_key"] = key()
    q = "&".join(f"{k}={v}" for k, v in params.items())
    with urllib.request.urlopen(f"{BASE}/{path}?{q}", timeout=40) as r:
        return json.loads(r.read().decode("utf-8"))


def corp_code(stock_code):
    """종목코드 -> DART 고유번호 (corpCode.xml 캐시)"""
    cache = f"{ROOT}/data/.cache"
    os.makedirs(cache, exist_ok=True)
    xml = f"{cache}/corpcode.xml"
    if not os.path.exists(xml):
        url = f"{BASE}/corpCode.xml?crtfc_key={key()}"
        with urllib.request.urlopen(url, timeout=90) as r:
            data = r.read()
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            open(xml, "wb").write(z.read(z.namelist()[0]))
    for e in ET.parse(xml).getroot().iter("list"):
        if (e.findtext("stock_code") or "").strip() == stock_code:
            return e.findtext("corp_code").strip(), e.findtext("corp_name").strip()
    raise SystemExit(f"종목코드 {stock_code} 를 찾을 수 없습니다")


def doc(rcept_no, limit=6000):
    """공시 원문 XML -> 텍스트"""
    import re
    url = f"{BASE}/document.xml?crtfc_key={key()}&rcept_no={rcept_no}"
    with urllib.request.urlopen(url, timeout=60) as r:
        blob = r.read()
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        raw = z.read(z.namelist()[0])
    for enc in ("utf-8", "cp949", "euc-kr"):
        try:
            txt = raw.decode(enc); break
        except UnicodeDecodeError:
            continue
    txt = re.sub(r"<[^>]+>", " ", txt)
    txt = re.sub(r"&[a-zA-Z]+;|&#\d+;", " ", txt)
    txt = re.sub(r"\s+", " ", txt)
    return txt.strip()[:limit]


def main():
    cmd = sys.argv[1]
    if cmd == "doc":
        return print(doc(sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 6000))
    cc, name = corp_code(sys.argv[2])

    if cmd == "corp":
        print(f"{name}  corp_code={cc}")

    elif cmd == "list":
        r = get("list.json", corp_code=cc, bgn_de=sys.argv[3], end_de=sys.argv[4],
                page_count=100)
        if r.get("status") != "000":
            return print("오류:", r.get("message"))
        print(f"# {name} 공시 {r['total_count']}건\n")
        for it in r["list"]:
            print(f"{it['rcept_dt']}  {it['report_nm'].strip()}  [{it['rcept_no']}]")

    elif cmd == "piic":
        r = get("piicDecsn.json", corp_code=cc, bgn_de=sys.argv[3], end_de=sys.argv[4])
        if r.get("status") != "000":
            return print("오류:", r.get("message"))
        for d in r["list"]:
            print(f"\n=== {d.get('rcept_no')} ===")
            for k, v in d.items():
                if v and v not in ("-",) and k not in ("rcept_no", "corp_cls",
                                                       "corp_code", "corp_name"):
                    print(f"  {k}: {v}")

    elif cmd == "shares":
        r = get("stockTotqySttus.json", corp_code=cc, bsns_year=sys.argv[3],
                reprt_code=sys.argv[4])
        if r.get("status") != "000":
            return print("오류:", r.get("message"))
        for d in r["list"]:
            print(f"  {d.get('se')}: 발행총수 {d.get('istc_totqy')} / "
                  f"유통 {d.get('distb_stock_co')}")


if __name__ == "__main__":
    main()
