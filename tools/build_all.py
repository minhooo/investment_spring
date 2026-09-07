"""등록된 모든 사례 대시보드와 통합 포털을 한 번에 다시 생성한다."""
import csv
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    with (ROOT / "data" / "cases.csv").open(encoding="utf-8", newline="") as f:
        cases = list(csv.DictReader(f))
    for row in cases:
        key = f"{row['종목코드']}_{row['종목명']}"
        subprocess.run([sys.executable, str(ROOT / "tools" / "build_dashboard.py"), key, "--skip-portal"], check=True)
    for split_key in ("036830_솔브레인홀딩스_인적분할", "207940_삼성바이오로직스_인적분할"):
        subprocess.run([sys.executable, str(ROOT / "tools" / "build_split.py"), split_key, "--skip-portal"], check=True)
    subprocess.run([sys.executable, str(ROOT / "tools" / "build_oil_link.py"), "--skip-portal"], check=True)
    subprocess.run([sys.executable, str(ROOT / "tools" / "validate_index_data.py"), "--index", "kospi200"], check=True)
    subprocess.run([sys.executable, str(ROOT / "tools" / "build_index_radar.py")], check=True)
    subprocess.run([sys.executable, str(ROOT / "tools" / "build_index_radar_history.py")], check=True)
    subprocess.run([sys.executable, str(ROOT / "tools" / "build_portal.py")], check=True)
    print(f"전체 빌드 완료: 표준 사례 {len(cases)}건 + 인적분할 2건·원유 검증 + 지수 레이더 현재·History + 통합 포털")


if __name__ == "__main__":
    main()
