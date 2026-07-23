from sqlalchemy import create_engine, Column, Integer, String, Text, Float, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import DeclarativeBase, sessionmaker, relationship
from datetime import datetime, timezone
from pathlib import Path
import enum

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "plagiarism.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


class ScanStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    text_content = Column(Text, nullable=False)
    word_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

    scans = relationship("Scan", back_populates="document")


class Scan(Base):
    __tablename__ = "scans"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    status = Column(String, default=ScanStatus.PENDING)
    similarity_score = Column(Float, default=0.0)
    web_matches = Column(Integer, default=0)
    academic_matches = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)

    document = relationship("Document", back_populates="scans")
    matches = relationship("ScanMatch", back_populates="scan")


class ScanMatch(Base):
    __tablename__ = "scan_matches"

    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(Integer, ForeignKey("scans.id"), nullable=False)
    chunk_text = Column(Text, nullable=False)
    source_text = Column(Text, nullable=False)
    source_url = Column(String, nullable=True)
    source_title = Column(String, nullable=True)
    similarity_score = Column(Float, nullable=False)
    match_type = Column(String, nullable=False)  # web, academic, internal
    start_position = Column(Integer, default=0)
    end_position = Column(Integer, default=0)

    scan = relationship("Scan", back_populates="matches")


class HumanizeLog(Base):
    __tablename__ = "humanize_logs"

    id = Column(Integer, primary_key=True, index=True)
    original_text = Column(Text, nullable=False)
    humanized_text = Column(Text, nullable=False)
    mode = Column(String, nullable=False)  # light, standard, aggressive
    meaning_similarity = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
