# 투자 샘터 Vercel 운영 가이드

기준일: 2026-09-06

고정 주소는 https://investment-spring.vercel.app 이며, 사례 탐색은 https://investment-spring.vercel.app/#cases 이다. Vercel 팀은 `skt-ir`, 프로젝트는 `investment-spring`이다. `fnguide_bot`의 `sktirdashboard`와는 별도 프로젝트다.

## 사례 추가와 운영 반영

```powershell
# 저장소 루트에서 전체 빌드 → 운영 배포 → 실제 주소 파일 검증
python tools/deploy_dashboard.py

# 배포 없이 현재 운영 화면과 로컬 산출물 일치 여부 확인
python tools/deploy_dashboard.py --verify-only

# 로컬 확인용 전체 빌드
python tools/build_all.py
```

`deploy_dashboard.bat`은 위 배포 명령을 감싼 배치 파일이다. 탐색기에서 더블클릭해도 되고, 인자를 그대로 넘겨 `deploy_dashboard.bat --verify-only`처럼 쓸 수 있다. 콘솔 코드페이지를 UTF-8로 맞추고 `py -3` 또는 `python`을 찾아 실행하며, 파이썬 종료 코드를 그대로 돌려준다. 결과 확인용으로 끝에서 멈추므로 다른 스크립트에서 부를 때는 `set NOPAUSE=1`을 먼저 둔다.

Node.js/npx와 Vercel 로그인이 필요하다. 처음 실행할 때 `skt-ir`의 `investment-spring` 프로젝트에 연결한다. 로그인 세션이 만료되면 `npx --yes vercel@59.11.7 login`으로 로그인한 뒤 다시 실행한다. 배포 스크립트는 연결된 프로젝트 이름이 다르면 중단한다.

전체 빌드는 표준 사례, 솔브레인 인적분할, 에쓰오일 검증, 지수 레이더, 포털을 생성한다. 지수 레이더 원본은 먼저 `python tools/fetch_index_data.py --index kospi200 --as-of YYYY-MM-DD`로 갱신하고 `python tools/validate_index_data.py --index kospi200`으로 확인한다. 새 종류의 전용 빌더를 추가하면 `tools/build_all.py`에도 편입한다. 개별 빌더는 로컬 포털까지만 갱신하므로 온라인 반영은 배포 명령까지 실행해야 완료다.

포털의 3초 리비전 확인은 같은 고정 주소에 새 배포가 올라온 후 새 사례 데이터를 반영한다. PC의 원본 파일 변경을 자동 업로드하는 서비스나 Git 자동 배포는 구성하지 않았다. 템플릿·스크립트 자체가 바뀌었을 때는 열린 페이지를 새로고침한다. 배포 뒤에는 PC를 꺼도 마지막 배포 화면을 이용할 수 있다.

## 배포 파일과 캐시

`vercel.json`은 `dist`를 웹 루트로 지정한다. 주소에는 `/dist/`를 붙이지 않는다. `.html` 상세 경로와 `#cases` 검색·필터 경로를 유지한다. `.vercelignore`는 `vercel.json`과 `dist/**`만 업로드하도록 제한한다. 이 중 `index-radar-data/**`는 지수 레이더가 늦게 불러오는 공개 웹 payload이며 원본 CSV·수집 인증정보는 포함하지 않는다. `dist` 파일명에는 한글을 쓰지 않는다. 한글이 든 경로는 배포돼도 Vercel이 404로 응답하므로 빌더가 `tools/dist_names.py` 규칙(종목코드+영문 접미사)으로 ASCII 이름만 만들고, 포털 빌드가 이를 검사한다. `.env`, 원본 CSV, 문서, 개발 도구는 배포 대상에서 제외된다. HTML에 포함된 분석·시세는 사이트를 통해 공개된다.

HTML은 재검증 캐시를 사용하고 `portal-data.js`, `index-radar-data/**`는 `no-store`로 제공한다. 데이터 기본값은 HTML에도 들어 있어 최초 표시가 가능하다. 정적 사이트에는 서버 API·R2·개인정보 입력 기능이 없다.

## 성공 판정과 복구

통합 인과망 `causal-network.html`도 모든 HTML 해시 검증에 자동 포함된다. 전체 빌드와 개별 포털 빌드는 통합망을 후속 생성하며 `.venv-network/Scripts/python.exe`가 있으면 해당 환경을 사용한다. 처음에는 `requirements-network.txt`의 의존성을 그 환경에 설치한다. 로컬 실행 스냅샷 `data/causal/runs/`와 원본·패키지는 기존 `.vercelignore`에 의해 업로드되지 않는다. 통합망 HTML에는 공개용 분석 결과·조건·상대 원본 파일명·해시·실행 환경 버전만 인라인한다. 브라우저 초안의 공식 채택은 원본 `data/causal/policy.json`을 버전·이유와 함께 수정한 뒤 다시 빌드·배포한다. JSON 내보내기나 로컬 초안 저장만으로 운영 기준이 바뀌지 않는다.

배포 명령이 성공한 뒤 고정 주소의 루트, 모든 HTML, `portal-data.js`, `index-radar-data/**`를 실제로 받아 로컬 파일과 SHA-256 또는 바이트를 비교한다. alias 전환 직후 이전 엣지 응답이 남는 경우에는 파일별로 짧게 재시도한 뒤 판단한다. 사례별 상세 파일이 존재하는지도 검사한다. 재시도 후에도 검증이 실패하면 성공으로 보고하지 않는다. 배포 자체가 성공하고 이후 검증에서 실패했다면 새 버전이 이미 공개됐을 수 있으므로 오류를 확인한다.

이전 버전 복구는 Vercel 프로젝트의 Deployments에서 정상 배포를 선택해 운영 버전으로 복원하거나, 정상 원본을 복원한 후 배포 명령을 실행한다. 원본을 고치지 않고 Vercel에서 예전 배포를 단순 재배포하면 최신 로컬 변경이 올라가지 않는다.

공식 참고: [CLI 운영 배포](https://vercel.com/docs/cli/deploy), [프로젝트 설정](https://vercel.com/docs/project-configuration/vercel-json).

### 2026-09-08 통합 인과망 운영 확인

`deploy_dashboard.py`로 운영 배포 `dpl_AGeUxykTfmuSSjfjnTZ5gD8mz6Qq`를 생성했고 고정 주소 30개 파일과 루트의 로컬 바이트 일치 검증이 통과했다. 통합망 분석 실행은 `c144f90aa4c5927f514f`다. 운영 1440/740px 밝은 모드·1024/360px 어두운 모드에서 그래프·상세·초안 기준 저장/복원·보고서 다운로드·통합 검색·거시 화면 복귀를 검증했고 가로 넘침과 JS 오류가 없었다. 테스트는 일회 실행이며 상시 감시 서비스가 아니다.
