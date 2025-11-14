import { useState } from "react";
import { Scale } from "lucide-react";
import { SignedIn, SignedOut, SignInButton, UserButton } from "@clerk/clerk-react";
import { FileUpload } from "@/components/FileUpload";
import { SearchBar } from "@/components/SearchBar";
import { SearchResults } from "@/components/SearchResults";
import { DocumentList } from "@/components/DocumentList";
import type { SearchResponse, UploadResponse } from "@/types/api";

function App() {
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
      <header className="border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Scale className="h-8 w-8 text-primary" />
              <div>
                <h1 className="text-2xl font-bold">LegalRAG</h1>
                <p className="text-sm text-muted-foreground">
                  Semantic search for legal documents
                </p>
              </div>
            </div>
            <div>
              <SignedOut>
                <SignInButton mode="modal">
                  <button className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90">
                    Sign In
                  </button>
                </SignInButton>
              </SignedOut>
              <SignedIn>
                <UserButton afterSignOutUrl="/" />
              </SignedIn>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <SignedOut>
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
        </SignedOut>

        <SignedIn>
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
        </SignedIn>
      </main>

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
