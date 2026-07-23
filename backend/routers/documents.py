from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from database.models import get_db, Document, Scan, ScanMatch
from services.ingestion import DocumentIngestion
from pathlib import Path
import os

router = APIRouter()
UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

EXTENSION_MAP = {
    ".pdf": ("application/pdf", "pdf"),
    ".docx": ("application/vnd.openxmlformats-officedocument.wordprocessingml.document", "docx"),
    ".doc": ("application/msword", "docx"),
    ".txt": ("text/plain", "txt"),
}


@router.post("/upload")
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    allowed_types = {
        "application/pdf": "pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
        "application/msword": "docx",
        "text/plain": "txt",
    }

    file_type = allowed_types.get(file.content_type)

    if not file_type and file.filename:
        ext = Path(file.filename).suffix.lower()
        if ext in EXTENSION_MAP:
            _, file_type = EXTENSION_MAP[ext]

    if not file_type:
        raise HTTPException(status_code=400, detail="Unsupported file type. Upload PDF, DOCX, or TXT.")

    file_path = UPLOAD_DIR / file.filename

    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    ingestion = DocumentIngestion()
    text_content = ingestion.extract_text(file_path, file_type)
    word_count = len(text_content.split())

    doc = Document(
        filename=file.filename,
        file_path=str(file_path),
        file_type=file_type,
        text_content=text_content,
        word_count=word_count,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    return {
        "id": doc.id,
        "filename": doc.filename,
        "word_count": doc.word_count,
        "created_at": doc.created_at.isoformat(),
    }


@router.get("/")
async def list_documents(db: Session = Depends(get_db)):
    docs = db.query(Document).all()
    return [
        {
            "id": d.id,
            "filename": d.filename,
            "file_type": d.file_type,
            "word_count": d.word_count,
            "created_at": d.created_at.isoformat(),
        }
        for d in docs
    ]


@router.get("/{doc_id}")
async def get_document(doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return {
        "id": doc.id,
        "filename": doc.filename,
        "file_type": doc.file_type,
        "text_content": doc.text_content,
        "word_count": doc.word_count,
        "created_at": doc.created_at.isoformat(),
    }


@router.delete("/{doc_id}")
async def delete_document(doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    scan_ids = [s.id for s in db.query(Scan).filter(Scan.document_id == doc_id).all()]
    if scan_ids:
        db.query(ScanMatch).filter(ScanMatch.scan_id.in_(scan_ids)).delete(synchronize_session=False)
        db.query(Scan).filter(Scan.document_id == doc_id).delete(synchronize_session=False)

    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)
    db.delete(doc)
    db.commit()
    return {"message": "Document deleted"}
