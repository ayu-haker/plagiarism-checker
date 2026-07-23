from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session
from database.models import get_db, Scan, ScanMatch, Document, ScanStatus
from io import BytesIO
from datetime import datetime, timezone
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_LEFT

router = APIRouter()


@router.post("/{doc_id}/scan")
async def start_scan(doc_id: int, request: Request, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    scan = Scan(document_id=doc_id, status=ScanStatus.PROCESSING)
    db.add(scan)
    db.commit()
    db.refresh(scan)

    try:
        engine = request.app.state.plagiarism_engine
        result = await engine.scan_document(doc.text_content)

        scan.status = ScanStatus.COMPLETED
        scan.similarity_score = result["overall_score"]
        scan.web_matches = result["web_matches_count"]
        scan.academic_matches = result["academic_matches_count"]
        scan.completed_at = datetime.now(timezone.utc)

        for match in result["matches"]:
            db_match = ScanMatch(
                scan_id=scan.id,
                chunk_text=match["chunk_text"],
                source_text=match["source_text"],
                source_url=match.get("source_url"),
                source_title=match.get("source_title"),
                similarity_score=match["score"],
                match_type=match["type"],
                start_position=match.get("start_position", 0),
                end_position=match.get("end_position", 0),
            )
            db.add(db_match)

        db.commit()
        db.refresh(scan)

    except Exception as e:
        scan.status = ScanStatus.FAILED
        db.commit()
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")

    return {
        "scan_id": scan.id,
        "status": scan.status,
        "similarity_score": scan.similarity_score,
        "web_matches": scan.web_matches,
        "academic_matches": scan.academic_matches,
    }


@router.get("/")
async def list_scans(db: Session = Depends(get_db)):
    scans = db.query(Scan).order_by(Scan.created_at.desc()).all()
    return [
        {
            "id": s.id,
            "document_id": s.document_id,
            "filename": s.document.filename,
            "status": s.status,
            "similarity_score": s.similarity_score,
            "web_matches": s.web_matches,
            "academic_matches": s.academic_matches,
            "created_at": s.created_at.isoformat(),
        }
        for s in scans
    ]


@router.get("/{scan_id}")
async def get_scan_result(scan_id: int, db: Session = Depends(get_db)):
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    doc = scan.document
    matches = db.query(ScanMatch).filter(ScanMatch.scan_id == scan_id).all()

    highlighted_segments = []
    for m in matches:
        text = m.chunk_text
        full_text = doc.text_content
        start = full_text.find(text[:80])
        if start == -1:
            start = m.start_position
        end = start + len(text) if start >= 0 else m.end_position

        highlighted_segments.append({
            "start": max(start, 0),
            "end": min(end, len(full_text)),
            "text": text,
            "score": m.similarity_score,
            "type": m.match_type,
        })

    highlighted_segments.sort(key=lambda x: x["start"])

    merged = []
    for seg in highlighted_segments:
        if merged and seg["start"] <= merged[-1]["end"] and seg["score"] >= merged[-1]["score"]:
            merged[-1]["end"] = max(merged[-1]["end"], seg["end"])
            if seg["score"] > merged[-1]["score"]:
                merged[-1]["score"] = seg["score"]
                merged[-1]["type"] = seg["type"]
        else:
            merged.append(dict(seg))

    return {
        "id": scan.id,
        "document_id": scan.document_id,
        "filename": doc.filename,
        "status": scan.status,
        "similarity_score": scan.similarity_score,
        "web_matches": scan.web_matches,
        "academic_matches": scan.academic_matches,
        "created_at": scan.created_at.isoformat(),
        "completed_at": scan.completed_at.isoformat() if scan.completed_at else None,
        "original_text": doc.text_content,
        "word_count": doc.word_count,
        "highlights": merged,
        "matches": [
            {
                "id": m.id,
                "chunk_text": m.chunk_text,
                "source_text": m.source_text,
                "source_url": m.source_url,
                "source_title": m.source_title,
                "similarity_score": m.similarity_score,
                "match_type": m.match_type,
                "start_position": m.start_position,
                "end_position": m.end_position,
            }
            for m in matches
        ],
    }


@router.get("/{scan_id}/pdf")
async def download_pdf(scan_id: int, db: Session = Depends(get_db)):
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    doc = scan.document
    matches = db.query(ScanMatch).filter(ScanMatch.scan_id == scan_id).all()

    highlights = []
    for m in matches:
        text = m.chunk_text
        full_text = doc.text_content
        start = full_text.find(text[:80])
        if start == -1:
            start = m.start_position
        end = start + len(text) if start >= 0 else m.end_position
        highlights.append({
            "start": max(start, 0),
            "end": min(end, len(full_text)),
            "score": m.similarity_score,
            "type": m.match_type,
        })
    highlights.sort(key=lambda x: x["start"])

    merged = []
    for h in highlights:
        if merged and h["start"] <= merged[-1]["end"]:
            merged[-1]["end"] = max(merged[-1]["end"], h["end"])
            if h["score"] > merged[-1]["score"]:
                merged[-1]["score"] = h["score"]
                merged[-1]["type"] = h["type"]
        else:
            merged.append(dict(h))

    pdf_buffer = BytesIO()
    pdf_doc = SimpleDocTemplate(pdf_buffer, pagesize=A4, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle("Title2", parent=styles["Title"], fontSize=18, spaceAfter=10)
    subtitle_style = ParagraphStyle("Subtitle2", parent=styles["Normal"], fontSize=11, textColor=HexColor("#666666"), spaceAfter=20)
    normal_style = ParagraphStyle("Normal2", parent=styles["Normal"], fontSize=10, leading=14, spaceAfter=6)
    flagged_style = ParagraphStyle("Flagged", parent=styles["Normal"], fontSize=10, leading=14, backColor=HexColor("#FEE2E2"), borderWidth=1, borderColor=HexColor("#EF4444"), borderPadding=4, spaceAfter=8)
    source_style = ParagraphStyle("Source", parent=styles["Normal"], fontSize=9, leading=12, textColor=HexColor("#3B82F6"), spaceAfter=4)
    header_style = ParagraphStyle("Header", parent=styles["Heading2"], fontSize=14, spaceAfter=10, spaceBefore=20)

    elements = []

    elements.append(Paragraph("Plagiarism Check Report", title_style))
    elements.append(Paragraph(f"File: {doc.filename} | Words: {doc.word_count} | Similarity: {scan.similarity_score}%", subtitle_style))

    score_color = "#22C55E" if scan.similarity_score < 15 else "#EAB308" if scan.similarity_score < 40 else "#F97316" if scan.similarity_score < 70 else "#EF4444"
    elements.append(Paragraph(f'<font color="{score_color}"><b>Overall Similarity: {scan.similarity_score}%</b></font>', subtitle_style))
    elements.append(Paragraph(f"Web Matches: {scan.web_matches} | Academic Matches: {scan.academic_matches}", subtitle_style))
    elements.append(Spacer(1, 15))

    elements.append(Paragraph("Highlighted Document", header_style))
    elements.append(Paragraph("Text highlighted in <font color='#EF4444'><b>red</b></font> = plagiarized content", subtitle_style))
    elements.append(Spacer(1, 5))

    full_text = doc.text_content
    if not merged:
        for para in full_text.split("\n\n"):
            para = para.strip()
            if para:
                safe = para.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                elements.append(Paragraph(safe, normal_style))
    else:
        last_end = 0
        for h in merged:
            if h["start"] > last_end:
                clean = full_text[last_end:h["start"]]
                for para in clean.split("\n\n"):
                    para = para.strip()
                    if para:
                        safe = para.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                        elements.append(Paragraph(safe, normal_style))

            flagged_text = full_text[h["start"]:h["end"]]
            pct = int(h["score"] * 100)
            label = f"[{pct}% match - {h['type']}]"
            safe_flagged = flagged_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            elements.append(Paragraph(f'<font color="#EF4444"><b>{label}</b></font> {safe_flagged}', flagged_style))
            last_end = h["end"]

        if last_end < len(full_text):
            remaining = full_text[last_end:]
            for para in remaining.split("\n\n"):
                para = para.strip()
                if para:
                    safe = para.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                    elements.append(Paragraph(safe, normal_style))

    elements.append(Spacer(1, 20))
    elements.append(Paragraph("Matched Sources", header_style))

    for i, m in enumerate(matches):
        safe_chunk = m.chunk_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")[:150]
        safe_source = m.source_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")[:200]
        pct = int(m.similarity_score * 100)
        elements.append(Paragraph(f'<font color="#EF4444"><b>Match {i+1} ({pct}%)</b></font>', normal_style))
        elements.append(Paragraph(f'Your text: "{safe_chunk}..."', normal_style))
        if m.source_title:
            elements.append(Paragraph(f'Source: {m.source_title}', source_style))
        if m.source_url:
            elements.append(Paragraph(f'URL: {m.source_url}', source_style))
        elements.append(Spacer(1, 8))

    pdf_doc.build(elements)
    pdf_buffer.seek(0)

    filename = f"plagiarism_report_{doc.filename.replace(' ', '_')}.pdf"
    return Response(
        content=pdf_buffer.read(),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.delete("/{scan_id}")
async def delete_scan(scan_id: int, db: Session = Depends(get_db)):
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    db.query(ScanMatch).filter(ScanMatch.scan_id == scan_id).delete()
    db.delete(scan)
    db.commit()
    return {"message": "Scan deleted"}
