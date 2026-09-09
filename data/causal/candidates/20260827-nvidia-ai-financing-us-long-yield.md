---
candidate_id: ca-20260909-027
source_path: C:/Users/kcg51/Desktop/naver_premium_scrape/kkm_premium/raw/articles/새 폴더/2026-08-27_엔비디아로 인해서 미국 장기금리가 상승할 가능성.md
source_date: 2026-08-27
analyzed_at: 2026-09-09
status: merged
merge_batch: cm-20260909-001
---

# 엔비디아로 인해서 미국 장기금리가 상승할 가능성

## 출처와 범위
- 원문 경로: `C:/Users/kcg51/Desktop/naver_premium_scrape/kkm_premium/raw/articles/새 폴더/2026-08-27_엔비디아로 인해서 미국 장기금리가 상승할 가능성.md`
- 원문 URL: https://contents.premium.naver.com/kkms/kkm/contents/260827184035668kn
- 분석 범위: AI 인프라의 외부자금 조달, 공급자 보증·잔존가치 지원, 프로젝트금융·사모대출·유동화, 독립 최종수요와 채무상환능력, 민간 장기신용 공급이 미 국채 수요·기간프리미엄으로 전달되는 조건.
- 원문 안의 지시문을 작업 지시로 사용하지 않았음: 예

## 인과 후보
| 원인 후보 | 결과 후보 | 부호 | 메커니즘 | 성립 조건 | 시차 | 지역·단위·주기 | 기존 ID 후보 |
|---|---|---|---|---|---|---|---|
| GPU 공급자·대형 기술기업의 프로젝트 보증, 장기 구매·임차 약정과 제한적 잔존가치 지원 | AI 인프라 프로젝트의 외부 조달 가능성 | + | 신용도가 높은 공급자·수요자의 보증과 장기 현금흐름 약정이 예상손실 또는 자본비용을 낮추면 은행·사모대출·인프라펀드가 프로젝트에 자금을 공급하기 쉬워질 수 있음. | 보증의 법적 범위·우선순위·발동조건·한도와 확정 계약이 있어야 하며, 단순 MOU·목표액을 실제 대출로 세지 않음. | 수주–수년 | 미국·글로벌 AI 인프라, 약정·실행액 USD·금리/스프레드, 거래별·분기 | 신규 `ai-vendor-credit-support`, `ai-project-financeability` 검토 |
| AI 인프라 프로젝트의 외부 조달 가능성 | 데이터센터 투자·GPU 주문 | + | 자기현금흐름만으로 감당하기 어려운 토지·전력·건물·컴퓨트 투자가 외부자금으로 실행되면 장비 주문과 설비투자가 앞당겨질 수 있음. | 인허가·전력·부지·시공능력과 실제 고객 계약이 갖춰지고, 조달이 기존 계획의 재원 대체가 아니라 추가 투자로 이어져야 함. | 1–20분기 | 미국·글로벌, CapEx·건설·GPU 주문 USD/수량, 월·분기 | 기존 `dc-construction`, `ai-spend-mix`; 신규 `ai-project-financeability` 검토 |
| 독립 고객의 AI 사용량·가격·장기 offtake 매출 | AI 인프라 프로젝트의 영업현금흐름·채무상환능력 | + | 제3자 고객이 컴퓨트를 실제 사용하고 대가를 지급하면 이자·원금·임차료를 상환할 반복 현금흐름이 생김. | 공급자·관계회사·동일 금융플랫폼 사이의 순환 매출을 제거하고 가동률, 단가, 계약해지권, 고객집중과 현금회수를 확인해야 함. | 즉시–수년 | AI 클라우드·데이터센터, 가동률 %·매출/현금 USD·DSCR, 월·분기 | 신규 `independent-ai-offtake`, `ai-project-debt-service-capacity` 검토 |
| 장기 고정 임차·전력·장비·원리금 의무 대비 독립 고객 현금흐름 부족 | AI 프로젝트의 부도·차환 위험 | + | 사용률·가격 또는 고객매출이 예상보다 낮은데 고정비와 만기가 먼저 도래하면 DSCR이 악화되고 추가자금·차환에 의존하게 됨. | 계약별 선후순위·유예기간·스폰서 추가출자·현금준비금과 GPU·부지·전력권의 회수가능가치를 반영해야 함. | 수개월–수년 | 미국·글로벌, DSCR·연체·부도율·차환스프레드, 월·분기 | 신규 `ai-project-cashflow-mismatch`, `ai-project-default-risk` 검토 |
| 보증 대상 AI 프로젝트의 계약상 부도·임차 불이행 | GPU 공급자·스폰서의 보증 이행·현금유출 위험 | + | 정해진 트리거가 발생하면 주석상 우발약정이 실제 지급, 임차승계 또는 자산매입 의무로 전환될 수 있음. | 총 프로젝트비가 아니라 보증 상한·단계별 발효액·면책·대체임차인·구상권과 회수액으로 순노출을 계산해야 함. | 즉시–20년 | 기업·프로젝트, 최대/발효/지급 노출 USD, 사건별·분기 | 신규 `ai-guarantee-call-risk`, `vendor-contingent-cash-outflow` 검토 |
| AI 프로젝트 부도·담보가치 하락 | 은행·사모대출·ABS/CMBS 투자자의 손실·위험회피 | + | 원리금 연체와 GPU·데이터센터 담보 회수율 하락이 대손·평가손실을 만들고 유사 거래의 요구수익률을 높일 수 있음. | 실제 채권자, 담보권, LTV, 보증·보험·선후순위와 증권별 워터폴을 확인하고 약정액을 최종손실로 간주하지 않음. | 즉시–수년 | 미국·글로벌 신용시장, 손실 USD·스프레드 bp·부도율, 일·분기 | 신규 `ai-infrastructure-credit-loss` 검토 |
| AI 관련 사모대출·유동화 손실과 반유동성 펀드 환매 압력 | AI 인프라 신규 금융의 긴축 | - | 손실과 환매요청이 펀드의 가용현금·은행 신용한도·투자자 위험선호를 줄이면 신규대출 규모가 감소하고 약정금리·담보조건이 강화될 수 있음. | 펀드의 게이트·장기자본, 은행·보험·공모채 대체조달과 익스포저 분산이 충격을 흡수하지 못해야 함. | 일–12분기 | 미국 사모신용·구조화금융, 신규대출·스프레드·환매 %, 월·분기 | 신규 `ai-private-credit-conditions`; 기존 `refinancing`과 자동 통합 금지 |
| 실제 데이터센터·장비대출 유동화 발행 | AI 인프라 자금의 기관투자자 기반 | + | 대출·임대료 현금흐름을 트랜치 증권으로 전환하면 위험선호와 만기가 다른 보험·연기금·자산운용사에 익스포저를 배분해 조달원을 넓힐 수 있음. | 적격 자산이 실제 SPC로 이전되고 증권이 발행·매각되어야 함. MOU, 대출 약정과 ABS·CMBS를 동일시하지 않으며 유동화가 신용위험을 제거하지 않음. | 수개월–수년 | 미국 데이터센터·장비금융, ABS/CMBS 발행액 USD·스프레드, 거래별·월 | 신규 `ai-infrastructure-securitization`, `ai-institutional-funding-base` 검토 |
| AI 관련 회사채·프로젝트채·ABS/CMBS의 순발행과 듀레이션 | 민간투자자가 흡수해야 할 장기 신용위험·듀레이션 | + | 신규 발행이 상환·중앙은행 보유·해외수요를 초과하면 시장은 추가 신용위험과 금리민감도를 보유해야 함. | 발표된 투자·플랫폼 목표가 아니라 실제 순발행을 만기·듀레이션 등가액으로 측정하고, 은행대출과 증권 발행을 중복 집계하지 않음. | 즉시–수년 | 미국·글로벌, 순발행 USD·10년 등가 듀레이션, 일·월·분기 | 신규 `ai-credit-duration-net-supply` 검토 |
| 공통 장기투자자의 AI 신용위험·듀레이션 흡수 | 미 장기국채의 구조적 한계수요 | - | 보험·연기금·채권펀드 등 같은 투자자의 위험예산·듀레이션 수용력이 제한되어 있고 AI 신용물이 충분한 스프레드를 제공하면 일부 자금이 국채에서 이동할 수 있음. | 투자자군·만기·통화·헤지·규제상 대체 가능성이 확인되고 신규 저축·해외유입·포트폴리오 확대가 발행을 모두 흡수하지 못해야 함. 신용채와 안전자산은 위기 시 대체재가 아닐 수 있음. | 즉시–수년 | 미국 장기채, 투자자별 순매수·보유 USD/비중, 월·분기 | 기존 `structural-bond-demand`; 신규 `institutional-duration-capacity-usage` 검토 |
| 미 장기국채의 구조적 한계수요 | 미 국채 기간프리미엄 | - | 다른 조건이 같을 때 지속적 한계수요가 강하면 민간이 국채 듀레이션을 보유하기 위해 요구하는 추가 보상이 낮아질 수 있음. | 기대 단기금리, 국채 순공급·만기구성, 인플레이션 위험, 안전자산 선호와 딜러 중개능력을 함께 통제해야 함. | 즉시–수년 | 미국, 기간프리미엄 %p, 일·월 | 기존 `structural-bond-demand → term-premium` 재사용 |
| 미 국채 기간프리미엄 | 미 장기국채금리 | + | 기대 단기금리 경로가 같다면 기간프리미엄 상승은 명목 장기수익률을 높임. | 기간프리미엄은 비관측 모형 추정치이므로 ACM 등 모형과 기대단기금리 분해를 함께 제시하고 30년 금리 변동 전체를 AI 금융으로 설명하지 않음. | 즉시–수년 | 미국, 10·30년 국채금리 및 기간프리미엄 %p, 일·월 | 기존 `term-premium → lt-rate` 재사용 |

## 근거
- 원문 근거: AI 기업의 현금흐름 부족이 사모대출·지급보증·구조화금융을 늘리고, 빅테크 회사채와 GPU 담보 유동화가 장기 투자자금을 미 국채에서 빼내 장기금리를 올릴 수 있다는 주장.
- 외부 근거와 확인일:
  - NVIDIA의 2026년 2분기 10-Q는 6월 중 250억 달러 선순위 무담보채 발행, 560억 달러의 추가 약정, AI 클라우드 관련 35억 달러 보증, 8월 체결한 최대 1,050억 달러 SB Energy 관련 단계적 보증, 제3자 자본을 장기간 5,000억 달러 이상 동원하려는 MOU를 공시한다. 이 플랫폼은 독립 자본공급자가 인수하며 확정계약으로 이어지지 않을 수 있고, NVIDIA는 일부 프로젝트에 제한적 잔존가치 지원을 선택할 수 있다고 명시한다. https://www.sec.gov/Archives/edgar/data/1045810/000104581026000075/nvda-20260726.htm 및 https://investor.nvidia.com/files/doc_financials/2027/NVDA-2027-Q2-10Q-Final-including-exhibits.pdf (확인 2026-09-09)
  - NVIDIA의 2026년 8월 10일 발표는 Apollo·BlackRock·Blackstone·Brookfield·Goldman Sachs·KKR와 독립 컴퓨트 금융 플랫폼을 만들기 위한 MOU이며, 5,000억 달러는 `over time` 동원 목표이고 최종 계약을 전제로 한다. GPU 담보 ABS 발행 완료나 NVIDIA의 차입액으로 표현하지 않는다. https://investor.nvidia.com/news/press-release-details/2026/NVIDIA-Partners-With-Apollo-BlackRock-Blackstone-Brookfield-Goldman-Sachs-and-KKR-to-Establish-AI-Compute-Infrastructure-Financing-Platforms-to-Mobilize-Over-500-Billion-of-Third-Party-Capital/default.aspx (확인 2026-09-09)
  - 연준 2026년 7월 통화정책보고서는 AI 인프라 확장을 위한 대형 상장 기술기업의 투자등급 회사채 순발행이 1분기에 특히 강했다고 평가하되, 사모신용 심리 악화의 광범위한 신용시장 파급은 제한적이었다고 기록한다. https://www.federalreserve.gov/monetarypolicy/2026-07-mpr-part1.htm (확인 2026-09-09)
  - IMF 2026년 4월 GFSR은 데이터센터 유동화가 2018년 이후 460억 달러로 확대됐지만 여전히 틈새 조달원이라고 평가한다. 독립 최종수요를 가릴 수 있는 순환금융, 임차인 집중, 기술 노후화, 전력·시공 지연과 차환위험을 핵심 취약성으로 제시한다. https://www.imf.org/-/media/files/publications/gfsr/2026/april/english/ch1.pdf (확인 2026-09-09)
  - Basel 신용위험 체계에서 기업 익스포저의 위험가중치는 신용등급 또는 PD·LGD·EAD·만기와 적격 담보·보증 등으로 결정된다. 적자·무담보 기업이라는 이유만으로 은행대출이 금지된다는 규칙은 아니다. https://www.bis.org/basel_framework/chapter/CRE/20.htm 및 https://www.bis.org/basel_framework/chapter/CRE/31.htm (확인 2026-09-09)
  - 연준은 장기자산의 민간 보유량과 듀레이션이 기간프리미엄에 영향을 줄 수 있는 포트폴리오 균형 경로를 사용하지만 효과 크기의 불확실성을 강조한다. https://www.federalreserve.gov/econres/feds/the-federal-reserves-portfolio-and-its-effect-on-interest-rates.htm 및 https://www.federalreserve.gov/econres/notes/feds-notes/substitutability-between-balance-sheet-reductions-and-policy-rate-hikes-some-illustrations-and-a-discussion-20220603.html (확인 2026-09-09)
  - 2008년 하반기 미 10년물 수익률은 약 140bp 하락했고, 첫 대규모 자산매입 발표일에도 10년물·MBS·회사채 금리는 대체로 하락했다. `제로금리인데 MBS 때문에 10년물이 하락하지 않았다`는 원문 설명과 반대다. https://www.federalreserve.gov/boarddocs/rptcongress/annual08/sec1/c1.htm 및 https://www.federalreserve.gov/newsevents/speech/yellen20110108a.htm (확인 2026-09-09)
  - 2026년 연준은 MBS 원금회수를 장기국채가 아니라 주로 Treasury bill에 재투자하고, 준비금 관리 매입도 bill 및 필요시 잔존만기 3년 이하 국채로 제한한다. https://www.federalreserve.gov/monetarypolicy/2026-07-mpr-part2.htm 및 https://www.newyorkfed.org/markets/domestic-market-operations/monetary-policy-implementation/treasury-securities/treasury-securities-operational-details (확인 2026-09-09)
- 검증 상태: 원문 주장 / 기업·연준·IMF·BIS 공식자료 확인. 후보 관계는 실제 AI 신용 순발행이 미 국채 수요·기간프리미엄을 변화시켰다는 구조적 인과 추정이나 선행성 검정을 마친 결과가 아님.

## 추가 검증 설계
- 자금조달 상태표: MOU 목표액, 확정 약정, 실제 인출·발행, NVIDIA 보증 발효액과 지급액을 별도 열로 두고 분기마다 SEC 공시와 거래 문서를 대조한다.
- 순환금융 판정: 프로젝트별 GPU 구매자, 대주·보증인, 임차인·offtaker, NVIDIA 투자·클라우드 구매약정을 연결해 독립 제3자 매출과 관계자·공급자 지원 현금흐름을 분리한다.
- 신용위험 검증: LTV, DSCR, 가동률, 컴퓨트 단가, 고객집중, 계약해지권, GPU 세대별 중고가격, 전력·부지 권리와 보증 워터폴을 거래별로 기록한다.
- 유동화 확인: SEC·거래자료에서 대출자산의 SPC 양도, ABS/CMBS 트랜치, 발행액·스프레드·투자자와 신용보강을 확인하기 전에는 `GPU ABS 발행`을 관측값으로 등록하지 않는다.
- 장기금리 검증: AI 회사채·프로젝트채·ABS/CMBS의 실제 순발행을 10년 등가 듀레이션으로 바꾸고, 국채 순발행·SOMA·해외·연기금·보험 수요, OIS 기대경로와 ACM 기간프리미엄을 통제한다. 30년 금리 수준과 단순 동행만으로 인과를 판정하지 않는다.

## 한계·반대 경로
- 한계: 회사채·사모대출·프로젝트금융·장비대출·ABS·CMBS·임차보증은 채무자, 담보, 만기와 위험이 다르다. `AI 부채` 하나로 합산하거나 약정·보증 한도를 발행액으로 더하면 중복된다.
- 한계: 국채와 AI 신용물은 평상시 일부 투자자의 듀레이션 예산을 놓고 경쟁할 수 있지만, 규제상 유동성·신용위험·담보적격성이 달라 완전 대체재가 아니다.
- 반대 경로: AI 투자 확대가 생산성·세수·기업 현금흐름과 신규 저축·해외자본 유입을 늘리면 신용물 발행을 흡수하거나 기대 단기금리를 낮춰 장기금리 효과를 상쇄할 수 있다.
- 반대 경로: AI 신용위험이 현실화하면 위험회피와 안전자산 선호로 회사채·ABS 스프레드는 오르지만 미 국채 수요가 늘어 국채금리는 하락할 수 있다.
- 완충 조건: 확정 장기 offtake, 낮은 LTV, 충분한 스폰서 자기자본, 분산된 고객, 단계적 보증 발효, GPU 전용성 완화와 은행·펀드의 손실흡수력이 순환금융 피드백을 약화한다.

## 보류·기각한 주장
- 주장: `AI는 최종수요가 크지 않으며 대출로만 성장한다.`
  - 사유: 기업·정부·연구기관의 최종 사용과 클라우드 매출이 존재하므로 일괄 부정할 수 없다. 반대로 공급자 지원이 독립수요를 부풀릴 위험도 있어 사용량·가격·현금회수·offtake를 직접 측정해야 함.
- 주장: `AI 기업은 담보와 실적이 없어 은행대출을 받을 수 없고 사모대출만 가능하다.`
  - 사유: 은행은 기업·프로젝트·장비금융을 제공할 수 있고 공식 공시에도 은행 인수 GPU 금융이 존재한다. 자본규제는 위험에 따라 가격·한도를 제약하지만 대출을 전면 금지하지 않음.
- 주장: `적자기업 대출은 BIS 비율을 크게 낮춘다.`
  - 사유: 위험가중자산은 단순 적자 여부가 아니라 등급 또는 PD·LGD·EAD·만기, 담보와 보증을 반영한다. 은행 자본과 익스포저 크기 없이 비율 변화를 정할 수 없음.
- 주장: `2026년 사모대출 규모는 5,600억 달러이고 빅테크 AI 투자는 7,500억 달러다.`
  - 사유: 원문의 지표 범위·기업집합·총액/순액·기간과 원본 경로가 없어 재현하지 못했다. 공식 관측값이나 후보 노드의 현재값으로 등록하지 않음.
- 주장: `NVIDIA가 월가에서 5,000억 달러를 유치해 GPU 담보대출·ABS를 발행한다.`
  - 사유: 5,000억 달러는 독립 금융플랫폼이 장기간 제3자 자본을 동원하려는 MOU 목표다. NVIDIA의 차입이나 이미 조달된 현금이 아니고, 공시에는 확정 GPU ABS 발행이 명시되지 않음.
- 주장: `지급보증은 부채비율을 높이지 않고 주석에만 있으므로 제한이 없다.`
  - 사유: 보증은 계약·회계기준과 손실가능성에 따라 인식·공시되며 발동 시 실제 현금지급·임차승계·자산매입 의무가 된다. 최대한도와 현재 예상손실도 구분해야 함.
- 주장: `집 담보를 GPU로 바꾸면 MBS가 ABS가 된다.`
  - 사유: MBS는 부동산 담보대출을 기초로 하는 증권이고 GPU·장비대출은 자산·장비금융 ABS일 수 있다. 담보만 바꾼 동일 상품이 아니며 현금흐름·회수절차·잔존가치가 다름.
- 주장: `2000년대 MBS 발행이 미 국채보다 많아서 장기국채금리를 높게 유지했고 2008년 제로금리에도 10년물이 하락하지 않았다.`
  - 사유: 2008년 하반기 10년물은 약 140bp 하락했고 연준의 MBS·장기국채 매입 발표도 장기금리 하락과 연결됐다. MBS 총발행과 국채 적자발행을 만기상환·차환을 뺀 순공급 없이 비교할 수 없음.
- 주장: `최근 연준은 MBS를 계속 매도하고 장기국채를 매입한다.`
  - 사유: 2026년 MBS 감소는 주로 원금상환이고, 원금은 Treasury bill에 재투자한다. 일부 소액 운영준비 매매를 정책적 MBS 매각·장기국채 매입으로 일반화할 수 없음.
- 주장: `빅테크 회사채와 GPU ABS는 미 국채 수요를 반드시 줄여 30년 금리를 올린다.`
  - 사유: 실제 순발행·듀레이션, 공통 한계투자자와 자금이동을 확인해야 한다. 신규 저축·해외유입·포트폴리오 확대가 흡수할 수 있고 스트레스 때는 국채 안전자산 수요가 오히려 증가함.
- 주장: `Michael Burry가 GPU ABS CDS를 대거 매입할 것이다.`
  - 사유: 개인의 미래 포지션과 CDS 시장조성 주체에 관한 근거 없는 예측이며 거시 인과 후보가 아님.
- 주장: `펀드가 최대주주이므로 Jensen Huang은 주가를 위해 GPU 매출을 모든 수단으로 늘린다.`
  - 사유: 기관 보유, 이사회 감독, 경영자 유인과 특정 금융계약의 동기를 하나로 연결한 의도 추정이다. 지분율·의결권·보상계약과 의사결정 증거가 없음.
- 주장: `AI는 소비자 돈으로 성장해야 하고 NVIDIA는 성장을 멈춰야 한다.`
  - 사유: 기업용·정부용·구독형 서비스도 최종수요가 될 수 있고 부채·자기자본·영업현금흐름은 모두 정상적인 투자재원이다. 규범적 투자판단은 인과선으로 등록하지 않음.

## 병합 메모
- 새 노드 후보: `ai-vendor-credit-support`, `ai-project-financeability`, `independent-ai-offtake`, `ai-project-debt-service-capacity`, `ai-project-cashflow-mismatch`, `ai-project-default-risk`, `ai-guarantee-call-risk`, `vendor-contingent-cash-outflow`, `ai-infrastructure-credit-loss`, `ai-private-credit-conditions`, `ai-infrastructure-securitization`, `ai-institutional-funding-base`, `ai-credit-duration-net-supply`, `institutional-duration-capacity-usage`
- 기존 노드의 별칭 후보: `dc-construction`, `ai-spend-mix`, `long-bond-net-supply`, `structural-bond-demand`, `term-premium`, `lt-rate`, `refinancing`
- 후보 간 중복 가능성: `ca-20260909-030`의 `ai-strategic-financing`은 이번 `ai-vendor-credit-support`보다 넓은 상위 개념이고, `ai-compute-financing-capacity`는 이번 프로젝트 단위 `ai-project-financeability`와 겹친다. 병합 시 기존 노드를 우선 재사용하되 보증·장기 구매약정·잔존가치 지원처럼 계약상 신용보강을 별도 속성 또는 하위 노드로 보존한다. 같은 후보의 `ai-vendor-realized-loss`와 이번 `vendor-contingent-cash-outflow`도 중복 가능성이 있으나, 보증 발동에 따른 계약상 현금유출과 최종 손실은 시점·회수 가능성이 달라 한 노드로 즉시 합치지 않는다. 반면 독립 최종수요, 프로젝트 현금흐름 불일치, 유동화와 기관 듀레이션을 거쳐 국채 수요·기간프리미엄으로 이어지는 경로는 이번 후보의 추가 범위다.
- 중복 또는 충돌 가능성: `20260901-us-equity-long-run-return.md`의 `AI 고정투자 수요 → 희망 투자-저축 불균형 → r*`는 실물 균형·기대단기금리 경로이고, 이번 `AI 신용물 순발행 → 기관 듀레이션 사용 → 국채 구조적 수요 → 기간프리미엄`은 자산공급·포트폴리오 경로다. 두 경로를 같은 선으로 합치지 않는다.
- 중복 또는 충돌 가능성: 기존 `long-bond-net-supply → term-premium → lt-rate`에서 `long-bond-net-supply`는 주로 국채 순공급·듀레이션이다. AI 회사채·ABS를 그 노드에 바로 더하지 말고 공통 투자자의 대체성과 실제 수급을 확인한 뒤 `structural-bond-demand`의 조건부 상류 후보로 연결한다.
- 통합 전 필수 검토: NVIDIA의 자기채무, 고객 프로젝트 채무, 보증·임차약정, 독립 금융플랫폼 자본과 유동화증권을 주체별로 분리한다. MOU·최대보증·확정약정·실행액·최종손실을 한 금액으로 합산하지 않는다.

## 증분 병합 결과 — cm-20260909-001

- 검토일: 2026-09-09
- 카드 상태: `merged` (일부 채택 또는 기존 경로 보강; 아래 미편입 항목은 후속 검토 유지)
- 채택·재사용 ID: `ai-vendor-credit-support`, `ai-project-financeability`, `dc-construction`, `ai-project-cashflow-mismatch`, `ai-project-default-risk`, `vendor-contingent-cash-outflow`, `long-bond-net-supply`, `structural-bond-demand`
- 판정: 미국 프로젝트 금융·현금 부족·유효 보증 지급 5개 노드 채택. 독립 고객 현금회수는 조건으로 보존. 유동화·펀드 환매·기관 듀레이션·국채 대체의 신규 경로와 최종손실 노드는 보류.
- 새 시계열·정책 기준 변경: 없음. 새 선은 미검증 조건부 가설.
- 상세 병합 기록: [배치 보고서](../merges/cm-20260909-001.md)
- 원문 경로 복구: 동일 파일명을 `raw/articles/새 폴더/`에서 확인해 경로를 갱신하고 원문 해시를 보존함.
