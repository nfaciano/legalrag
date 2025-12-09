import { useState, useEffect } from 'react';
import { useApi } from '@/lib/useApi';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Alert, AlertDescription } from '../ui/alert';
import { Settings as SettingsIcon, Mail, FileText, Save, CheckCircle2, Loader2 } from 'lucide-react';

interface UserSettings {
  // Return Address (for envelopes)
  return_address_name: string;
  return_address_line1: string;
  return_address_line2: string;
  return_address_city_state_zip: string;

  // Document Settings
  signature_name: string;
  initials: string;
  closing: string;
}

export function Settings() {
  const apiClient = useApi();
  const [settings, setSettings] = useState<UserSettings>({
    return_address_name: '',
    return_address_line1: '',
    return_address_line2: '',
    return_address_city_state_zip: '',
    signature_name: '',
    initials: '',
    closing: 'Very truly yours,'
  });

  const [success, setSuccess] = useState<string>('');
  const [saving, setSaving] = useState(false);

  // Load settings from API on mount
  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const response: any = await apiClient.get('/user-settings');
      setSettings(response.settings);
    } catch (e) {
      console.error('Failed to load settings:', e);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await apiClient.put('/user-settings', settings);
      setSuccess('Settings saved successfully!');
      setTimeout(() => setSuccess(''), 3000);
    } catch (e: any) {
      console.error('Failed to save settings:', e);
      setSuccess('Error saving settings');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      {success && (
        <Alert className="bg-green-50 border-green-200">
          <CheckCircle2 className="h-4 w-4 text-green-600" />
          <AlertDescription className="text-green-800">{success}</AlertDescription>
        </Alert>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Return Address Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Mail className="h-5 w-5" />
              Return Address
            </CardTitle>
            <CardDescription>
              Your firm's mailing address for envelopes
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="return-name">Name/Firm</Label>
              <Input
                id="return-name"
                placeholder="Your Law Firm"
                value={settings.return_address_name}
                onChange={(e) => setSettings({ ...settings, return_address_name: e.target.value })}
              />
            </div>
            <div>
              <Label htmlFor="return-line1">Street Address</Label>
              <Input
                id="return-line1"
                placeholder="123 Main Street"
                value={settings.return_address_line1}
                onChange={(e) => setSettings({ ...settings, return_address_line1: e.target.value })}
              />
            </div>
            <div>
              <Label htmlFor="return-line2">Suite/Floor (optional)</Label>
              <Input
                id="return-line2"
                placeholder="Suite 100"
                value={settings.return_address_line2}
                onChange={(e) => setSettings({ ...settings, return_address_line2: e.target.value })}
              />
            </div>
            <div>
              <Label htmlFor="return-city">City, State ZIP</Label>
              <Input
                id="return-city"
                placeholder="New York, NY 10001"
                value={settings.return_address_city_state_zip}
                onChange={(e) => setSettings({ ...settings, return_address_city_state_zip: e.target.value })}
              />
            </div>
          </CardContent>
        </Card>

        {/* Document Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              Document Settings
            </CardTitle>
            <CardDescription>
              Default information for document generation
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="signature-name">Signature Name</Label>
              <Input
                id="signature-name"
                placeholder="John P. Harrison, Esq."
                value={settings.signature_name}
                onChange={(e) => setSettings({ ...settings, signature_name: e.target.value })}
              />
              <p className="text-xs text-muted-foreground mt-1">
                Name that appears above the signature line
              </p>
            </div>
            <div>
              <Label htmlFor="initials">Reference Initials</Label>
              <Input
                id="initials"
                placeholder="ABC/xyz"
                value={settings.initials}
                onChange={(e) => setSettings({ ...settings, initials: e.target.value })}
              />
              <p className="text-xs text-muted-foreground mt-1">
                Attorney initials/Assistant initials (e.g., "ABC/xyz")
              </p>
            </div>
            <div>
              <Label htmlFor="closing">Default Closing</Label>
              <Input
                id="closing"
                placeholder="Sincerely"
                value={settings.closing}
                onChange={(e) => setSettings({ ...settings, closing: e.target.value })}
              />
              <p className="text-xs text-muted-foreground mt-1">
                Default closing phrase (e.g., "Sincerely", "Best regards")
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Save Button */}
      <div className="flex justify-end">
        <Button onClick={handleSave} size="lg" className="px-8" disabled={saving}>
          {saving ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Saving...
            </>
          ) : (
            <>
              <Save className="mr-2 h-4 w-4" />
              Save Settings
            </>
          )}
        </Button>
      </div>

      {/* Info Box */}
      <Card className="bg-slate-50 dark:bg-slate-900">
        <CardContent className="pt-6">
          <div className="flex gap-3">
            <SettingsIcon className="h-5 w-5 text-muted-foreground flex-shrink-0 mt-0.5" />
            <div className="space-y-2">
              <p className="text-sm font-medium">About Settings</p>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>• Settings are saved to your account and synced across all devices</li>
                <li>• Return address is used when generating envelopes</li>
                <li>• Document settings auto-populate when creating documents</li>
                <li>• Date is automatically set to today when generating documents</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
