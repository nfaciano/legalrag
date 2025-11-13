import { useState } from "react";
import { Scale } from "lucide-react";
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
          <div className="flex items-center gap-3">
            <Scale className="h-8 w-8 text-primary" />
            <div>
              <h1 className="text-2xl font-bold">LegalRAG</h1>
              <p className="text-sm text-muted-foreground">
                Semantic search for legal documents
              </p>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
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
