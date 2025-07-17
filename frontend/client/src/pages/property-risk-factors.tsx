import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { useQuery, useMutation } from "@tanstack/react-query";
import { useToast } from "@/hooks/use-toast";
import { apiClient } from "@/lib/api";
import { Shield, AlertTriangle, CheckCircle, Info, MapPin, Home, FileText } from "lucide-react";

interface Policy {
  id: number;
  policyNumber: string;
  policyholderName: string;
  propertyAddress?: string;
}

interface RiskAnalysisResponse {
  zipCode: string;
  riskFactors: {
    floodRisk: string;
    tornadoRisk: string;
    hailRisk: string;
    winterRisk: string;
    agriculturalRisk: string;
    region: string;
  };
  recommendations: {
    riskMitigation: string[];
    coverageRecommendations: string[];
    homeImprovements: string[];
    emergencyPreparedness: string[];
    iowaSpecificNotes: string[];
  };
  policyContext: any;
  iowaSpecific: boolean;
}

export function PropertyRiskFactors() {
  const [selectedPolicy, setSelectedPolicy] = useState("");
  const [userQuery, setUserQuery] = useState("");
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<RiskAnalysisResponse | null>(null);
  const [extractedZipCode, setExtractedZipCode] = useState<string>("");
  const { toast } = useToast();

  // Load policies for selection
  const { data } = useQuery<Policy[]>({
    queryKey: ['policies'],
    queryFn: async (): Promise<Policy[]> => {
      const result = await apiClient.getPolicies();
      return (result.data as Policy[]) || [];
    }
  });
  const policies = Array.isArray(data) ? data : [];
  

  const analyzeRiskMutation = useMutation({
    mutationFn: async (data: { policyId: string; userQuery?: string }) => {
      const response = await fetch('/api/risk-factors/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      if (!response.ok) throw new Error('Failed to analyze risk factors');
      return response.json();
    },
    onSuccess: (data) => {
      setAnalysisResult(data);
      setExtractedZipCode(data.zipCode);
      toast({
        title: "Risk Analysis Complete",
        description: `Analyzed risks for ZIP code ${data.zipCode}`,
      });
    },
    onError: (error) => {
      toast({
        title: "Analysis Failed",
        description: error.message,
        variant: "destructive",
      });
    }
  });

  const handleAnalyze = () => {
    if (!selectedPolicy) {
      toast({
        title: "Policy Required",
        description: "Please select a policy to analyze",
        variant: "destructive",
      });
      return;
    }

    setIsAnalyzing(true);
    analyzeRiskMutation.mutate({
      policyId: selectedPolicy,
      userQuery: userQuery || undefined
    }, {
      onSettled: () => setIsAnalyzing(false)
    });
  };

  const getRiskColor = (risk: string) => {
    switch (risk.toLowerCase()) {
      case 'high': return 'bg-red-100 text-red-800 border-red-200';
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'low': return 'bg-green-100 text-green-800 border-green-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getRiskIcon = (risk: string) => {
    switch (risk.toLowerCase()) {
      case 'high': return <AlertTriangle className="w-4 h-4" />;
      case 'medium': return <Info className="w-4 h-4" />;
      case 'low': return <CheckCircle className="w-4 h-4" />;
      default: return <Info className="w-4 h-4" />;
    }
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center space-x-2">
        <AlertTriangle className="w-8 h-8 text-orange-500" />
        <div>
          <h1 className="text-3xl font-bold">Property Risk Factors</h1>
          <p className="text-gray-600">Iowa-specific risk analysis based on policy data</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Policy Selection */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <FileText className="w-5 h-5" />
              <span>Select Policy</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="policy-select">Choose a Policy</Label>
              <Select value={selectedPolicy} onValueChange={setSelectedPolicy}>
                <SelectTrigger>
                  <SelectValue placeholder="Select a policy to analyze..." />
                </SelectTrigger>
                <SelectContent>
                  {policies.map((policy) => (
                    <SelectItem key={policy.id} value={policy.id.toString()}>
                      <div className="flex flex-col">
                        <span className="font-medium">{policy.policyNumber}</span>
                        <span className="text-sm text-gray-500">{policy.policyholderName}</span>
                        {policy.propertyAddress && (
                          <span className="text-xs text-gray-400">{policy.propertyAddress}</span>
                        )}
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {selectedPolicy && (
              <div className="p-3 bg-blue-50 rounded-lg">
                <div className="flex items-center space-x-2 text-sm text-blue-700">
                  <MapPin className="w-4 h-4" />
                  <span>
                    ZIP code will be automatically extracted from the property address
                  </span>
                </div>
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="user-query">Custom Question (Optional)</Label>
              <Textarea
                id="user-query"
                placeholder="Ask a specific question about risk factors, coverage recommendations, or home improvements..."
                value={userQuery}
                onChange={(e) => setUserQuery(e.target.value)}
                rows={3}
              />
            </div>

            <Button 
              onClick={handleAnalyze} 
              disabled={!selectedPolicy || isAnalyzing}
              className="w-full"
            >
              {isAnalyzing ? "Analyzing..." : "Analyze Risk Factors"}
            </Button>
          </CardContent>
        </Card>

        {/* Results */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Shield className="w-5 h-5" />
              <span>Risk Analysis Results</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {analysisResult ? (
              <div className="space-y-6">
                {/* ZIP Code Display */}
                <div className="flex items-center space-x-2 p-3 bg-gray-50 rounded-lg">
                  <MapPin className="w-4 h-4 text-gray-600" />
                  <span className="font-medium">ZIP Code: {extractedZipCode}</span>
                  <Badge variant="outline">{analysisResult.riskFactors.region}</Badge>
                </div>

                {/* Risk Factors */}
                <div>
                  <h3 className="font-semibold mb-3">Risk Assessment</h3>
                  <div className="grid grid-cols-1 gap-2">
                    {Object.entries(analysisResult.riskFactors).filter(([key]) => key !== 'region' && key !== 'zipCode').map(([risk, level]) => (
                      <div key={risk} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                        <span className="capitalize">{risk.replace('Risk', '')}</span>
                        <Badge className={getRiskColor(level)}>
                          <div className="flex items-center space-x-1">
                            {getRiskIcon(level)}
                            <span className="capitalize">{level}</span>
                          </div>
                        </Badge>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Recommendations */}
                <div className="space-y-4">
                  <h3 className="font-semibold">Recommendations</h3>
                  
                  {analysisResult.recommendations.riskMitigation.length > 0 && (
                    <div>
                      <h4 className="font-medium text-sm text-gray-700 mb-2">Risk Mitigation</h4>
                      <ul className="space-y-1 text-sm">
                        {analysisResult.recommendations.riskMitigation.map((item, index) => (
                          <li key={index} className="flex items-start space-x-2">
                            <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                            <span>{item}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {analysisResult.recommendations.coverageRecommendations.length > 0 && (
                    <div>
                      <h4 className="font-medium text-sm text-gray-700 mb-2">Coverage Recommendations</h4>
                      <ul className="space-y-1 text-sm">
                        {analysisResult.recommendations.coverageRecommendations.map((item, index) => (
                          <li key={index} className="flex items-start space-x-2">
                            <Shield className="w-4 h-4 text-blue-500 mt-0.5 flex-shrink-0" />
                            <span>{item}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {analysisResult.recommendations.homeImprovements.length > 0 && (
                    <div>
                      <h4 className="font-medium text-sm text-gray-700 mb-2">Home Improvements</h4>
                      <ul className="space-y-1 text-sm">
                        {analysisResult.recommendations.homeImprovements.map((item, index) => (
                          <li key={index} className="flex items-start space-x-2">
                            <Home className="w-4 h-4 text-purple-500 mt-0.5 flex-shrink-0" />
                            <span>{item}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {analysisResult.recommendations.iowaSpecificNotes.length > 0 && (
                    <div>
                      <h4 className="font-medium text-sm text-gray-700 mb-2">Iowa-Specific Considerations</h4>
                      <ul className="space-y-1 text-sm">
                        {analysisResult.recommendations.iowaSpecificNotes.map((item, index) => (
                          <li key={index} className="flex items-start space-x-2">
                            <AlertTriangle className="w-4 h-4 text-orange-500 mt-0.5 flex-shrink-0" />
                            <span>{item}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <Shield className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                <p>Select a policy and click "Analyze Risk Factors" to get started</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default PropertyRiskFactors; 