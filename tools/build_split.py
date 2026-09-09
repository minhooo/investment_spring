"""
인적분할 쌍대 비교 대시보드 빌더 (케이스 공용).

    python tools/build_split.py 207940_삼성바이오로직스_인적분할
    python tools/build_split.py 036830_솔브레인홀딩스_인적분할

메타(`data/meta/<key>.json`)에서 두 종목의 가격 파일 키와 라벨을 읽는다.
- holding_key   : 투자회사 가격 파일 키 (data/prices/<key>.csv)
- operating_key : 사업회사 가격 파일 키
- labels        : 페이지 문구 (종목명·벤치마크·기준점 이름 등)

출발점(평가가격/분할 전 종가) 기준의 가격발견과, 첫 종가 이후의 투자성과를
분리해서 계산한다. 두 값을 섞으면 인적분할 케이스의 결론이 뒤집힌다.
"""
import csv
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dist_names import dist_page
from site_shell import render_nav


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_KEY = "036830_솔브레인홀딩스_인적분할"


def read_prices(key):
    path = ROOT / "data" / "prices" / f"{key}.csv"
    with path.open(encoding="utf-8", newline="") as f:
        return {
            row["date"]: {
                "close": float(row["close"]),
                "volume": int(float(row["volume"])),
                "bm_close": float(row["bm_close"]),
            }
            for row in csv.DictReader(f)
        }


def pct(value, base):
    return (value / base - 1) * 100


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    meta_key = args[0] if args else DEFAULT_KEY
    page = dist_page(f"{meta_key}_demerger")

    meta_path = ROOT / "data" / "meta" / f"{meta_key}.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    split = meta["split"]
    hold = read_prices(meta["holding_key"])
    operating = read_prices(meta["operating_key"])
    dates = sorted(set(hold) & set(operating))
    if not dates:
        raise ValueError("두 종목의 공통 거래일이 없습니다.")

    wh, wo = split["holding_ratio"], split["operating_ratio"]
    hold_eval = split["holding_evaluation_price"]
    op_eval = split["operating_evaluation_price"]
    bundle_eval = wh * hold_eval + wo * op_eval

    hold_close = [hold[d]["close"] for d in dates]
    op_close = [operating[d]["close"] for d in dates]
    bm_close = [hold[d]["bm_close"] for d in dates]
    bundle = [wh * h + wo * o for h, o in zip(hold_close, op_close)]

    def index(values, base):
        return [round(value / base * 100, 2) for value in values]

    checkpoints = []
    for day in meta["checkpoints"]:
        if day >= len(dates):
            continue
        checkpoints.append({
            "day": day,
            "date": dates[day],
            "holdingClose": round(hold_close[day]),
            "operatingClose": round(op_close[day]),
            "holdingFromEvaluation": round(pct(hold_close[day], hold_eval), 1),
            "operatingFromEvaluation": round(pct(op_close[day], op_eval), 1),
            "bundleFromEvaluation": round(pct(bundle[day], bundle_eval), 1),
            "holdingFromFirstClose": round(pct(hold_close[day], hold_close[0]), 1),
            "operatingFromFirstClose": round(pct(op_close[day], op_close[0]), 1),
            "bundleFromFirstClose": round(pct(bundle[day], bundle[0]), 1),
            "kosdaqFromFirstClose": round(pct(bm_close[day], bm_close[0]), 1),
            "bundleExcessFromFirstClose": round(
                pct(bundle[day], bundle[0]) - pct(bm_close[day], bm_close[0]), 1
            ),
        })

    stages = []
    for label, h, o in [
        (meta["labels"]["baseline"], hold_eval, op_eval),
        ("첫 시초가", split["holding_open"], split["operating_open"]),
        ("첫 종가", hold_close[0], op_close[0]),
    ]:
        value = wh * h + wo * o
        stages.append({
            "label": label,
            "holding": round(h),
            "operating": round(o),
            "bundle": round(value),
            "holdingReturn": round(pct(h, hold_eval), 1),
            "operatingReturn": round(pct(o, op_eval), 1),
            "bundleReturn": round(pct(value, bundle_eval), 1),
        })

    payload = {
        "meta": meta,
        "dates": dates,
        "holdingClose": [round(v) for v in hold_close],
        "operatingClose": [round(v) for v in op_close],
        "bundleValue": [round(v, 2) for v in bundle],
        "kosdaqClose": [round(v, 2) for v in bm_close],
        "evaluationIndex": {
            "holding": index(hold_close, hold_eval),
            "operating": index(op_close, op_eval),
            "bundle": index(bundle, bundle_eval),
            "kosdaq": index(bm_close, bm_close[0]),
        },
        "firstCloseIndex": {
            "holding": index(hold_close, hold_close[0]),
            "operating": index(op_close, op_close[0]),
            "bundle": index(bundle, bundle[0]),
            "kosdaq": index(bm_close, bm_close[0]),
        },
        "bundleEvaluation": round(bundle_eval, 2),
        "stages": stages,
        "checkpoints": checkpoints,
    }

    template = (ROOT / "tools" / "split_pair_template.html").read_text(encoding="utf-8")
    safe_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    output = template.replace("/*__DATA__*/null", safe_json).replace(
        "<!--__SITE_NAV__-->", render_nav("cases")
    )
    out_path = ROOT / "dist" / page
    out_path.parent.mkdir(exist_ok=True)
    out_path.write_text(output, encoding="utf-8")

    d0, dl = checkpoints[0], checkpoints[-1]
    hn = meta["labels"]["holding"]
    on = meta["labels"]["operating"]
    print(f"완료: {out_path.relative_to(ROOT)}")
    print(
        f"  {meta['labels']['baseline']}→첫 종가: {hn} {d0['holdingFromEvaluation']:+.1f}% / "
        f"{on} {d0['operatingFromEvaluation']:+.1f}% / 합산 {d0['bundleFromEvaluation']:+.1f}%"
    )
    print(
        f"  첫 종가→D+{dl['day']}: {hn} {dl['holdingFromFirstClose']:+.1f}% / "
        f"{on} {dl['operatingFromFirstClose']:+.1f}% / 합산 {dl['bundleFromFirstClose']:+.1f}% "
        f"(초과 {dl['bundleExcessFromFirstClose']:+.1f}%p)"
    )
    if "--skip-portal" not in sys.argv:
        subprocess.run([sys.executable, str(ROOT / "tools" / "build_portal.py")], check=True)


if __name__ == "__main__":
    main()
