import type {
  SearchRequest,
  SearchResponse,
  UploadResponse,
  DocumentListResponse,
  DeleteResponse,
  DocumentTextResponse,
} from "@/types/api";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export class ApiClient {
  public baseURL: string;
  private getTokenFn?: () => Promise<string | null>;

  constructor(baseUrl: string = API_BASE_URL, getToken?: () => Promise<string | null>) {
    this.baseURL = baseUrl;
    this.getTokenFn = getToken;
  }

  async getToken(): Promise<string | null> {
    if (this.getTokenFn) {
      return await this.getTokenFn();
    }
    return null;
  }

  private async getHeaders(includeContentType = false): Promise<HeadersInit> {
    const headers: HeadersInit = {};

    if (includeContentType) {
      headers["Content-Type"] = "application/json";
    }

    if (this.getTokenFn) {
      const token = await this.getTokenFn();
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }
    }

    return headers;
  }

  // Generic HTTP methods
  async get<T>(path: string): Promise<T> {
    const headers = await this.getHeaders();
    const response = await fetch(`${this.baseURL}${path}`, { headers });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`GET ${path} failed: ${error}`);
    }

    return response.json();
  }

  async post<T>(path: string, data: any): Promise<T> {
    const headers = await this.getHeaders(true);
    const response = await fetch(`${this.baseURL}${path}`, {
      method: "POST",
      headers,
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`POST ${path} failed: ${error}`);
    }

    return response.json();
  }

  async put<T>(path: string, data: any): Promise<T> {
    const headers = await this.getHeaders(true);
    const response = await fetch(`${this.baseURL}${path}`, {
      method: "PUT",
      headers,
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`PUT ${path} failed: ${error}`);
    }

    return response.json();
  }

  async upload<T>(path: string, formData: FormData): Promise<T> {
    const headers = await this.getHeaders();
    const response = await fetch(`${this.baseURL}${path}`, {
      method: "POST",
      headers,
      body: formData,
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Upload to ${path} failed: ${error}`);
    }

    return response.json();
  }

  async delete(path: string): Promise<any> {
    const headers = await this.getHeaders();
    const response = await fetch(`${this.baseURL}${path}`, {
      method: "DELETE",
      headers,
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`DELETE ${path} failed: ${error}`);
    }

    return response.json();
  }

  async downloadFile(path: string): Promise<Response> {
    const headers = await this.getHeaders();
    const response = await fetch(`${this.baseURL}${path}`, {
      method: "GET",
      headers,
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Download from ${path} failed: ${error}`);
    }

    return response;
  }

  async uploadDocument(file: File): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append("file", file);

    const headers = await this.getHeaders();

    const response = await fetch(`${this.baseURL}/upload`, {
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

    const response = await fetch(`${this.baseURL}/search`, {
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

    const response = await fetch(`${this.baseURL}/documents`, {
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

    const response = await fetch(`${this.baseURL}/documents/${documentId}`, {
      method: "DELETE",
      headers,
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Failed to delete document: ${error}`);
    }

    return response.json();
  }

  async getDocumentText(documentId: string): Promise<DocumentTextResponse> {
    const headers = await this.getHeaders();

    const response = await fetch(`${this.baseURL}/documents/${documentId}/text`, {
      headers,
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Failed to get document text: ${error}`);
    }

    return response.json();
  }
}

// Export singleton instance
export const apiClient = new ApiClient();
