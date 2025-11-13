# LegalRAG - Semantic Legal Document Search

A production-ready RAG (Retrieval-Augmented Generation) system for semantic search over legal documents. Built with FastAPI, ChromaDB, and sentence-transformers.

## Features

- **PDF Document Upload**: Process and index legal PDFs automatically
- **Semantic Search**: Natural language queries over your document corpus
- **Vector Search**: Fast similarity search using ChromaDB
- **Local Embeddings**: Free sentence-transformers (no API costs)
- **Document Management**: List and delete indexed documents
- **Production Ready**: Async FastAPI with proper error handling and logging

## Architecture

```
User uploads PDF → PDF Parser (PyMuPDF) → Text Chunker (500 words, 50 overlap)
                                              ↓
                            Sentence Transformer (all-MiniLM-L6-v2)
                                              ↓
                                    ChromaDB Vector Store
                                              ↓
User query → Embed query → Vector search → Ranked results with citations
```

## Tech Stack

- **FastAPI**: Modern async Python web framework
- **ChromaDB**: Open-source vector database (local, persistent)
- **sentence-transformers**: Free embedding model (all-MiniLM-L6-v2)
- **PyMuPDF**: Fast PDF text extraction
- **Pydantic**: Data validation and serialization

## Installation

### Prerequisites
- Python 3.9+
- pip

### Setup

```bash
# Clone or navigate to project
cd legalrag

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Start the Server

```bash
# From legalrag directory
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

Interactive API docs: `http://localhost:8000/docs`

### API Endpoints

#### 1. Upload Document

```bash
curl -X POST "http://localhost:8000/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/contract.pdf"
```

Response:
```json
{
  "document_id": "a1b2c3d4e5f6",
  "filename": "contract.pdf",
  "total_chunks": 47,
  "message": "Successfully indexed contract.pdf into 47 chunks"
}
```

#### 2. Search Documents

```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the termination clauses?",
    "top_k": 5
  }'
```

Response:
```json
{
  "query": "What are the termination clauses?",
  "results": [
    {
      "text": "Either party may terminate this agreement...",
      "metadata": {
        "document_id": "a1b2c3d4e5f6",
        "filename": "contract.pdf",
        "page": 12,
        "chunk_id": "a1b2c3d4e5f6_chunk_23"
      },
      "similarity_score": 0.8532
    }
  ],
  "total_results": 5
}
```

#### 3. List Documents

```bash
curl -X GET "http://localhost:8000/documents"
```

#### 4. Delete Document

```bash
curl -X DELETE "http://localhost:8000/documents/a1b2c3d4e5f6"
```

## Project Structure

```
legalrag/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app and endpoints
│   ├── models.py            # Pydantic data models
│   ├── database.py          # ChromaDB vector database
│   ├── embeddings.py        # Sentence transformer wrapper
│   ├── document_processor.py # PDF parsing and chunking
│   └── search.py            # Semantic search logic
├── uploads/                 # Temporary PDF storage
├── chroma_db/              # ChromaDB persistent storage
├── requirements.txt
├── Dockerfile
└── README.md
```

## How It Works

### 1. Document Upload
1. User uploads PDF via `/upload` endpoint
2. PyMuPDF extracts text from each page
3. Text is split into 500-word chunks with 50-word overlap
4. Each chunk is embedded using sentence-transformers (384-dim vectors)
5. Chunks + embeddings + metadata stored in ChromaDB

### 2. Search
1. User sends natural language query to `/search`
2. Query is embedded using the same model
3. ChromaDB performs vector similarity search (cosine similarity)
4. Top K most similar chunks returned with metadata (filename, page, score)

## Configuration

Edit `app/document_processor.py` to customize chunking:

```python
DocumentProcessor(
    chunk_size=500,      # Words per chunk
    chunk_overlap=50     # Overlap between chunks
)
```

Edit `app/embeddings.py` to use a different model:

```python
EmbeddingModel(model_name="all-MiniLM-L6-v2")
# Alternatives: "all-mpnet-base-v2", "e5-large-v2"
```

## Deployment

### Docker

```bash
# Build image
docker build -t legalrag .

# Run container
docker run -p 8000:8000 -v $(pwd)/chroma_db:/app/chroma_db legalrag
```

### Railway / Render / Fly.io

1. Push to GitHub
2. Connect repo to platform
3. Set start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Deploy

## Example Use Cases

- **Contract Analysis**: "What are the payment terms?"
- **Legal Research**: "Find cases about intellectual property disputes"
- **Due Diligence**: "What liability clauses exist?"
- **Compliance**: "What are the data privacy requirements?"

## Performance

- **Embedding Generation**: ~100 chunks/second on CPU
- **Search Latency**: <100ms for typical queries
- **Storage**: ~1KB per chunk (text + embeddings + metadata)

## Limitations & Future Improvements

### Current Limitations
- PDF-only (no .docx, .txt yet)
- Simple chunking (doesn't preserve document structure)
- No reranking (could add Cohere rerank for better results)
- No LLM synthesis (returns raw chunks, not generated answers)

### Potential Enhancements
- Add reranking model for better result quality
- Integrate with Claude/GPT for answer synthesis
- Support more file formats (.docx, .txt, .html)
- Add hybrid search (keyword + semantic)
- Implement user authentication
- Add caching for common queries
- Fine-tune embeddings on legal corpus

## Cost Analysis

- **Development**: $0 (all open-source)
- **Running locally**: $0
- **Deployment**: $0-5/month (Railway free tier or AWS free tier)
- **Embeddings**: $0 (sentence-transformers runs locally)
- **Vector DB**: $0 (ChromaDB is free)

**Total**: $0 for MVP, scalable to production for <$50/month

## Resume Talking Points

This project demonstrates:
- **RAG Architecture**: End-to-end retrieval-augmented generation pipeline
- **Vector Databases**: ChromaDB integration with embeddings and similarity search
- **ML Infrastructure**: Production-ready FastAPI backend with async operations
- **Document Processing**: PDF parsing, text chunking, and ETL pipelines
- **Semantic Search**: Embedding generation and vector similarity retrieval
- **Domain Expertise**: Legal document understanding (leverage paralegal background)

## License

MIT

## Author

Built as a portfolio project demonstrating ML infrastructure and RAG system design.
