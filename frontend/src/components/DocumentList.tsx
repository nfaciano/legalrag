import { useEffect, useState } from "react";
import { FileText, Trash2, RefreshCw, ScanLine, Eye } from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useApi } from "@/lib/useApi";
import type { DocumentInfo } from "@/types/api";

interface DocumentListProps {
  refreshTrigger: number;
}

export function DocumentList({ refreshTrigger }: DocumentListProps) {
  const apiClient = useApi();
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchDocuments = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await apiClient.listDocuments();
      setDocuments(response.documents);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load documents");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, [refreshTrigger]);

  const handleDelete = async (documentId: string) => {
    if (!confirm("Are you sure you want to delete this document?")) {
      return;
    }

    try {
      await apiClient.deleteDocument(documentId);
      await fetchDocuments();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete document");
    }
  };

  const handleViewText = async (documentId: string) => {
    try {
      const textResponse = await apiClient.getDocumentText(documentId);

      // Open text in new window
      const newWindow = window.open('', '_blank');
      if (newWindow) {
        newWindow.document.write(`
          <!DOCTYPE html>
          <html>
            <head>
              <title>${textResponse.filename} - Extracted Text</title>
              <style>
                body {
                  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                  max-width: 800px;
                  margin: 40px auto;
                  padding: 20px;
                  line-height: 1.6;
                  background: #f5f5f5;
                }
                .header {
                  background: white;
                  padding: 20px;
                  border-radius: 8px;
                  margin-bottom: 20px;
                  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                .header h1 {
                  margin: 0 0 10px 0;
                  color: #333;
                }
                .meta {
                  color: #666;
                  font-size: 14px;
                }
                .warning {
                  background: #fff3cd;
                  border-left: 4px solid #ffc107;
                  padding: 12px;
                  margin: 20px 0;
                  border-radius: 4px;
                }
                .content {
                  background: white;
                  padding: 30px;
                  border-radius: 8px;
                  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                  white-space: pre-wrap;
                  word-wrap: break-word;
                }
              </style>
            </head>
            <body>
              <div class="header">
                <h1>${textResponse.filename}</h1>
                <div class="meta">
                  Document ID: ${textResponse.document_id} |
                  Total Chunks: ${textResponse.total_chunks} |
                  Pages: ${textResponse.total_pages}
                </div>
                ${textResponse.ocr_used ? `
                  <div class="warning">
                    ⚠️ <strong>Scanned Document:</strong> OCR was used on ${textResponse.ocr_pages}/${textResponse.total_pages} pages.
                    Text extraction may not be 100% accurate.
                  </div>
                ` : ''}
              </div>
              <div class="content">${textResponse.full_text.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</div>
            </body>
          </html>
        `);
        newWindow.document.close();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load document text");
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Indexed Documents</CardTitle>
            <CardDescription>
              {documents.length} document{documents.length !== 1 ? "s" : ""} in
              the database
            </CardDescription>
          </div>
          <Button
            variant="outline"
            size="icon"
            onClick={fetchDocuments}
            disabled={isLoading}
          >
            <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {error && (
          <p className="text-sm text-destructive mb-4">{error}</p>
        )}

        {isLoading && documents.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <RefreshCw className="mx-auto h-8 w-8 mb-2 animate-spin" />
            <p>Loading documents...</p>
          </div>
        ) : documents.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <FileText className="mx-auto h-12 w-12 mb-4 opacity-50" />
            <p>No documents indexed yet. Upload one to get started.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {documents.map((doc) => (
              <div
                key={doc.document_id}
                className="flex items-center justify-between p-3 border rounded-lg hover:bg-accent/50 transition-colors"
              >
                <div className="flex items-center gap-3 flex-1 min-w-0">
                  <FileText className="h-5 w-5 text-primary flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <p className="font-medium truncate">{doc.filename}</p>
                      {doc.ocr_used && (
                        <Badge variant="secondary" className="flex-shrink-0 gap-1">
                          <ScanLine className="h-3 w-3" />
                          <span>Scanned</span>
                        </Badge>
                      )}
                    </div>
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      <span>{doc.total_chunks} chunks</span>
                      <span>•</span>
                      <span>
                        {new Date(doc.upload_date).toLocaleDateString()}
                      </span>
                      {doc.ocr_used && doc.ocr_pages && doc.total_pages && (
                        <>
                          <span>•</span>
                          <span>OCR: {doc.ocr_pages}/{doc.total_pages} pages</span>
                        </>
                      )}
                    </div>
                  </div>
                  <Badge variant="outline" className="flex-shrink-0">
                    {doc.document_id.slice(0, 8)}
                  </Badge>
                </div>
                <div className="flex items-center gap-1 ml-2 flex-shrink-0">
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => handleViewText(doc.document_id)}
                    title="View extracted text"
                  >
                    <Eye className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => handleDelete(doc.document_id)}
                    title="Delete document"
                  >
                    <Trash2 className="h-4 w-4 text-destructive" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
