"""등록된 모든 사례 대시보드와 통합 포털을 한 번에 다시 생성한다."""
import csv
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from dist_names import dist_page  # noqa: E402


def meta_key_for(row):
    """cases.csv 한 행이 쓸 메타 키를 찾는다.

    한 종목에 이슈가 둘 이상이면 `<코드>_<종목명>` 만으로는 어느 메타인지 정할 수 없다
    (207940 = 인적분할 + 유상증자, 450080 = 지수편입 + RCPS 유상증자).
    그래서 행의 `대시보드` 열이 가리키는 산출물 이름과 같은 파일을 만드는 메타를 먼저 찾고,
    없을 때만 종목명 규칙으로 되돌아간다.
    """
    want = Path(row.get("대시보드", "")).name
    if want:
        for meta in sorted((ROOT / "data" / "meta").glob("*.json")):
            if dist_page(f"{meta.stem}_dashboard") == want:
                return meta.stem
    return f"{row['종목코드']}_{row['종목명']}"


def main():
    with (ROOT / "data" / "cases.csv").open(encoding="utf-8", newline="") as f:
        cases = list(csv.DictReader(f))
    for row in cases:
        key = meta_key_for(row)
        subprocess.run([sys.executable, str(ROOT / "tools" / "build_dashboard.py"), key, "--skip-portal"], check=True)
    for split_key in ("036830_솔브레인홀딩스_인적분할", "207940_삼성바이오로직스_인적분할"):
        subprocess.run([sys.executable, str(ROOT / "tools" / "build_split.py"), split_key, "--skip-portal"], check=True)
    subprocess.run([sys.executable, str(ROOT / "tools" / "build_oil_link.py"), "--skip-portal"], check=True)
    subprocess.run([sys.executable, str(ROOT / "tools" / "validate_index_data.py"), "--index", "kospi200"], check=True)
    subprocess.run([sys.executable, str(ROOT / "tools" / "build_index_radar.py")], check=True)
    subprocess.run([sys.executable, str(ROOT / "tools" / "build_index_radar_history.py")], check=True)
    subprocess.run([sys.executable, str(ROOT / "tools" / "validate_financing_data.py")], check=True)
    subprocess.run([sys.executable, str(ROOT / "tools" / "build_funding_radar.py")], check=True)
    subprocess.run([sys.executable, str(ROOT / "tools" / "build_portal.py"), '--skip-network'], check=True)
    network_python = ROOT / '.venv-network' / 'Scripts' / 'python.exe'
    subprocess.run([str(network_python) if network_python.exists() else sys.executable,
                    str(ROOT / 'tools' / 'build_causal_network.py')], check=True)
    print(f"전체 빌드 완료: 표준 사례 {len(cases)}건 + 인적분할 2건·원유 검증 + 자금·지수 레이더 + 통합 포털")


if __name__ == "__main__":
    main()
