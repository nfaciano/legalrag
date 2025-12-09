import { useState } from 'react';
import { useApi } from '@/lib/useApi';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Textarea } from '../ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Alert, AlertDescription } from '../ui/alert';
import { Mail, Loader2, Sparkles, FileCheck } from 'lucide-react';

export function EnvelopeGeneration() {
  const apiClient = useApi();

  // Envelope generation state
  const [envelopePrompt, setEnvelopePrompt] = useState<string>('');
  const [recipient, setRecipient] = useState({
    name: '',
    line1: '',
    line2: '',
    city_state_zip: ''
  });

  // UI state
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string>('');
  const [success, setSuccess] = useState<string>('');

  // Get return address from settings API
  const getReturnAddress = async () => {
    try {
      const response: any = await apiClient.get('/user-settings');
      return {
        name: response.settings.return_address_name || '',
        line1: response.settings.return_address_line1 || '',
        line2: response.settings.return_address_line2 || '',
        city_state_zip: response.settings.return_address_city_state_zip || ''
      };
    } catch (e) {
      console.error('Failed to load return address:', e);
      return { name: '', line1: '', line2: '', city_state_zip: '' };
    }
  };

  const handleGenerateEnvelopeAI = async () => {
    setError('');
    setSuccess('');
    setGenerating(true);

    try {
      const returnAddress = await getReturnAddress();

      // Check if return address is configured
      if (!returnAddress.name || !returnAddress.line1) {
        setError('Please configure your return address in Settings first');
        setGenerating(false);
        return;
      }

      const requestBody = {
        return_address: returnAddress,
        ai_prompt: envelopePrompt,
        recipient: null
      };

      const response: any = await apiClient.post('/generate-envelope', requestBody);
      setSuccess(`Envelope generated: ${response.filename}`);
      setEnvelopePrompt('');

      // Auto-download the generated envelope
      await downloadEnvelope(response.envelope_id, response.filename);
    } catch (err: any) {
      setError(err.message || 'Failed to generate envelope');
    } finally {
      setGenerating(false);
    }
  };

  const handleGenerateEnvelopeManual = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setGenerating(true);

    try {
      const returnAddress = await getReturnAddress();

      // Check if return address is configured
      if (!returnAddress.name || !returnAddress.line1) {
        setError('Please configure your return address in Settings first');
        setGenerating(false);
        return;
      }

      const requestBody = {
        return_address: returnAddress,
        ai_prompt: null,
        recipient: recipient
      };

      const response: any = await apiClient.post('/generate-envelope', requestBody);
      setSuccess(`Envelope generated: ${response.filename}`);

      // Clear form
      setRecipient({ name: '', line1: '', line2: '', city_state_zip: '' });

      // Auto-download the generated envelope
      await downloadEnvelope(response.envelope_id, response.filename);
    } catch (err: any) {
      setError(err.message || 'Failed to generate envelope');
    } finally {
      setGenerating(false);
    }
  };

  const downloadEnvelope = async (envelopeId: string, filename: string) => {
    try {
      const response = await apiClient.downloadFile(`/generated-documents/${envelopeId}`);

      // Extract filename from Content-Disposition header if available
      const contentDisposition = response.headers.get('Content-Disposition');
      let downloadFilename = filename;
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/);
        if (filenameMatch && filenameMatch[1]) {
          downloadFilename = filenameMatch[1];
        }
      }

      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = downloadUrl;
      a.download = downloadFilename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(downloadUrl);
      document.body.removeChild(a);
    } catch (err: any) {
      console.error('Download failed:', err);
      setError('Generated but failed to download. Check generated documents list.');
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

      <div className="max-w-4xl mx-auto">
        {/* Main Envelope Generation Area */}
        <div>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Mail className="h-5 w-5" />
                Generate Envelope
              </CardTitle>
              <CardDescription>
                Create print-ready envelopes in #10 business format (9.5" × 4.125")
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="bg-gradient-to-br from-green-50 to-blue-50 dark:from-green-950/20 dark:to-blue-950/20 rounded-lg p-6 border-2 border-dashed border-green-200 dark:border-green-800">
                <>
                    {/* AI Quick Mode */}
                    <div className="space-y-4 mb-6">
                      <div>
                        <Label htmlFor="envelope-prompt" className="text-base font-semibold flex items-center gap-2">
                          <Sparkles className="h-4 w-4" />
                          AI Quick Mode
                        </Label>
                        <p className="text-sm text-muted-foreground mb-3">
                          Just describe who you're mailing to in natural language
                        </p>
                      </div>
                      <Textarea
                        id="envelope-prompt"
                        placeholder='Example: "Create envelope to John Smith at 123 Main Street, Boston MA 02101"'
                        value={envelopePrompt}
                        onChange={(e) => setEnvelopePrompt(e.target.value)}
                        rows={3}
                        className="resize-none"
                      />
                      <Button
                        onClick={handleGenerateEnvelopeAI}
                        disabled={generating || !envelopePrompt.trim()}
                        className="w-full"
                        size="lg"
                      >
                        {generating ? (
                          <>
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            Generating...
                          </>
                        ) : (
                          <>
                            <Sparkles className="mr-2 h-4 w-4" />
                            Generate Envelope with AI
                          </>
                        )}
                      </Button>
                    </div>

                    <div className="my-6 flex items-center gap-3">
                      <div className="flex-1 h-px bg-gradient-to-r from-transparent via-gray-300 to-transparent"></div>
                      <span className="text-sm text-muted-foreground font-medium px-3">OR</span>
                      <div className="flex-1 h-px bg-gradient-to-r from-transparent via-gray-300 to-transparent"></div>
                    </div>

                    {/* Manual Form */}
                    <form onSubmit={handleGenerateEnvelopeManual} className="space-y-4">
                      <div>
                        <Label className="text-base font-semibold">Manual Entry</Label>
                        <p className="text-sm text-muted-foreground mb-3">
                          Enter recipient details manually
                        </p>
                      </div>

                      <div className="grid grid-cols-2 gap-4">
                        <div className="col-span-2">
                          <Label htmlFor="recipient-name">Recipient Name</Label>
                          <Input
                            id="recipient-name"
                            placeholder="John Smith"
                            value={recipient.name}
                            onChange={(e) => setRecipient({ ...recipient, name: e.target.value })}
                            required
                          />
                        </div>

                        <div className="col-span-2">
                          <Label htmlFor="recipient-line1">Street Address</Label>
                          <Input
                            id="recipient-line1"
                            placeholder="123 Main Street"
                            value={recipient.line1}
                            onChange={(e) => setRecipient({ ...recipient, line1: e.target.value })}
                            required
                          />
                        </div>

                        <div className="col-span-2">
                          <Label htmlFor="recipient-line2">Apt/Suite (optional)</Label>
                          <Input
                            id="recipient-line2"
                            placeholder="Apt 3B"
                            value={recipient.line2}
                            onChange={(e) => setRecipient({ ...recipient, line2: e.target.value })}
                          />
                        </div>

                        <div className="col-span-2">
                          <Label htmlFor="recipient-city">City, State ZIP</Label>
                          <Input
                            id="recipient-city"
                            placeholder="Boston, MA 02101"
                            value={recipient.city_state_zip}
                            onChange={(e) => setRecipient({ ...recipient, city_state_zip: e.target.value })}
                            required
                          />
                        </div>
                      </div>

                      <Button
                        type="submit"
                        disabled={generating}
                        className="w-full"
                        variant="outline"
                        size="lg"
                      >
                        {generating ? (
                          <>
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            Generating...
                          </>
                        ) : (
                          <>
                            <Mail className="mr-2 h-4 w-4" />
                            Generate Envelope
                          </>
                        )}
                      </Button>
                    </form>
                  </>
              </div>

              {/* Preview/Info Section */}
              <div className="mt-6 p-4 bg-slate-50 dark:bg-slate-900 rounded-lg">
                <h4 className="font-semibold text-sm mb-2">💡 How it works:</h4>
                <ul className="text-sm text-muted-foreground space-y-1 list-disc list-inside">
                  <li>Generates Word document sized for #10 business envelopes</li>
                  <li>Return address appears in top-left corner (configured in Settings)</li>
                  <li>Recipient address is centered for proper printing</li>
                  <li>Download, open in Word, and print directly on envelope</li>
                  <li>⚙️ Configure your return address in Settings first</li>
                </ul>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
