# InternOS Recruiter Resume Analyzer

InternOS is a recruiter-focused resume analysis system built with FastAPI and Streamlit. It accepts PDF and DOCX resumes, extracts text with OCR support, analyzes candidate information, and presents the output in plain language for non-technical users.

## What It Does

- Upload one or many resumes in `.pdf` or `.docx`
- Detect whether the uploaded file is actually a resume
- Extract candidate identity details such as name, email, and handle
- Extract skills across programming languages, frameworks, libraries, tools, platforms, databases, and cloud/devops technologies
- Infer education details such as degree, graduation status, graduation year, and expected graduation
- Score resume clarity, impact evidence, and overall fit
- Search candidates by skill, degree, graduation status, name, or handle
- Review candidates in compact recruiter-friendly cards with expandable details

## Tech Stack

- Backend: FastAPI, SQLAlchemy, Pydantic
- Frontend: Streamlit, Pandas
- Resume parsing: `pdfplumber`, `python-docx`
- OCR: `PyMuPDF`, `pytesseract`, `Pillow`
- Optional LLM support: generic HTTP endpoint via `httpx`
- Database: SQLite by default

## Project Structure

```text
InternOS/
|-- backend/
|   |-- app/
|   |   |-- main.py
|   |   |-- routes.py
|   |   |-- resume_parser.py
|   |   |-- nlp_pipeline.py
|   |   |-- llm_client.py
|   |   |-- db.py
|   |   |-- models.py
|   |   `-- schemas.py
|   `-- requirements.txt
|-- streamlit_app/
|   |-- app.py
|   `-- home.py
|-- .streamlit/
|   `-- config.toml
|-- requirements.txt
`-- README.md
```

## Requirements

- Python 3.11+ recommended
- Windows, macOS, or Linux
- Tesseract OCR installed locally if you want OCR for scanned/image resumes

## Installation

Create and activate a virtual environment, then install the full project dependencies:

```bash
pip install -r requirements.txt
```

If you want backend-only dependencies, use:

```bash
pip install -r backend/requirements.txt
```

## Environment Variables

These are optional unless noted otherwise:

- `DATABASE_URL`
  Default: `sqlite:///./internos.db`
- `ARTIFACTS_DIR`
  Default: `./artifacts`
- `INTERNOS_API_URL`
  Used by Streamlit to point to the backend
  Default: `http://127.0.0.1:8000`
- `TESSERACT_CMD`
  Full path to the Tesseract executable if it is not on `PATH`
- `LLM_MODE`
  Use `http` to enable LLM-backed cleanup/classification
  Default: `stub`
- `LLM_HTTP_URL`
  Required when `LLM_MODE=http`
- `LLM_HTTP_KEY`
  Optional auth token for the LLM endpoint
- `N8N_WEBHOOK_URL`
  Optional webhook for analysis events

## OCR Setup

OCR is used for scanned PDFs and images embedded in DOCX files.

1. Install Tesseract OCR on your machine
2. Add `tesseract` to your system `PATH`
3. If it is not on `PATH`, set `TESSERACT_CMD` to the full executable path

Without Tesseract:

- text-based PDFs still work through direct extraction
- DOCX files still work through direct text extraction
- scanned/image-heavy resumes will have weaker extraction quality

## Running the Backend

From the project root:

```bash
cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Backend health check:

```text
http://127.0.0.1:8000/
```

## Running the Streamlit App

From the project root:

```bash
streamlit run streamlit_app/app.py
```

Default UI URL:

```text
http://localhost:8501
```

## Main Features

### Resume Upload

- Multi-file upload
- 100 MB total batch limit
- PDF and DOCX support
- Resume/non-resume detection before analysis

### Candidate Analysis

- Candidate handle derived from the resume
- Name and email extraction
- Degree and graduation inference
- Skill extraction grouped into categories
- Plain-language recruiter summary

### Candidate Review

- Search by first name, last name, full name, handle, `*`, or `all`
- Compact candidate cards
- Expandable detailed review

### Candidate Search

- Filter by required skills
- Filter by graduation status
- Filter by degree text
- Filter by minimum fit score

## Main API Endpoints

- `POST /resumes/analyze`
- `GET /resumes/{handle}/latest`
- `GET /resumes/find`
- `GET /resumes/all`
- `GET /resumes/search`

## LLM Integration

LLM support is optional.

When enabled, the backend can use an HTTP LLM endpoint to:

- clean noisy OCR text
- classify whether a document is a resume
- return structured facts such as degree, graduation status, and skills
- generate recruiter-friendly summaries

If `LLM_MODE` is not set to `http`, the project falls back to rule-based behavior.

## Notes

- Existing saved analyses will not automatically update after parser changes; re-analyze resumes to refresh results
- OCR and LLM improve quality, but they do not guarantee perfect extraction
- SQLite is the default database and is suitable for local development

## GitHub Push Checklist

Before pushing:

1. Make sure `.venv` and local database files are ignored
2. Remove any local secrets or machine-specific paths
3. Verify the app starts with `uvicorn` and `streamlit`
4. Re-test one PDF and one DOCX upload

## License

Add your preferred license before publishing publicly.
