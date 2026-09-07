"""
유동주식수 / 유통비율 수집기 — 키움 ka10001 (주식기본정보)

    python tools/fetch_shares.py 007660 이수페타시스

출력: data/shares/<코드>_<종목명>.json
    { listed_now, float_shares_now, float_ratio, mkt_cap_now, for_exh_rt, as_of,
      steps: [{from, listed, note}] }

왜 유동시총인가:
  회전율을 **총시가총액**으로 나누면 안 된다.
  최대주주·자사주·보호예수 물량은 애초에 거래에 나오지 않으므로 분모가 부풀고,
  유통비율이 다른 종목끼리는 비교 자체가 성립하지 않는다.
  실측 예: 에코프로머티 유통비율 53.6% vs 알테오젠 79.6% — 같은 거래대금이라도
  유동시총 대비 회전율은 1.5배 차이가 난다.

  회전율 = 일 거래대금 ÷ 유동시가총액
  유동시가총액 = 원주가 × 상장주식수(시점) × 유통비율

한계 (반드시 인지할 것):
  * 유통비율은 **현재 시점 스냅샷**이다. 과거의 유통비율은 달랐다.
  * 특히 **IPO 직후 보호예수 구간**은 실제 유통물량이 훨씬 적었으므로
    이 방식은 그 구간의 회전율을 **과소평가**한다.
  * 상장주식수 변동(유상증자 신주상장·무상증자)은 meta.json 의
    `share_steps` 에 DART 확정치로 직접 적는다. 자동 추정하지 않는다.
"""
import sys, os, io, json, time, urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = f"{ROOT}/data/.cache"


def env(k):
    for line in open(f"{ROOT}/.env", encoding="utf-8"):
        if line.startswith(k + "="):
            return line.split("=", 1)[1].strip()
    raise SystemExit(f".env 에 {k} 가 없습니다")


def token():
    p = f"{CACHE}/kiwoom_token.json"
    if os.path.exists(p):
        c = json.load(open(p))
        if c.get("expires_dt", "") > time.strftime("%Y%m%d%H%M%S"):
            return c["token"]
    os.makedirs(CACHE, exist_ok=True)
    body = json.dumps({"grant_type": "client_credentials",
                       "appkey": env("KIWOOM_APP_KEY"),
                       "secretkey": env("KIWOOM_APP_SECRET")}).encode()
    req = urllib.request.Request("https://api.kiwoom.com/oauth2/token", data=body,
                                 headers={"Content-Type": "application/json;charset=UTF-8"})
    r = json.loads(urllib.request.urlopen(req, timeout=20).read().decode())
    if r.get("return_code") != 0:
        raise SystemExit(f"토큰 실패: {r.get('return_msg')}")
    json.dump({"token": r["token"], "expires_dt": r.get("expires_dt", "")}, open(p, "w"))
    return r["token"]


def main():
    code, name = sys.argv[1], sys.argv[2]
    key = f"{code}_{name}"
    req = urllib.request.Request("https://api.kiwoom.com/api/dostk/stkinfo",
        data=json.dumps({"stk_cd": code}).encode(),
        headers={"Content-Type": "application/json;charset=UTF-8",
                 "authorization": f"Bearer {token()}", "api-id": "ka10001",
                 "cont-yn": "N", "next-key": ""})
    r = json.loads(urllib.request.urlopen(req, timeout=25).read().decode())
    if r.get("return_code") != 0:
        raise SystemExit(r.get("return_msg"))

    listed = int(r["flo_stk"]) * 1000              # 천주 -> 주
    floatn = int(r["dstr_stk"]) * 1000
    ratio = float(r["dstr_rt"]) / 100

    # 상장주식수 변동 이력은 meta.json 의 share_steps 에서 (DART 확정치)
    steps = []
    mpath = f"{ROOT}/data/meta/{key}.json"
    if os.path.exists(mpath):
        steps = json.load(open(mpath, encoding="utf-8")).get("share_steps", [])
    if not steps:
        steps = [{"from": "1900-01-01", "listed": listed, "note": "변동 이력 미기재 — 현재값 상수 적용"}]

    out = {"code": code, "name": name, "as_of": time.strftime("%Y-%m-%d"),
           "listed_now": listed, "float_shares_now": floatn, "float_ratio": ratio,
           "mkt_cap_now_eok": int(r["mac"]), "for_exh_rt": r["for_exh_rt"],
           "steps": steps,
           "note": "유통비율은 현재 스냅샷. IPO 보호예수 구간의 회전율은 과소평가된다."}
    os.makedirs(f"{ROOT}/data/shares", exist_ok=True)
    json.dump(out, open(f"{ROOT}/data/shares/{key}.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print(f"완료: data/shares/{key}.json")
    print(f"  상장 {listed:,}주 · 유통 {floatn:,}주 · 유통비율 {ratio*100:.1f}% "
          f"· 시총 {int(r['mac']):,}억 · 외인소진율 {r['for_exh_rt']}")
    print(f"  상장주식수 구간 {len(steps)}개: " +
          " / ".join(f"{s['from']}~ {s['listed']:,}" for s in steps))


if __name__ == "__main__":
    main()
