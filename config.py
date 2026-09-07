from fastapi.templating import Jinja2Templates
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

STATUS_LABEL = {
    "draft": "작성중",
    "submitted": "견적문의 접수",
    "quoted": "가견적 산정완료",
    "approved": "가견적 승인",
    "scheduled": "일정확정대기",
    "schedule_confirmed": "수거예정",
    "collected": "수거완료",
    "priced": "최종금액 산정완료",
    "branch_confirmed": "대리점 확인완료",
    "completed": "거래완료",
}

STATUS_COLOR = {
    "draft": "secondary",
    "submitted": "warning",
    "quoted": "info",
    "approved": "info",
    "scheduled": "primary",
    "schedule_confirmed": "primary",
    "collected": "info",
    "priced": "warning",
    "branch_confirmed": "success",
    "completed": "success",
}

# 가견적 대량 등록 등 전 화면 공통 자산 카테고리 (단일 출처)
CATEGORIES = [
    "BOARD", "CPU", "HDD", "PC", "RAM", "SSD",
    "그래픽카드", "기타전산기기", "노트북", "맥북", "모니터", "서버", "태블릿",
]

# 메모리/저장장치 등 상세 사양 입력이 필요한 카테고리
SPEC_CATEGORIES = ["PC", "노트북", "맥북", "서버"]

templates.env.globals["STATUS_LABEL"] = STATUS_LABEL
templates.env.globals["STATUS_COLOR"] = STATUS_COLOR
templates.env.globals["CATEGORIES"] = CATEGORIES
templates.env.globals["SPEC_CATEGORIES"] = SPEC_CATEGORIES
