# Plagiarism Checker & Humanizer

A full-stack plagiarism detection and text humanization tool — like iThenticate but self-hosted and free.

**Live on Docker Hub:**
- [Backend Image](https://hub.docker.com/r/ayushman21/plagiarism-backend)
- [Frontend Image](https://hub.docker.com/r/ayushman21/plagiarism-frontend)

---

## Features

### Plagiarism Detection
- **Upload** PDF, DOCX, or TXT files
- **Scan** against web sources (DuckDuckGo, Wikipedia) and academic databases (OpenAlex, arXiv)
- **Multi-layer similarity** engine: TF-IDF + n-gram + exact phrase matching
- **Highlighted text view** with color-coded severity (red = high, orange = medium, yellow = low)
- **Filter** highlights by source type (web / academic)
- **PDF report export** with flagged sections highlighted
- **Scan history** with delete option

### Text Humanizer
- 3 modes: **Light** (synonym swap, 96%+ meaning preserved), **Standard** (+ contractions), **Aggressive** (full rewrite)
- Upload files or paste text directly
- Side-by-side comparison of original vs humanized
- Copy to clipboard / download as .txt
- Humanize history tracking

---

## Quick Start (Docker)

```bash
docker compose up -d
```

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000/docs

---

## Quick Start (Local)

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

- **Frontend:** http://localhost:3000
- **Swagger UI:** http://localhost:8000/docs

---

## Architecture

```
frontend/          React + TypeScript + Vite + Tailwind
  src/
    pages/
      Dashboard.tsx       Upload docs, scan, view history
      ScanResults.tsx     Highlights, matches, PDF export
      Humanizer.tsx       Text/file humanization
    services/api.ts       API client

backend/           Python FastAPI
  services/
    plagiarism_engine.py  Scan pipeline
    similarity.py        Multi-layer scoring
    web_search.py        DuckDuckGo + Wikipedia
    academic_search.py   OpenAlex + arXiv
    humanizer.py         Rule-based text rewriting
    ingestion.py         PDF/DOCX/TXT extraction
  routers/
    documents.py         Upload, list, delete
    scans.py             Scan, results, PDF export, delete
    humanize.py          Humanize text/file, history
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/documents/upload` | Upload PDF/DOCX/TXT |
| GET | `/api/documents/` | List all documents |
| DELETE | `/api/documents/{id}` | Delete document + scans |
| POST | `/api/scans/{id}/scan` | Run plagiarism scan |
| GET | `/api/scans/` | List all scans |
| GET | `/api/scans/{id}` | Get scan results + highlights |
| GET | `/api/scans/{id}/pdf` | Download PDF report |
| DELETE | `/api/scans/{id}` | Delete scan |
| POST | `/api/humanize/` | Humanize text |
| POST | `/api/humanize/file` | Humanize uploaded file |
| GET | `/api/humanize/history` | Humanize history |

---

## Tech Stack

- **Frontend:** React 18, TypeScript, Vite, Tailwind CSS
- **Backend:** Python 3.11, FastAPI, SQLAlchemy, SQLite
- **Search:** DuckDuckGo, Wikipedia, OpenAlex, arXiv (all free, no API keys)
- **Deployment:** Docker Compose

---

## License

MIT
