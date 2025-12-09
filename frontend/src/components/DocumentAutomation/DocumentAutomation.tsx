import { useState, useEffect } from 'react';
import { useApi } from '../../lib/useApi';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Textarea } from '../ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Alert, AlertDescription } from '../ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Upload, FileText, Trash2, Loader2, FileCheck, Sparkles, Edit3 } from 'lucide-react';
import type {
  LetterheadInfo,
  LetterheadListResponse,
  LetterheadUploadResponse,
  DocumentGenerationRequest,
  GeneratedDocumentResponse
} from '../../types/api';

// Helper function to get settings from API
// Note: This needs apiClient, so we'll make it a method inside the component

const getTodaysDate = () => {
  const today = new Date();
  return today.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });
};

export function DocumentAutomation() {
  const apiClient = useApi();

  // Letterhead state
  const [letterheads, setLetterheads] = useState<LetterheadInfo[]>([]);
  const [selectedLetterhead, setSelectedLetterhead] = useState<string>('');
  const [uploadingLetterhead, setUploadingLetterhead] = useState(false);

  // Document generation state
  const [generating, setGenerating] = useState(false);
  const [formData, setFormData] = useState<DocumentGenerationRequest>({
    date: getTodaysDate(),
    recipient_name: '',
    recipient_company: '',
    recipient_address: '',
    subject: '',
    salutation: '',
    body_text: '',
    closing: 'Very truly yours,',
    signature_name: '',
    initials: '',
    enclosures: '',
    ai_generate_body: false,
    ai_prompt: ''
  });

  // AI Quick Mode state
  const [aiQuickPrompt, setAiQuickPrompt] = useState<string>('');

  // UI state
  const [error, setError] = useState<string>('');
  const [success, setSuccess] = useState<string>('');

  // Get user settings from API
  const getUserSettings = async () => {
    try {
      const response: any = await apiClient.get('/user-settings');
      return {
        signature_name: response.settings.signature_name || '',
        initials: response.settings.initials || '',
        closing: response.settings.closing || 'Very truly yours,'
      };
    } catch (e) {
      console.error('Failed to load user settings:', e);
      return {
        signature_name: '',
        initials: '',
        closing: 'Very truly yours,'
      };
    }
  };

  // Load settings and populate formData
  useEffect(() => {
    const loadSettings = async () => {
      const settings = await getUserSettings();
      setFormData(prev => ({
        ...prev,
        closing: settings.closing,
        signature_name: settings.signature_name,
        initials: settings.initials
      }));
    };
    loadSettings();
  }, []);

  // Load letterheads on mount
  useEffect(() => {
    loadLetterheads();
  }, []);

  const loadLetterheads = async () => {
    try {
      const data = await apiClient.get<LetterheadListResponse>('/templates');
      setLetterheads(data.letterheads);
      if (data.letterheads.length > 0 && !selectedLetterhead) {
        setSelectedLetterhead(data.letterheads[0].letterhead_id);
      }
    } catch (err: any) {
      console.error('Error loading letterheads:', err);
    }
  };

  const handleLetterheadUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setError('');
    setSuccess('');
    setUploadingLetterhead(true);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const data = await apiClient.upload<LetterheadUploadResponse>('/templates', formData);

      setSuccess(`Template uploaded successfully: ${data.original_filename}`);
      await loadLetterheads();

      // Auto-select the newly uploaded template
      setSelectedLetterhead(data.letterhead_id);
    } catch (err: any) {
      setError(err.message || 'Failed to upload template');
    } finally {
      setUploadingLetterhead(false);
      e.target.value = ''; // Reset file input
    }
  };

  const handleDeleteLetterhead = async (letterheadId: string) => {
    if (!confirm('Are you sure you want to delete this letterhead?')) return;

    try {
      await apiClient.delete(`/templates/${letterheadId}`);
      setSuccess('Letterhead deleted successfully');
      await loadLetterheads();

      if (selectedLetterhead === letterheadId) {
        setSelectedLetterhead('');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to delete letterhead');
    }
  };

  const handleGenerateDocument = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    // Validation
    if (!formData.ai_generate_body && !formData.body_text) {
      setError('Please provide body text or enable AI generation');
      return;
    }

    if (formData.ai_generate_body && !formData.ai_prompt) {
      setError('Please provide an AI prompt');
      return;
    }

    setGenerating(true);

    try {
      const request: DocumentGenerationRequest = {
        ...formData,
        letterhead_id: selectedLetterhead || null,
        recipient_company: formData.recipient_company || null,
        subject: formData.subject || null,
        enclosures: formData.enclosures || null,
        body_text: formData.ai_generate_body ? null : formData.body_text,
        ai_prompt: formData.ai_generate_body ? formData.ai_prompt : null
      };

      const response = await apiClient.post<GeneratedDocumentResponse>(
        '/generate-document',
        request
      );

      setSuccess(`Document generated successfully: ${response.filename}`);

      // Auto-download the generated document
      handleDownloadDocument(response.document_id);
    } catch (err: any) {
      setError(err.message || 'Failed to generate document');
    } finally {
      setGenerating(false);
    }
  };

  const handleAiQuickGenerate = async () => {
    if (!selectedLetterhead || !aiQuickPrompt.trim()) {
      setError('Please select a template and enter your request');
      return;
    }

    setError('');
    setSuccess('');
    setGenerating(true);

    try {
      const settings = await getUserSettings();

      const requestBody: DocumentGenerationRequest = {
        letterhead_id: selectedLetterhead,
        date: getTodaysDate(),
        recipient_name: '',
        recipient_company: '',
        recipient_address: '',
        subject: '',
        salutation: '',
        body_text: '',
        closing: settings.closing,
        signature_name: settings.signature_name,
        initials: settings.initials,
        enclosures: '',
        ai_generate_body: true,
        ai_prompt: aiQuickPrompt
      };

      const response = await apiClient.post<GeneratedDocumentResponse>(
        '/generate-document',
        requestBody
      );

      setSuccess('Document generated successfully!');
      setAiQuickPrompt('');

      // Auto-download
      handleDownloadDocument(response.document_id);
    } catch (err: any) {
      setError(err.message || 'Failed to generate document with AI');
    } finally {
      setGenerating(false);
    }
  };

  const handleDownloadDocument = async (documentId: string) => {
    try {
      const url = `${apiClient.baseURL}/generated-documents/${documentId}`;
      const token = await apiClient.getToken();

      const response = await fetch(url, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Download failed');
      }

      // Extract filename from Content-Disposition header
      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = `document_${documentId}.docx`; // default to .docx
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/);
        if (filenameMatch && filenameMatch[1]) {
          filename = filenameMatch[1];
        }
      }

      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = downloadUrl;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(downloadUrl);
      document.body.removeChild(a);
    } catch (err: any) {
      setError('Failed to download document');
    }
  };

  return (
    <div className="space-y-6">
      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {success && (
        <Alert>
          <FileCheck className="h-4 w-4" />
          <AlertDescription>{success}</AlertDescription>
        </Alert>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Template Management Sidebar */}
        <div className="lg:col-span-1 space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Upload className="h-5 w-5" />
                Templates
              </CardTitle>
              <CardDescription>Manage your letterhead templates</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="letterhead-upload" className="cursor-pointer">
                  <div className="border-2 border-dashed rounded-lg p-4 text-center hover:border-primary/50 transition-all hover:bg-primary/5">
                    {uploadingLetterhead ? (
                      <Loader2 className="h-6 w-6 mx-auto animate-spin text-muted-foreground" />
                    ) : (
                      <>
                        <Upload className="h-6 w-6 mx-auto text-muted-foreground mb-2" />
                        <p className="text-xs text-muted-foreground font-medium">
                          Upload .docx
                        </p>
                      </>
                    )}
                  </div>
                  <Input
                    id="letterhead-upload"
                    type="file"
                    accept=".docx"
                    onChange={handleLetterheadUpload}
                    className="hidden"
                    disabled={uploadingLetterhead}
                  />
                </Label>
              </div>

              {letterheads.length > 0 && (
                <div className="space-y-2">
                  <Label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Saved Templates ({letterheads.length})
                  </Label>
                  <div className="space-y-1 max-h-60 overflow-y-auto">
                    {letterheads.map((lh) => (
                      <div
                        key={lh.letterhead_id}
                        className={`group flex items-center justify-between p-3 border-2 rounded-lg transition-all ${
                          selectedLetterhead === lh.letterhead_id
                            ? 'border-primary bg-primary/5 shadow-sm'
                            : 'border-border hover:border-primary/30 hover:bg-muted/50'
                        }`}
                      >
                        <button
                          onClick={() => setSelectedLetterhead(lh.letterhead_id)}
                          className="flex-1 text-left"
                        >
                          <div className="flex items-center gap-2">
                            <FileText className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                            <span className="text-sm font-medium truncate">
                              {lh.original_filename}
                            </span>
                          </div>
                        </button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDeleteLetterhead(lh.letterhead_id)}
                          className="opacity-0 group-hover:opacity-100 transition-opacity"
                        >
                          <Trash2 className="h-3.5 w-3.5 text-destructive" />
                        </Button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {letterheads.length === 0 && (
                <p className="text-xs text-muted-foreground text-center py-4">
                  No templates uploaded yet
                </p>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Main Generation Area with Tabs */}
        <div className="lg:col-span-3">
          <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              Generate Document
            </CardTitle>
            <CardDescription>Choose how you want to generate your document</CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="ai" className="w-full">
              <TabsList className="grid w-full grid-cols-2 mb-6">
                <TabsTrigger value="ai" className="flex items-center gap-2">
                  <Sparkles className="h-4 w-4" />
                  AI Quick
                </TabsTrigger>
                <TabsTrigger value="manual" className="flex items-center gap-2">
                  <Edit3 className="h-4 w-4" />
                  Manual Form
                </TabsTrigger>
              </TabsList>

              {/* AI Quick Mode */}
              <TabsContent value="ai" className="space-y-4">
                <div className="bg-gradient-to-br from-blue-50 to-violet-50 dark:from-blue-950/20 dark:to-violet-950/20 rounded-lg p-4 border-2 border-dashed border-blue-200 dark:border-blue-800">
                  <div className="flex items-start gap-3 mb-3">
                    <Sparkles className="h-5 w-5 text-blue-600 mt-0.5" />
                    <div>
                      <h4 className="font-semibold text-sm mb-1">AI Quick Generate</h4>
                      <p className="text-xs text-muted-foreground">
                        Paste all information in natural language and let AI parse it
                      </p>
                    </div>
                  </div>
                  <div className="bg-white dark:bg-slate-900 rounded p-2 text-xs text-muted-foreground font-mono">
                    Example: "Draft a cover letter to John Smith at 123 Main St, New York, NY 10001 telling them enclosed they'll find the signed contract and payment receipt."
                  </div>
                </div>

                <div className="space-y-3">
                  <Label htmlFor="ai-prompt">Your Request</Label>
                  <Textarea
                    id="ai-prompt"
                    placeholder="Example: I want to draft a letter to Jane Doe at ABC Law Firm, 456 Legal Blvd, Los Angeles, CA addressed to her as Managing Partner informing her that we've enclosed the requested discovery documents..."
                    value={aiQuickPrompt}
                    onChange={(e) => setAiQuickPrompt(e.target.value)}
                    className="min-h-[200px] resize-none"
                  />
                  <Button
                    onClick={handleAiQuickGenerate}
                    disabled={!selectedLetterhead || !aiQuickPrompt.trim() || generating}
                    className="w-full bg-gradient-to-r from-blue-600 to-violet-600 hover:from-blue-700 hover:to-violet-700"
                  >
                    {generating ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Generating...
                      </>
                    ) : (
                      <>
                        <Sparkles className="mr-2 h-4 w-4" />
                        Generate with AI
                      </>
                    )}
                  </Button>
                  {!selectedLetterhead && (
                    <p className="text-xs text-muted-foreground text-center">
                      Please select a template first
                    </p>
                  )}
                </div>
              </TabsContent>

              {/* Manual Form Mode */}
              <TabsContent value="manual" className="space-y-4">
            <form onSubmit={handleGenerateDocument} className="space-y-4">
              <div className="space-y-3 mb-4 p-3 bg-slate-50 dark:bg-slate-900 rounded-lg">
                <p className="text-sm text-muted-foreground">
                  📅 Date is automatically set to today: <span className="font-medium text-foreground">{getTodaysDate()}</span>
                </p>
                <p className="text-sm text-muted-foreground">
                  ⚙️ Signature settings are configured in Settings
                </p>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="initials">Initials</Label>
                  <Input
                    id="initials"
                    value={formData.initials}
                    onChange={(e) => setFormData({ ...formData, initials: e.target.value })}
                    placeholder="ABC/xyz"
                    required
                  />
                </div>
              </div>

              <div>
                <Label htmlFor="recipient_name">Recipient Name</Label>
                <Input
                  id="recipient_name"
                  value={formData.recipient_name}
                  onChange={(e) => setFormData({ ...formData, recipient_name: e.target.value })}
                  required
                />
              </div>

              <div>
                <Label htmlFor="recipient_company">Recipient Company (Optional)</Label>
                <Input
                  id="recipient_company"
                  value={formData.recipient_company || ''}
                  onChange={(e) => setFormData({ ...formData, recipient_company: e.target.value })}
                />
              </div>

              <div>
                <Label htmlFor="recipient_address">Recipient Address</Label>
                <Textarea
                  id="recipient_address"
                  value={formData.recipient_address}
                  onChange={(e) => setFormData({ ...formData, recipient_address: e.target.value })}
                  rows={3}
                  required
                />
              </div>

              <div>
                <Label htmlFor="subject">Subject (Optional)</Label>
                <Input
                  id="subject"
                  value={formData.subject || ''}
                  onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
                  placeholder="Re: Case Name"
                />
              </div>

              <div>
                <Label htmlFor="salutation">Salutation</Label>
                <Input
                  id="salutation"
                  value={formData.salutation}
                  onChange={(e) => setFormData({ ...formData, salutation: e.target.value })}
                  placeholder="Dear Mr. Smith:"
                  required
                />
              </div>

              <div>
                <div className="flex items-center gap-2 mb-2">
                  <input
                    type="checkbox"
                    id="ai_generate"
                    checked={formData.ai_generate_body}
                    onChange={(e) =>
                      setFormData({ ...formData, ai_generate_body: e.target.checked })
                    }
                    className="rounded"
                  />
                  <Label htmlFor="ai_generate" className="cursor-pointer">
                    Generate body with AI
                  </Label>
                </div>

                {formData.ai_generate_body ? (
                  <Textarea
                    id="ai_prompt"
                    value={formData.ai_prompt || ''}
                    onChange={(e) => setFormData({ ...formData, ai_prompt: e.target.value })}
                    placeholder="Describe what the letter should say..."
                    rows={4}
                    required={formData.ai_generate_body}
                  />
                ) : (
                  <Textarea
                    id="body_text"
                    value={formData.body_text || ''}
                    onChange={(e) => setFormData({ ...formData, body_text: e.target.value })}
                    placeholder="Enter the letter body..."
                    rows={6}
                    required={!formData.ai_generate_body}
                  />
                )}
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="closing">Closing</Label>
                  <Input
                    id="closing"
                    value={formData.closing}
                    onChange={(e) => setFormData({ ...formData, closing: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="signature_name">Signature Name</Label>
                  <Input
                    id="signature_name"
                    value={formData.signature_name}
                    onChange={(e) => setFormData({ ...formData, signature_name: e.target.value })}
                    required
                  />
                </div>
              </div>

              <div>
                <Label htmlFor="enclosures">Enclosures (Optional)</Label>
                <Input
                  id="enclosures"
                  value={formData.enclosures || ''}
                  onChange={(e) => setFormData({ ...formData, enclosures: e.target.value })}
                  placeholder="Enc:"
                />
              </div>

              <Button type="submit" disabled={generating} className="w-full">
                {generating ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <FileText className="mr-2 h-4 w-4" />
                    Generate Document
                  </>
                )}
              </Button>
            </form>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
        </div>
      </div>
    </div>
  );
}
