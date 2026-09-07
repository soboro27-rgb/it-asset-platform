# WORKLOG — it-asset-platform

## 2026-09-02 — LG전자 대리점 IT자산 매입/구매지원금 시나리오 (Phase 1)

**요청 (팔렌시아):**
LG전자 대리점 약 30개사가 신품을 고객사에 납품할 때, 고객사가 보유한 구형 IT자산을
매입하고, 그 금액을 ①현금 정산 또는 ②신품 구매지원금 차감으로 처리하는 프로세스.
기존 IT자산 매각 플랫폼(새마을금고용 mgit 사촌)을 재활용해 구축.
디자인은 lge.co.kr/business 컨셉(LG 화이트/레드, 각진, Pretendard)에 맞춤.

**확정된 조건:**
1. 매입·파기 주체 = 월드와이드메모리 단일 (기존 coretail/operator 관리자)
2. 정산 = 월드메모리가 30개 대리점에 월별 일괄 지급 (4자 정산 체인 폐기)
3. 세금계산서 발행 기능 불필요 — 금액 확정 프로세스만 유지
4. 플랫폼 수수료 = 필드만 두고 기본 0, 차후 산정
5. 대리점이 로그인해 고객사 대행 입력. 고객사 직접 로그인 없음
6. 로그인 = 대리점 드롭다운(30개) + 비밀번호. 관리자는 토글 링크로 아이디 입력

### 완료 (Phase 1)

- **models.py**
  - `Application` + 고객사 필드: `customer_name/business_no/address/contact_name/contact_phone`
  - `Settlement` + `platform_fee_rate`, `payout_mode`(cash|credit),
    `new_purchase_desc/amount`, `credit_applied`, `remaining_cash`, `dealer_paid/at`
  - 구 4자 정산 컬럼(operator_fee/welfare_*/buyer_paid/operator_paid)은 호환용으로 남김(미사용)
- **main.py** — 위 신규 컬럼 마이그레이션 블록 추가
- **admin_router.py**
  - `_get_platform_fee_rate()` 추가
  - `set_pricing`: 2단 수수료 캐스케이드 → `platform_fee_rate` 1단. payout_mode/credit 처리
  - `buyer_payment`/`operator_payment`/`complete_payment` 삭제 →
    `dealer_payment`(건별) + `settlement_pay_batch`(대리점별 일괄) 신설
  - `settlement_page`: `_group_by_dealer()` — 지급대기/지급완료를 대리점별 그룹으로
  - settings에 `platform_fee_rate` 추가
- **auth_router.py** — login_page/login에서 활성 대리점 목록 전달
- **login.html** — 대리점 `<select>` + 비밀번호, "관리자 로그인" 토글(아이디 input),
  LG 컨셉 리디자인(화이트/레드 #A50034/각진/Pretendard)
- **base.html** — 전체 테마를 LG 컨셉으로 (--mg = #A50034). 헤더 화이트+레드 좌측바,
  사이드바 용어 대리점/월드와이드메모리로
- **branch/new_application.html, edit_application.html** — 고객사 정보 카드 추가
- **branch_router.py** — 고객사 필드 저장 (create/update)
- **admin/application_detail.html** — 단가확정 폼에 정산방식(현금/지원금)+지원금 필드,
  정산정보/액션패널을 대리점 단일지급 흐름으로 교체
- **admin/settlement.html** — 대리점별 지급대기(체크박스 일괄지급)/지급완료 뷰로 재작성

### 검증

로컬 Python 3.14 + jinja2 3.1.2 는 실행 불가(기존 이슈) → `.venv-test`(starlette 0.27 고정)로 스모크.
전체 라이프사이클 curl 테스트 통과: 대리점 로그인 → 고객사+자산 접수 → 승인/일정/수거 →
단가확정(credit, 지원금 400k) → 대리점 확인 → 일괄지급. 
결과: total 540,000 / branch_total 540,000(수수료0) / credit 400,000 / remaining_cash 140,000 / completed.
UTF-8 폼 입력 정상(Python 클라이언트 확인. Git Bash curl 한글은 깨져서 테스트 데이터만 mojibake).

### 배포 (2026-09-02)

- `git push origin master:main` → Render 자동 배포 완료. https://it-asset-platform.onrender.com
- 대리점 30개 시드: LGD01~29("대리점 01"~"대리점 29") + LGD30(하주씨앤씨).
  `seed_dealers.py` 멱등, main.py 기동 시 호출. 계정표 = `CREDENTIALS.md`(gitignore).
- 라이브 검증: 로그인 화면 대리점 30개 드롭다운, LGD01/LGD30/CORETAIL01 로그인 302 OK.

## 2026-09-02 — 워크플로우 순서 수정 (가견적 단계 추가)

기존: 대리점 접수 → 관리자 승인(가부만) → 일정 → 수거 → 금액입력 → 대리점 승인
수정: **대리점 견적문의 → 관리자 가견적 입력 → 대리점 가견적 승인 → 일정 → 수거 →
      관리자 최종금액 입력 → 대리점 확인**

- `status`에 `quoted`(가견적 산정완료) 추가. 순서:
  draft→submitted→quoted→approved→scheduled→schedule_confirmed→collected→priced→branch_confirmed→completed
- `approved` 의미 변경: 관리자 승인 → **대리점의 가견적 승인**
- admin_router: `approve` 라우트 삭제 → `set_estimate`(submitted→quoted, 자산별
  `estimated_unit_price` 입력) 신설
- branch_router: `approve_quote`(quoted→approved) 신설
- 최종금액 폼(collected→priced)은 가견적을 참고단가로 표시, unit_price 미입력 시 가견적으로 프리필
- config.py STATUS_LABEL/COLOR, 양 detail 템플릿 step-bar(9단계), base 사이드바·admin
  대시보드 상태 필터 갱신
- `IN_PROGRESS_STATUSES` 에 quoted 추가
- 라이브 배포됨

## 2026-09-02 — 용어 정리 (복지회/주관사/운영사/매입사/지점 제거)

- 전 템플릿·라우터에서 복지회·주관사·운영사·매입사 → "관리자"(월드와이드메모리),
  지점 → 대리점, "IT자산 매각" → "매입" 로 치환
- `admin/settings.html` 전면 재작성: 운영사·복지회 2단 수수료 → 플랫폼 수수료 1단
- `branch/application_detail.html`: 세금계산서 발행 카드 삭제, branch_confirmed 안내를
  대리점 지급 대기로, 지원금 차감 표시 추가
- `branch_router.py`: `/report/business-cert` 라우트(새마을금고복지회 하드코딩) 삭제
- `user_router.py` ROLE_LABEL / 엑셀 양식 문구 갱신
- `process.html`·`pricing_standard.html` 문구 갱신 + 푸터
- 배포: origin/main 푸시

### 남은 작업 (Phase 2)

- `process.html`·`pricing_standard.html` 은 base.html 미상속 독립 스타일(다크+그린) →
  LG 레드 테마로 재도색 필요
- 엑셀 export(settlement)도 대리점별 그룹 반영
- `init_data.py` — migrate()가 OPERATOR01 만들면 init() 시드가 스킵되는 버그.
  라이브(Render)는 CORETAIL01 존재. 로컬 재현 시 수동 시드 필요.
- `welfare` role 자체는 스키마/권한 체크에 남아있음(미사용). 완전 제거는 마이그레이션 필요.

## 2026-09-05 — /process 페이지에 "회계 효과" 섹션 추가

**요청 (팔렌시아):** 기존 "회계감사 규정 완벽 대응" 섹션에, 내용연수 종료 자산
(장부가 1,000원) 재판매 시 잡이익 계상 문제와 다수 업체 참여로 인한 데이터
유출·담합 리스크를 짚고, 이를 월드와이드메모리 단일 매입 구조 + 신품 구매지원금
전환으로 해결한다는 논리를 보강해달라는 요청.

- `templates/process.html`에 `#financial` 섹션 신설 (감사 섹션과 CTA 사이).
  기존 `.compare-grid`/`.compare-card` 컴포넌트 재사용 (bad=기존 리스크,
  good=플랫폼 구조), 하단에 `.audit` 위 70%박스와 같은 스타일의 요약 콜아웃 추가.
- 상단 nav에 `#financial` → "회계 효과" 링크 추가.
- 새 CSS 클래스 없이 기존 디자인시스템만으로 구현 (fade-in 애니메이션도
  `.compare-card` 셀렉터에 이미 포함되어 자동 적용됨).
- 배포 완료 (`origin/main` `cc14f3c`). 배포 전 클론이 9/2 리브랜딩 이후로
  동기화가 안 돼있던 걸 발견 — `git reset --hard origin/main` 후 재작업.

**추가 요청**: "잡이익 리스크를... 맨 위로 올려줘" → `#financial` 섹션을
히어로 바로 다음(문제/해결 섹션보다 앞)으로 이동, nav 순서도 동일하게 조정.
배포 완료 (`origin/main` `261c60a`).

## 2026-09-07 — 자산 카테고리 재분류 (가견적 대량 등록)

**요청 (팔렌시아):** 가견적 대량 등록 시 카테고리를 스크린샷대로 분류해 반영.
새 목록: BOARD / CPU / HDD / PC / RAM / SSD / 그래픽카드 / 기타전산기기 / 노트북 /
맥북 / 모니터 / 서버 / 태블릿 (기존 모바일·프린터·복합기 제거, 서버부품·맥북·모니터·서버 추가).

- `config.py` — `CATEGORIES`를 단일 출처로 새 13종 목록으로 교체.
  `SPEC_CATEGORIES = [PC, 노트북, 맥북, 서버]` 신설 (메모리/저장장치 상세행 표시 대상).
  둘 다 Jinja 전역으로 등록.
- `routers/branch_router.py` — `VALID_CATEGORIES = CATEGORIES` 로 통일.
  자산 엑셀 양식 예시행(프린터→서버·모니터), 작성요령 문구 갱신.
- `routers/admin_router.py` — 가견적 기준가 bulk `VALID_CATS = CATEGORIES`.
  기준가 엑셀 양식 예시/문구 갱신. 인수인계서(`_ASSET_TO_TRANSFER`)·
  폐기목록(`_DISPOSAL_CAT_MAP`) 매핑에 신규 카테고리 반영 (서버→워크스테이션/컴퓨터본체,
  맥북→노트북, 모니터→모니터, 부품류→기타).
- 템플릿 — `price_refs.html` 카테고리 select, `new/edit_application.html` 안내 뱃지를
  `{% for c in CATEGORIES %}` 루프로 전환. `onCategoryChange`는 `SPEC_CATEGORIES.includes()` 로.
  `application_detail.html`(admin/branch) 상세 사양 표시 조건도 `SPEC_CATEGORIES` 기준.
- `models.py` — `AssetItem.category` 주석 갱신.
- DB 스키마 변경 없음. 기존 데이터의 옛 카테고리 값(모바일 등)은 그대로 표시됨.
