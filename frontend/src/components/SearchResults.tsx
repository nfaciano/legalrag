import { FileText, AlertCircle, Sparkles } from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { SearchResponse } from "@/types/api";

interface SearchResultsProps {
  searchResponse: SearchResponse | null;
}

export function SearchResults({ searchResponse }: SearchResultsProps) {
  if (!searchResponse) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="text-center py-8 text-muted-foreground">
            <AlertCircle className="mx-auto h-12 w-12 mb-4 opacity-50" />
            <p>No search results yet. Try searching above.</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (searchResponse.results.length === 0) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="text-center py-8 text-muted-foreground">
            <AlertCircle className="mx-auto h-12 w-12 mb-4 opacity-50" />
            <p>No results found for "{searchResponse.query}"</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {/* Synthesized Answer (if available) */}
      {searchResponse.synthesized_answer && (
        <Card className="border-primary/50 bg-primary/5">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-primary" />
              <CardTitle>AI-Generated Answer</CardTitle>
            </div>
            <CardDescription>
              Synthesized from {searchResponse.total_results} relevant sources using Groq
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="prose prose-sm max-w-none">
              <p className="text-sm leading-relaxed whitespace-pre-wrap">
                {searchResponse.synthesized_answer}
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Header */}
      <Card>
        <CardHeader>
          <CardTitle>
            {searchResponse.synthesized_answer ? "Source Documents" : "Search Results"}
          </CardTitle>
          <CardDescription>
            Found {searchResponse.total_results} relevant passages for "
            {searchResponse.query}"
          </CardDescription>
        </CardHeader>
      </Card>

      {/* Results */}
      {searchResponse.results.map((result) => (
        <Card key={result.metadata.chunk_id} className="hover:shadow-md transition-shadow">
          <CardHeader>
            <div className="flex items-start justify-between gap-4">
              <div className="flex items-center gap-2 flex-1">
                <FileText className="h-5 w-5 text-primary" />
                <div>
                  <CardTitle className="text-base">
                    {result.metadata.filename}
                  </CardTitle>
                  <CardDescription className="text-xs">
                    Page {result.metadata.page} • Chunk {result.metadata.chunk_id.split("_").pop()}
                  </CardDescription>
                </div>
              </div>
              <Badge variant="secondary">
                Score: {(result.similarity_score * 100).toFixed(1)}%
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-sm leading-relaxed">{result.text}</p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
