"""
ITAD 견적 시스템 계수 공식 기반 가견적 산출 모듈
공식: 단가 = 기준가 × C1(등급) × C2(연식)
계수/기준가는 SystemConfig DB에서 로드 (없으면 기본값 사용)
"""
from datetime import datetime

# ── 기본값 (DB 설정이 없을 때 폴백) ──────────────────────────────
DEFAULT_GRADE = {"상": 1.00, "중": 0.75, "하": 0.45}
DEFAULT_AGE   = [1.00, 0.85, 0.70, 0.55, 0.45, 0.35, 0.25]
DEFAULT_BASE  = {
    "PC":         120_000,
    "노트북":      200_000,
    "태블릿":      100_000,
    "모바일":       60_000,
    "프린터":       30_000,
    "복합기":       50_000,
    "기타전산기기":  30_000,
}

CATEGORIES = ["PC", "노트북", "태블릿", "모바일", "프린터", "복합기", "기타전산기기"]


def load_pricing_config(db) -> dict:
    """SystemConfig에서 가견적 계수/기준가 로드. 항목 없으면 기본값 반환."""
    grade = dict(DEFAULT_GRADE)
    age   = list(DEFAULT_AGE)
    base  = dict(DEFAULT_BASE)
    if db is None:
        return {"grade": grade, "age": age, "base": base}
    try:
        from models import SystemConfig
        configs = {
            c.key: c.value
            for c in db.query(SystemConfig).filter(
                SystemConfig.key.like("pricing_%")
            ).all()
        }
        for g in ("상", "중", "하"):
            k = f"pricing_grade_{g}"
            if k in configs:
                try:
                    grade[g] = float(configs[k])
                except ValueError:
                    pass
        for i in range(7):
            k = f"pricing_age_{i}"
            if k in configs:
                try:
                    age[i] = float(configs[k])
                except ValueError:
                    pass
        for cat in CATEGORIES:
            k = f"pricing_base_{cat}"
            if k in configs:
                try:
                    base[cat] = int(configs[k])
                except ValueError:
                    pass
    except Exception:
        pass
    return {"grade": grade, "age": age, "base": base}


def get_age_coefficient(manufacture_year, age_table=None) -> float:
    tbl = age_table if age_table is not None else DEFAULT_AGE
    if manufacture_year is None:
        return 0.40
    try:
        year_val = int(str(manufacture_year).split("-")[0].split("/")[0].split(".")[0].strip())
    except (ValueError, AttributeError):
        return 0.40
    if not (1990 <= year_val <= 2030):
        return 0.40
    age = max(0, datetime.now().year - year_val)
    return tbl[min(age, 6)]


def estimate_unit_price(
    category: str,
    model_name: str,
    manufacture_year,
    condition: str,
    db=None,
) -> int:
    """가견적 단가 산출 (원). 모델명 매칭 → 카테고리 폴백. DB에서 계수/기준가 로드."""
    cfg = load_pricing_config(db)
    base = cfg["base"].get(category, 30_000)

    if db and model_name:
        try:
            from models import AssetPriceRef
            refs = (
                db.query(AssetPriceRef)
                .filter(AssetPriceRef.category == category, AssetPriceRef.base_price > 0)
                .all()
            )
            model_lower = model_name.lower()
            best_base, best_score = None, 0
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

    c1 = cfg["grade"].get(condition, 0.75)
    c2 = get_age_coefficient(manufacture_year, cfg["age"])
    return round(base * c1 * c2)


def estimate_items(items: list, db=None) -> dict:
    """
    items: [{"category","model_name","manufacture_year","condition","quantity"}, ...]
    returns: {"items":[{"unit_price","quantity","line_total"},...], "total":int}
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
