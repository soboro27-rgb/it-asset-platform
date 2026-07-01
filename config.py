from fastapi.templating import Jinja2Templates
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

STATUS_LABEL = {
    "draft": "작성중",
    "submitted": "접수대기",
    "approved": "승인완료",
    "scheduled": "일정확정대기",
    "schedule_confirmed": "수거예정",
    "collected": "수거완료",
    "priced": "금액산정완료",
    "branch_confirmed": "지점승인완료",
    "completed": "거래완료",
}

STATUS_COLOR = {
    "draft": "secondary",
    "submitted": "warning",
    "approved": "info",
    "scheduled": "primary",
    "schedule_confirmed": "primary",
    "collected": "info",
    "priced": "warning",
    "branch_confirmed": "success",
    "completed": "success",
}

CATEGORIES = ["PC", "노트북", "태블릿", "모바일", "프린터", "복합기", "기타전산기기"]

templates.env.globals["STATUS_LABEL"] = STATUS_LABEL
templates.env.globals["STATUS_COLOR"] = STATUS_COLOR
templates.env.globals["CATEGORIES"] = CATEGORIES
