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
  private getToken?: () => Promise<string | null>;

  constructor(baseUrl: string = API_BASE_URL, getToken?: () => Promise<string | null>) {
    this.baseUrl = baseUrl;
    this.getToken = getToken;
  }

  private async getHeaders(includeContentType = false): Promise<HeadersInit> {
    const headers: HeadersInit = {};

    if (includeContentType) {
      headers["Content-Type"] = "application/json";
    }

    if (this.getToken) {
      const token = await this.getToken();
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }
    }

    return headers;
  }

  async uploadDocument(file: File): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append("file", file);

    const headers = await this.getHeaders();

    const response = await fetch(`${this.baseUrl}/upload`, {
      method: "POST",
      headers,
      body: formData,
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Upload failed: ${error}`);
    }

    return response.json();
  }

  async searchDocuments(request: SearchRequest): Promise<SearchResponse> {
    const headers = await this.getHeaders(true);

    const response = await fetch(`${this.baseUrl}/search`, {
      method: "POST",
      headers,
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Search failed: ${error}`);
    }

    return response.json();
  }

  async listDocuments(): Promise<DocumentListResponse> {
    const headers = await this.getHeaders();

    const response = await fetch(`${this.baseUrl}/documents`, {
      headers,
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Failed to list documents: ${error}`);
    }

    return response.json();
  }

  async deleteDocument(documentId: string): Promise<DeleteResponse> {
    const headers = await this.getHeaders();

    const response = await fetch(`${this.baseUrl}/documents/${documentId}`, {
      method: "DELETE",
      headers,
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
