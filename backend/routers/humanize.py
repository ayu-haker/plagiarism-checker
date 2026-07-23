from fastapi import APIRouter, Depends, Request, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from database.models import get_db, HumanizeLog
from services.ingestion import DocumentIngestion
from pydantic import BaseModel
from typing import Optional
import os

router = APIRouter()
ingestion = DocumentIngestion()


class HumanizeRequest(BaseModel):
    text: str
    mode: str = "standard"


class HumanizeResponse(BaseModel):
    original_text: str
    humanized_text: str
    mode: str
    meaning_similarity: float


@router.post("/")
async def humanize_text(
    req: HumanizeRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    humanizer = request.app.state.humanizer_service
    result = humanizer.humanize(req.text, mode=req.mode)

    log = HumanizeLog(
        original_text=req.text[:5000],
        humanized_text=result["humanized_text"][:5000],
        mode=req.mode,
        meaning_similarity=result["meaning_similarity"],
    )
    db.add(log)
    db.commit()

    return HumanizeResponse(**result)


@router.post("/file")
async def humanize_file(
    request: Request,
    file: UploadFile = File(...),
    mode: str = Form("standard"),
    db: Session = Depends(get_db),
):
    allowed_types = {
        "application/pdf": "pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
        "application/msword": "docx",
        "text/plain": "txt",
    }

    EXTENSION_MAP = {
        ".pdf": "pdf",
        ".docx": "docx",
        ".doc": "docx",
        ".txt": "txt",
    }

    file_type = allowed_types.get(file.content_type)
    if not file_type and file.filename:
        ext = os.path.splitext(file.filename)[1].lower()
        file_type = EXTENSION_MAP.get(ext)

    if not file_type:
        raise HTTPException(status_code=400, detail="Upload PDF, DOCX, or TXT file")

    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_type}") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        text = ingestion.extract_text(tmp_path, file_type)
    except Exception as e:
        os.unlink(tmp_path)
        raise HTTPException(status_code=400, detail=f"Failed to extract text: {str(e)}")

    os.unlink(tmp_path)

    if not text.strip():
        raise HTTPException(status_code=400, detail="No text found in file")

    humanizer = request.app.state.humanizer_service
    result = humanizer.humanize(text, mode=mode)

    log = HumanizeLog(
        original_text=text[:5000],
        humanized_text=result["humanized_text"][:5000],
        mode=mode,
        meaning_similarity=result["meaning_similarity"],
    )
    db.add(log)
    db.commit()

    return {
        "filename": file.filename,
        "original_text": result["original_text"],
        "humanized_text": result["humanized_text"],
        "mode": mode,
        "meaning_similarity": result["meaning_similarity"],
        "word_count": len(text.split()),
    }


@router.get("/history")
async def humanize_history(db: Session = Depends(get_db)):
    logs = db.query(HumanizeLog).order_by(HumanizeLog.created_at.desc()).limit(50).all()
    return [
        {
            "id": l.id,
            "original_text": l.original_text[:200],
            "humanized_text": l.humanized_text[:200],
            "mode": l.mode,
            "meaning_similarity": l.meaning_similarity,
            "created_at": l.created_at.isoformat(),
        }
        for l in logs
    ]
