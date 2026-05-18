"""
ITAD 견적 시스템 계수 공식 기반 가견적 산출 모듈
공식: 단가 = (기준가 + 메모리가 + 저장장치가) × C1(등급) × C2(연식)
계수/기준가는 SystemConfig DB에서 로드 (없으면 기본값 사용)
"""
import re
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

# 메모리(RAM) 용량별 기준가 (GB 이상 → 가격), 내림차순
DEFAULT_MEMORY_TIERS = [
    (128, 120_000),
    ( 64,  65_000),
    ( 32,  35_000),
    ( 16,  18_000),
    (  8,  10_000),
    (  4,   5_000),
]

# SSD/NVMe 용량별 기준가 (GB 이상 → 가격), 내림차순
DEFAULT_SSD_TIERS = [
    (2048, 100_000),
    (1024,  55_000),
    ( 512,  30_000),
    ( 256,  18_000),
    ( 128,  10_000),
]

# HDD 용량별 기준가, 내림차순
DEFAULT_HDD_TIERS = [
    (2000, 12_000),
    (1000,  8_000),
    ( 500,  5_000),
]


def parse_memory_gb(spec: str) -> int | None:
    """메모리 사양 문자열에서 GB 용량 추출. 예: '16GB DDR4' → 16"""
    if not spec:
        return None
    m = re.search(r'(\d+(?:\.\d+)?)\s*TB', spec, re.IGNORECASE)
    if m:
        return int(float(m.group(1)) * 1024)
    m = re.search(r'(\d+(?:\.\d+)?)\s*GB', spec, re.IGNORECASE)
    if m:
        return int(float(m.group(1)))
    return None


def parse_storage(spec: str) -> tuple:
    """저장장치 사양에서 (용량GB, 타입) 추출. 타입: 'SSD' | 'HDD'"""
    if not spec:
        return None, 'SSD'
    spec_up = spec.upper()
    is_hdd = 'HDD' in spec_up
    m = re.search(r'(\d+(?:\.\d+)?)\s*TB', spec, re.IGNORECASE)
    if m:
        gb = int(float(m.group(1)) * 1024)
    else:
        m = re.search(r'(\d+(?:\.\d+)?)\s*GB', spec, re.IGNORECASE)
        if m:
            gb = int(float(m.group(1)))
        else:
            return None, 'SSD'
    return gb, ('HDD' if is_hdd else 'SSD')


def estimate_spec_price(memory_spec: str, storage_spec: str) -> int:
    """메모리 + 저장장치 사양 기준가 합산"""
    total = 0
    mem_gb = parse_memory_gb(memory_spec)
    if mem_gb is not None:
        for threshold, price in DEFAULT_MEMORY_TIERS:
            if mem_gb >= threshold:
                total += price
                break
    storage_gb, stype = parse_storage(storage_spec)
    if storage_gb is not None:
        tiers = DEFAULT_HDD_TIERS if stype == 'HDD' else DEFAULT_SSD_TIERS
        for threshold, price in tiers:
            if storage_gb >= threshold:
                total += price
                break
    return total


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
    memory_spec: str = "",
    storage_spec: str = "",
    db=None,
) -> int:
    """가견적 단가 산출 (원).
    공식: (기준가 + 메모리가 + 저장장치가) × C1(등급) × C2(연식)
    """
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

    spec_bonus = estimate_spec_price(memory_spec or "", storage_spec or "")
    c1 = cfg["grade"].get(condition, 0.75)
    c2 = get_age_coefficient(manufacture_year, cfg["age"])
    return round((base + spec_bonus) * c1 * c2)


def estimate_items(items: list, db=None) -> dict:
    """
    items: [{"category","model_name","manufacture_year","condition","memory_spec","storage_spec","quantity"}, ...]
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
            memory_spec=item.get("memory_spec", ""),
            storage_spec=item.get("storage_spec", ""),
            db=db,
        )
        qty = max(1, int(item.get("quantity") or 1))
        line_total = unit_price * qty
        total += line_total
        results.append({"unit_price": unit_price, "quantity": qty, "line_total": line_total})
    return {"items": results, "total": total}
