import io
import os
import zipfile
from shutil import which


def _configure_tesseract() -> None:
    import pytesseract

    configured = os.getenv("TESSERACT_CMD", "").strip()
    if configured:
        pytesseract.pytesseract.tesseract_cmd = configured

    cmd = pytesseract.pytesseract.tesseract_cmd
    binary = cmd if os.path.isabs(cmd) else which(cmd)
    if not binary and not configured:
        binary = which("tesseract")

    if not binary:
        raise RuntimeError(
            "Tesseract OCR is required. Install Tesseract and set TESSERACT_CMD if it is not on PATH."
        )

    pytesseract.pytesseract.tesseract_cmd = binary


def _ocr_image_bytes(image_bytes: bytes) -> str:
    import pytesseract
    from PIL import Image

    _configure_tesseract()
    with Image.open(io.BytesIO(image_bytes)) as image:
        text = pytesseract.image_to_string(image)
    return text.strip()


def _optional_ocr_image_bytes(image_bytes: bytes) -> str:
    try:
        return _ocr_image_bytes(image_bytes)
    except Exception:
        return ""


def _normalize_chunks(chunks: list[str]) -> str:
    return "\n".join(chunk.strip() for chunk in chunks if chunk and chunk.strip()).strip()


def extract_text_from_pdf(data: bytes) -> str:
    import pdfplumber

    chunks: list[str] = []
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        for page in pdf.pages:
            direct = (page.extract_text() or "").strip()
            if direct:
                chunks.append(direct)

    # OCR is optional. If PyMuPDF or Tesseract is missing, keep direct extraction.
    try:
        import fitz

        doc = fitz.open(stream=data, filetype="pdf")
        try:
            for page in doc:
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
                ocr = _optional_ocr_image_bytes(pix.tobytes("png"))
                if ocr:
                    chunks.append(ocr)
        finally:
            doc.close()
    except Exception:
        pass

    return _normalize_chunks(chunks)


def extract_text_from_docx(data: bytes) -> str:
    from docx import Document

    chunks: list[str] = []
    doc = Document(io.BytesIO(data))
    chunks.extend(paragraph.text for paragraph in doc.paragraphs if paragraph.text.strip())

    # OCR embedded images inside the DOCX archive.
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        for name in archive.namelist():
            if not name.startswith("word/media/"):
                continue
            if not name.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp")):
                continue
            ocr = _optional_ocr_image_bytes(archive.read(name))
            if ocr:
                chunks.append(ocr)

    return _normalize_chunks(chunks)


def extract_resume_text(filename: str, data: bytes) -> str:
    lower = filename.lower()
    if lower.endswith(".pdf"):
        return extract_text_from_pdf(data)
    if lower.endswith(".docx"):
        return extract_text_from_docx(data)
    raise ValueError("Only .pdf or .docx supported")
