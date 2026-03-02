from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
from dotenv import load_dotenv

from app.database import get_vector_db
from app.embeddings import get_embedding_model
from app.document_processor import get_document_processor
from app.routes import (
    documents_router,
    search_router,
    generation_router,
    settings_router,
    cases_router,
)

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="LegalRAG API",
    description="Semantic search over legal documents using RAG",
    version="1.0.0"
)

# Configure CORS
allowed_origins = [
    "http://localhost:5173",
    "http://localhost:3000",
]

frontend_url = os.environ.get("FRONTEND_URL")
if frontend_url:
    allowed_origins.append(frontend_url)
    allowed_origins.append(frontend_url.rstrip("/"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register route modules
app.include_router(documents_router)
app.include_router(search_router)
app.include_router(generation_router)
app.include_router(settings_router)
app.include_router(cases_router)


@app.on_event("startup")
async def startup_event():
    """Initialize models and database on startup."""
    logger.info("Starting up LegalRAG API...")
    get_embedding_model()
    get_vector_db()
    get_document_processor()
    logger.info("Startup complete!")


@app.get("/")
async def root():
    """Health check and API info."""
    db = get_vector_db()
    return {
        "message": "LegalRAG API is running",
        "version": "1.0.0",
        "total_chunks": db.count(),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
