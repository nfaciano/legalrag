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
}

export interface DocumentInfo {
  document_id: string;
  filename: string;
  total_chunks: number;
  upload_date: string;
}

export interface DocumentListResponse {
  documents: DocumentInfo[];
  total_documents: number;
}

export interface DeleteResponse {
  message: string;
  chunks_deleted: number;
}
