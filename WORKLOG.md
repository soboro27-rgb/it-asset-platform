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

### 남은 작업 (Phase 2)

- 템플릿 용어 정리: "지점"→"대리점", "매각"→"매입", 복지회/포스라/주관사/운영사/매입사
  잔여 문구(base 일부, admin/users·user_form·access_logs, branch/application_detail 등 ~10파일)
- `branch/application_detail.html` — 고객사 정보 표시, 구 정산 라벨 정리
- `process.html`, `pricing_standard.html` 문구 LG 시나리오로
- 엑셀 export(settlement)도 대리점별 그룹 반영
- `init_data.py` — migrate()가 OPERATOR01 만들면 init() 시드가 스킵되는 버그
