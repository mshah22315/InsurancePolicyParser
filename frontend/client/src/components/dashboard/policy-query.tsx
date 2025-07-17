import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useState, useEffect } from "react";
import { useToast } from "@/hooks/use-toast";
import { Search, MessageSquare, Loader2 } from "lucide-react";
import { apiClient } from "@/lib/api";

interface QueryResponse {
  answer: string;
  sources: string[];
  confidence: number;
}

export function PolicyQuery() {
  const [query, setQuery] = useState("");
  const [selectedPolicy, setSelectedPolicy] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [response, setResponse] = useState<QueryResponse | null>(null);
  const [policies, setPolicies] = useState<any[]>([]);
  const { toast } = useToast();

  // Load policies for selection
  useEffect(() => {
    const loadPolicies = async () => {
      try {
        const result = await apiClient.getPolicies();
        if (result.data && Array.isArray(result.data)) {
          setPolicies(result.data);
        }
      } catch (error) {
        console.error("Failed to load policies:", error);
      }
    };
    loadPolicies();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || !selectedPolicy) {
      toast({
        title: "Missing Information",
        description: "Please enter a question and select a policy.",
        variant: "destructive",
      });
      return;
    }

    setIsLoading(true);
    setResponse(null);

    try {
      // This would call your backend query endpoint
      const result = await apiClient.queryPolicy(selectedPolicy, query);
      
      if (result.data && typeof result.data === 'object') {
        setResponse(result.data as QueryResponse);
        toast({
          title: "Query Successful",
          description: "Found answer in policy documents.",
        });
      } else {
        toast({
          title: "No Answer Found",
          description: "Could not find relevant information in the selected policy.",
          variant: "destructive",
        });
      }
    } catch (error) {
      toast({
        title: "Query Failed",
        description: "Failed to process your question. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const exampleQueries = [
    "What is the total premium for this policy?",
    "What is the deductible for wind damage?",
    "What is the effective date of this policy?",
    "What coverage is included for flood damage?",
    "What is the property address?"
  ];

  const handleExampleClick = (example: string) => {
    setQuery(example);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <MessageSquare className="w-5 h-5" />
          Policy Query System
        </CardTitle>
      </CardHeader>
      
      <CardContent className="space-y-6">
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Policy Selection */}
          <div>
            <Label htmlFor="policy">Select Policy</Label>
            <Select value={selectedPolicy} onValueChange={setSelectedPolicy}>
              <SelectTrigger>
                <SelectValue placeholder="Choose a policy to query" />
              </SelectTrigger>
              <SelectContent>
                {policies.map((policy) => (
                  <SelectItem key={policy.id} value={policy.id.toString()}>
                    {policy.policyNumber} - {policy.policyholderName}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Query Input */}
          <div>
            <Label htmlFor="query">Your Question</Label>
            <Textarea
              id="query"
              placeholder="Ask a question about the selected policy..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              rows={3}
              className="resize-none"
            />
          </div>

          {/* Example Queries */}
          <div>
            <Label className="text-sm text-gray-600">Example Questions:</Label>
            <div className="flex flex-wrap gap-2 mt-2">
              {exampleQueries.map((example, index) => (
                <Button
                  key={index}
                  variant="outline"
                  size="sm"
                  onClick={() => handleExampleClick(example)}
                  className="text-xs"
                >
                  {example}
                </Button>
              ))}
            </div>
          </div>

          {/* Submit Button */}
          <Button 
            type="submit" 
            className="w-full" 
            disabled={!query.trim() || !selectedPolicy || isLoading}
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Searching...
              </>
            ) : (
              <>
                <Search className="w-4 h-4 mr-2" />
                Ask Question
              </>
            )}
          </Button>
        </form>

        {/* Response Display */}
        {response && (
          <div className="mt-6 p-4 bg-blue-50 rounded-lg border">
            <h4 className="font-semibold text-blue-900 mb-2">Answer:</h4>
            <p className="text-blue-800 mb-3">{response.answer}</p>
            
            {response.sources && response.sources.length > 0 && (
              <div>
                <h5 className="font-medium text-blue-900 mb-1">Sources:</h5>
                <ul className="text-sm text-blue-700">
                  {response.sources.map((source, index) => (
                    <li key={index}>• {source}</li>
                  ))}
                </ul>
              </div>
            )}
            
            {response.confidence && (
              <div className="mt-2">
                <span className="text-sm text-blue-600">
                  Confidence: {Math.round(response.confidence * 100)}%
                </span>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
} 