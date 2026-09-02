"""LG전자 대리점 30개사 초기 계정 시드.
main.py 기동 시 자동 호출.

- 없는 계정은 생성.
- SEED_VERSION 이 올라간 배포에서는 DEALERS 목록의 비밀번호/대리점명으로 1회 동기화
  (관리자가 개별 재설정한 비밀번호가 있으면 이때 함께 초기화되니, 배포용 비번을
  바꿀 때만 SEED_VERSION 을 올릴 것).
- 같은 SEED_VERSION 재배포 시에는 생성만 하고 기존 계정은 건드리지 않음.
"""
from datetime import datetime

SEED_VERSION = 2

DEALERS = [
    ('LGD01', '대리점 01', 'wmbwxw5a'),
    ('LGD02', '대리점 02', 'wmqhfyy4'),
    ('LGD03', '대리점 03', 'wm7mrqrt'),
    ('LGD04', '대리점 04', 'wmnptu6n'),
    ('LGD05', '대리점 05', 'wmedu58r'),
    ('LGD06', '대리점 06', 'wmc59fc4'),
    ('LGD07', '대리점 07', 'wm3smk7c'),
    ('LGD08', '대리점 08', 'wmwsmbh9'),
    ('LGD09', '대리점 09', 'wmcd6q5p'),
    ('LGD10', '대리점 10', 'wmzregj8'),
    ('LGD11', '대리점 11', 'wmvebnxp'),
    ('LGD12', '대리점 12', 'wm24f464'),
    ('LGD13', '대리점 13', 'wmz43g4a'),
    ('LGD14', '대리점 14', 'wmn9cfpv'),
    ('LGD15', '대리점 15', 'wm2smvas'),
    ('LGD16', '대리점 16', 'wm3ygvr7'),
    ('LGD17', '대리점 17', 'wmw5x596'),
    ('LGD18', '대리점 18', 'wmtutsey'),
    ('LGD19', '대리점 19', 'wmxrdatx'),
    ('LGD20', '대리점 20', 'wm8j4a7c'),
    ('LGD21', '대리점 21', 'wm95besx'),
    ('LGD22', '대리점 22', 'wmq7t78f'),
    ('LGD23', '대리점 23', 'wmt77xn7'),
    ('LGD24', '대리점 24', 'wmdugjp7'),
    ('LGD25', '대리점 25', 'wmnh4fhb'),
    ('LGD26', '대리점 26', 'wmsfv6cd'),
    ('LGD27', '대리점 27', 'wmezugnw'),
    ('LGD28', '대리점 28', 'wmad9hyv'),
    ('LGD29', '대리점 29', 'wm9e9ygy'),
    ('LGD30', '하주씨앤씨', 'wm6xjwm5'),
]


def seed_dealers():
    from database import SessionLocal
    import models
    from auth import hash_password
    db = SessionLocal()
    try:
        cfg = db.query(models.SystemConfig).filter(
            models.SystemConfig.key == "dealer_seed_version"
        ).first()
        try:
            applied_version = int(cfg.value) if cfg else 0
        except (ValueError, TypeError):
            applied_version = 0
        sync = applied_version < SEED_VERSION

        created = synced = 0
        for code, name, pw in DEALERS:
            user = db.query(models.User).filter(models.User.branch_code == code).first()
            if not user:
                db.add(models.User(
                    branch_code=code, password_hash=hash_password(pw),
                    branch_name=name, role="branch", region="",
                    created_at=datetime.now(),
                ))
                created += 1
            elif sync:
                user.password_hash = hash_password(pw)
                user.branch_name = name
                user.role = "branch"
                user.is_active = True
                synced += 1

        if sync:
            if cfg:
                cfg.value = str(SEED_VERSION)
                cfg.updated_at = datetime.now()
            else:
                db.add(models.SystemConfig(key="dealer_seed_version", value=str(SEED_VERSION)))

        db.commit()
        if created or synced:
            print(f"[seed_dealers] 생성 {created} / 동기화 {synced} (v{SEED_VERSION})")
    except Exception as e:
        db.rollback()
        print(f"[seed_dealers] 오류: {e}")
    finally:
        db.close()
