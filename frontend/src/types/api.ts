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

// Document Generation Types

export interface LetterheadInfo {
  letterhead_id: string;
  original_filename: string;
  file_size: number;
  upload_date: string;
}

export interface LetterheadUploadResponse {
  letterhead_id: string;
  original_filename: string;
  file_size: number;
  upload_date: string;
}

export interface LetterheadListResponse {
  letterheads: LetterheadInfo[];
  total_letterheads: number;
}

export interface DocumentGenerationRequest {
  letterhead_id?: string | null;
  document_type?: string;

  // Letter fields
  date: string;
  recipient_name: string;
  recipient_company?: string | null;
  recipient_address: string;
  subject?: string | null;
  salutation: string;
  body_text?: string | null;
  closing?: string;
  signature_name: string;
  initials: string;
  enclosures?: string | null;

  // AI generation fields
  ai_generate_body?: boolean;
  ai_prompt?: string | null;
}

export interface GeneratedDocumentResponse {
  document_id: string;
  filename: string;
  file_size: number;
  generated_at: string;
  download_url: string;
}

export interface GeneratedDocumentInfo {
  document_id: string;
  filename: string;
  file_size: number;
  generated_at: string;
}

export interface GeneratedDocumentListResponse {
  documents: GeneratedDocumentInfo[];
  total_documents: number;
}

// ============================================================================
// Case & Court Pleading Types
// ============================================================================

export interface CaseInfo {
  case_id: string;
  case_name: string;
  case_number: string;
  court_name: string;
  court_location: string;
  plaintiff_names: string[];
  defendant_names: string[];
  plaintiff_label: string;
  file_reference: string;
  created_at: string;
  updated_at: string;
}

export interface CaseCreateRequest {
  case_name: string;
  case_number: string;
  court_name: string;
  court_location?: string;
  plaintiff_names: string[];
  defendant_names: string[];
  plaintiff_label?: string;
  file_reference?: string;
}

export interface CaseListResponse {
  cases: CaseInfo[];
  total_cases: number;
}

export interface PleadingGenerationRequest {
  case_id: string;
  document_title: string;
  body_text?: string | null;
  body_paragraphs?: string[] | null;
  representing_party: string;
  attorney_capacity?: string;
  include_certification?: boolean;
  certification_date?: string | null;
  filing_method?: string;
  service_method?: string;
  service_list?: string[] | null;
  ai_generate_body?: boolean;
  ai_prompt?: string | null;
}

export interface PleadingResponse {
  document_id: string;
  filename: string;
  file_size: number;
  generated_at: string;
  download_url: string;
}
