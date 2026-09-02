"""LG전자 대리점 30개사 초기 계정 시드 (멱등).
main.py 기동 시 자동 호출. 이미 있는 branch_code는 건드리지 않음.
비밀번호는 최초 배포용 — 배포 후 관리자 화면에서 대리점별로 재설정 권장.
"""
from datetime import datetime

DEALERS = [
    ('LGD01', '대리점 01', 'WMklWv67O'),
    ('LGD02', '대리점 02', 'WM7y2njyg'),
    ('LGD03', '대리점 03', 'WMtWEvq75'),
    ('LGD04', '대리점 04', 'WMr31dh8n'),
    ('LGD05', '대리점 05', 'WMCnwHIQC'),
    ('LGD06', '대리점 06', 'WM406adO0'),
    ('LGD07', '대리점 07', 'WM9DGOQGL'),
    ('LGD08', '대리점 08', 'WM9P7FI6T'),
    ('LGD09', '대리점 09', 'WMIXQ4de1'),
    ('LGD10', '대리점 10', 'WMuxmSlKW'),
    ('LGD11', '대리점 11', 'WM8WAHawx'),
    ('LGD12', '대리점 12', 'WMO2oiGIE'),
    ('LGD13', '대리점 13', 'WM2S52GmM'),
    ('LGD14', '대리점 14', 'WMWMKxLd0'),
    ('LGD15', '대리점 15', 'WM0GM3cGv'),
    ('LGD16', '대리점 16', 'WM9ZdRaIX'),
    ('LGD17', '대리점 17', 'WMsgEDvkb'),
    ('LGD18', '대리점 18', 'WMpeRhFF8'),
    ('LGD19', '대리점 19', 'WMDngy3hW'),
    ('LGD20', '대리점 20', 'WMhq68Jqe'),
    ('LGD21', '대리점 21', 'WMjWWcdNv'),
    ('LGD22', '대리점 22', 'WMg1AT2TM'),
    ('LGD23', '대리점 23', 'WMQskZbUQ'),
    ('LGD24', '대리점 24', 'WMMVpLtMR'),
    ('LGD25', '대리점 25', 'WM6VaOGgB'),
    ('LGD26', '대리점 26', 'WMnjvsuYa'),
    ('LGD27', '대리점 27', 'WMsDQoC4L'),
    ('LGD28', '대리점 28', 'WMe6OJcus'),
    ('LGD29', '대리점 29', 'WM9hJEpbK'),
    ('LGD30', '하주씨앤씨', 'WMvhFAETo'),
]


def seed_dealers():
    from database import SessionLocal
    import models
    from auth import hash_password
    db = SessionLocal()
    try:
        created = 0
        for code, name, pw in DEALERS:
            exists = db.query(models.User).filter(models.User.branch_code == code).first()
            if exists:
                continue
            db.add(models.User(
                branch_code=code, password_hash=hash_password(pw),
                branch_name=name, role="branch", region="",
                created_at=datetime.now(),
            ))
            created += 1
        db.commit()
        if created:
            print(f"[seed_dealers] {created}개 대리점 계정 생성")
    except Exception as e:
        db.rollback()
        print(f"[seed_dealers] 오류: {e}")
    finally:
        db.close()
