import { useState } from "react";
import { Search, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { apiClient } from "@/lib/api";
import type { SearchResponse } from "@/types/api";

interface SearchBarProps {
  onSearchComplete: (response: SearchResponse) => void;
}

export function SearchBar({ onSearchComplete }: SearchBarProps) {
  const [query, setQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [generateAnswer, setGenerateAnswer] = useState(false);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!query.trim()) {
      setError("Please enter a search query");
      return;
    }

    setIsSearching(true);
    setError(null);

    try {
      const response = await apiClient.searchDocuments({
        query: query.trim(),
        top_k: 5,
        use_reranking: true,
        synthesize_answer: generateAnswer,
      });
      onSearchComplete(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed");
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <Card>
      <CardContent className="pt-6">
        <form onSubmit={handleSearch} className="space-y-4">
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                type="text"
                placeholder="Ask a question about your legal documents..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="pl-10"
                disabled={isSearching}
              />
            </div>
            <Button type="submit" disabled={isSearching}>
              {isSearching ? "Searching..." : "Search"}
            </Button>
          </div>
          <div className="flex items-center space-x-2">
            <Checkbox
              id="generate-answer"
              checked={generateAnswer}
              onCheckedChange={(checked) => setGenerateAnswer(checked === true)}
              disabled={isSearching}
            />
            <label
              htmlFor="generate-answer"
              className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 cursor-pointer flex items-center gap-1"
            >
              <Sparkles className="h-3 w-3 text-primary" />
              Generate AI Answer (powered by Groq)
            </label>
          </div>
          {error && <p className="text-sm text-destructive">{error}</p>}
        </form>
      </CardContent>
    </Card>
  );
}
