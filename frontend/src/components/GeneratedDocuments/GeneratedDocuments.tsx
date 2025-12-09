import { useState, useEffect } from 'react';
import { useApi } from '@/lib/useApi';
import { Button } from '../ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Alert, AlertDescription } from '../ui/alert';
import { FileText, Download, Trash2, AlertCircle, Loader2 } from 'lucide-react';
import type { GeneratedDocumentListResponse } from '@/types/api';

export function GeneratedDocuments() {
  const apiClient = useApi();
  const [documents, setDocuments] = useState<GeneratedDocumentListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState<string | null>(null);
  const [error, setError] = useState<string>('');
  const [success, setSuccess] = useState<string>('');

  useEffect(() => {
    loadDocuments();
  }, []);

  const loadDocuments = async () => {
    try {
      const data = await apiClient.get<GeneratedDocumentListResponse>('/generated-documents');
      setDocuments(data);
    } catch (err: any) {
      console.error('Error loading documents:', err);
      setError('Failed to load documents');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async (documentId: string) => {
    try {
      const url = `${apiClient.baseURL}/generated-documents/${documentId}`;
      const token = await apiClient.getToken();

      const response = await fetch(url, {
        headers: {
          ...(token ? { Authorization: `Bearer ${token}` } : {})
        }
      });

      if (!response.ok) throw new Error('Download failed');

      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = downloadUrl;

      // Get filename from Content-Disposition header
      const contentDisposition = response.headers.get('Content-Disposition');
      const filenameMatch = contentDisposition?.match(/filename="?(.+)"?/);
      a.download = filenameMatch?.[1] || 'document.pdf';

      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(downloadUrl);
      document.body.removeChild(a);
    } catch (err: any) {
      console.error('Download error:', err);
      setError('Failed to download document');
    }
  };

  const handleDelete = async (documentId: string) => {
    if (!confirm('Are you sure you want to delete this document?')) return;

    setDeleting(documentId);
    setError('');

    try {
      await apiClient.delete(`/generated-documents/${documentId}`);
      setSuccess('Document deleted successfully');
      setTimeout(() => setSuccess(''), 3000);
      await loadDocuments();
    } catch (err: any) {
      console.error('Delete error:', err);
      setError('Failed to delete document');
    } finally {
      setDeleting(null);
    }
  };

  const handleDeleteAll = async () => {
    if (!confirm('Are you sure you want to delete ALL documents? This cannot be undone.')) return;

    setError('');

    try {
      await apiClient.delete('/generated-documents');
      setSuccess('All documents deleted successfully');
      setTimeout(() => setSuccess(''), 3000);
      await loadDocuments();
    } catch (err: any) {
      console.error('Delete all error:', err);
      setError('Failed to delete documents');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {success && (
        <Alert className="bg-green-50 border-green-200">
          <AlertDescription className="text-green-800">{success}</AlertDescription>
        </Alert>
      )}

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                Generated Documents
                {documents && documents.documents.length > 0 && (
                  <span className="text-sm font-normal text-muted-foreground">
                    ({documents.documents.length})
                  </span>
                )}
              </CardTitle>
              <CardDescription>
                View, download, and manage your generated documents
              </CardDescription>
            </div>
            {documents && documents.documents.length > 0 && (
              <Button
                variant="outline"
                size="sm"
                onClick={handleDeleteAll}
                className="text-red-600 hover:text-red-700 hover:bg-red-50"
              >
                <Trash2 className="h-4 w-4 mr-2" />
                Delete All
              </Button>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {!documents || documents.documents.length === 0 ? (
            <div className="text-center py-12">
              <FileText className="h-12 w-12 text-muted-foreground mx-auto mb-4 opacity-50" />
              <p className="text-muted-foreground mb-2">No generated documents yet</p>
              <p className="text-sm text-muted-foreground">
                Documents you generate will appear here
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              {documents.documents.map((doc) => (
                <div
                  key={doc.document_id}
                  className="flex items-center justify-between p-4 border rounded-lg hover:bg-slate-50 dark:hover:bg-slate-900 transition-colors"
                >
                  <div className="flex-1 min-w-0">
                    <p className="font-medium truncate">{doc.filename}</p>
                    <p className="text-sm text-muted-foreground">
                      {new Date(doc.generated_at).toLocaleString()} • {(doc.file_size / 1024).toFixed(1)} KB
                    </p>
                  </div>
                  <div className="flex gap-2 ml-4">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleDownload(doc.document_id)}
                    >
                      <Download className="h-4 w-4 mr-1" />
                      Download
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleDelete(doc.document_id)}
                      disabled={deleting === doc.document_id}
                      className="text-red-600 hover:text-red-700 hover:bg-red-50"
                    >
                      {deleting === doc.document_id ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Trash2 className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Info Box */}
      <Card className="bg-slate-50 dark:bg-slate-900">
        <CardContent className="pt-6">
          <div className="flex gap-3">
            <FileText className="h-5 w-5 text-muted-foreground flex-shrink-0 mt-0.5" />
            <div className="space-y-2">
              <p className="text-sm font-medium">About Generated Documents</p>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>• Documents are stored securely in your account</li>
                <li>• Download documents to save them permanently to your device</li>
                <li>• Delete documents you no longer need to save space</li>
                <li>• All documents include your letterhead and formatting</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
