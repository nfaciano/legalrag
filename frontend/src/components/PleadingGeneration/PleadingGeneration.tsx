import { useState, useEffect, useCallback } from 'react';
import { useApi } from '@/lib/useApi';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Textarea } from '../ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Alert, AlertDescription } from '../ui/alert';
import { ConfirmDialog } from '../ui/confirm-dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import {
  Gavel, Plus, Trash2, Loader2, Sparkles, Edit3, FileCheck, ChevronDown, ChevronUp, X,
  Pilcrow, List, ListOrdered
} from 'lucide-react';
import type {
  CaseInfo, CaseCreateRequest, CaseListResponse,
  PleadingGenerationRequest, PleadingResponse
} from '@/types/api';

// Section builder types
type ContentItem = {
  id: string;
  type: 'paragraph' | 'bullet' | 'numbered';
  text: string;
};

type Section = {
  id: string;
  heading: string;
  items: ContentItem[];
};

const RI_COURTS: { value: string; label: string; needsLocation: boolean }[] = [
  { value: 'STATE OF RHODE ISLAND\nSUPERIOR COURT', label: 'Rhode Island Superior Court', needsLocation: true },
  { value: 'STATE OF RHODE ISLAND\nDISTRICT COURT', label: 'Rhode Island District Court', needsLocation: true },
  { value: 'STATE OF RHODE ISLAND\nFAMILY COURT', label: 'Rhode Island Family Court', needsLocation: true },
  { value: 'STATE OF RHODE ISLAND\nSUPREME COURT', label: 'Rhode Island Supreme Court', needsLocation: false },
  { value: 'STATE OF RHODE ISLAND\nWORKERS\' COMPENSATION COURT', label: "Rhode Island Workers' Compensation Court", needsLocation: false },
  { value: 'UNITED STATES DISTRICT COURT\nFOR THE DISTRICT OF RHODE ISLAND', label: 'U.S. District Court — District of Rhode Island', needsLocation: false },
  { value: 'UNITED STATES BANKRUPTCY COURT\nFOR THE DISTRICT OF RHODE ISLAND', label: 'U.S. Bankruptcy Court — District of Rhode Island', needsLocation: false },
  { value: 'UNITED STATES COURT OF APPEALS\nFOR THE FIRST CIRCUIT', label: 'U.S. Court of Appeals — First Circuit', needsLocation: false },
];

const RI_LOCATIONS = [
  'PROVIDENCE, SC.',
  'KENT, SC.',
  'WASHINGTON, SC.',
  'NEWPORT, SC.',
  'BRISTOL, SC.',
];

let _nextId = 1;
function uid() { return `_${_nextId++}`; }

function makeSection(heading = ''): Section {
  return { id: uid(), heading, items: [{ id: uid(), type: 'paragraph', text: '' }] };
}

function sectionsToBodyText(sections: Section[]): string {
  const parts: string[] = [];

  for (const section of sections) {
    if (section.heading.trim()) {
      parts.push(`## ${section.heading.trim()}`);
      parts.push('');
    }

    let numberedCounter = 0;

    for (let i = 0; i < section.items.length; i++) {
      const item = section.items[i];
      const text = item.text.trim();
      if (!text) continue;

      // Reset numbered counter when type changes from numbered
      if (item.type !== 'numbered') numberedCounter = 0;

      if (item.type === 'paragraph') {
        parts.push(text);
        parts.push('');
      } else if (item.type === 'bullet') {
        parts.push(`- ${text}`);
        // Add blank line after last bullet in a consecutive group
        const next = section.items[i + 1];
        if (!next || next.type !== 'bullet') parts.push('');
      } else if (item.type === 'numbered') {
        numberedCounter++;
        parts.push(`${numberedCounter}. ${text}`);
        const next = section.items[i + 1];
        if (!next || next.type !== 'numbered') {
          parts.push('');
          numberedCounter = 0;
        }
      }
    }
  }

  // Remove trailing blank lines
  while (parts.length > 0 && parts[parts.length - 1] === '') parts.pop();
  return parts.join('\n');
}

export function PleadingGeneration() {
  const apiClient = useApi();

  // Cases state
  const [cases, setCases] = useState<CaseInfo[]>([]);
  const [selectedCaseId, setSelectedCaseId] = useState<string>('');
  const [showNewCase, setShowNewCase] = useState(false);
  const [deleteCaseTarget, setDeleteCaseTarget] = useState<string | null>(null);
  const [newCase, setNewCase] = useState<CaseCreateRequest>({
    case_name: '',
    case_number: '',
    court_name: 'STATE OF RHODE ISLAND\nSUPERIOR COURT',
    court_location: 'PROVIDENCE, SC.',
    plaintiff_names: [''],
    defendant_names: [''],
    plaintiff_label: 'VS.',
    file_reference: '',
  });
  const [savingCase, setSavingCase] = useState(false);

  // Pleading form state
  const [generating, setGenerating] = useState(false);
  const [documentTitle, setDocumentTitle] = useState('');
  const [sections, setSections] = useState<Section[]>([makeSection()]);
  const [aiPrompt, setAiPrompt] = useState('');
  const [representingParty, setRepresentingParty] = useState('');
  const [attorneyCapacity, setAttorneyCapacity] = useState('By his Attorney,');
  const [includeCertification, setIncludeCertification] = useState(true);
  const [certificationDate, setCertificationDate] = useState('');
  const [filingMethod, setFilingMethod] = useState('ecf');
  const [serviceMethod, setServiceMethod] = useState('ecf_auto');
  const [serviceListText, setServiceListText] = useState('');

  // UI state
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => { loadCases(); }, []);

  const loadCases = async () => {
    try {
      const data = await apiClient.get<CaseListResponse>('/cases');
      setCases(data.cases);
      if (data.cases.length > 0 && !selectedCaseId) {
        setSelectedCaseId(data.cases[0].case_id);
      }
    } catch (err: any) {
      console.error('Error loading cases:', err);
    }
  };

  const handleSaveCase = async () => {
    if (!newCase.case_name || !newCase.case_number) {
      setError('Case name and number are required');
      return;
    }

    setSavingCase(true);
    setError('');

    try {
      const payload: CaseCreateRequest = {
        ...newCase,
        plaintiff_names: newCase.plaintiff_names.filter(n => n.trim()),
        defendant_names: newCase.defendant_names.filter(n => n.trim()),
      };
      const saved = await apiClient.post<CaseInfo>('/cases', payload);
      setSuccess(`Case "${saved.case_name}" saved`);
      setTimeout(() => setSuccess(''), 3000);
      setSelectedCaseId(saved.case_id);
      setShowNewCase(false);
      setNewCase({
        case_name: '', case_number: '',
        court_name: 'STATE OF RHODE ISLAND\nSUPERIOR COURT',
        court_location: 'PROVIDENCE, SC.',
        plaintiff_names: [''], defendant_names: [''],
        plaintiff_label: 'VS.', file_reference: '',
      });
      await loadCases();
    } catch (err: any) {
      setError(err.message || 'Failed to save case');
    } finally {
      setSavingCase(false);
    }
  };

  const handleDeleteCase = useCallback(async () => {
    if (!deleteCaseTarget) return;
    try {
      await apiClient.delete(`/cases/${deleteCaseTarget}`);
      if (selectedCaseId === deleteCaseTarget) setSelectedCaseId('');
      setSuccess('Case deleted');
      setTimeout(() => setSuccess(''), 3000);
      await loadCases();
    } catch (err: any) {
      setError(err.message || 'Failed to delete case');
    } finally {
      setDeleteCaseTarget(null);
    }
  }, [deleteCaseTarget, selectedCaseId]);

  const addPartyField = (side: 'plaintiff' | 'defendant') => {
    const key = side === 'plaintiff' ? 'plaintiff_names' : 'defendant_names';
    setNewCase({ ...newCase, [key]: [...newCase[key], ''] });
  };

  const updatePartyField = (side: 'plaintiff' | 'defendant', idx: number, value: string) => {
    const key = side === 'plaintiff' ? 'plaintiff_names' : 'defendant_names';
    const updated = [...newCase[key]];
    updated[idx] = value;
    setNewCase({ ...newCase, [key]: updated });
  };

  const removePartyField = (side: 'plaintiff' | 'defendant', idx: number) => {
    const key = side === 'plaintiff' ? 'plaintiff_names' : 'defendant_names';
    if (newCase[key].length <= 1) return;
    setNewCase({ ...newCase, [key]: newCase[key].filter((_, i) => i !== idx) });
  };

  // Section builder helpers
  const addSection = () => {
    setSections([...sections, makeSection()]);
  };
  const removeSection = (sectionId: string) => {
    if (sections.length <= 1) return;
    setSections(sections.filter(s => s.id !== sectionId));
  };
  const updateHeading = (sectionId: string, heading: string) => {
    setSections(sections.map(s => s.id === sectionId ? { ...s, heading } : s));
  };
  const addItem = (sectionId: string, type: ContentItem['type']) => {
    setSections(sections.map(s => s.id === sectionId
      ? { ...s, items: [...s.items, { id: uid(), type, text: '' }] }
      : s
    ));
  };
  const removeItem = (sectionId: string, itemId: string) => {
    setSections(sections.map(s => {
      if (s.id !== sectionId) return s;
      if (s.items.length <= 1) return s;
      return { ...s, items: s.items.filter(it => it.id !== itemId) };
    }));
  };
  const updateItem = (sectionId: string, itemId: string, text: string) => {
    setSections(sections.map(s => s.id === sectionId
      ? { ...s, items: s.items.map(it => it.id === itemId ? { ...it, text } : it) }
      : s
    ));
  };

  const handleDownload = async (documentId: string) => {
    try {
      const url = `${apiClient.baseURL}/generated-documents/${documentId}`;
      const token = await apiClient.getToken();
      const response = await fetch(url, {
        headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}) },
      });
      if (!response.ok) throw new Error('Download failed');
      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = downloadUrl;
      const cd = response.headers.get('Content-Disposition');
      a.download = cd?.match(/filename="?(.+)"?/)?.[1] || 'pleading.docx';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(downloadUrl);
      document.body.removeChild(a);
    } catch (err: any) {
      setError('Failed to download document');
    }
  };

  const handleGenerate = async (aiMode: boolean) => {
    if (!selectedCaseId) {
      setError('Please select a case first');
      return;
    }
    if (!documentTitle.trim()) {
      setError('Document title is required');
      return;
    }
    if (aiMode && !aiPrompt.trim()) {
      setError('Please describe what to draft');
      return;
    }
    if (!aiMode) {
      const bodyContent = sectionsToBodyText(sections);
      if (!bodyContent.trim()) {
        setError('Body text is required — add content to at least one section');
        return;
      }
    }
    if (!representingParty.trim()) {
      setError('Representing party line is required');
      return;
    }

    setError('');
    setSuccess('');
    setGenerating(true);

    try {
      // Parse service list (entries separated by blank lines)
      const serviceList = serviceListText.trim()
        ? serviceListText.split(/\n\n+/).filter(e => e.trim())
        : null;

      const request: PleadingGenerationRequest = {
        case_id: selectedCaseId,
        document_title: documentTitle,
        body_text: aiMode ? null : sectionsToBodyText(sections),
        body_paragraphs: null,
        representing_party: representingParty,
        attorney_capacity: attorneyCapacity,
        include_certification: includeCertification,
        certification_date: certificationDate || null,
        filing_method: filingMethod,
        service_method: serviceMethod,
        service_list: serviceList,
        ai_generate_body: aiMode,
        ai_prompt: aiMode ? aiPrompt : null,
      };

      const response = await apiClient.post<PleadingResponse>('/generate-pleading', request);
      setSuccess(`Pleading generated: ${response.filename}`);
      handleDownload(response.document_id);
    } catch (err: any) {
      setError(err.message || 'Failed to generate pleading');
    } finally {
      setGenerating(false);
    }
  };

  const selectedCase = cases.find(c => c.case_id === selectedCaseId);

  return (
    <div className="space-y-6">
      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
      {success && (
        <Alert className="bg-green-50 border-green-200">
          <FileCheck className="h-4 w-4 text-green-600" />
          <AlertDescription className="text-green-800">{success}</AlertDescription>
        </Alert>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Left Sidebar: Case Manager */}
        <div className="lg:col-span-1 space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Gavel className="h-5 w-5" />
                Cases
              </CardTitle>
              <CardDescription>Saved case captions</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Button
                variant="outline"
                size="sm"
                className="w-full"
                onClick={() => setShowNewCase(!showNewCase)}
              >
                {showNewCase ? <ChevronUp className="h-4 w-4 mr-2" /> : <Plus className="h-4 w-4 mr-2" />}
                {showNewCase ? 'Cancel' : 'New Case'}
              </Button>

              {/* New Case Form */}
              {showNewCase && (
                <div className="space-y-3 p-3 border rounded-lg bg-slate-50 dark:bg-slate-900">
                  <div>
                    <Label className="text-xs">Case Name</Label>
                    <Input
                      placeholder="Vincent v. Dolan"
                      value={newCase.case_name}
                      onChange={(e) => setNewCase({ ...newCase, case_name: e.target.value })}
                    />
                  </div>
                  <div>
                    <Label className="text-xs">Case Number</Label>
                    <Input
                      placeholder="1:24-cv-00155-JJM-LDA"
                      value={newCase.case_number}
                      onChange={(e) => setNewCase({ ...newCase, case_number: e.target.value })}
                    />
                  </div>
                  <div>
                    <Label className="text-xs">Court</Label>
                    <select
                      value={RI_COURTS.find(c => c.value === newCase.court_name) ? newCase.court_name : '_custom'}
                      onChange={(e) => {
                        if (e.target.value === '_custom') {
                          setNewCase({ ...newCase, court_name: '', court_location: '' });
                        } else {
                          setNewCase({ ...newCase, court_name: e.target.value });
                        }
                      }}
                      className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                    >
                      {RI_COURTS.map((court) => (
                        <option key={court.value} value={court.value}>{court.label}</option>
                      ))}
                      <option value="_custom">Other (type below)</option>
                    </select>
                    {!RI_COURTS.find(c => c.value === newCase.court_name) && (
                      <Textarea
                        rows={2}
                        placeholder="COURT NAME LINE 1&#10;LINE 2"
                        value={newCase.court_name}
                        onChange={(e) => setNewCase({ ...newCase, court_name: e.target.value })}
                        className="mt-2"
                      />
                    )}
                  </div>
                  {RI_COURTS.find(c => c.value === newCase.court_name)?.needsLocation && (
                    <div>
                      <Label className="text-xs">County / Location</Label>
                      <select
                        value={RI_LOCATIONS.includes(newCase.court_location || '') ? newCase.court_location : '_custom'}
                        onChange={(e) => {
                          if (e.target.value === '_custom') {
                            setNewCase({ ...newCase, court_location: '' });
                          } else {
                            setNewCase({ ...newCase, court_location: e.target.value });
                          }
                        }}
                        className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                      >
                        {RI_LOCATIONS.map((loc) => (
                          <option key={loc} value={loc}>{loc}</option>
                        ))}
                        <option value="_custom">Other</option>
                      </select>
                      {!RI_LOCATIONS.includes(newCase.court_location || '') && (
                        <Input
                          placeholder="e.g. KENT, SC."
                          value={newCase.court_location || ''}
                          onChange={(e) => setNewCase({ ...newCase, court_location: e.target.value })}
                          className="mt-2"
                        />
                      )}
                    </div>
                  )}

                  {/* Plaintiffs */}
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <Label className="text-xs">Plaintiffs</Label>
                      <button
                        type="button"
                        onClick={() => addPartyField('plaintiff')}
                        className="text-xs text-primary hover:underline"
                      >
                        + Add
                      </button>
                    </div>
                    {newCase.plaintiff_names.map((name, idx) => (
                      <div key={idx} className="flex gap-1 mb-1">
                        <Input
                          placeholder={`Plaintiff ${idx + 1}`}
                          value={name}
                          onChange={(e) => updatePartyField('plaintiff', idx, e.target.value)}
                        />
                        {newCase.plaintiff_names.length > 1 && (
                          <Button variant="ghost" size="icon" onClick={() => removePartyField('plaintiff', idx)}>
                            <X className="h-3 w-3" />
                          </Button>
                        )}
                      </div>
                    ))}
                  </div>

                  {/* Defendants */}
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <Label className="text-xs">Defendants</Label>
                      <button
                        type="button"
                        onClick={() => addPartyField('defendant')}
                        className="text-xs text-primary hover:underline"
                      >
                        + Add
                      </button>
                    </div>
                    {newCase.defendant_names.map((name, idx) => (
                      <div key={idx} className="flex gap-1 mb-1">
                        <Input
                          placeholder={`Defendant ${idx + 1}`}
                          value={name}
                          onChange={(e) => updatePartyField('defendant', idx, e.target.value)}
                        />
                        {newCase.defendant_names.length > 1 && (
                          <Button variant="ghost" size="icon" onClick={() => removePartyField('defendant', idx)}>
                            <X className="h-3 w-3" />
                          </Button>
                        )}
                      </div>
                    ))}
                  </div>

                  <div>
                    <Label className="text-xs">File Reference (optional)</Label>
                    <Input
                      placeholder="MJC:ljc 7930/3"
                      value={newCase.file_reference}
                      onChange={(e) => setNewCase({ ...newCase, file_reference: e.target.value })}
                    />
                  </div>

                  <Button
                    size="sm"
                    className="w-full"
                    onClick={handleSaveCase}
                    disabled={savingCase}
                  >
                    {savingCase ? <Loader2 className="h-4 w-4 animate-spin mr-1" /> : null}
                    Save Case
                  </Button>
                </div>
              )}

              {/* Case List */}
              {cases.length > 0 ? (
                <div className="space-y-1 max-h-72 overflow-y-auto">
                  {cases.map((c) => (
                    <div
                      key={c.case_id}
                      className={`group flex items-center justify-between p-3 border-2 rounded-lg transition-all cursor-pointer ${
                        selectedCaseId === c.case_id
                          ? 'border-primary bg-primary/5 shadow-sm'
                          : 'border-border hover:border-primary/30 hover:bg-muted/50'
                      }`}
                    >
                      <button
                        onClick={() => setSelectedCaseId(c.case_id)}
                        className="flex-1 text-left"
                      >
                        <p className="text-sm font-medium truncate">{c.case_name}</p>
                        <p className="text-xs text-muted-foreground truncate">{c.case_number}</p>
                      </button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => { e.stopPropagation(); setDeleteCaseTarget(c.case_id); }}
                        className="opacity-0 group-hover:opacity-100 transition-opacity"
                      >
                        <Trash2 className="h-3.5 w-3.5 text-destructive" />
                      </Button>
                    </div>
                  ))}
                </div>
              ) : !showNewCase ? (
                <p className="text-xs text-muted-foreground text-center py-4">
                  No cases saved yet
                </p>
              ) : null}
            </CardContent>
          </Card>
        </div>

        {/* Main Generation Area */}
        <div className="lg:col-span-3">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Gavel className="h-5 w-5" />
                Generate Court Filing
              </CardTitle>
              <CardDescription>
                {selectedCase
                  ? `Case: ${selectedCase.case_name} (${selectedCase.case_number})`
                  : 'Select a case from the sidebar to begin'}
              </CardDescription>
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

                {/* Shared fields */}
                <div className="space-y-4 mb-6">
                  <div>
                    <Label htmlFor="doc-title">Document Title</Label>
                    <Input
                      id="doc-title"
                      placeholder="DEFENDANT DOLAN'S MOTION TO DISMISS"
                      value={documentTitle}
                      onChange={(e) => setDocumentTitle(e.target.value)}
                    />
                    <p className="text-xs text-muted-foreground mt-1">
                      Appears centered, bold, and underlined below the caption
                    </p>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="rep-party">Representing Party</Label>
                      <Input
                        id="rep-party"
                        placeholder="DEFENDANT, DANIEL DOLAN,"
                        value={representingParty}
                        onChange={(e) => setRepresentingParty(e.target.value)}
                      />
                    </div>
                    <div>
                      <Label htmlFor="atty-capacity">Attorney Capacity</Label>
                      <Input
                        id="atty-capacity"
                        placeholder="By his Attorney,"
                        value={attorneyCapacity}
                        onChange={(e) => setAttorneyCapacity(e.target.value)}
                      />
                    </div>
                  </div>
                </div>

                {/* AI Quick Mode */}
                <TabsContent value="ai" className="space-y-4">
                  <div className="bg-gradient-to-br from-amber-50 to-orange-50 dark:from-amber-950/20 dark:to-orange-950/20 rounded-lg p-4 border-2 border-dashed border-amber-200 dark:border-amber-800">
                    <div className="flex items-start gap-3 mb-3">
                      <Sparkles className="h-5 w-5 text-amber-600 mt-0.5" />
                      <div>
                        <h4 className="font-semibold text-sm mb-1">AI Quick Draft</h4>
                        <p className="text-xs text-muted-foreground">
                          Describe the motion and AI will generate the body paragraphs
                        </p>
                      </div>
                    </div>
                    <div className="bg-white dark:bg-slate-900 rounded p-2 text-xs text-muted-foreground font-mono">
                      Example: "Motion to dismiss pursuant to Rule 12(b)(6) arguing plaintiffs fail to state a claim for excessive force under 42 USC 1983..."
                    </div>
                  </div>

                  <Textarea
                    placeholder="Describe what the motion should argue..."
                    value={aiPrompt}
                    onChange={(e) => setAiPrompt(e.target.value)}
                    className="min-h-[180px] resize-none"
                  />

                  {/* Certification options */}
                  {_renderCertificationSection()}

                  <Button
                    onClick={() => handleGenerate(true)}
                    disabled={!selectedCaseId || generating}
                    className="w-full bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-700 hover:to-orange-700"
                  >
                    {generating ? (
                      <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Generating...</>
                    ) : (
                      <><Sparkles className="mr-2 h-4 w-4" />Generate with AI</>
                    )}
                  </Button>
                </TabsContent>

                {/* Manual Form Mode — Section Builder */}
                <TabsContent value="manual" className="space-y-4">
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <Label className="text-sm font-medium">Document Body</Label>
                      <p className="text-xs text-muted-foreground">
                        Use <code className="bg-muted px-1 rounded">**bold**</code> and <code className="bg-muted px-1 rounded">__underline__</code> in text
                      </p>
                    </div>

                    {sections.map((section, sIdx) => (
                      <div key={section.id} className="border rounded-lg bg-slate-50/50 dark:bg-slate-900/50">
                        {/* Section header */}
                        <div className="flex items-center gap-2 px-3 py-2 border-b bg-slate-100/80 dark:bg-slate-800/50 rounded-t-lg">
                          <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                            Section {sIdx + 1}
                          </span>
                          <Input
                            placeholder="Section heading (optional, e.g. STATEMENT OF FACTS)"
                            value={section.heading}
                            onChange={(e) => updateHeading(section.id, e.target.value)}
                            className="h-7 text-sm flex-1 bg-white dark:bg-slate-900"
                          />
                          {sections.length > 1 && (
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-7 w-7 p-0 text-destructive hover:text-destructive"
                              onClick={() => removeSection(section.id)}
                            >
                              <Trash2 className="h-3.5 w-3.5" />
                            </Button>
                          )}
                        </div>

                        {/* Content items */}
                        <div className="p-3 space-y-2">
                          {section.items.map((item, iIdx) => {
                            // Compute display number for numbered items
                            let displayNum = 0;
                            if (item.type === 'numbered') {
                              let count = 0;
                              for (let k = 0; k <= iIdx; k++) {
                                if (section.items[k].type === 'numbered') count++;
                                else count = 0;
                              }
                              displayNum = count;
                            }

                            return (
                              <div key={item.id} className="flex items-start gap-2">
                                {/* Type indicator */}
                                <div className="flex-shrink-0 w-7 h-9 flex items-center justify-center text-muted-foreground">
                                  {item.type === 'paragraph' && <Pilcrow className="h-3.5 w-3.5" />}
                                  {item.type === 'bullet' && <span className="text-base leading-none">&bull;</span>}
                                  {item.type === 'numbered' && <span className="text-xs font-medium">{displayNum}.</span>}
                                </div>

                                <Textarea
                                  placeholder={
                                    item.type === 'paragraph'
                                      ? 'Paragraph text...'
                                      : item.type === 'bullet'
                                      ? 'Bullet point...'
                                      : 'Numbered item...'
                                  }
                                  value={item.text}
                                  onChange={(e) => updateItem(section.id, item.id, e.target.value)}
                                  rows={item.type === 'paragraph' ? 3 : 1}
                                  className="flex-1 text-sm min-h-[36px] resize-y"
                                />

                                {section.items.length > 1 && (
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    className="h-9 w-7 p-0 flex-shrink-0"
                                    onClick={() => removeItem(section.id, item.id)}
                                  >
                                    <X className="h-3.5 w-3.5" />
                                  </Button>
                                )}
                              </div>
                            );
                          })}

                          {/* Add content buttons */}
                          <div className="flex items-center gap-2 pt-1">
                            <Button
                              variant="outline"
                              size="sm"
                              className="h-7 text-xs"
                              onClick={() => addItem(section.id, 'paragraph')}
                            >
                              <Pilcrow className="h-3 w-3 mr-1" />
                              Paragraph
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              className="h-7 text-xs"
                              onClick={() => addItem(section.id, 'bullet')}
                            >
                              <List className="h-3 w-3 mr-1" />
                              Bullet
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              className="h-7 text-xs"
                              onClick={() => addItem(section.id, 'numbered')}
                            >
                              <ListOrdered className="h-3 w-3 mr-1" />
                              Numbered
                            </Button>
                          </div>
                        </div>
                      </div>
                    ))}

                    <Button
                      variant="outline"
                      size="sm"
                      className="w-full"
                      onClick={addSection}
                    >
                      <Plus className="h-4 w-4 mr-2" />
                      Add Section
                    </Button>
                  </div>

                  {/* Certification options */}
                  {_renderCertificationSection()}

                  <Button
                    onClick={() => handleGenerate(false)}
                    disabled={!selectedCaseId || generating}
                    className="w-full"
                  >
                    {generating ? (
                      <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Generating...</>
                    ) : (
                      <><Gavel className="mr-2 h-4 w-4" />Generate Pleading</>
                    )}
                  </Button>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>
        </div>
      </div>

      <ConfirmDialog
        open={!!deleteCaseTarget}
        onOpenChange={(open) => !open && setDeleteCaseTarget(null)}
        onConfirm={handleDeleteCase}
        description="This will permanently delete this saved case. Any previously generated documents will not be affected."
      />
    </div>
  );

  function _renderCertificationSection() {
    const selectClass = "flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring";

    return (
      <div className="space-y-3 p-4 border rounded-lg bg-slate-50 dark:bg-slate-900">
        <div className="flex items-center gap-2">
          <input
            type="checkbox"
            id="include-cert"
            checked={includeCertification}
            onChange={(e) => setIncludeCertification(e.target.checked)}
            className="rounded"
          />
          <Label htmlFor="include-cert" className="cursor-pointer text-sm font-medium">
            Include Certification of Service (Page 2)
          </Label>
        </div>

        {includeCertification && (
          <div className="space-y-3 pl-6">
            <div>
              <Label className="text-xs">Filing Date</Label>
              <Input
                placeholder="31st day of July 2024"
                value={certificationDate}
                onChange={(e) => setCertificationDate(e.target.value)}
              />
            </div>

            <div>
              <Label className="text-xs">Filing Method</Label>
              <select
                value={filingMethod}
                onChange={(e) => setFilingMethod(e.target.value)}
                className={selectClass}
              >
                <option value="ecf">ECF (Federal Electronic Filing)</option>
                <option value="tyler">Tyler (State Electronic Filing)</option>
                <option value="mail_clerk">Mail to Clerk of Court</option>
                <option value="hand_clerk">Hand Delivery to Clerk</option>
              </select>
            </div>

            <div>
              <Label className="text-xs">Service Method</Label>
              <select
                value={serviceMethod}
                onChange={(e) => setServiceMethod(e.target.value)}
                className={selectClass}
              >
                <option value="ecf_auto">ECF Auto-Serve (no service list needed)</option>
                <option value="email">Email to Counsel</option>
                <option value="mail">U.S. Mail, First Class</option>
                <option value="hand">Hand Delivery</option>
              </select>
            </div>

            {serviceMethod !== 'ecf_auto' && (
              <div>
                <Label className="text-xs">Service List</Label>
                <Textarea
                  placeholder={"James P. Howe, Esq.\n336 High Street, Suite 5A\nWakefield, RI 02879\n\nMarc DeSisto, Esq.\nDeSisto Law\n60 Ship Street\nProvidence, RI 02903"}
                  value={serviceListText}
                  onChange={(e) => setServiceListText(e.target.value)}
                  rows={6}
                />
                <p className="text-xs text-muted-foreground mt-1">
                  Separate each attorney/firm with a blank line
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    );
  }
}
