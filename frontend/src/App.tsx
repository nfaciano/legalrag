import { useState } from "react";
import { Scale, Search, FileText, Home, ArrowRight, Mail, Settings as SettingsIcon, Files } from "lucide-react";
import { SignedIn, SignedOut, SignInButton, UserButton } from "@clerk/clerk-react";
import { FileUpload } from "@/components/FileUpload";
import { SearchBar } from "@/components/SearchBar";
import { SearchResults } from "@/components/SearchResults";
import { DocumentList } from "@/components/DocumentList";
import { DocumentAutomation } from "@/components/DocumentAutomation";
import { EnvelopeGeneration } from "@/components/EnvelopeGeneration";
import { GeneratedDocuments } from "@/components/GeneratedDocuments";
import { Settings } from "@/components/Settings";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { SearchResponse, UploadResponse } from "@/types/api";

type Tab = 'home' | 'search' | 'automation' | 'envelope' | 'documents' | 'settings';

function App() {
  const [activeTab, setActiveTab] = useState<Tab>('home');
  const [searchResponse, setSearchResponse] = useState<SearchResponse | null>(
    null
  );
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const handleUploadComplete = (response: UploadResponse) => {
    console.log("Upload complete:", response);

    // Show OCR warning if document was scanned
    if (response.ocr_used) {
      const ocrMessage = `Scanned document detected: OCR was used on ${response.ocr_pages}/${response.total_pages} pages. Text extraction may not be 100% accurate.`;
      alert(ocrMessage);
    }

    // Trigger document list refresh
    setRefreshTrigger((prev) => prev + 1);
  };

  const handleSearchComplete = (response: SearchResponse) => {
    console.log("Search complete:", response);
    setSearchResponse(response);
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-50 border-b bg-white/80 dark:bg-slate-950/80 backdrop-blur-lg shadow-sm">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-3 group">
                <div className="p-2 bg-gradient-to-br from-blue-500 to-violet-600 rounded-xl shadow-lg shadow-blue-500/20 group-hover:shadow-blue-500/40 transition-all">
                  <Scale className="h-6 w-6 text-white" />
                </div>
                <div>
                  <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-violet-600 bg-clip-text text-transparent">
                    LegalRAG
                  </h1>
                  <p className="text-xs text-muted-foreground font-medium">
                    Legal Document Tools
                  </p>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <SignedOut>
                <SignInButton mode="modal">
                  <button className="px-6 py-2.5 bg-gradient-to-r from-blue-600 to-violet-600 text-white rounded-lg hover:shadow-lg hover:shadow-blue-500/30 transition-all font-medium">
                    Sign In
                  </button>
                </SignInButton>
              </SignedOut>
              <SignedIn>
                <div className="flex items-center gap-3">
                  <div className="hidden sm:block text-right">
                    <p className="text-sm font-medium text-foreground">Welcome back</p>
                    <p className="text-xs text-muted-foreground">Manage your documents</p>
                  </div>
                  <UserButton
                    afterSignOutUrl="/"
                    appearance={{
                      elements: {
                        avatarBox: "w-10 h-10 ring-2 ring-primary/20 hover:ring-primary/40 transition-all"
                      }
                    }}
                  />
                </div>
              </SignedIn>
            </div>
          </div>
        </div>
      </header>

      {/* Signed Out View */}
      <SignedOut>
        <main className="container mx-auto px-4 py-8">
          <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
            <Scale className="h-20 w-20 text-primary mb-6" />
            <h2 className="text-3xl font-bold mb-4">Welcome to LegalRAG</h2>
            <p className="text-lg text-muted-foreground mb-8 max-w-2xl">
              Secure, multi-tenant semantic search for legal documents.
              Upload PDFs, search with natural language, and get AI-powered answers.
            </p>
            <SignInButton mode="modal">
              <button className="px-6 py-3 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 text-lg">
                Sign In to Get Started
              </button>
            </SignInButton>
          </div>
        </main>
      </SignedOut>

      {/* Signed In View with Sidebar */}
      <SignedIn>
        <div className="flex min-h-[calc(100vh-73px)]">
          {/* Left Sidebar */}
          <aside className="w-72 border-r bg-slate-50/50 dark:bg-slate-900/50 flex flex-col">
            <div className="flex-1 p-6">
              <div className="mb-6">
                <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">
                  Navigation
                </p>
                <nav className="space-y-1">
                  <button
                    onClick={() => setActiveTab('home')}
                    className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all font-medium ${
                      activeTab === 'home'
                        ? 'bg-primary text-primary-foreground shadow-sm'
                        : 'text-muted-foreground hover:text-foreground hover:bg-white dark:hover:bg-slate-800'
                    }`}
                  >
                    <Home className="h-5 w-5" />
                    <span>Dashboard</span>
                  </button>
                  <button
                    onClick={() => setActiveTab('search')}
                    className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all font-medium ${
                      activeTab === 'search'
                        ? 'bg-primary text-primary-foreground shadow-sm'
                        : 'text-muted-foreground hover:text-foreground hover:bg-white dark:hover:bg-slate-800'
                    }`}
                  >
                    <Search className="h-5 w-5" />
                    <span>Search Documents</span>
                  </button>
                  <button
                    onClick={() => setActiveTab('automation')}
                    className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all font-medium ${
                      activeTab === 'automation'
                        ? 'bg-primary text-primary-foreground shadow-sm'
                        : 'text-muted-foreground hover:text-foreground hover:bg-white dark:hover:bg-slate-800'
                    }`}
                  >
                    <FileText className="h-5 w-5" />
                    <span>Document Automation</span>
                  </button>
                  <button
                    onClick={() => setActiveTab('envelope')}
                    className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all font-medium ${
                      activeTab === 'envelope'
                        ? 'bg-primary text-primary-foreground shadow-sm'
                        : 'text-muted-foreground hover:text-foreground hover:bg-white dark:hover:bg-slate-800'
                    }`}
                  >
                    <Mail className="h-5 w-5" />
                    <span>Envelopes</span>
                  </button>
                  <button
                    onClick={() => setActiveTab('documents')}
                    className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all font-medium ${
                      activeTab === 'documents'
                        ? 'bg-primary text-primary-foreground shadow-sm'
                        : 'text-muted-foreground hover:text-foreground hover:bg-white dark:hover:bg-slate-800'
                    }`}
                  >
                    <Files className="h-5 w-5" />
                    <span>Documents</span>
                  </button>
                  <button
                    onClick={() => setActiveTab('settings')}
                    className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all font-medium ${
                      activeTab === 'settings'
                        ? 'bg-primary text-primary-foreground shadow-sm'
                        : 'text-muted-foreground hover:text-foreground hover:bg-white dark:hover:bg-slate-800'
                    }`}
                  >
                    <SettingsIcon className="h-5 w-5" />
                    <span>Settings</span>
                  </button>
                </nav>
              </div>
            </div>
          </aside>

          {/* Main Content Area */}
          <main className="flex-1 bg-slate-50/30 dark:bg-slate-950/30">
          {/* Dashboard Home */}
          {activeTab === 'home' && (
            <div className="p-8">
              <div className="max-w-6xl mx-auto">
                <div className="mb-10">
                  <h2 className="text-4xl font-bold mb-3 bg-gradient-to-r from-slate-900 to-slate-700 dark:from-slate-100 dark:to-slate-300 bg-clip-text text-transparent">
                    Welcome to LegalRAG
                  </h2>
                  <p className="text-lg text-muted-foreground">
                    Choose a tool to get started with your legal workflows
                  </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Search Card */}
                  <Card
                    className="group cursor-pointer border-2 hover:border-primary/50 transition-all duration-300 hover:shadow-xl hover:-translate-y-1 bg-gradient-to-br from-white to-slate-50/50 dark:from-slate-900 dark:to-slate-800/50"
                    onClick={() => setActiveTab('search')}
                  >
                    <CardHeader className="pb-4">
                      <div className="flex items-start justify-between mb-4">
                        <div className="p-4 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl shadow-lg shadow-blue-500/20 group-hover:shadow-blue-500/40 transition-shadow">
                          <Search className="h-7 w-7 text-white" />
                        </div>
                        <ArrowRight className="h-5 w-5 text-muted-foreground group-hover:text-primary group-hover:translate-x-1 transition-all" />
                      </div>
                      <CardTitle className="text-2xl mb-2">Document Search</CardTitle>
                      <CardDescription className="text-base">
                        Semantic search & AI-powered answers
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm text-muted-foreground leading-relaxed">
                        Upload legal documents and search using natural language queries.
                        Get AI-powered answers with accurate source citations.
                      </p>
                    </CardContent>
                  </Card>

                  {/* Document Automation Card */}
                  <Card
                    className="group cursor-pointer border-2 hover:border-primary/50 transition-all duration-300 hover:shadow-xl hover:-translate-y-1 bg-gradient-to-br from-white to-slate-50/50 dark:from-slate-900 dark:to-slate-800/50"
                    onClick={() => setActiveTab('automation')}
                  >
                    <CardHeader className="pb-4">
                      <div className="flex items-start justify-between mb-4">
                        <div className="p-4 bg-gradient-to-br from-violet-500 to-violet-600 rounded-xl shadow-lg shadow-violet-500/20 group-hover:shadow-violet-500/40 transition-shadow">
                          <FileText className="h-7 w-7 text-white" />
                        </div>
                        <ArrowRight className="h-5 w-5 text-muted-foreground group-hover:text-primary group-hover:translate-x-1 transition-all" />
                      </div>
                      <CardTitle className="text-2xl mb-2">Document Automation</CardTitle>
                      <CardDescription className="text-base">
                        Generate formatted legal documents
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm text-muted-foreground leading-relaxed">
                        Create professional letters and documents using your custom
                        letterhead templates with automated field filling.
                      </p>
                    </CardContent>
                  </Card>

                  {/* Envelope Generation Card */}
                  <Card
                    className="group cursor-pointer border-2 hover:border-primary/50 transition-all duration-300 hover:shadow-xl hover:-translate-y-1 bg-gradient-to-br from-white to-slate-50/50 dark:from-slate-900 dark:to-slate-800/50"
                    onClick={() => setActiveTab('envelope')}
                  >
                    <CardHeader className="pb-4">
                      <div className="flex items-start justify-between mb-4">
                        <div className="p-4 bg-gradient-to-br from-green-500 to-green-600 rounded-xl shadow-lg shadow-green-500/20 group-hover:shadow-green-500/40 transition-shadow">
                          <Mail className="h-7 w-7 text-white" />
                        </div>
                        <ArrowRight className="h-5 w-5 text-muted-foreground group-hover:text-primary group-hover:translate-x-1 transition-all" />
                      </div>
                      <CardTitle className="text-2xl mb-2">Envelopes</CardTitle>
                      <CardDescription className="text-base">
                        Generate print-ready envelopes
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm text-muted-foreground leading-relaxed">
                        Create professional #10 business envelopes with your return
                        address and AI-powered recipient parsing.
                      </p>
                    </CardContent>
                  </Card>

                  {/* Generated Documents Card */}
                  <Card
                    className="group cursor-pointer border-2 hover:border-primary/50 transition-all duration-300 hover:shadow-xl hover:-translate-y-1 bg-gradient-to-br from-white to-slate-50/50 dark:from-slate-900 dark:to-slate-800/50"
                    onClick={() => setActiveTab('documents')}
                  >
                    <CardHeader className="pb-4">
                      <div className="flex items-start justify-between mb-4">
                        <div className="p-4 bg-gradient-to-br from-orange-500 to-orange-600 rounded-xl shadow-lg shadow-orange-500/20 group-hover:shadow-orange-500/40 transition-shadow">
                          <Files className="h-7 w-7 text-white" />
                        </div>
                        <ArrowRight className="h-5 w-5 text-muted-foreground group-hover:text-primary group-hover:translate-x-1 transition-all" />
                      </div>
                      <CardTitle className="text-2xl mb-2">Documents</CardTitle>
                      <CardDescription className="text-base">
                        View your generated documents
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm text-muted-foreground leading-relaxed">
                        Browse, download, and manage all your previously generated
                        documents and envelopes in one place.
                      </p>
                    </CardContent>
                  </Card>
                </div>
              </div>
            </div>
          )}

          {/* Search View */}
          {activeTab === 'search' && (
            <div className="p-8">
              <div className="mb-6">
                <h2 className="text-3xl font-bold mb-2">Document Search</h2>
                <p className="text-muted-foreground">
                  Upload and search through your legal documents
                </p>
              </div>
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Left Column - Upload & Documents */}
                <div className="space-y-6">
                  <FileUpload onUploadComplete={handleUploadComplete} />
                  <DocumentList refreshTrigger={refreshTrigger} />
                </div>

                {/* Right Column - Search & Results */}
                <div className="lg:col-span-2 space-y-6">
                  <SearchBar onSearchComplete={handleSearchComplete} />
                  <SearchResults searchResponse={searchResponse} />
                </div>
              </div>
            </div>
          )}

          {/* Document Automation View */}
          {activeTab === 'automation' && (
            <div className="p-8">
              <div className="mb-6">
                <h2 className="text-3xl font-bold mb-2">Document Automation</h2>
                <p className="text-muted-foreground">
                  Generate professional documents from templates
                </p>
              </div>
              <DocumentAutomation />
            </div>
          )}

          {/* Envelope Generation View */}
          {activeTab === 'envelope' && (
            <div className="p-8">
              <div className="mb-6">
                <h2 className="text-3xl font-bold mb-2">Envelope Generation</h2>
                <p className="text-muted-foreground">
                  Create print-ready #10 business envelopes
                </p>
              </div>
              <EnvelopeGeneration />
            </div>
          )}

          {/* Generated Documents View */}
          {activeTab === 'documents' && (
            <div className="p-8">
              <div className="mb-6">
                <h2 className="text-3xl font-bold mb-2">Generated Documents</h2>
                <p className="text-muted-foreground">
                  View, download, and manage your generated documents
                </p>
              </div>
              <GeneratedDocuments />
            </div>
          )}

          {/* Settings View */}
          {activeTab === 'settings' && (
            <div className="p-8">
              <div className="mb-6">
                <h2 className="text-3xl font-bold mb-2">Settings</h2>
                <p className="text-muted-foreground">
                  Manage your default settings and preferences
                </p>
              </div>
              <Settings />
            </div>
          )}
          </main>
        </div>
      </SignedIn>

      {/* Footer */}
      <footer className="border-t mt-12">
        <div className="container mx-auto px-4 py-6 text-center text-sm text-muted-foreground">
          <p>
            Built with FastAPI, ChromaDB, sentence-transformers, React, TypeScript & shadcn/ui
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;
