"""
투자자별 순매수 **금액** 수집기 — 키움증권 REST API (ka10059 종목별투자자기관별)

    python tools/fetch_investors.py 007660 이수페타시스 20231001

출력: data/investors/<코드>_<종목명>.csv   (단위: 억원, 순매수)
    date, close, trde_prica, indiv, frgn, orgn, fin_invt, insur, invtrt,
    etc_fin, bank, pension, pe_fund, natn, etc_corp, natfor

왜 키움인가:
  네이버는 외국인·기관만, 그것도 **수량**으로 준다.
  키움 ka10059 는 **개인(ind_invsr)** 을 포함하고 **금액**을 직접 준다.
  개인 수급은 "누가 사서 오른 상승인가"를 판정하는 핵심 변수인데
  네이버로는 -(외국인+기관) 근사밖에 안 된다.

단위: API 원본은 백만원 → 이 파일은 **억원**으로 환산해 저장한다.
인증: 프로젝트 루트 .env 의 KIWOOM_APP_KEY / KIWOOM_APP_SECRET (gitignore 처리)
"""
import sys, os, io, csv, json, time, urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOST = "https://api.kiwoom.com"
CACHE = f"{ROOT}/data/.cache"

FIELDS = [("ind_invsr", "indiv"), ("frgnr_invsr", "frgn"), ("orgn", "orgn"),
          ("fnnc_invt", "fin_invt"), ("insrnc", "insur"), ("invtrt", "invtrt"),
          ("etc_fnnc", "etc_fin"), ("bank", "bank"), ("penfnd_etc", "pension"),
          ("samo_fund", "pe_fund"), ("natn", "natn"), ("etc_corp", "etc_corp"),
          ("natfor", "natfor")]


def env(k):
    for line in open(f"{ROOT}/.env", encoding="utf-8"):
        if line.startswith(k + "="):
            return line.split("=", 1)[1].strip()
    raise SystemExit(f".env 에 {k} 가 없습니다")


def token():
    os.makedirs(CACHE, exist_ok=True)
    p = f"{CACHE}/kiwoom_token.json"
    if os.path.exists(p):
        c = json.load(open(p))
        if c.get("expires_dt", "") > time.strftime("%Y%m%d%H%M%S"):
            return c["token"]
    body = json.dumps({"grant_type": "client_credentials",
                       "appkey": env("KIWOOM_APP_KEY"),
                       "secretkey": env("KIWOOM_APP_SECRET")}).encode()
    req = urllib.request.Request(f"{HOST}/oauth2/token", data=body,
                                 headers={"Content-Type": "application/json;charset=UTF-8"})
    r = json.loads(urllib.request.urlopen(req, timeout=20).read().decode())
    if r.get("return_code") != 0:
        raise SystemExit(f"토큰 발급 실패: {r.get('return_msg')}")
    json.dump({"token": r["token"], "expires_dt": r.get("expires_dt", "")}, open(p, "w"))
    return r["token"]


def num(x):
    try:
        return int(str(x).replace(",", "").replace("+", "") or 0)
    except ValueError:
        return 0


def main():
    code, name = sys.argv[1], sys.argv[2]
    until = sys.argv[3] if len(sys.argv) > 3 else "20230101"
    tok, rows, cont, nk = token(), [], "N", ""

    for _ in range(40):                      # 100행/페이지, 최대 4000행
        body = {"dt": time.strftime("%Y%m%d"), "stk_cd": code,
                "amt_qty_tp": "1", "trde_tp": "0", "unit_tp": "1000"}
        req = urllib.request.Request(f"{HOST}/api/dostk/stkinfo",
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json;charset=UTF-8",
                     "authorization": f"Bearer {tok}", "api-id": "ka10059",
                     "cont-yn": cont, "next-key": nk})
        with urllib.request.urlopen(req, timeout=30) as res:
            r = json.loads(res.read().decode())
            h = dict(res.headers)
        if r.get("return_code") != 0:
            print(f"  오류: {r.get('return_msg')}")
            break
        got = r.get("stk_invsr_orgn") or []
        if not got:
            break
        for d in got:
            rec = {"date": f"{d['dt'][:4]}-{d['dt'][4:6]}-{d['dt'][6:]}",
                   "close": abs(num(d.get("cur_prc"))),
                   "trde_prica": round(num(d.get("acc_trde_prica")) / 100, 1)}
            for src, dst in FIELDS:                 # 백만원 -> 억원
                rec[dst] = round(num(d.get(src)) / 100, 1)
            rows.append(rec)
        if rows[-1]["date"].replace("-", "") <= until:
            break
        cont, nk = h.get("cont-yn", "N"), h.get("next-key", "")
        if cont != "Y" or not nk:
            break
        time.sleep(0.3)

    rows = [r for r in rows if r["date"].replace("-", "") >= until]
    seen, out = set(), []
    for r in sorted(rows, key=lambda x: x["date"]):
        if r["date"] not in seen:
            seen.add(r["date"]); out.append(r)

    os.makedirs(f"{ROOT}/data/investors", exist_ok=True)
    path = f"{ROOT}/data/investors/{code}_{name}.csv"
    cols = ["date", "close", "trde_prica"] + [d for _, d in FIELDS]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader(); w.writerows(out)
    tot = lambda k: sum(r[k] for r in out)
    print(f"완료: data/investors/{code}_{name}.csv  ({len(out)}행, "
          f"{out[0]['date']} ~ {out[-1]['date']})")
    print(f"  누적 순매수(억): 개인 {tot('indiv'):+,.0f} / 외국인 {tot('frgn'):+,.0f} / "
          f"기관 {tot('orgn'):+,.0f} / 기타법인 {tot('etc_corp'):+,.0f}")


if __name__ == "__main__":
    main()
