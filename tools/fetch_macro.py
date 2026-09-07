"""
매크로 일별 시계열 수집기 (FRED / St. Louis Fed, API 키 불필요)

사용법:
    python tools/fetch_macro.py 20201201

출력:
    data/macro/<series_id>.csv   (observation_date, <series_id>)

수집 계열:
    DCOILBRENTEU  브렌트유 현물 (EIA, $/bbl)
    DCOILWTICO    WTI 현물 ($/bbl)
    DDFUELUSGULF  US Gulf Coast 초저유황 경유(ULSD) 현물 ($/gal)
    DGASUSGULF    US Gulf Coast 재래식 휘발유 현물 ($/gal)
    DJFUELUSGULF  US Gulf Coast 항공유 현물 ($/gal)
    DEXKOUS       원/달러 환율

주의:
- FRED 유가 계열은 **미국 동부시간 기준 결제가**다. KRX 종가(15:30 KST)
  시점에 알려져 있는 최신 브렌트 값은 '직전 영업일 결제가'이므로,
  상관을 볼 때는 반드시 하루 시차를 맞춰야 한다 (build_oil_link.py 가 처리).
- 정제마진(크랙)은 FRED 에 직접 계열이 없어 제품가에서 합성한다.
  디젤크랙 = ULSD($/gal) x 42 - Brent($/bbl).
  실제 S-Oil 이 받는 것은 싱가포르 복합정제마진(두바이유 기준)이므로
  이 값은 **방향성 프록시**이지 회사 실적 마진 그 자체가 아니다. [확인필요]
"""
import os, sys, urllib.request

SERIES = ["DCOILBRENTEU", "DCOILWTICO", "DDFUELUSGULF",
          "DGASUSGULF", "DJFUELUSGULF", "DEXKOUS"]
BASE = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}&cosd={cosd}"


def main():
    start = sys.argv[1] if len(sys.argv) > 1 else "20201201"
    cosd = f"{start[:4]}-{start[4:6]}-{start[6:]}"
    os.makedirs("data/macro", exist_ok=True)
    for sid in SERIES:
        url = BASE.format(sid=sid, cosd=cosd)
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        body = urllib.request.urlopen(req, timeout=40).read().decode("utf-8")
        path = f"data/macro/{sid}.csv"
        open(path, "w", encoding="utf-8", newline="").write(body)
        lines = [l for l in body.splitlines() if l.strip()]
        print(f"{sid:14s} {len(lines)-1:5d}행  {lines[1].split(',')[0]} ~ {lines[-1].split(',')[0]}")


if __name__ == "__main__":
    main()
