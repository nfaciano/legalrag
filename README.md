# LegalRAG - AI-Powered Legal Document Automation

Full-stack RAG (Retrieval-Augmented Generation) system with semantic search, AI-powered document generation, and envelope automation for law firms. Built with FastAPI, ChromaDB, React, TypeScript, and Groq AI.

![Tech Stack](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white)
![Tailwind](https://img.shields.io/badge/Tailwind-06B6D4?style=for-the-badge&logo=tailwindcss&logoColor=white)

## Features

### Document Intelligence
- **Document Upload**: Drag-and-drop PDF upload with automatic indexing
- **Semantic Search**: Natural language queries over legal documents with AI-powered answer synthesis
- **Vector Search**: Fast similarity search using ChromaDB with 250-word chunks
- **Source Citations**: Results include filename, page number, and relevance scores

### Document Automation
- **AI Document Generation**: Generate legal letters with RAG-powered content from your uploaded documents
- **Envelope Generation**: AI-powered address parsing with #10 business envelope formatting
- **Template Management**: Save and reuse document templates with placeholders
- **Settings Sync**: Persistent return address, signature, and initials across devices

### User Experience
- **Multi-Tenant**: Secure user authentication with Clerk (isolated data per user)
- **Document Management**: View, download, and delete all generated documents
- **Modern UI**: Clean interface with shadcn/ui components and dark mode support
- **Type-Safe**: Full TypeScript coverage on frontend and Python type hints on backend

## Tech Stack

### Backend
- **FastAPI** - Modern async Python web framework
- **ChromaDB** - Open-source vector database
- **sentence-transformers** - Free embedding model (all-MiniLM-L6-v2)
- **Groq API** - Lightning-fast AI inference (llama-3.3-70b-versatile)
- **python-docx** - Word document generation for letters and envelopes
- **Clerk** - User authentication and JWT validation
- **SQLite** - User settings and document metadata storage
- **PyMuPDF** - Fast PDF text extraction
- **Pydantic** - Data validation

### Frontend
- **React 18** - UI library
- **TypeScript** - Type safety
- **Clerk React** - Authentication UI components
- **Vite** - Lightning-fast build tool
- **Tailwind CSS** - Utility-first styling
- **shadcn/ui** - High-quality component library
- **Lucide React** - Modern icon set

## Architecture

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   React     │  HTTP   │   FastAPI    │  Store  │  ChromaDB   │
│  Frontend   ├────────>│   Backend    ├────────>│  Vector DB  │
│   + Clerk   │  (JWT)  │   + Auth     │         │             │
└─────────────┘         └──────────────┘         └─────────────┘
                               │                         │
                     ┌─────────┼─────────┬───────────────┘
                     ↓         ↓         ↓
              ┌──────────┐ ┌─────┐ ┌──────────┐
              │  Groq    │ │SQLite│ │sentence- │
              │   API    │ │ DB  │ │transformers│
              │ (LLM)    │ │     │ │(embeddings)│
              └──────────┘ └─────┘ └──────────┘
```

### Data Flow

**Document Search**:
1. **Upload**: PDF → PyMuPDF (extract text) → Chunk (250 words, 25 overlap)
2. **Embed**: Chunks → sentence-transformers → 384-dim vectors
3. **Store**: Vectors + metadata → ChromaDB (user-isolated collections)
4. **Search**: Query → Embed → Vector similarity → Groq synthesis → Answer

**Document Generation**:
1. **Template**: User input + RAG context → Groq AI → Structured content
2. **Generate**: Content + letterhead → python-docx → .docx file
3. **Store**: Metadata → SQLite, File → user uploads folder
4. **Download**: Secure file serving with JWT validation

**Envelope Generation**:
1. **Parse**: Natural language → Groq AI → Structured address
2. **Format**: Return + recipient address → #10 envelope layout
3. **Generate**: python-docx → Print-ready .docx

## Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+
- [Groq API key](https://console.groq.com) (free tier available)
- [Clerk account](https://clerk.com) (free tier available)

### Backend Setup

```bash
cd legalrag

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows (use `source venv/bin/activate` on Mac/Linux)

# Install dependencies
pip install -r requirements.txt

# Configure environment (copy .env.example to .env and add keys)
cp .env.example .env
# Edit .env and add:
#   GROQ_API_KEY=your_groq_key
#   CLERK_SECRET_KEY=your_clerk_secret
#   FRONTEND_URL=http://localhost:5173

# Run server
uvicorn app.main:app --reload
```

Backend runs at `http://localhost:8000`

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env
# Edit .env and add:
#   VITE_API_BASE_URL=http://localhost:8000
#   VITE_CLERK_PUBLISHABLE_KEY=your_clerk_publishable_key

# Run dev server
npm run dev
```

Frontend runs at `http://localhost:5173`

## Project Structure

```
RagLaw/
├── legalrag/                    # FastAPI backend
│   ├── app/
│   │   ├── main.py              # API endpoints (search, upload, generation)
│   │   ├── auth.py              # Clerk JWT validation
│   │   ├── database.py          # ChromaDB integration
│   │   ├── embeddings.py        # Sentence transformers
│   │   ├── document_processor.py # PDF parsing & chunking
│   │   ├── search.py            # Semantic search
│   │   ├── synthesis.py         # Groq AI answer generation
│   │   ├── user_settings_db.py  # SQLite user settings
│   │   ├── models.py            # Pydantic models
│   │   └── document_generation/
│   │       ├── document_builder.py  # Letter generation
│   │       ├── document_generator.py # Word doc creation
│   │       ├── envelope_builder.py  # Envelope generation
│   │       └── envelope_generator.py # Envelope formatting
│   ├── requirements.txt
│   ├── .env.example
│   └── README.md
├── frontend/                    # React + TypeScript frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── ui/              # shadcn/ui components
│   │   │   ├── FileUpload/      # PDF upload
│   │   │   ├── SearchBar/       # Search interface
│   │   │   ├── SearchResults/   # Results display
│   │   │   ├── DocumentList/    # Indexed documents
│   │   │   ├── DocumentAutomation/ # Letter generation
│   │   │   ├── EnvelopeGeneration/ # Envelope creation
│   │   │   ├── GeneratedDocuments/ # Document management
│   │   │   └── Settings/        # User settings
│   │   ├── lib/
│   │   │   ├── api.ts           # API client with auth
│   │   │   ├── useApi.ts        # React hook for API
│   │   │   └── utils.ts
│   │   ├── types/api.ts         # TypeScript types
│   │   └── App.tsx              # Main app with navigation
│   ├── package.json
│   ├── .env.example
│   └── tailwind.config.js
└── README.md
```

## API Endpoints

All endpoints require JWT authentication via `Authorization: Bearer <token>` header.

### Document Search

**Upload Document**
```http
POST /upload
Content-Type: multipart/form-data
Authorization: Bearer {jwt_token}

Response:
{
  "document_id": "abc123",
  "filename": "contract.pdf",
  "total_chunks": 47,
  "message": "Successfully indexed contract.pdf"
}
```

**Search Documents**
```http
POST /search
Content-Type: application/json
Authorization: Bearer {jwt_token}

{
  "query": "What are the termination clauses?",
  "top_k": 5
}

Response:
{
  "query": "What are the termination clauses?",
  "answer": "According to the contract, either party may terminate...",
  "results": [...]
}
```

**List Documents**
```http
GET /documents
Authorization: Bearer {jwt_token}

Response:
{
  "documents": [...],
  "total_documents": 5
}
```

**Delete Document**
```http
DELETE /documents/{document_id}
Authorization: Bearer {jwt_token}
```

### Document Automation

**Generate Letter**
```http
POST /generate-document
Content-Type: application/json
Authorization: Bearer {jwt_token}

{
  "template_id": "custom_letter",
  "use_rag": true,
  "rag_query": "What are the payment terms?",
  "fields": {
    "recipient_name": "John Doe",
    "recipient_address": "123 Main St",
    "date": "December 9, 2024",
    "body": "Regarding payment terms...",
    "closing": "Very truly yours,",
    "signature_name": "Jane Attorney",
    "initials": "JA/kb"
  }
}

Response:
{
  "document_id": "doc_abc123",
  "filename": "john_doe_2024-12-09_doc_abc123.docx"
}
```

**Generate Envelope**
```http
POST /generate-envelope
Content-Type: application/json
Authorization: Bearer {jwt_token}

{
  "return_address": {
    "name": "Law Firm Name",
    "line1": "123 Attorney Ave",
    "line2": "Suite 100",
    "city_state_zip": "City, ST 12345"
  },
  "ai_prompt": "Send to John Doe at 456 Client St, Town, ST 67890",
  "recipient": null
}

Response:
{
  "envelope_id": "env_xyz789",
  "filename": "john_doe_envelope_2024-12-09_env_xyz789.docx"
}
```

**List Generated Documents**
```http
GET /generated-documents
Authorization: Bearer {jwt_token}

Response:
{
  "documents": [
    {
      "document_id": "doc_abc123",
      "filename": "john_doe_2024-12-09_doc_abc123.docx",
      "generated_at": "2024-12-09T10:30:00",
      "file_size": 15234
    }
  ]
}
```

**Download Generated Document**
```http
GET /generated-documents/{document_id}
Authorization: Bearer {jwt_token}

Response: Binary .docx file
```

**Delete Generated Document**
```http
DELETE /generated-documents/{document_id}
Authorization: Bearer {jwt_token}
```

### User Settings

**Get Settings**
```http
GET /user-settings
Authorization: Bearer {jwt_token}

Response:
{
  "settings": {
    "return_address_name": "Law Firm Name",
    "return_address_line1": "123 Attorney Ave",
    "signature_name": "Jane Attorney",
    "initials": "JA/kb",
    "closing": "Very truly yours,"
  }
}
```

**Update Settings**
```http
PUT /user-settings
Content-Type: application/json
Authorization: Bearer {jwt_token}

{
  "return_address_name": "Law Firm Name",
  "signature_name": "Jane Attorney",
  "initials": "JA/kb",
  "closing": "Very truly yours,"
}

Response:
{
  "settings": {...}
}
```

## Example Queries

- "What are the payment terms?"
- "Who are the parties to this agreement?"
- "What are the liability limitations?"
- "When does the contract terminate?"
- "What are the confidentiality requirements?"
- "What are the indemnification clauses?"

## Cost Analysis

| Component | Cost | Notes |
|-----------|------|-------|
| Development | $0 | All open-source tools |
| Embeddings | $0 | Local sentence-transformers |
| Vector DB | $0 | ChromaDB local storage |
| LLM (Groq) | $0-5/month | Free tier: 30 req/min, then $0.05-0.27 per 1M tokens |
| Auth (Clerk) | $0-25/month | Free tier: 10k MAU, then $25/month |
| Backend Hosting | $5/month | Railway Hobby plan |
| Frontend Hosting | $0 | Vercel free tier |
| **Total** | **$0-10/month** | Free for personal use, <$40/month at scale |

**Usage Estimates** (for free tier):
- Groq: ~1,000 document generations/month or ~5,000 searches
- Clerk: Up to 10,000 monthly active users
- Perfect for law firm teams (<20 users) or personal use

## Performance

- **Embedding Generation**: ~100 chunks/second on CPU
- **Search Latency**: <100ms for typical queries
- **LLM Synthesis**: ~200-500ms via Groq (llama-3.3-70b)
- **Document Generation**: ~1-2 seconds for letters, ~500ms for envelopes
- **Storage**: ~0.5KB per chunk (text + embeddings + metadata)
- **Chunk Size**: 250 words with 25-word overlap (optimized for precision)

## Resume Talking Points

This project demonstrates:

✅ **RAG Architecture** - End-to-end retrieval-augmented generation with LLM synthesis
✅ **Vector Databases** - ChromaDB integration with sentence-transformers embeddings
✅ **LLM Integration** - Groq API for document generation and answer synthesis
✅ **Authentication** - Multi-tenant architecture with Clerk JWT validation
✅ **Document Processing** - PDF parsing, Word generation, envelope formatting
✅ **ML Infrastructure** - Production-ready FastAPI backend with async endpoints
✅ **Semantic Search** - Embedding generation, cosine similarity, and retrieval
✅ **Full-Stack** - Modern React/TypeScript SPA with API-first design
✅ **Database Design** - SQLite for user settings, ChromaDB for vectors
✅ **Domain Expertise** - Legal document automation and law firm workflows
✅ **Modern Stack** - FastAPI, React, TypeScript, Tailwind, shadcn/ui, Groq, Clerk

## Deployment

### Backend (Railway)

1. **Push to GitHub**
```bash
git add .
git commit -m "Deploy to production"
git push
```

2. **Deploy to Railway**
```bash
railway init
railway up
```

3. **Set Environment Variables** (in Railway dashboard)
```
GROQ_API_KEY=your_groq_api_key
CLERK_SECRET_KEY=your_clerk_secret_key
FRONTEND_URL=https://your-app.vercel.app
```

4. **Set Start Command** (in Railway settings)
```
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### Frontend (Vercel)

1. **Deploy to Vercel**
```bash
cd frontend
vercel
```

2. **Set Environment Variables** (in Vercel dashboard)
```
VITE_API_BASE_URL=https://your-backend.railway.app
VITE_CLERK_PUBLISHABLE_KEY=your_clerk_publishable_key
```

3. **Build Settings**
- Framework Preset: Vite
- Build Command: `npm run build`
- Output Directory: `dist`

## Future Enhancements

**Completed** ✅
- [x] LLM synthesis for answer generation (Groq)
- [x] User authentication (Clerk)
- [x] Document generation (Word documents)
- [x] Multi-tenant data isolation

**Roadmap** 🚀
- [ ] Template library with pre-built legal letters
- [ ] Batch envelope generation from CSV
- [ ] Document version history and tracking
- [ ] Reranking with Cohere for better search results
- [ ] Hybrid search (keyword + semantic)
- [ ] Multi-document chat conversations
- [ ] Fine-tuned embeddings on legal corpus
- [ ] Document highlighting in search results
- [ ] Export search results to PDF
- [ ] Email integration for document sending
- [ ] Calendar integration for deadline tracking

## Security

This repository is **safe for public hosting** and follows security best practices:

### Authentication & Authorization
- **Clerk JWT validation** on all API endpoints
- **Multi-tenant data isolation** - users can only access their own data
- **User-specific folders** for uploads and generated documents
- **User-specific ChromaDB collections** for vector storage

### Secrets Management
- **No hardcoded API keys** - all keys loaded from environment variables
- **`.env` files excluded** from version control via `.gitignore`
- **`.env.example` templates** provided with placeholder values only

### Data Protection
- **User uploads excluded** - `uploads/` directory not tracked
- **Vector database excluded** - `chroma_db/` directory not tracked
- **SQLite databases excluded** - `*.db` files not tracked
- **Generated documents excluded** - `TEMPLATE_*.docx`, `document_*.docx` not tracked

### Best Practices
- All sensitive data stored in environment variables
- JWT tokens validated on every request
- User data isolated per Clerk user ID
- Proper CORS configuration
- Input validation with Pydantic models

## License

MIT

## Author

Built as a portfolio project demonstrating AI-powered document automation with RAG architecture.

Combines legal domain expertise with modern ML engineering to create a production-ready system for law firms.

---

**Resume Keywords**: RAG, vector databases, embeddings, LLM integration, FastAPI, React, TypeScript, semantic search, document automation, ML infrastructure, ChromaDB, Groq AI, Clerk authentication, multi-tenant architecture, python-docx, sentence-transformers, Tailwind CSS, shadcn/ui, JWT authentication, SQLite
