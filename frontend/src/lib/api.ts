import type {
  SearchRequest,
  SearchResponse,
  UploadResponse,
  DocumentListResponse,
  DeleteResponse,
} from "@/types/api";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  async uploadDocument(file: File): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${this.baseUrl}/upload`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Upload failed: ${error}`);
    }

    return response.json();
  }

  async searchDocuments(request: SearchRequest): Promise<SearchResponse> {
    const response = await fetch(`${this.baseUrl}/search`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Search failed: ${error}`);
    }

    return response.json();
  }

  async listDocuments(): Promise<DocumentListResponse> {
    const response = await fetch(`${this.baseUrl}/documents`);

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Failed to list documents: ${error}`);
    }

    return response.json();
  }

  async deleteDocument(documentId: string): Promise<DeleteResponse> {
    const response = await fetch(`${this.baseUrl}/documents/${documentId}`, {
      method: "DELETE",
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Failed to delete document: ${error}`);
    }

    return response.json();
  }
}

// Export singleton instance
export const apiClient = new ApiClient();
