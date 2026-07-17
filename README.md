# DataPoint

A production-style REST API built with **FastAPI** that automates data file validation, mismatch report generation, and scheduled reporting — designed to eliminate manual data review workflows.

> Built independently as a proof-of-concept during a Data Analysis Internship at Morgan Stanley Wealth Management — an idea sparked by AI case study research and team-meeting conversations, built on my own initiative rather than as an assigned project.

***

## What It Does

DataPoint accepts uploaded data files (CSV/Excel), validates them against expected schemas, detects mismatches (delta between expected vs. actual records), and generates downloadable reports — all through a clean REST API with no manual steps required.

**Core capabilities:**
- 📂 **File Ingestion** — accepts CSV/Excel uploads via REST endpoint
- ✅ **Data Validation** — Pydantic schema validation with configurable column mappings and row corrections
- 📊 **Mismatch Detection** — calculates delta between expected and actual record counts per team/month/year
- 📥 **Multi-Format Report Downloads** — streams CSV, XLSX, and PDF reports in-memory (no temp files written to disk)
- ⏰ **Scheduled Reporting** — APScheduler auto-generates monthly and annual mismatch reports at midnight on the 1st of each period
- 🤖 **RAG Layer (in progress)** — LangChain + OpenAI + Chroma vector store integration for document Q&A over validated data files

***

## Tech Stack

| Layer | Technology |
|---|---|
| API Framework | FastAPI |
| Data Processing | Pandas |
| Schema Validation | Pydantic |
| Background Scheduling | APScheduler |
| Report Generation | openpyxl (XLSX), xhtml2pdf (PDF) |
| RAG / LLM Layer | LangChain, OpenAI, Chroma |
| Language | Python 3.10+ |

***

## Project Structure

```
DataPoint/
├── app/
│   ├── web_app.py          # FastAPI app entry point, lifespan, middleware
│   ├── config.py           # Path configuration (input_docs, approved_docs)
│   ├── api/
│   │   ├── file_router.py      # POST /files/validate — file upload & validation
│   │   └── report_router.py    # GET /reports/... — report generation & download
│   ├── core/
│   │   ├── file_manager.py     # File parsing, validation logic, team/month/year extraction
│   │   ├── data_manager.py     # Data processing utilities
│   │   ├── report_manager.py   # Mismatch calculation, scheduled jobs, buffer export
│   │   └── rag.py              # RAG pipeline (LangChain + OpenAI + Chroma) — in progress
│   └── models/
│       └── valid_file.py       # Pydantic models for file validation
```

***

## API Endpoints

### File Endpoints — `/files`

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/files/` | Health check |
| `POST` | `/files/validate` | Upload and validate a CSV/Excel file |

**POST `/files/validate` — Form Parameters:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `input_file` | File | ✅ | CSV or Excel file to validate |
| `mappings` | JSON string | ❌ | Column name remappings |
| `row_correction` | JSON string | ❌ | Row-level data corrections |
| `new_file_name` | string | ❌ | Rename the file on save |

### Report Endpoints — `/reports`

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/reports/generate_mismatch_report` | Generate mismatch report (JSON response) |
| `GET` | `/reports/download` | Download report as CSV, XLSX, or PDF |
| `GET` | `/reports/mismatch_reports` | List existing mismatch reports |
| `GET` | `/reports/summary_reports` | List existing summary reports |

**GET `/reports/download` — Query Parameters:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `file_ext` | string | ✅ | `csv`, `xlsx`, or `pdf` |
| `report_type` | string | ✅ | `mismatch` |
| `year` | int | ❌ | Filter by year |
| `groupBy` | string | ❌ | Group by `Team`, `Month`, etc. |
| `groupValue` | string | ❌ | Value to filter on |
| `file_name` | string | ❌ | Custom download filename |

***

## How It Works

### Validation Pipeline

```
Upload File
    │
    ▼
Parse CSV/Excel → Pandas DataFrame
    │
    ▼
Apply Column Mappings (optional)
    │
    ▼
Pydantic Schema Validation
    │
    ├── ❌ Validation Fails → Return mismatch details to client
    │
    └── ✅ Validation Passes → Save to approved_docs/{year}/filename.csv
```

### Mismatch Report Flow

```
Load approved CSVs (filtered by year/team/month)
    │
    ▼
Merge into single DataFrame
    │
    ▼
Calculate Delta: Expected Records Deleted − Actual Records Deleted
    │
    ▼
Filter rows where Delta ≠ 0
    │
    ▼
Stream as CSV / XLSX / PDF → Client (no disk write)
```

### Scheduled Reports

APScheduler runs two background jobs on app startup:
- **Annual** — runs January 1st at midnight for the current year
- **Monthly** — runs the 1st of each month at midnight, grouped by Month

***

## Getting Started

### Prerequisites

- Python 3.10+
- OpenAI API key (for RAG layer)

### Installation

```bash
git clone https://github.com/DENISE-LEON/DataPoint.git
cd DataPoint
pip install -r requirements.txt
```

### Environment Setup

Create a `.env` file in the root:

```
OPENAI_API_KEY=your_openai_api_key_here
```

### Run the API

```bash
uvicorn app.web_app:app --reload
```

API will be available at `http://localhost:8000`

Interactive docs: `http://localhost:8000/docs`

***

## Example Usage

### Validate a File

```bash
curl -X POST "http://localhost:8000/files/validate" \
  -F "input_file=@your_data.csv" \
  -F 'mappings={"OldColumnName": "NewColumnName"}'
```

### Download a Mismatch Report as Excel

```bash
curl "http://localhost:8000/reports/download?file_ext=xlsx&report_type=mismatch&year=2026" \
  --output mismatch_report_2026.xlsx
```

***
