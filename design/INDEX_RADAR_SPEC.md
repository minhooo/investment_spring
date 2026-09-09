# 지수 레이더 — 제품·데이터·구현 설계서

문서 상태: 구현 전 설계 · 기준일: 2026-09-06 · 대상 구현자: Terra

이 문서는 투자 샘터에 새 상위 메뉴를 추가하기 위한 실행 명세다. 현재 구현된 기능을 설명하는 문서가 아니며, 구현하지 않은 항목은 모두 단계별 확장 계획으로 취급한다. UI 공통 규칙은 [`DESIGN_GUIDE.md`](DESIGN_GUIDE.md)가 우선하고, 지수 편입 사건의 해석은 [`../framework/지수편입/10_판단프레임.md`](../framework/지수편입/10_판단프레임.md)를 함께 따른다.

---

## 1. 메뉴명과 제품 정의

### 확정 메뉴명: **지수 레이더**

- 내부 영문명: `Index Radar`
- URL 슬러그: `index-radar`
- 생성 파일: `dist/index-radar.html`
- 헤더 표기: `지수 레이더`
- 페이지 설명: `지수의 현재 구성, 변경 이력과 편입 조건의 형성 과정을 추적합니다.`

이 이름은 KOSPI 200 같은 특정 지수에 묶이지 않고 다음 세 역할을 함께 담는다.

1. **관측** — 현재 구성종목과 비중을 본다.
2. **추적** — 과거 편입·편출과 발표 전 조건 형성 과정을 복원한다.
3. **탐지** — 충분한 검증 후 잠재 후보 신호를 찾는다.

`지수 예측`은 초기 메뉴명으로 쓰지 않는다. 1단계 화면은 사실 조회와 과거 분석이 중심이고, 검증되지 않은 후보 신호를 제품 전체가 예측하는 것처럼 보이게 해서는 안 된다.

---

## 2. 목표, 비목표, 성공 조건

### 2.1 최종 목표

사용자가 한 화면에서 다음 질문에 답할 수 있게 한다.

- 지금 이 지수에는 어떤 종목이 들어 있고 각 종목의 비중은 얼마인가?
- 기준일을 바꾸면 구성과 비중이 어떻게 달라졌는가?
- 과거 신규 편입 종목은 발표 전까지 어떤 조건을 언제 충족했는가?
- 같은 조건 형성 패턴이 과거에 얼마나 자주 실제 편입으로 이어졌는가?
- 현재 경계선에 가까운 종목은 무엇이며, 어떤 조건이 남아 있는가?

### 2.2 초기 비목표

- 실시간 매매 신호나 자동 주문
- 검증되지 않은 편입 확률의 공개
- 공식 비중과 자체 추정 비중의 혼합
- 결과를 알고 난 뒤 임계값을 맞추는 사후 최적화
- MSCI가 허용하지 않는 구성종목 데이터의 무단 수집·재배포
- 브라우저가 원본 데이터 전체를 내려받아 즉석에서 계산하는 구조

### 2.3 성공 조건

1단계는 KOSPI 200 한 지수에 대해 최신 구성, 현재가 기준 추정 비중, 과거 스냅샷 비교, 출처·기준시각을 오류 없이 제공하면 성공이다. 예측 기능이 없어도 1단계는 완결된 제품이어야 한다.

---

## 3. 개념을 반드시 분리한다

### 3.1 공식 비중과 현재가 추정 비중

화면에는 아래 두 값을 구분해서 저장하고 표시한다.

| 값 | 정의 | 화면 라벨 |
|---|---|---|
| 공식 비중 | 지수 산출기관 또는 정식 데이터 공급자가 특정 시점에 발표한 값 | `공식 비중` |
| 현재가 추정 비중 | 마지막으로 확인된 지수주식수·유동비율을 최신 가격에 적용해 자체 계산한 값 | `현재가 추정` |

현재가 추정 비중의 기본식은 다음과 같다.

```text
추정 유동시가총액(i,t) = 최신 가격(i,t) × 지수 반영 주식수(i) × 적용 유동비율(i)
추정 비중(i,t) = 추정 유동시가총액(i,t) ÷ 전체 구성종목 추정 유동시가총액 합계(t)
```

공급 데이터의 `지수 반영 주식수`가 이미 유동비율을 반영한 값이면 유동비율을 다시 곱하지 않는다. 이 여부를 `shares_basis = full | float_adjusted`로 저장한다. 공식 비중이 없으면 빈 값으로 두며 추정치를 공식값처럼 대체하지 않는다.

정적 사이트에서 `현재가`는 **가장 최근 수집에 성공한 가격**을 뜻한다. 실시간이라고 표현하려면 별도 API와 장중 갱신 인프라를 구현하고 실제 갱신 지연을 표시해야 한다. 1단계 기본값은 일별 종가 또는 명시된 수집시각의 스냅샷이다.

### 3.2 사실, 계산, 판단, 모델

모든 값은 다음 네 종류 중 하나로 구분한다.

| 종류 | 예 | 저장 원칙 |
|---|---|---|
| `observed` | KRX 발표 구성종목, 종가, 발표일 | 원출처·수집시각·원본 해시 필수 |
| `derived` | 추정 비중, 순위, 누적 시총 비율 | 계산식·입력 기준일·코드 버전 필수 |
| `judgment` | 편입 외 스토리 I1~I5 분류 | 작성자·근거·작성시각 필수 |
| `model` | 후보 점수, 편입 확률 | 모델 버전·학습종료일·실행시각 필수 |

화면의 배지와 툴팁도 이 구분을 유지한다. `추정`, `수작업 판단`, `모델 신호`를 숨기지 않는다.

### 3.3 편입 예측과 편입 후 주가 예측

둘은 별개다.

- **편입 예측**: 다음 리뷰에서 지수에 들어갈 가능성을 추정한다.
- **사후 성과 분석**: 편입 발표·적용 전후 가격과 수급이 어떻게 움직였는지 측정한다.

기존 `framework/지수편입/`의 P1~P4, I1~I5, 스코어카드는 사후 성과와 편입 외 스토리를 해석하는 층이다. 지수 규칙 충족 엔진과 같은 점수로 합치지 않는다.

---

## 4. 화면 정보구조

### 4.1 전역 진입

헤더의 다섯 번째 상위 메뉴로 `지수 레이더`를 추가한다. 네 번째 `자금 레이더`는 발행결정 공시 기반의 별도 작업 공간으로 둔다.

```text
홈 | 사례 탐색 | 거시 인과지도 | 자금 레이더 | 지수 레이더
```

홈에는 세 번째 진입 카드를 추가한다.

```text
지수 레이더
지수의 구성과 편입 조건은 어떻게 변했을까?
[지수 살펴보기 →]
```

상위 메뉴는 5개이므로 현재 디자인 가이드의 직접 노출 범위 안이다. 1024px에서 검색창과 충돌하면 메뉴 글자를 줄이지 말고 헤더 줄바꿈을 허용한다. 740px 이하에서는 메뉴를 별도 행에 놓고, 실제 너비가 부족해지면 접을 수 있는 모바일 메뉴로 전환한다.

### 4.2 페이지 URL 상태

전용 정적 페이지 하나와 query parameter를 사용한다.

```text
index-radar.html?index=kospi200&view=constituents&asof=2026-09-04
index-radar.html?index=kospi200&view=history&compare=2026-06-12,2026-09-04
index-radar.html?index=kospi200&view=path&review=kospi200-2026h1&security=KRX:KR7005930003
```

- `index`: 지수 ID. 기본값은 registry의 `default_index`.
- `view`: `constituents | history | path | validation | candidates`.
- `asof`: 실제 데이터가 있는 날짜로 스냅하며 화면에 스냅 사실을 알린다.
- `compare`: 시작·종료 스냅샷 두 날짜.
- `review`, `security`: 편입 경로 상세의 영구 ID.
- 알 수 없는 값은 조용히 무시하지 말고 빈 상태와 복귀 링크를 제공한다.

1단계에서 구현하지 않은 `validation`, `candidates` 탭은 빈 탭이나 `준비 중` 메뉴로 노출하지 않는다. 데이터와 검증 기준을 갖춘 단계에서 추가한다.

### 4.3 공통 상단

```text
홈 / 지수 레이더
지수 레이더
지수의 현재 구성, 변경 이력과 편입 조건의 형성 과정을 추적합니다.

[지수 선택: KOSPI 200] [기준일: 2026-09-04] [데이터 상태]
[현재 구성] [변경 이력] [편입 경로]
```

`데이터 상태`에는 다음을 한 줄로 표시한다.

- 가격 기준시각
- 구성 기준일 또는 적용일
- 공식/추정 여부
- 데이터 품질 경고 수
- 원출처 링크

### 4.4 현재 구성 화면

#### 요약 카드

- 구성종목 수
- 추정 유동시가총액 합계
- 상위 10종목 비중 합계
- 최대 종목 비중
- 가격 데이터 커버리지

#### 시각화

- `상위 종목 비중`: 가로 막대. 상위 10개와 기타를 표시한다.
- `산업군 비중`: 산업군별 가로 막대 또는 누적 막대.
- 면적 트리맵은 1단계 필수사항이 아니다. 작은 종목의 비교와 모바일 접근성이 나빠질 수 있으므로 표와 막대가 먼저다.

#### 구성종목 표

| 열 | 기본 표시 | 설명 |
|---|:---:|---|
| 순위 | O | 현재가 추정 비중 순위 |
| 종목명·코드 | O | 상세 진입 링크 |
| 산업군 | O | 공급자별 분류체계와 버전 표시 |
| 최신 가격 | O | 통화·가격 기준시각 포함 |
| 공식 비중 | O | 없으면 `—` |
| 현재가 추정 | O | 자체 계산 배지 표시 |
| 기준일 대비 변화 | O | 선택한 비교일과의 `%p` 변화 |
| 유동시가총액 | 데스크톱 | 계산 기준 확인 가능 |
| 편입일 | 선택 | 최초 편입과 최근 재편입을 구분 |
| 데이터 품질 | 선택 | 결측·지연·보정 상태 |

기본 정렬은 현재가 추정 비중 내림차순이다. 종목명·코드 검색, 산업군 필터, 편입/편출 예정 필터, 정렬을 URL에 보존한다. 넓은 표는 표 컨테이너 안에서만 가로 스크롤하며 첫 번째 종목 열을 고정할 수 있다.

### 4.5 변경 이력 화면

- 두 기준일을 선택해 `신규 편입`, `편출`, `잔류`, `비중 증가`, `비중 감소`로 나눈다.
- 정기변경과 수시변경을 타임라인에서 구분한다.
- 발표일, 적용일, 리밸런싱 기준시각을 서로 다른 필드로 저장하고 표시한다.
- 비교표는 종목별 이전 비중, 이후 비중, 변화 `%p`, 당시 가격, 사유, 출처를 제공한다.
- 일별 가격만 변한 비중 변화와 구성·지수주식수 변경으로 발생한 변화를 구분한다.

#### 현재 구현된 리뷰 단위 History

- 첫 리뷰는 `kospi200-2026-h1`이며 `index-radar-history.html` 한 페이지가 정기변경의 공통 기준일·방법론·출처를 소유한다.
- 편입 종목별 별도 페이지를 복제하지 않고 네 종목 비교표와 `#stock-<ticker>` 영구 앵커를 제공한다.
- 키움 `ka10059`의 가격·거래대금·투자자 순매수는 `관측`, 증권사 지수 비중·패시브 수요는 `리서치 추정`, 특례·경계선 판단은 `해석`으로 구분한다.
- 발표 전 심사 신호와 발표 후 성과를 별도 열과 카드로 분리한다. 발표 후 가격을 편입 근거로 사용하지 않는다.
- 이 구현은 첫 과거 리뷰의 수직 분석이다. 임의의 두 구성 스냅샷 비교와 완전한 방법론 adapter가 구현됐다는 의미는 아니다.

### 4.6 편입 경로 화면

리뷰와 종목을 선택하면 **발표 전에 조건이 어떻게 형성됐는지**를 보여준다.

```text
리뷰 요약
발표일 · 적용일 · 방법론 버전 · 당시 사용 가능한 데이터 마감시점

자격 조건 체크
보통주 / 상장기간 / 관리종목 / 유동주식비율 / 유동성 등

조건 형성 차트
일평균 시총 순위 ── 편입 경계선
누적 산업군 시총 비율 ── 기준선
거래대금 순위 ── 유동성 기준선

판정 시점 카드
후보 → 경계 → 규칙상 선정 → 실제 발표

사후 성과 연결
P1~P4 사례가 있으면 사례 탐색의 기존 대시보드로 이동
```

종목이 조건을 충족했다고 해서 `편입 확정`이라고 표현하지 않는다. 화면 상태는 다음으로 제한한다.

- `자격 미충족`
- `자격 충족`
- `1차 선정권`
- `버퍼 적용 후 후보`
- `실제 편입`
- `실제 미편입`

규칙으로 완전히 재현되지 않는 운영위원회 판단, 예외, 공급자 재량은 `재량/예외 가능`으로 표시한다.

### 4.7 검증 화면 — 3단계 이후

- 과거 리뷰별 예상 후보와 실제 결과
- 편입/편출 각각의 Precision, Recall, 후보 순위 적중률
- 확률 모델을 쓸 경우 Brier score와 구간별 calibration
- 방법론 버전별 성능
- 누락 데이터와 예외 처리 실패 건수
- 성공 사례뿐 아니라 미편입 오탐과 편입 누락을 같은 비중으로 노출

### 4.8 후보 신호 화면 — 최종 단계

후보 신호는 `유력/가능/관찰` 같은 근거 기반 단계로 먼저 제공한다. 검증 없이 73.4% 같은 정밀 확률을 표시하지 않는다.

각 후보 행에는 다음이 있어야 한다.

- 현재 규칙 단계
- 컷오프까지 남은 거리
- 최근 1·3·6개월 조건 추세
- 기존 구성종목 버퍼와 경쟁 관계
- 결측 또는 불확실한 조건
- 사용한 방법론 버전과 데이터 기준시각
- 과거 유사 경로
- 모델 신호가 있다면 모델 버전과 최근 백테스트 성능

---

## 5. 데이터 아키텍처

### 5.1 핵심 원칙

1. `index_id`와 `security_id`는 이름이 바뀌어도 유지되는 영구 ID다.
2. 원본은 수정하지 않는 스냅샷으로 보존하고, 정규화 데이터와 웹 산출물을 분리한다.
3. 모든 데이터는 `effective_at`, `observed_at`, `captured_at`을 구분한다.
4. 방법론은 버전과 유효기간을 가진다. 현재 규칙을 과거 리뷰에 소급 적용하지 않는다.
5. 원출처가 바뀌면 과거 값을 조용히 덮어쓰지 않고 정정 이력을 남긴다.
6. 브라우저에는 필요한 집계 JSON만 배포한다. 원본·키·개발 데이터는 배포하지 않는다.

### 5.2 권장 원본 구조

```text
data/indexes/
├─ registry.json
├─ security_master.csv
├─ _raw/                              # 배포 제외, 원본 응답·파일·해시
│  └─ <provider>/<YYYY-MM-DD>/...
└─ <index_id>/
   ├─ sources.json
   ├─ methodology_versions.json
   ├─ memberships.csv                 # 편입 유효구간
   ├─ official_weights.csv            # 공식값이 있을 때만
   ├─ daily_metrics/
   │  └─ <YYYY>.csv                   # 가격·주식수·유동비율·추정 비중
   ├─ reviews.csv                     # 발표·적용·정기/수시 변경
   ├─ review_assessments/
   │  └─ <review_id>.csv              # 발표 전 시점의 규칙 입력과 판정
   └─ historical_cases/
      └─ <review_id>__<security_id>.json
```

폴더와 생성 파일은 ASCII로 유지한다. 종목명은 파일명이 아니라 데이터 필드에 저장한다.

### 5.3 웹 배포 구조

```text
dist/
├─ index-radar.html
└─ index-radar-data/
   ├─ manifest.json                   # 최신 리비전·지수 목록·사용 가능 날짜
   ├─ indexes/<index_id>/latest.json  # 첫 화면용 최소 데이터
   ├─ indexes/<index_id>/history/<YYYY>.json
   ├─ indexes/<index_id>/reviews.json
   └─ indexes/<index_id>/paths/<review_id>.json
```

`latest.json`만 첫 화면에서 불러오고 이력과 편입 경로는 사용자가 해당 탭을 열 때 지연 로드한다. 각 JSON에는 `schema_version`, `revision`, `generated_at`, `source_as_of`를 넣는다.

### 5.4 필수 식별자

| 필드 | 예 | 설명 |
|---|---|---|
| `index_id` | `kospi200` | 내부 영구 ID |
| `provider_id` | `krx` | 지수 산출기관 |
| `security_id` | `KRX:KR7005930003` | 시장+ISIN 권장 |
| `listing_id` | `KRX:005930` | 거래소 종목코드가 바뀔 수 있는 상장 단위 |
| `review_id` | `kospi200-2026-h1-regular` | 리뷰 영구 ID |
| `methodology_version` | `krx-kospi200-2021-07` | 유효기간과 원문 출처 연결 |
| `snapshot_id` | `kospi200-2026-09-04-eod` | 재현 가능한 스냅샷 ID |

### 5.5 `daily_metrics` 최소 스키마

```csv
index_id,date,security_id,listing_id,close,currency,index_shares,shares_basis,float_factor,full_market_cap,float_market_cap,official_weight,estimated_weight,weight_kind,price_observed_at,membership_effective_at,methodology_version,source_id,quality_flags
```

- `official_weight`가 없으면 빈 값이다.
- `estimated_weight` 합계는 반올림 전 기준으로 1 또는 100이 되도록 검증한다.
- `weight_kind`는 `official | eod_estimate | intraday_estimate` 중 하나다.
- 결측 가격 종목은 이전 가격으로 자동 대체하지 않는다. 불가피한 경우 `stale_price` 품질 플래그와 원 가격일을 표시한다.

### 5.6 `reviews` 최소 스키마

```csv
review_id,index_id,review_type,announcement_at,effective_at,rebalance_at,data_cutoff_at,methodology_version,source_id,status
```

모든 timestamp는 ISO 8601과 timezone을 포함한다. MSCI처럼 한국시간 새벽 발표와 현지 기준일이 다른 경우 원 timezone과 KST 표시값을 함께 보존한다.

### 5.7 `review_assessments` 최소 스키마

공통 열 뒤에 공급자별 규칙 열을 추가할 수 있는 wide table을 사용한다.

```csv
review_id,security_id,calculated_as_of,was_incumbent,eligible,sector,avg_market_cap,market_cap_rank,sector_market_cap_rank,sector_cumulative_market_cap_pct,avg_trading_value,trading_value_percentile,float_factor,buffer_result,special_rule_result,rule_stage,actual_result,input_revision,engine_version,quality_flags
```

MSCI 확장 시 KRX 전용 열을 억지로 재사용하지 않는다. 공통 열은 유지하고 공급자별 상세 근거는 `provider_metrics` JSON object 또는 별도 provider table로 확장한다.

---

## 6. 출처와 수집 정책

### 6.1 KOSPI 200 우선순위

1. KRX 공식 지수 구성·방법론·정기변경 공지
2. 정식으로 이용 가능한 KRX 데이터 또는 계약된 데이터 공급자
3. 가격·거래대금·주식수 보완용 기존 키움 수집 경로
4. 기업행사 확인용 DART

공식 구성종목과 자체 가격 계산의 출처가 다르면 출처를 각각 저장한다. 화면의 `출처`를 하나로 뭉개지 않는다.

### 6.2 MSCI 확장 원칙

- `msci-korea-standard`처럼 지수군과 크기 구간을 명확히 식별한다.
- 공개 factsheet, 공식 리뷰 발표와 합법적으로 이용 가능한 보유 데이터만 사용한다.
- 전체 구성과 비중 데이터의 라이선스·재배포 권한을 먼저 확인한다.
- 방법론의 공개 범위가 제한된 조건은 `unknown`으로 남긴다. 역산값을 공식 규칙처럼 저장하지 않는다.
- KRX 규칙 엔진에 MSCI 조건을 if 문으로 덧붙이지 말고 provider adapter로 분리한다.

### 6.3 수집 실패 정책

- 마지막 성공 데이터는 보이되 `최신 아님` 상태와 마지막 성공시각을 표시한다.
- 일부 종목의 가격 누락은 커버리지와 품질 경고에 반영한다.
- 구성 원본이 없으면 추정 구성 목록을 최신 공식 구성으로 표시하지 않는다.
- 원본 형식 변경, 종목 수 불일치, 비중 합계 오류는 빌드를 실패시킨다.
- 자동 보정은 로그와 품질 플래그 없이 수행하지 않는다.

---

## 7. 규칙 엔진과 과거 분석

### 7.1 공급자 adapter 계약

```python
class IndexMethodologyAdapter:
    def eligible_universe(self, as_of, data): ...
    def calculate_features(self, review, data): ...
    def apply_selection_rules(self, review, features): ...
    def explain(self, security_id, result): ...
```

초기 구현은 `Kospi200Adapter` 하나다. 이후 `MsciKoreaStandardAdapter`를 추가하되 공통 UI payload로 변환한다.

### 7.2 방법론 버전 적용

`methodology_versions.json`은 적어도 다음을 가진다.

```json
{
  "version": "krx-kospi200-2021-07",
  "effective_from": "2021-07-01",
  "effective_to": null,
  "source_url": "...",
  "source_hash": "sha256:...",
  "parameters": {},
  "manual_exceptions": []
}
```

실제 규칙 숫자를 코드 곳곳에 하드코딩하지 말고 versioned parameter로 둔다. 문서상 규칙과 실제 코드 파라미터가 다르면 검증이 실패해야 한다.

### 7.3 발표 전 조건 경로 생성

각 과거 리뷰에 대해 다음 순서로 실행한다.

1. 당시 방법론 버전을 선택한다.
2. `data_cutoff_at` 이전에 관측 가능했던 데이터만 자른다.
3. 당시에 알려진 기존 구성종목과 기업행사를 복원한다.
4. 월별 또는 거래일별 feature를 계산한다.
5. 각 시점에서 자격·1차선정·버퍼·특례 단계를 저장한다.
6. 실제 발표 결과와 비교하되 입력 feature를 다시 바꾸지 않는다.
7. 불일치를 `data_gap | methodology_gap | discretionary_exception | implementation_bug`로 분류한다.

### 7.4 사례 연결

기존 사례 대시보드는 편입 전후 가격·수급·P1~P4를 담당한다. 지수 레이더의 과거 편입 경로는 규칙 충족 과정을 담당한다.

두 데이터는 `review_id + security_id`로 연결하고 서로 복제하지 않는다.

- 지수 레이더 → `사후 주가·수급 사례 보기`
- 사례 상세 → `발표 전 편입 조건 보기`

---

## 8. 예측 및 백테스트 원칙

### 8.1 단계

1. **규칙 재현** — 과거 공식 결과를 방법론 엔진이 얼마나 재현하는지 측정
2. **경계선 신호** — 컷오프 거리와 추세를 제공하되 확률은 표시하지 않음
3. **통계 모델** — 표본과 검증이 충분할 때만 확률 또는 등급 산출
4. **후보 화면 공개** — 검증 결과와 불확실성을 같은 화면에 공개

### 8.2 누수 방지

- 리뷰별 walk-forward 방식만 사용한다.
- 학습 데이터는 예측 대상 발표시점 이전에 공개된 값으로 제한한다.
- 나중에 정정된 주식수, 산업군, 유동비율은 당시 이용 가능 버전과 분리한다.
- `announcement_at` 이후 기사·리포트·가격은 발표 전 feature에 넣지 않는다.
- 현재 방법론으로 과거 전체를 다시 계산한 결과는 연구용 비교값일 뿐 실제 백테스트가 아니다.

### 8.3 최소 평가 지표

| 목적 | 지표 |
|---|---|
| 편입 후보 순위 | Precision@K, Recall@K, 평균 실제 편입 순위 |
| 이진 편입 판단 | Precision, Recall, F1, confusion matrix |
| 확률 | Brier score, calibration curve |
| 규칙 엔진 | 공식 결과 일치율, 예외 분류율, 데이터 결측률 |
| 운영 | 최신 데이터 지연, 가격 커버리지, 비중 합계 오차 |

### 8.4 공개 게이트

후보 화면은 다음 조건을 모두 충족한 뒤 노출한다.

- 적어도 여러 정기 리뷰를 포함한 walk-forward 결과가 존재한다.
- 편입과 미편입 표본을 모두 포함한다.
- 방법론 버전별 예외와 결측 건이 문서화돼 있다.
- 규칙 엔진 불일치가 수치와 원인으로 공개돼 있다.
- 화면에서 신호 생성일, 데이터 기준일, 모델 버전을 확인할 수 있다.

정확도 목표 숫자는 표본을 본 뒤 정한다. 먼저 임의의 80% 같은 수치를 성공 기준으로 고정하지 않는다.

---

## 9. 구현 파일 계약

### 9.1 새 파일

```text
tools/index_radar_template.html
tools/build_index_radar.py
tools/fetch_index_data.py
tools/validate_index_data.py
data/indexes/registry.json
data/indexes/security_master.csv
data/indexes/kospi200/...
dist/index-radar.html                       # 생성물
dist/index-radar-data/...                  # 생성물
```

실제 수집 API가 서로 다르면 `tools/index_providers/krx.py`, `tools/index_providers/kiwoom.py`로 분리한다. 수집, 정규화, 규칙 계산, 화면 생성을 한 스크립트에 넣지 않는다.

### 9.2 기존 파일 수정

- `tools/build_all.py`: 지수 레이더 빌더 호출 추가
- `tools/deploy_dashboard.py`: 새 HTML·manifest의 운영 파일 일치 검증 추가
- `.vercelignore`: `index-radar.html`과 필요한 `index-radar-data/**`만 허용
- `tools/portal_template.html`: 헤더 메뉴와 홈 진입 카드 추가
- `tools/build_portal.py`: macro 셸 헤더에도 동일 메뉴 추가
- `tools/dashboard_template.html`: 사례 상세 헤더 추가
- `tools/split_case_template.html`: 인적분할 상세 헤더 추가
- `tools/oil_link_template.html`: 현재 공통 헤더 예외를 해소하고 메뉴 추가
- `README.md`: 실행 명령과 지수 레이더 설계·화면 링크 추가
- `design/DESIGN_GUIDE.md`: 구현 상태와 검증 결과를 실제 상태로 갱신

`dist/`를 직접 수정하지 않는다. 신규 전역 메뉴를 여러 템플릿에 문자열로 복제하기 전에 공통 메뉴 정의를 만드는 것을 우선한다.

권장 구조:

```text
data/site_navigation.json       # href, label, key, order
tools/site_shell.py             # active 상태와 상대경로를 받아 헤더 HTML 생성
```

템플릿에는 `<!--__SITE_HEADER__-->` 자리표시자를 두고 각 빌더가 공통 셸을 삽입한다. 정적 HTML에서도 현재 메뉴와 검색 복귀 경로가 유지되어야 한다.

### 9.3 명령 계약

```powershell
# 특정 기준일의 KOSPI 200 자료 수집 및 정규화
python tools/fetch_index_data.py --index kospi200 --as-of 2026-09-04

# 원본·스키마·종목 수·비중 합계·참조 무결성 검사
python tools/validate_index_data.py --index kospi200

# 지수 레이더 화면과 웹 payload 생성
python tools/build_index_radar.py

# 전체 정적 사이트 생성
python tools/build_all.py

# 전체 빌드·운영 배포·고정 주소 검증
python tools/deploy_dashboard.py
```

수집에 인증이 필요할 경우 키나 계정 정보는 저장소와 `dist/`에 기록하지 않는다. `build_index_radar.py`는 네트워크 없이 정규화된 데이터만으로 재현 가능해야 한다.

---

## 10. 단계별 구현 순서

### Phase 0 — 공통 셸과 계약

- 공통 메뉴 정의와 헤더 생성 경로 마련
- index registry와 schema version 정의
- 품질 플래그, timestamp, 출처 계약 구현
- 샘플 데이터가 아니라 검증 가능한 KRX 소스 1개로 작은 fixture 작성

완료 조건: 모든 기존 화면이 이전 기능을 유지하면서 같은 다섯 개 메뉴와 정확한 `aria-current`를 보인다.

### Phase 1 — KOSPI 200 현재 구성 MVP

- 최신 공식 구성 수집
- 최신 가격, 지수주식수·유동비율 확보
- 공식 비중과 현재가 추정 비중 분리 계산
- 상위 종목·산업군 막대와 구성 표 구현
- 기준시각·출처·커버리지·품질 상태 표시
- 홈 진입 카드와 통합 검색 연결

완료 조건: 종목 수, 비중 합계, 가격 커버리지, 화면 정렬이 검증되고 고정 주소에 배포된다.

### Phase 2 — 스냅샷과 변경 이력

- 일별 또는 수집 주기별 append-only 기록
- 기준일 선택, 두 날짜 비교, 편입·편출 타임라인
- 기업행사와 stale price 처리

완료 조건: 임의의 두 보유 스냅샷을 URL로 재현하고 신규·제외·비중 변화를 같은 결과로 다시 계산할 수 있다.

현재 상태: `2026년 상반기 KOSPI 200` 리뷰 1건의 발표·적용·리밸런싱 기준일과 편입 4종목 분석을 구현했다. 임의 스냅샷 비교는 미구현이다.

### Phase 3 — 과거 편입 조건 분석

- 방법론 버전 저장
- KOSPI 200 규칙 adapter 구현
- 리뷰별 당시 데이터 컷오프 복원
- 실제 편입/미편입과 규칙 단계 비교
- 기존 지수편입 사례와 양방향 링크

완료 조건: 최소 몇 개의 과거 리뷰에서 오탐과 누락을 숨기지 않은 검증표가 생성된다.

현재 상태: 첫 리뷰의 실제 편입 종목 4개에 대한 조건 경로를 구현했다. 미편입 후보와 다수 리뷰를 포함한 오탐·누락 검증표 및 자동 규칙 adapter는 미구현이다.

### Phase 4 — 후보 신호

- 규칙 기반 경계선 목록
- walk-forward 백테스트
- 신호 등급과 근거 설명
- 공개 게이트 통과 후 후보 탭 노출

완료 조건: 모든 후보가 동일 스냅샷, 방법론, 엔진 버전으로 재현되고 최근 검증 성능을 함께 표시한다.

### Phase 5 — MSCI 확장

- 라이선스와 공개 가능 범위 확인
- MSCI 전용 provider와 methodology adapter 추가
- 발표 timezone과 리뷰 유형 확장
- 공통 화면 payload 호환성 검증

완료 조건: KRX 전용 필드가 없는 MSCI 데이터도 화면이 깨지지 않고, 미공개 조건을 `unknown`으로 표현한다.

---

## 11. 테스트와 검수

### 11.1 데이터 테스트

- 구성종목 영구 ID 중복 없음
- 지수별·일자별 종목 수가 기대 범위와 일치
- 공식 또는 추정 비중 합계가 허용 오차 이내
- 음수 가격·주식수·유동비율 없음
- `effective_at <= asof` 관계 검증
- 리뷰의 발표일과 적용일 순서 검증
- 모든 파생값이 입력 snapshot과 engine version을 참조
- corporate action 전후 시총 불연속 경고
- 결측을 0으로 계산하지 않음

### 11.2 규칙 엔진 테스트

- 방법론 문서의 대표 예제를 fixture로 고정
- 기존 구성종목 버퍼와 신규 후보 문턱을 별도 테스트
- 대형 신규상장 특례, 합병·분할, 관리종목 같은 예외 테스트
- 현재 데이터가 과거 계산에 유입되지 않는지 cutoff 테스트
- 같은 입력과 엔진 버전에서 동일 결과가 생성되는지 결정성 테스트

### 11.3 UI 테스트

- 360, 440, 740, 1024, 1440px
- 밝은/어두운 모드
- 긴 종목명·영문 지수명·결측값·품질 경고 다수
- 키보드로 메뉴, 지수 선택, 탭, 표 정렬 사용 가능
- 표의 가로 스크롤이 페이지 전체를 밀지 않음
- URL 복사 후 같은 지수·기준일·탭·필터 복원
- 공식/추정 라벨과 출처가 모바일에서도 사라지지 않음
- JavaScript 오류, 404 asset, JSON schema 불일치 없음

### 11.4 배포 검증

- `python tools/build_all.py` 성공
- Python 문법과 생성 JSON 파싱 성공
- `dist/index-radar.html`과 manifest 생성
- `.vercelignore`에 원본·인증정보가 포함되지 않음
- `python tools/deploy_dashboard.py`가 운영 배포 후 고정 주소의 HTML과 manifest 해시를 확인
- 실제 `https://investment-spring.vercel.app/index-radar.html`에서 메뉴·데이터 로드·상세 URL 확인

---

## 12. Terra 작업 지시 요약

1. 시작 전에 `AGENTS.md`, `design/DESIGN_GUIDE.md`, 이 문서를 전부 읽는다.
2. 사용자 기존 변경을 보존하고 `dist/`를 원본처럼 직접 수정하지 않는다.
3. Phase 0과 Phase 1을 먼저 구현한다. 예측 UI를 앞당기지 않는다.
4. 공식 비중과 현재가 추정 비중을 데이터·계산·라벨 모두에서 분리한다.
5. 데이터가 없으면 값을 만들지 말고 결측과 수집 실패를 표시한다.
6. 새 빌더를 `tools/build_all.py`와 운영 배포 검증에 편입한다.
7. 전역 메뉴는 모든 헤더와 상세 화면에 같은 작업 안에서 적용한다.
8. 구현 결과에 맞춰 `DESIGN_GUIDE.md` 본문·파일 대응표·변경 이력을 갱신한다.
9. 로컬 빌드, 브라우저, 운영 고정 주소 검증을 실제로 수행한 범위만 완료 보고한다.

---

## 13. 구현 의사결정 기록

| 결정 | 이유 |
|---|---|
| 메뉴명 `지수 레이더` | 현재 관측·과거 추적·미래 탐지에 모두 맞고 특정 지수에 종속되지 않음 |
| 전용 `index-radar.html` | 대용량 이력과 독립적인 작업 목적을 포털 hash view와 분리 |
| 공식/추정 비중 분리 | 기준시각과 산식이 다른 값을 혼동하지 않기 위해 |
| append-only 스냅샷 | 과거 시점 재현과 사후편향 방지 |
| 방법론 versioning | 지수 규칙 변경을 과거에 소급하지 않기 위해 |
| provider adapter | KRX와 MSCI의 규칙·라이선스·필드 차이를 격리 |
| 후보 탭 지연 공개 | 과거 재현과 검증 없는 정밀 예측을 피하기 위해 |
| 정적 집계 JSON | 현재 Vercel 정적 배포 구조를 유지하고 원본 데이터 노출을 막기 위해 |
