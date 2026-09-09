# 거시 인과 분석 수집 로그

이 파일은 [`design/CAUSAL_ANALYSIS_BATCH_WORKFLOW.md`](../../design/CAUSAL_ANALYSIS_BATCH_WORKFLOW.md)의 카운터와 작업 상태를 기록하는 단일 원장이다.

## 현재 상태

| 항목 | 값 |
|---|---:|
| 운영 기준일 | 2026-09-09 |
| 증분 대기 건수 | 1 |
| 전체 감사 누계 | 19 |
| 다음 증분 병합 질문 | 10 |
| 다음 전체 감사 질문 | 100 |
| 마지막 증분 병합 | 2026-09-09 · `cm-20260909-001` |
| 마지막 전체 감사 | 기준선 설정(2026-09-09) |

기존 정식 편입 자료는 기준선 이전 작업으로 보고 소급 집계하지 않는다. 이 표의 숫자는 아래 작업 목록과 병합·감사 이력으로 다시 계산할 수 있어야 한다.

## 작업 목록

| 순번 | 후보 ID | 분석일 | 원문 | 상태 | 병합 배치 | 비고 |
|---:|---|---|---|---|---|---|
| 1 | `ca-20260909-001` | 2026-09-09 | `2026-09-01-us-equity-long-run-return.md` | deferred | `cm-20260909-001` | r*·희망 저축/투자·미국 장기 기대수익률은 기존 착공·정책금리·한국 주가 배수와 지역·개념이 다름. 별도 모형·노드 정의 후 검토. 채택·재사용 ID: 없음. |
| 2 | `ca-20260909-002` | 2026-09-09 | `2026-08-29-us-treasury-buybacks-gold-bitcoin.md` | merged | `cm-20260909-001` | 유동성 지원 바이백만 채택. 현금관리 바이백·TGA–준비금 회계·준비금 희소성·금/비트코인은 미편입. 채택·재사용 ID: `treasury-liquidity-support-buyback`, `off-the-run-treasury-liquidity`. |
| 3 | `ca-20260909-003` | 2026-09-09 | `2026-08-31-new-asset-regime.md` | merged | `cm-20260909-001` | 일본 수입물가·종합 CPI를 별도 등록. QT·금리 기존 경로 재사용. 일본 정책금리 노드와 자동 연결하지 않음. 채택·재사용 ID: `usd-jpy-rate`, `jp-import-price-index`, `jp-headline-inflation`, `long-bond-net-supply`. |
| 4 | `ca-20260909-028` | 2026-09-09 | `2026-08-28-france-debt-reset.md` | deferred | `cm-20260909-001` | 프랑스 OAT–Bund 신용·유동성·분절화 스프레드는 기존 일반 기간프리미엄과 합치지 않음. 국가별 경로와 정책수단의 현재 유효기간·적격성 확인 필요. 채택·재사용 ID: 없음. |
| 5 | `ca-20260909-004` | 2026-09-09 | `2026-08-30-agricultural-prices-korea-inflation.md` | deferred | `cm-20260909-001` | 밀·옥수수·대두 및 한국 식품·사료·축산물은 별도 품목·지역 노드가 필요. 기존 임금 전가·글로벌 물가와 합치지 않음. CPI 기여는 산술 관계로 보존. 채택·재사용 ID: 없음. |
| 6 | `ca-20260909-029` | 2026-09-09 | `2026-08-31-kospi-fx-rate-outlook.md` | merged | `cm-20260909-001` | 반도체 실적의 순환노출·기능통화와 기대물가/위험보상 조건을 보강. USD/KRW 수준·한미 금리차·범용 수출기업 이익 노드는 보류. 후보 첫 행의 하락 충격 부호를 수준 부호로 가져오지 않음. 채택·재사용 ID: `earnings`, `term-premium`. |
| 7 | `ca-20260909-030` | 2026-09-09 | `2026-08-27-ai-industry-financing-triggers.md` | merged | `cm-20260909-001` | 027·031과 겹치는 프로젝트 계약상 신용보강 부분만 좁혀 채택. 지분투자·클라우드 크레딧·기업 runway·경쟁 동기는 별개로 보류. 필요자금과 조달능력도 분리. 채택·재사용 ID: `ai-vendor-credit-support`, `ai-project-financeability`, `ai-provider-profit`. |
| 8 | `ca-20260909-027` | 2026-09-09 | `2026-08-27-nvidia-ai-financing-us-long-yield.md` | merged | `cm-20260909-001` | 미국 프로젝트 금융·현금 부족·유효 보증 지급 5개 노드 채택. 독립 고객 현금회수는 조건으로 보존. 유동화·펀드 환매·기관 듀레이션·국채 대체의 신규 경로와 최종손실 노드는 보류. 채택·재사용 ID: `ai-vendor-credit-support`, `ai-project-financeability`, `dc-construction`, `ai-project-cashflow-mismatch`, `ai-project-default-risk`, `vendor-contingent-cash-outflow`, `long-bond-net-supply`, `structural-bond-demand`. |
| 9 | `ca-20260909-260826` | 2026-09-09 | `2026-08-26-kospi-volatility-option-strategy.md` | deferred | `cm-20260909-001` | V-KOSPI200·옵션 보험수요·마진은 한국 국채선물과 기초자산·계약이 다름. 별도 옵션 곡면·만기·실현변동성 정의 필요. 현금결제 산술은 인과선으로 등록하지 않음. 채택·재사용 ID: 없음. |
| 10 | `ca-20260909-025` | 2026-09-09 | `2026-08-25-yield-curve-treasury-futures.md` | merged | `cm-20260909-001` | 기존 금리 분해·고정채 가격선 재사용과 조건 보강. 회사채 스프레드 분해·미국 ZB CTD/인도·TLT 총수익은 별도 정의로 보류. 채택·재사용 ID: `expected-policy-path`, `term-premium`, `lt-rate`, `fixed-rate-bond-price`. |
| 11 | `ca-20260909-031` | 2026-09-09 | `2026-08-26-korea-housing-ai-circular-finance.md` | merged | `cm-20260909-001` | 미국 AI 프로젝트 분기를 027과 중복 없이 병합. 한국 정책모기지·HF MBS·HUG 전체 상품손실은 기존 PF와 다르므로 보류. 한국 주택→미국 AI 직접선 없음. 채택·재사용 ID: `ai-vendor-credit-support`, `ai-project-financeability`, `ai-project-cashflow-mismatch`, `ai-project-default-risk`, `vendor-contingent-cash-outflow`, `refinancing`, `power-price`. |
| 12 | `ca-20260909-023` | 2026-09-09 | `2026-08-23-current-most-promising-investment.md` | merged | `cm-20260909-001` | 듀레이션·볼록성 및 가격/분배/총수익·YTM의 차이를 기존 상세에 반영. TLT 원화수익·CIP/베이시스·미국 ZB 순DV01은 기존 한국 선물·주식 환산과 합치지 않고 보류. 채택·재사용 ID: `fixed-rate-bond-price`, `expected-policy-path`, `structural-bond-demand`. |
| 13 | `ca-20260909-260824` | 2026-09-09 | `2026-08-24-long-treasury-investment-methods.md` | merged | `cm-20260909-001` | 장기채 가격·바이백 유동성 경로를 기존·002와 재사용. TMF 일일재설정·CME 인도/롤·원화 총수익은 별도 상품/관측 정의로 보류. 채택·재사용 ID: `fixed-rate-bond-price`, `treasury-liquidity-support-buyback`, `off-the-run-treasury-liquidity`. |
| 14 | `ca-20260909-032` | 2026-09-09 | `2026-08-22-gold-bitcoin-rally-drivers.md` | deferred | `cm-20260909-001` | 금·비트코인의 핵심 경로는 보류. 실질금리·준비자산 다변화·암호자산 위험선호를 분리해야 함. 바이백의 공통 부분은 002의 공식 ID 참조만 남기며 카드 전체를 병합으로 세지 않음. 채택·재사용 ID: 없음. |
| 15 | `ca-20260909-033` | 2026-09-09 | `2026-08-24-kospi-foreign-selling-buyback-liquidity.md` | merged | `cm-20260909-001` | 기존 매입·유동성 조건 보강. 체결 투자자 순매매의 합은 0이므로 외국인 매도에서 다른 순매수를 뺀 잔여 불균형 정의는 수정·기각. 공격적 주문/호가를 정의한 뒤 새 미시구조 노드 검토. 예탁금·곡물·AI 신용물 추가 분기는 보류. 채택·재사용 ID: `buyback-flow-intensity`, `issuer-price-support-pressure`, `long-bond-net-supply`, `structural-bond-demand`. |
| 16 | `ca-20260909-260903` | 2026-09-09 | `2026-09-03-samsung-us-cross-listing.md` | merged | `cm-20260909-001` | 기존 접근성·공시·유동성·자본비용 선 재사용, 상장 유지비용·미확정 사건 한계 보강. 저축/투자/경상계정 산술·스테이블코인·해외 주식 배분은 보류. 채택·재사용 ID: `us-cross-listing-access`. |
| 17 | `ca-20260909-260820` | 2026-09-09 | `2026-08-20-usdkrw-futures-short-strategy.md` | deferred | `cm-20260909-001` | KRX 달러선물·NDF·FX스왑·현물의 만기/결제/단위가 달라 별도 한국 FX 부분망 필요. 국민연금·당국 실집행과 환율 수준 정의 후 검토. 계약 손익·인수도는 인과선 제외. 채택·재사용 ID: 없음. |
| 18 | `ca-20260909-034` | 2026-09-09 | `2026-08-21-midterm-tariffs-equities.md` | merged | `cm-20260909-001` | 매입·후속 소각·배당을 분리하고 EPS 분모 중복 계산을 교정. 관세는 전력요금 tariff와 별개. 대미투자·공공보증·관세·중간선거 신규 경로는 보류. 채택·재사용 ID: `buyback-post-use`, `buyback-flow-intensity`. |
| 19 | `ca-20260909-035` | 2026-09-09 | `2026-08-19-us-treasury-buybacks-kospi.md` | pending | — | QE·QT·준비금 관리 매입을 구분하고, 레포·마진→국채 베이시스 청산→시장유동성, MBS 순공급→스프레드→모기지금리 후보를 추가. 바이백→30년물·환율·KOSPI 직접선은 기각. |

상태 값은 `pending`(대기), `merged`(병합), `deferred`(보류), `rejected`(기각), `no-candidate`(인과 없음) 중 하나만 사용한다. `deferred`, `rejected`, `no-candidate`도 분석 완료 작업단위이므로 전체 감사 누계에는 포함한다. 증분 대기 건수에는 아직 증분 병합에서 검토하지 않은 `pending` 행만 포함한다.

현재 보류 카드는 6건이며, 일부 병합한 12건의 미편입 항목도 [첫 배치 보고서](merges/cm-20260909-001.md)에 남긴다. 검토한 보류는 신규 증분 대기에 다시 세지 않는다. 다음 신규 `pending` 10건에서 병합 여부를 묻고, 전체 감사까지 82건 남았다.

## 증분 병합 이력

| 배치 ID | 완료일 | 검토 작업 수 | 병합 | 보류 | 기각 | 변경 파일·노드·관계 | 검증 |
|---|---|---:|---:|---:|---:|---|---|
| `cm-20260909-001` | 2026-09-09 | 18 | 12 | 6 | 0 | [보고서](merges/cm-20260909-001.md) · 변수 +9·가설 +9·기존 상세 12개·연결 설명 2개 보강, 원문 경로 14건 복구 | 단위 8개·부분망·로컬/운영 4폭×2모드·전체 빌드·31파일+루트 일치 통과 |

## 전체 감사 이력

| 감사 ID | 완료일 | 감사 대상 작업 수 | 결과 보고서 | 미해결 항목 | 검증·배포 |
|---|---|---:|---|---|---|
