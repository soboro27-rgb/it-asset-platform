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
            ("welfare_fee_rate", "FLOAT DEFAULT 0.0"),
            ("branch_total_amount", "FLOAT DEFAULT 0.0"),
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


def seed_price_refs():
    """ITAD 시스템 기준 주요 모델 가견적 기준가 초기 데이터 (없을 때만 삽입)"""
    db = SessionLocal()
    if db.query(models.AssetPriceRef).count() > 0:
        db.close()
        return

    # 기준가 = 신품 소매가 × 20% (B2B 중고 매입 기준, 연식 계수는 별도 적용)
    price_refs = [
        # ── 노트북 ────────────────────────────────────────────
        ("노트북", "LG 그램 14/16", "lg,그램,gram,14z90,16z90,15z95,17z90", 300_000),
        ("노트북", "삼성 갤럭시북", "samsung,삼성,galaxy book,갤럭시북,nt950,nt960,nt760,nt550", 280_000),
        ("노트북", "HP EliteBook 840/850", "hp,elitebook,840,850", 320_000),
        ("노트북", "HP ProBook", "hp,probook,450,430", 220_000),
        ("노트북", "Dell Latitude 5000", "dell,latitude,5430,5440,5530,5540,5340", 280_000),
        ("노트북", "Dell Latitude 7000", "dell,latitude,7430,7440,7530,7540", 380_000),
        ("노트북", "Lenovo ThinkPad X1 Carbon", "lenovo,thinkpad,x1 carbon,x1c", 420_000),
        ("노트북", "Lenovo ThinkPad T/E 시리즈", "lenovo,thinkpad,t14,t15,e15,e14", 250_000),
        ("노트북", "Apple MacBook Air M1/M2", "apple,macbook,air,m1,m2", 500_000),
        ("노트북", "Apple MacBook Pro", "apple,macbook,pro", 650_000),
        ("노트북", "Microsoft Surface Pro", "microsoft,surface,pro", 280_000),
        ("노트북", "HP ZBook", "hp,zbook,firefly", 480_000),
        # ── PC (데스크탑) ─────────────────────────────────────
        ("PC", "HP ProDesk 400", "hp,prodesk,400", 170_000),
        ("PC", "HP ProDesk 600/EliteDesk 800", "hp,prodesk,600,elitedesk,800", 240_000),
        ("PC", "Dell OptiPlex 3000", "dell,optiplex,3090,3080,3000,3010", 160_000),
        ("PC", "Dell OptiPlex 5000/7000", "dell,optiplex,5090,5080,7090,7080,7010", 240_000),
        ("PC", "Lenovo ThinkCentre M70", "lenovo,thinkcentre,m70,m720", 160_000),
        ("PC", "Lenovo ThinkCentre M80/M90", "lenovo,thinkcentre,m80,m90,m720t", 240_000),
        ("PC", "삼성 DM 시리즈", "samsung,삼성,dm500,dm400,db400", 160_000),
        # ── 프린터 ───────────────────────────────────────────
        ("프린터", "HP LaserJet Pro", "hp,laserjet,pro,m404,m403", 40_000),
        ("프린터", "HP LaserJet Enterprise", "hp,laserjet,enterprise,m507,m506", 70_000),
        ("프린터", "Brother 레이저", "brother,hl-l,dcp-l", 35_000),
        # ── 복합기 ───────────────────────────────────────────
        ("복합기", "HP LaserJet MFP", "hp,laserjet,mfp,m428,m429,m430", 70_000),
        ("복합기", "신도리코/캐논/제록스", "신도리코,canon,xerox,ricoh", 80_000),
    ]

    for cat, display, keywords, price in price_refs:
        db.add(models.AssetPriceRef(
            category=cat,
            model_display=display,
            keywords=keywords,
            base_price=price,
        ))

    db.commit()
    db.close()
    print("  [seed] AssetPriceRef 기준가 데이터 초기화 완료")


if __name__ == "__main__":
    init()
    seed_price_refs()
