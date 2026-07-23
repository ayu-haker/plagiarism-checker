from pypdf import PdfReader
from docx import Document as DocxDocument


class DocumentIngestion:
    def extract_text(self, file_path: str, file_type: str) -> str:
        if file_type == "pdf":
            return self._extract_pdf(file_path)
        elif file_type == "docx":
            return self._extract_docx(file_path)
        elif file_type == "txt":
            return self._extract_txt(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

    def _extract_pdf(self, path: str) -> str:
        reader = PdfReader(path)
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
        return "\n\n".join(pages)

    def _extract_docx(self, path: str) -> str:
        doc = DocxDocument(path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n\n".join(paragraphs)

    def _extract_txt(self, path: str) -> str:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
