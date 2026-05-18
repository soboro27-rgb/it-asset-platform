from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    branch_code = Column(String(20), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    branch_name = Column(String(100), nullable=False)
    region = Column(String(50), default="")
    role = Column(String(20), default="branch")  # branch / welfare / coretail
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)

    applications = relationship("Application", back_populates="user")


class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String(30), default="draft")
    # draft → submitted → approved → scheduled → schedule_confirmed
    # → collected → priced → branch_confirmed → completed
    title = Column(String(200), default="")
    notes = Column(Text, default="")
    submitted_at = Column(DateTime, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now)

    user = relationship("User", back_populates="applications")
    assets = relationship("AssetItem", back_populates="application", cascade="all, delete-orphan")
    schedule = relationship("VisitSchedule", back_populates="application", uselist=False, cascade="all, delete-orphan")
    settlement = relationship("Settlement", back_populates="application", uselist=False, cascade="all, delete-orphan")
    data_wipe_record = relationship("DataWipeRecord", back_populates="application", uselist=False, cascade="all, delete-orphan")


class AssetItem(Base):
    __tablename__ = "asset_items"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    category = Column(String(20), nullable=False)  # PC/노트북/태블릿/모바일/프린터/복합기/기타전산기기
    model_name = Column(String(100), default="")
    manufacturer = Column(String(50), default="")
    manufacture_year = Column(Integer, nullable=True)
    quantity = Column(Integer, default=1)
    condition = Column(String(10), default="중")  # 상/중/하
    description = Column(Text, default="")
    unit_price = Column(Float, default=0.0)  # 수거 후 코어테일이 입력
    memory_spec = Column(String(100), default="")    # 메모리 사양 (PC/노트북)
    storage_spec = Column(String(100), default="")   # 저장장치 사양 (PC/노트북)
    data_wiped = Column(String(20), default="")      # 데이터 삭제 여부: 파쇄/블랑코/""
    has_adapter = Column(String(10), default="")     # 아답터 유무 (노트북): 있음/없음/""

    application = relationship("Application", back_populates="assets")


class VisitSchedule(Base):
    __tablename__ = "visit_schedules"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), unique=True, nullable=False)
    visit_date = Column(String(20), default="")
    visit_time = Column(String(10), default="")
    collector_name = Column(String(50), default="")
    collector_phone = Column(String(20), default="")
    notes = Column(Text, default="")
    branch_confirmed = Column(Boolean, default=False)
    confirmed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    application = relationship("Application", back_populates="schedule")


class Settlement(Base):
    __tablename__ = "settlements"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), unique=True, nullable=False)
    total_amount = Column(Float, default=0.0)          # 코어테일 매입 합계
    welfare_fee_rate = Column(Float, default=0.0)      # 산정 당시 수수료율 스냅샷 (%)
    branch_total_amount = Column(Float, default=0.0)   # 지점 수령 예정액 (수수료 차감 후)
    pricing_notes = Column(Text, default="")
    branch_confirmed = Column(Boolean, default=False)
    branch_confirmed_at = Column(DateTime, nullable=True)
    welfare_confirmed = Column(Boolean, default=False)
    welfare_confirmed_at = Column(DateTime, nullable=True)
    payment_date = Column(String(20), default="")
    payment_confirmed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)

    application = relationship("Application", back_populates="settlement")


class DataWipeRecord(Base):
    __tablename__ = "data_wipe_records"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), unique=True, nullable=False)
    wipe_date = Column(String(20), default="")
    technician_company = Column(String(100), default="")
    technician_name = Column(String(50), default="")
    wipe_location = Column(String(200), default="")
    blancco_method = Column(String(100), default="")
    destruction_method = Column(String(100), default="")
    destruction_certificate_no = Column(String(100), default="")
    blancco_report_file = Column(String(255), default="")
    blancco_received = Column(Boolean, default=False)
    blancco_received_at = Column(DateTime, nullable=True)
    blancco_certificate_file = Column(String(255), default="")
    destruction_photo1 = Column(String(255), default="")
    destruction_photo2 = Column(String(255), default="")
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now)

    application = relationship("Application", back_populates="data_wipe_record")
    item_records = relationship("BlanccoItemRecord", back_populates="data_wipe_record", cascade="all, delete-orphan")


class BlanccoItemRecord(Base):
    __tablename__ = "blancco_item_records"

    id = Column(Integer, primary_key=True, index=True)
    data_wipe_record_id = Column(Integer, ForeignKey("data_wipe_records.id"), nullable=False)
    asset_item_id = Column(Integer, ForeignKey("asset_items.id"), nullable=False)
    serial_number = Column(String(100), default="")
    certificate_no = Column(String(100), default="")
    wipe_result = Column(String(20), default="성공")
    notes = Column(Text, default="")

    data_wipe_record = relationship("DataWipeRecord", back_populates="item_records")
    asset_item = relationship("AssetItem")


class SystemConfig(Base):
    __tablename__ = "system_configs"

    id = Column(Integer, primary_key=True)
    key = Column(String(50), unique=True, nullable=False)
    value = Column(String(200), default="")
    updated_at = Column(DateTime, default=datetime.now)
