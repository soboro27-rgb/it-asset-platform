"""
최초 실행 시 기본 계정 데이터를 생성합니다.
사용법: python init_data.py
"""
from database import SessionLocal, engine
import models
from auth import hash_password


def migrate():
    """기존 테이블에 신규 컬럼 추가 (없을 경우에만)"""
    with engine.connect() as conn:
        from sqlalchemy import text
        for col, col_type in [
            ("welfare_fee_rate",   "FLOAT DEFAULT 0.0"),
            ("branch_total_amount","FLOAT DEFAULT 0.0"),
            ("operator_fee_rate",  "FLOAT DEFAULT 0.0"),
            ("welfare_view_amount","FLOAT DEFAULT 0.0"),
        ]:
            try:
                conn.execute(text(f"ALTER TABLE settlements ADD COLUMN {col} {col_type}"))
                conn.commit()
                print(f"  [migrate] settlements.{col} 컬럼 추가")
            except Exception:
                conn.rollback()

    # CORETAIL01 비밀번호 업데이트
    db = SessionLocal()
    user = db.query(models.User).filter(models.User.branch_code == "CORETAIL01").first()
    if user:
        user.password_hash = hash_password("11111111")
        db.commit()
        print("  [migrate] CORETAIL01 비밀번호 업데이트 완료")

    # 운영사 계정 보장 (없을 경우에만 생성)
    op = db.query(models.User).filter(models.User.branch_code == "OPERATOR01").first()
    if not op:
        from datetime import datetime
        db.add(models.User(
            branch_code="OPERATOR01",
            password_hash=hash_password("11111111"),
            branch_name="운영사",
            region="전국",
            role="operator",
            created_at=datetime.now(),
        ))
        db.commit()
        print("  [migrate] OPERATOR01 계정 생성 완료")
    db.close()


def init():
    models.Base.metadata.create_all(bind=engine)
    migrate()
    db = SessionLocal()

    if db.query(models.User).count() > 0:
        print("이미 초기화되어 있습니다.")
        db.close()
        return

    # 지점 계정 (지점코드 + 비밀번호)
    branches = [
        ("MG001", "Mg001!2024", "서울강남지점", "서울"),
        ("MG002", "Mg002!2024", "서울강서지점", "서울"),
        ("MG003", "Mg003!2024", "부산해운대지점", "부산"),
        ("MG004", "Mg004!2024", "대구수성지점", "대구"),
        ("MG005", "Mg005!2024", "인천남동지점", "인천"),
        ("MG006", "Mg006!2024", "광주북구지점", "광주"),
        ("MG007", "Mg007!2024", "대전유성지점", "대전"),
        ("MG008", "Mg008!2024", "수원영통지점", "경기"),
        ("MG009", "Mg009!2024", "성남분당지점", "경기"),
        ("MG010", "Mg010!2024", "울산남구지점", "울산"),
    ]

    for code, pw, name, region in branches:
        db.add(models.User(
            branch_code=code,
            password_hash=hash_password(pw),
            branch_name=name,
            region=region,
            role="branch",
        ))

    # 주관사 관리자
    db.add(models.User(
        branch_code="WELFARE01",
        password_hash=hash_password("Welfare!2024"),
        branch_name="주관사",
        region="전국",
        role="welfare",
    ))

    # 코어테일 관리자
    db.add(models.User(
        branch_code="CORETAIL01",
        password_hash=hash_password("11111111"),
        branch_name="코어테일",
        region="전국",
        role="coretail",
    ))

    db.commit()
    db.close()

    print("=" * 50)
    print("  데이터베이스 초기화 완료")
    print("=" * 50)
    print()
    print("[지점 담당자 계정]")
    for code, pw, name, _ in branches:
        print(f"  {code} / {pw}  ({name})")
    print()
    print("[복지회 관리자]")
    print("  WELFARE01 / Welfare!2024")
    print()
    print("[코어테일 관리자]")
    print("  CORETAIL01 / Coretail!2024")
    print("=" * 50)

    seed_price_refs()


PRICE_REF_DATA = [
    ("PC", "DB400S3A",     "Intel Core i5-4590(3.3GHz)",                                   "4GB DDR3 1600",    "Windows 7 Professional",        40_000),
    ("PC", "DB400S6B",     "Intel Core i5-6500(3.2GHz)",                                   "4GB DDR4 2133MHz", "Windows 7 Professional(32bit)", 60_000),
    ("PC", "DB400S6(7)B",  "Intel Core i5-6500(3.20G)",                                    "4GB DDR4 2133MHz", "Windows 7 Professional(32bit)", 60_000),
    ("PC", "DB400S7B",     "Intel Core i5 6600(3.2GHz)",                                   "4GB DDR4 2400MHz", "Windows 10 Professional(64bit)",60_000),
    ("PC", "DB400S9A",     "Intel Core i5-9400(2.9GHz ~ 4.1GHz)",                          "8GB DDR4 2666MHz", "Windows 10 Professional(64bit)",200_000),
    ("PC", "DB400SDA",     "Intel Core i5-11400",                                           "8GB DDR4 2666MHz", "Windows 10 Professional(64bit)",320_000),
    ("PC", "DB400SDA",     "Intel Core i5-12400 Processor(2.6GHz, 12MB)",                  "8GB DDR4",         "Windows 10 Pro 64bit",          360_000),
    ("PC", "DB400SEA-Z0A/R","Intel Core i7-12700 Processor(2.1GHz up to 4.9GHz 25MB L3)", "16GB DDR4",        "Windows 10 Pro 64bit",          520_000),
]


def seed_price_refs():
    """가견적 기준가 초기 데이터 삽입 (없을 때만)"""
    db = SessionLocal()
    if db.query(models.AssetPriceRef).count() == 0:
        for category, code, display, mem, os_s, price in PRICE_REF_DATA:
            db.add(models.AssetPriceRef(
                category=category,
                model_code=code,
                model_display=display,
                mem_spec=mem,
                os_spec=os_s,
                base_price=price,
            ))
        db.commit()
        print(f"  [seed] 가견적 기준가 {len(PRICE_REF_DATA)}건 등록 완료")
    db.close()


if __name__ == "__main__":
    init()
    seed_price_refs()
