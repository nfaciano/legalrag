# LegalRAG - Semantic Legal Document Search

Full-stack RAG (Retrieval-Augmented Generation) system for semantic search over legal documents. Built with FastAPI, ChromaDB, React, and TypeScript.

![Tech Stack](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white)
![Tailwind](https://img.shields.io/badge/Tailwind-06B6D4?style=for-the-badge&logo=tailwindcss&logoColor=white)

## Features

- **Document Upload**: Drag-and-drop PDF upload with automatic indexing
- **Semantic Search**: Natural language queries over legal documents
- **Vector Search**: Fast similarity search using ChromaDB
- **Source Citations**: Results include filename, page number, and relevance scores
- **Document Management**: List, view, and delete indexed documents
- **Modern UI**: Clean interface with shadcn/ui components
- **Type-Safe**: Full TypeScript coverage on frontend and Python type hints on backend

## Tech Stack

### Backend
- **FastAPI** - Modern async Python web framework
- **ChromaDB** - Open-source vector database
- **sentence-transformers** - Free embedding model (all-MiniLM-L6-v2)
- **PyMuPDF** - Fast PDF text extraction
- **Pydantic** - Data validation

### Frontend
- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Lightning-fast build tool
- **Tailwind CSS** - Utility-first styling
- **shadcn/ui** - High-quality component library
- **Lucide React** - Modern icon set

## Architecture

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   React     │  HTTP   │   FastAPI    │  Store  │  ChromaDB   │
│  Frontend   ├────────>│   Backend    ├────────>│  Vector DB  │
│             │         │              │         │             │
└─────────────┘         └──────────────┘         └─────────────┘
                               │
                               ↓
                        ┌──────────────┐
                        │  sentence-   │
                        │ transformers │
                        │  (embeddings)│
                        └──────────────┘
```

### Data Flow

1. **Upload**: PDF → PyMuPDF (extract text) → Chunk (500 words, 50 overlap)
2. **Embed**: Chunks → sentence-transformers → 384-dim vectors
3. **Store**: Vectors + metadata → ChromaDB
4. **Search**: Query → Embed → Vector similarity → Ranked results

## Quick Start

See [QUICKSTART.md](QUICKSTART.md) for 5-minute setup guide.

### Backend Setup

```bash
cd legalrag
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Backend runs at `http://localhost:8000`

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`

## Project Structure

```
RagLaw/
├── legalrag/           # FastAPI backend
│   ├── app/
│   │   ├── main.py              # API endpoints
│   │   ├── database.py          # ChromaDB integration
│   │   ├── embeddings.py        # Sentence transformers
│   │   ├── document_processor.py # PDF parsing & chunking
│   │   ├── search.py            # Semantic search
│   │   └── models.py            # Pydantic models
│   ├── requirements.txt
│   ├── Dockerfile
│   └── README.md
├── frontend/           # React + TypeScript frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── ui/              # shadcn/ui components
│   │   │   ├── FileUpload.tsx
│   │   │   ├── SearchBar.tsx
│   │   │   ├── SearchResults.tsx
│   │   │   └── DocumentList.tsx
│   │   ├── lib/
│   │   │   ├── api.ts           # API client
│   │   │   └── utils.ts
│   │   ├── types/api.ts
│   │   └── App.tsx
│   ├── package.json
│   └── tailwind.config.js
├── QUICKSTART.md
└── README.md
```

## API Endpoints

### Upload Document
```http
POST /upload
Content-Type: multipart/form-data

Response:
{
  "document_id": "abc123",
  "filename": "contract.pdf",
  "total_chunks": 47,
  "message": "Successfully indexed contract.pdf"
}
```

### Search Documents
```http
POST /search
Content-Type: application/json

{
  "query": "What are the termination clauses?",
  "top_k": 5
}

Response:
{
  "query": "What are the termination clauses?",
  "results": [
    {
      "text": "Either party may terminate...",
      "metadata": {
        "filename": "contract.pdf",
        "page": 12,
        "chunk_id": "abc123_chunk_23"
      },
      "similarity_score": 0.8532
    }
  ]
}
```

### List Documents
```http
GET /documents

Response:
{
  "documents": [...],
  "total_documents": 5
}
```

### Delete Document
```http
DELETE /documents/{document_id}
```

## Example Queries

- "What are the payment terms?"
- "Who are the parties to this agreement?"
- "What are the liability limitations?"
- "When does the contract terminate?"
- "What are the confidentiality requirements?"
- "What are the indemnification clauses?"

## Cost Analysis

| Component | Cost |
|-----------|------|
| Development | $0 (all open-source) |
| Embeddings | $0 (local sentence-transformers) |
| Vector DB | $0 (ChromaDB local) |
| Deployment | $0-5/month (Railway free tier) |
| **Total** | **$0 for MVP** |

Scale to production for <$50/month (Railway + optional Pinecone).

## Performance

- **Embedding Generation**: ~100 chunks/second on CPU
- **Search Latency**: <100ms for typical queries
- **Storage**: ~1KB per chunk (text + embeddings + metadata)
- **Chunk Size**: 500 words with 50-word overlap

## Resume Talking Points

This project demonstrates:

✅ **RAG Architecture** - End-to-end retrieval-augmented generation pipeline
✅ **Vector Databases** - ChromaDB integration with embeddings
✅ **ML Infrastructure** - Production-ready FastAPI backend
✅ **Document Processing** - PDF parsing, chunking, ETL pipelines
✅ **Semantic Search** - Embedding generation and similarity retrieval
✅ **Full-Stack** - Backend + modern React/TypeScript frontend
✅ **Domain Expertise** - Legal document understanding
✅ **Modern Stack** - FastAPI, React, TypeScript, Tailwind, shadcn/ui

## Deployment

### Backend (Railway)

```bash
# Push to GitHub
git init && git add . && git commit -m "Initial commit"

# Deploy to Railway
railway init
railway up
```

### Frontend (Vercel)

```bash
cd frontend
vercel
```

## Future Enhancements

- [ ] Reranking with Cohere for better results
- [ ] LLM synthesis (Claude/GPT) for answer generation
- [ ] Hybrid search (keyword + semantic)
- [ ] Multi-document chat
- [ ] Fine-tuned embeddings on legal corpus
- [ ] User authentication
- [ ] Document highlighting
- [ ] Export results to PDF

## License

MIT

## Author

Built as a portfolio project demonstrating ML infrastructure and full-stack RAG system design.

Combines paralegal domain expertise with modern ML engineering to create a production-ready semantic search system.

---

**Resume Keywords**: RAG, vector databases, embeddings, FastAPI, React, TypeScript, semantic search, document processing, ML infrastructure, ChromaDB, sentence-transformers, Tailwind CSS, shadcn/ui
