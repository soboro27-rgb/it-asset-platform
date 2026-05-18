"""
ITAD 견적 시스템 계수 공식 기반 가견적 산출 모듈
공식: 단가 = 기준가 × C1(등급) × C2(연식)
"""
from datetime import datetime

# C1: 등급 계수 (ITAD 시스템과 동일)
GRADE_COEFFICIENTS = {
    "상": 1.00,   # Grade A
    "중": 0.75,   # Grade B
    "하": 0.45,   # Grade C
}

# C2: 연식 계수 (ITAD 시스템과 동일, 0~6+년)
AGE_TABLE = [1.00, 0.85, 0.70, 0.55, 0.45, 0.35, 0.25]

# 카테고리별 기준 단가 (원, 이력 없을 때 폴백 — B2B 중고 매입 기준)
CATEGORY_BASE_PRICES = {
    "PC":         120_000,
    "노트북":      200_000,
    "태블릿":      100_000,
    "모바일":       60_000,
    "프린터":       30_000,
    "복합기":       50_000,
    "기타전산기기":  30_000,
}


def get_age_coefficient(manufacture_year) -> float:
    if manufacture_year is None:
        return 0.40
    # 날짜 문자열(YYYY-MM-DD 등)에서 연도 추출
    try:
        year_val = int(str(manufacture_year).split("-")[0].split("/")[0].split(".")[0].strip())
    except (ValueError, AttributeError):
        return 0.40
    if not (1990 <= year_val <= 2030):
        return 0.40
    age = max(0, datetime.now().year - year_val)
    return AGE_TABLE[min(age, 6)]


def estimate_unit_price(
    category: str,
    model_name: str,
    manufacture_year,
    condition: str,
    db=None,
) -> int:
    """가견적 단가 산출 (원). 모델명 매칭 → 카테고리 폴백 순으로 기준가 결정."""
    base = CATEGORY_BASE_PRICES.get(category, 30_000)

    if db and model_name:
        try:
            from models import AssetPriceRef
            refs = (
                db.query(AssetPriceRef)
                .filter(AssetPriceRef.category == category, AssetPriceRef.base_price > 0)
                .all()
            )
            model_lower = model_name.lower()
            best_base = None
            best_score = 0
            for ref in refs:
                keywords = [k.strip().lower() for k in ref.keywords.split(",") if k.strip()]
                if not keywords:
                    continue
                score = sum(1 for kw in keywords if kw in model_lower)
                if score > best_score:
                    best_score = score
                    best_base = ref.base_price
            if best_base is not None and best_score > 0:
                base = best_base
        except Exception:
            pass

    c1 = GRADE_COEFFICIENTS.get(condition, 0.75)
    c2 = get_age_coefficient(manufacture_year)
    return round(base * c1 * c2)


def estimate_items(items: list, db=None) -> dict:
    """
    items: [{"category", "model_name", "manufacture_year", "condition", "quantity"}, ...]
    returns: {"items": [{"unit_price", "quantity", "line_total"}, ...], "total": int}
    """
    results = []
    total = 0
    for item in items:
        unit_price = estimate_unit_price(
            category=item.get("category", ""),
            model_name=item.get("model_name", ""),
            manufacture_year=item.get("manufacture_year"),
            condition=item.get("condition", "중"),
            db=db,
        )
        qty = max(1, int(item.get("quantity") or 1))
        line_total = unit_price * qty
        total += line_total
        results.append({"unit_price": unit_price, "quantity": qty, "line_total": line_total})
    return {"items": results, "total": total}
