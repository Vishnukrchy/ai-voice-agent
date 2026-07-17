"""Document text extraction + chunking for the knowledge base pipeline."""
from pathlib import Path

import pypdf
from docx import Document as DocxDocument


def extract_text(file_path: str, file_type: str) -> str:
    """Extracts raw text from a PDF, DOCX, or TXT file."""
    path = Path(file_path)

    if file_type == "pdf":
        reader = pypdf.PdfReader(str(path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    if file_type == "docx":
        doc = DocxDocument(str(path))
        return "\n".join(p.text for p in doc.paragraphs)

    if file_type == "txt":
        return path.read_text(encoding="utf-8", errors="ignore")

    raise ValueError(f"Unsupported file type: {file_type}")


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 150) -> list[str]:
    """Splits text into overlapping chunks by character count, breaking on
    whitespace where possible to avoid cutting words mid-token."""
    text = " ".join(text.split())
    if not text:
        return []

    chunks: list[str] = []
    start = 0
    text_len = len(text)
    while start < text_len:
        end = min(start + chunk_size, text_len)
        if end < text_len:
            last_space = text.rfind(" ", start, end)
            if last_space > start:
                end = last_space
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= text_len:
            break
        start = max(end - overlap, start + 1)  # always make progress
    return chunks
