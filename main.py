import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse, JSONResponse
from pathlib import Path
from database import engine
import models
from routers import auth_router, branch_router, admin_router, user_router

models.Base.metadata.create_all(bind=engine)

# Migration: add new asset_items columns if they don't exist
from sqlalchemy import text, inspect as _sa_inspect
try:
    _cols = [c['name'] for c in _sa_inspect(engine).get_columns('asset_items')]
    _new = [
        ("memory_spec", "VARCHAR(100) DEFAULT ''"),
        ("storage_spec", "VARCHAR(100) DEFAULT ''"),
        ("data_wiped", "VARCHAR(20) DEFAULT ''"),
        ("has_adapter", "VARCHAR(10) DEFAULT ''"),
    ]
    with engine.connect() as _c:
        for _n, _d in _new:
            if _n not in _cols:
                _c.execute(text(f"ALTER TABLE asset_items ADD COLUMN {_n} {_d}"))
        _c.commit()
except Exception as _e:
    print(f"Migration warning: {_e}")

# Migration: create data_wipe_records and blancco_item_records tables if not exist
try:
    _inspector = _sa_inspect(engine)
    _existing_tables = _inspector.get_table_names()
    with engine.connect() as _c:
        if "data_wipe_records" not in _existing_tables:
            _c.execute(text("""
                CREATE TABLE data_wipe_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    application_id INTEGER NOT NULL UNIQUE REFERENCES applications(id),
                    wipe_date VARCHAR(20) DEFAULT '',
                    technician_company VARCHAR(100) DEFAULT '',
                    technician_name VARCHAR(50) DEFAULT '',
                    wipe_location VARCHAR(200) DEFAULT '',
                    blancco_method VARCHAR(100) DEFAULT '',
                    destruction_method VARCHAR(100) DEFAULT '',
                    destruction_certificate_no VARCHAR(100) DEFAULT '',
                    notes TEXT DEFAULT '',
                    created_at DATETIME,
                    updated_at DATETIME
                )
            """))
        else:
            _dwr_cols = [c['name'] for c in _sa_inspect(engine).get_columns('data_wipe_records')]
            if 'wipe_location' not in _dwr_cols:
                _c.execute(text("ALTER TABLE data_wipe_records ADD COLUMN wipe_location VARCHAR(200) DEFAULT ''"))
            if 'destruction_photo1' not in _dwr_cols:
                _c.execute(text("ALTER TABLE data_wipe_records ADD COLUMN destruction_photo1 VARCHAR(255) DEFAULT ''"))
            if 'destruction_photo2' not in _dwr_cols:
                _c.execute(text("ALTER TABLE data_wipe_records ADD COLUMN destruction_photo2 VARCHAR(255) DEFAULT ''"))
            if 'blancco_report_file' not in _dwr_cols:
                _c.execute(text("ALTER TABLE data_wipe_records ADD COLUMN blancco_report_file VARCHAR(255) DEFAULT ''"))
            if 'blancco_received' not in _dwr_cols:
                _c.execute(text("ALTER TABLE data_wipe_records ADD COLUMN blancco_received BOOLEAN DEFAULT FALSE"))
            if 'blancco_received_at' not in _dwr_cols:
                _c.execute(text("ALTER TABLE data_wipe_records ADD COLUMN blancco_received_at TIMESTAMP"))
            if 'blancco_certificate_file' not in _dwr_cols:
                _c.execute(text("ALTER TABLE data_wipe_records ADD COLUMN blancco_certificate_file VARCHAR(255) DEFAULT ''"))
        if "blancco_item_records" not in _existing_tables:
            _c.execute(text("""
                CREATE TABLE blancco_item_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    data_wipe_record_id INTEGER NOT NULL REFERENCES data_wipe_records(id),
                    asset_item_id INTEGER NOT NULL REFERENCES asset_items(id),
                    serial_number VARCHAR(100) DEFAULT '',
                    certificate_no VARCHAR(100) DEFAULT '',
                    wipe_result VARCHAR(20) DEFAULT '성공',
                    notes TEXT DEFAULT ''
                )
            """))
        _c.commit()
except Exception as _e:
    print(f"Migration warning (wipe tables): {_e}")

# Migration: add estimated_price columns (asset_price_refs is created by create_all)
try:
    _app_cols = [c['name'] for c in _sa_inspect(engine).get_columns('applications')]
    _item_cols = [c['name'] for c in _sa_inspect(engine).get_columns('asset_items')]
    with engine.connect() as _c:
        if 'estimated_price' not in _app_cols:
            _c.execute(text("ALTER TABLE applications ADD COLUMN estimated_price FLOAT DEFAULT 0.0"))
        if 'estimated_unit_price' not in _item_cols:
            _c.execute(text("ALTER TABLE asset_items ADD COLUMN estimated_unit_price FLOAT DEFAULT 0.0"))
        _c.commit()
except Exception as _e:
    print(f"Migration warning (estimated_price): {_e}")

app = FastAPI(title="IT 매각자산 플랫폼")
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY", "mgit-saemaul-2024-secret"))

STATIC_DIR = Path(__file__).resolve().parent / "static"
STATIC_DIR.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

templates = Jinja2Templates(directory="templates")

app.include_router(auth_router.router)
app.include_router(branch_router.router, prefix="/branch")
app.include_router(admin_router.router, prefix="/admin")
app.include_router(user_router.router, prefix="/admin")


@app.get("/health")
def health():
    return JSONResponse({"status": "ok"})


@app.get("/process")
def process_page(request: Request):
    return templates.TemplateResponse("process.html", {"request": request})


@app.get("/")
def root(request: Request):
    if not request.session.get("user_id"):
        return RedirectResponse("/login")
    role = request.session.get("role")
    if role == "branch":
        return RedirectResponse("/branch/dashboard")
    return RedirectResponse("/admin/dashboard")
