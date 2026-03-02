# LegalRAG - Legal Document Search & Court Filing Generator

A full-stack legal practice tool combining semantic document search (RAG) with automated court filing generation. Built with FastAPI, React, ChromaDB, and python-docx.

## Features

### Document Search (RAG)
- **PDF Upload with OCR**: Process and index legal PDFs, with automatic OCR for scanned documents
- **Semantic Search**: Natural language queries over your document corpus using QA-optimized embeddings
- **AI Answer Synthesis**: Optional Groq-powered answer generation from search results
- **Document Management**: Upload, list, view full text, and delete indexed documents

### Document Automation
- **Letter Generation**: Professional letters with letterhead support and AI body generation
- **Envelope Printing**: Generate envelopes from recipient addresses
- **Template Management**: SQLite-backed letterhead and template storage

### Court Filing Generator
- **Case Management**: Save and manage case information (parties, court, case number)
- **Pleading Generation**: Generate formatted .docx court filings with:
  - Caption table with party names, court name, and case number
  - Support for all RI state courts and federal courts with county/location selection
  - Markdown-lite body formatting: `## headings`, `**bold**`, `__underline__`, numbered lists, bullets
  - Signature block with attorney info pulled from settings
  - Certification of service with configurable filing method (ECF, Tyler, mail, hand delivery) and service method (ECF auto-serve, email, mail, hand delivery)
- **Section Builder UI**: Visual drag-and-drop section builder for motion body content (paragraphs, bullets, numbered items)
- **AI Body Generation**: Generate motion body text via Groq AI from natural language prompts

### Platform
- **JWT Authentication**: Secure user sessions
- **User Settings**: Attorney info, bar number, firm details persisted per user
- **Responsive React Frontend**: Sidebar navigation with dashboard

## Tech Stack

### Backend
- **FastAPI** with modular route splitting
- **ChromaDB** for vector storage
- **sentence-transformers** (`multi-qa-MiniLM-L6-cos-v1`) for QA-optimized embeddings
- **PyMuPDF** for PDF text extraction + OCR
- **python-docx** for .docx court filing generation
- **Groq API** for AI answer synthesis and document body generation
- **SQLite** for case data, user settings, and template management

### Frontend
- **React 18** + **TypeScript**
- **Tailwind CSS** + **shadcn/ui** components
- **Vite** build tooling

## Project Structure

```
legalrag/
├── app/
│   ├── main.py                          # FastAPI app setup and startup
│   ├── models.py                        # Pydantic models (search, documents, cases, pleadings)
│   ├── database.py                      # ChromaDB vector database
│   ├── embeddings.py                    # Sentence transformer wrapper
│   ├── document_processor.py            # PDF parsing, OCR, and chunking
│   ├── search.py                        # Semantic search logic
│   ├── auth.py                          # JWT authentication
│   ├── case_db.py                       # Case CRUD (SQLite)
│   ├── user_settings_db.py              # User settings persistence
│   ├── routes/
│   │   ├── documents.py                 # Upload, list, delete, view documents
│   │   ├── search.py                    # Search endpoint
│   │   ├── generation.py                # Letter/envelope generation
│   │   ├── cases.py                     # Case CRUD + pleading generation
│   │   └── settings.py                  # User settings endpoints
│   └── document_generation/
│       ├── pleading_generator.py        # .docx court filing formatter
│       ├── pleading_builder.py          # Orchestrates AI + formatting
│       ├── template_manager.py          # SQLite letterhead/template storage
│       └── envelope_builder.py          # Envelope generation
├── data/                                # Persistent storage (ChromaDB, SQLite, uploads)
├── requirements.txt
├── Dockerfile
└── README.md

frontend/
├── src/
│   ├── App.tsx                          # Main app with sidebar navigation
│   ├── types/api.ts                     # TypeScript API interfaces
│   └── components/
│       ├── PleadingGeneration/          # Court filing generator UI
│       ├── DocumentAutomation/          # Letter & envelope generation
│       ├── GeneratedDocuments/          # Generated document list & download
│       ├── Settings/                    # Attorney info & user settings
│       ├── DocumentList.tsx             # Uploaded document management
│       └── ui/                          # shadcn/ui components
└── package.json
```

## Setup

### Prerequisites
- Python 3.9+
- Node.js 18+

### Backend

```bash
cd legalrag
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `JWT_SECRET` | Yes | Secret key for JWT token signing |
| `GROQ_API_KEY` | Optional | Groq API key for AI features (answer synthesis, body generation) |

## Deployment

Configured for Railway with persistent volume at `/app/data`:

```bash
docker build -t legalrag .
docker run -p 8000:8000 -v $(pwd)/data:/app/data legalrag
```

## License

MIT
