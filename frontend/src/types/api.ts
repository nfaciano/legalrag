export interface DocumentMetadata {
  document_id: string;
  filename: string;
  page: number;
  chunk_id: string;
  total_chunks: number;
}

export interface SearchResult {
  text: string;
  metadata: DocumentMetadata;
  similarity_score: number;
}

export interface SearchRequest {
  query: string;
  top_k?: number;
  use_reranking?: boolean;
  synthesize_answer?: boolean;
}

export interface SearchResponse {
  query: string;
  results: SearchResult[];
  total_results: number;
  synthesized_answer?: string | null;
}

export interface UploadResponse {
  document_id: string;
  filename: string;
  total_chunks: number;
  message: string;
  ocr_used?: boolean;
  ocr_pages?: number;
  total_pages?: number;
}

export interface DocumentInfo {
  document_id: string;
  filename: string;
  total_chunks: number;
  upload_date: string;
  ocr_used?: boolean;
  ocr_pages?: number;
  total_pages?: number;
}

export interface DocumentListResponse {
  documents: DocumentInfo[];
  total_documents: number;
}

export interface DeleteResponse {
  message: string;
  chunks_deleted: number;
}

export interface DocumentTextChunk {
  chunk_id: string;
  text: string;
  page: number;
  chunk_index: number;
}

export interface DocumentTextResponse {
  document_id: string;
  filename: string;
  total_chunks: number;
  ocr_used: boolean;
  ocr_pages: number;
  total_pages: number;
  chunks: DocumentTextChunk[];
  full_text: string;
}
