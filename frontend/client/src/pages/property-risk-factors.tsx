import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { useQuery, useMutation } from "@tanstack/react-query";
import { useToast } from "@/hooks/use-toast";
import { apiClient } from "@/lib/api";
import { Shield, AlertTriangle, CheckCircle, Info, MapPin, Home, FileText, ThumbsUp, ThumbsDown } from "lucide-react";
import jsPDF from "jspdf";

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
  const [mode, setMode] = useState<'policy' | 'zip'>('policy');
  const [manualZip, setManualZip] = useState("");
  const [homeType, setHomeType] = useState("");
  const [userFeedback, setUserFeedback] = useState<boolean | null>(null);
  const [feedbackComment, setFeedbackComment] = useState("");
  const [isSubmittingFeedback, setIsSubmittingFeedback] = useState(false);
  const [customQuestions, setCustomQuestions] = useState<string[]>([]);
  const [newQuestion, setNewQuestion] = useState("");
  const { toast } = useToast();
  const [feedbackHistory, setFeedbackHistory] = useState<any[]>([]);
  const [recommendationFeedback, setRecommendationFeedback] = useState<Record<string, boolean | null>>({});

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
    mutationFn: async (data: any) => {
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

  // Add question to list
  const handleAddQuestion = () => {
    if (newQuestion.trim()) {
      setCustomQuestions([...customQuestions, newQuestion.trim()]);
      setNewQuestion("");
    }
  };

  // Remove question from list
  const handleRemoveQuestion = (idx: number) => {
    setCustomQuestions(customQuestions.filter((_, i) => i !== idx));
  };

  // Add a helper to check if a question is coverage/deductible related
  const isCoverageOrDeductible = (q: string) => /coverage|deductible/i.test(q);

  const handleAnalyze = () => {
    const combinedUserQuery = [
      ...customQuestions,
      userQuery.trim() ? userQuery.trim() : null
    ].filter(Boolean).join("\n");
    if (mode === 'policy') {
      if (!selectedPolicy) {
        toast({
          title: "Policy Required",
          description: "Please select a policy to analyze",
          variant: "destructive",
        });
        return;
      }
      if (!homeType) {
        toast({
          title: "Home Type Required",
          description: "Please select a home type",
          variant: "destructive",
        });
        return;
      }
      setIsAnalyzing(true);
      analyzeRiskMutation.mutate({
        policyId: selectedPolicy,
        userQuery: combinedUserQuery || undefined,
        policyContext: {
          homeType: homeType
        }
      }, {
        onSettled: () => setIsAnalyzing(false)
      });
    } else {
      // Manual ZIP mode
      if (!manualZip.match(/^\d{5}$/)) {
        toast({
          title: "ZIP Code Required",
          description: "Please enter a valid 5-digit ZIP code",
          variant: "destructive",
        });
        return;
      }
      if (!homeType) {
        toast({
          title: "Home Type Required",
          description: "Please select a home type",
          variant: "destructive",
        });
        return;
      }
      setIsAnalyzing(true);
      analyzeRiskMutation.mutate({
        zipCode: manualZip,
        userQuery: combinedUserQuery || undefined,
        policyContext: {
          propertyFeatures: [],
          homeType: homeType
        }
      }, {
        onSettled: () => setIsAnalyzing(false)
      });
    }
  };

  // Helper to send feedback to backend
  const sendFeedback = async (feedback: boolean, comment?: string) => {
    setIsSubmittingFeedback(true);
    const payload: any = {
      userFeedback: feedback,
      zipCode: analysisResult?.zipCode,
      policyId: mode === 'policy' ? selectedPolicy : undefined,
      userQuery: comment || userQuery,
      policyContext: mode === 'policy' ? { homeType } : { homeType, propertyFeatures: [] }
    };
    await fetch('/api/feedback/risk-analysis', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    setIsSubmittingFeedback(false);
  };

  // Handler for upvote
  const handleUpvote = async () => {
    setUserFeedback(true);
    await sendFeedback(true);
  };

  // Handler for downvote
  const handleDownvote = () => {
    setUserFeedback(false);
  };

  // Handler for submitting downvote comment and triggering new analysis
  const handleSubmitFeedback = async () => {
    await sendFeedback(false, feedbackComment);
    setUserQuery(feedbackComment);
    setFeedbackComment("");
    setUserFeedback(null);
    setIsAnalyzing(true);
    analyzeRiskMutation.mutate(
      mode === 'policy'
        ? {
            policyId: selectedPolicy,
            userQuery: feedbackComment,
            policyContext: { homeType }
          }
        : {
            zipCode: manualZip,
            userQuery: feedbackComment,
            policyContext: { homeType, propertyFeatures: [] }
          },
      {
        onSettled: () => setIsAnalyzing(false)
      }
    );
  };

  // Helper to send per-recommendation feedback
  const sendRecommendationFeedback = useCallback(async (recText: string, recType: string, feedback: boolean) => {
    const payload: any = {
      userFeedback: feedback,
      zipCode: analysisResult?.zipCode,
      policyId: mode === 'policy' ? selectedPolicy : undefined,
      userQuery: recText,
      policyContext: mode === 'policy' ? { homeType } : { homeType, propertyFeatures: [] },
      feedbackComment: null,
      recommendationType: recType,
      recommendationText: recText
    };
    await fetch('/api/feedback/risk-analysis', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
  }, [analysisResult, mode, selectedPolicy, homeType, manualZip]);

  // Handler for per-recommendation feedback
  const handleRecommendationFeedback = (recText: string, recType: string, feedback: boolean) => {
    setRecommendationFeedback(prev => ({ ...prev, [recType + ':' + recText]: feedback }));
    sendRecommendationFeedback(recText, recType, feedback);
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

  // Add a helper to get numeric value for risk
  const getRiskNumeric = (risk: string) => {
    switch (risk.toLowerCase()) {
      case 'high': return 3;
      case 'medium': return 2;
      case 'low': return 1;
      default: return 0;
    }
  };

  // Fetch feedback history on mount
  useEffect(() => {
    fetch('/api/feedback/risk-analysis/history')
      .then(res => res.json())
      .then(data => setFeedbackHistory(Array.isArray(data) ? data : []));
  }, []);

  // PDF export handler
  const handleExportPDF = () => {
    if (!analysisResult) return;
    const doc = new jsPDF({ unit: 'mm', format: 'a4' });
    let y = 10;
    const pageHeight = 297; // A4 height in mm
    const bottomMargin = 20;
    const maxWidth = 180; // page width minus margins
    const checkPage = (lines = 1) => {
      if (y + lines * 6 > pageHeight - bottomMargin) {
        doc.addPage();
        y = 10;
      }
    };
    doc.setFontSize(16);
    doc.text("Property Risk Analysis Report", 10, y);
    y += 10;
    doc.setFontSize(10);
    doc.text(`ZIP Code: ${analysisResult.zipCode || ''}`, 10, y);
    y += 7;
    doc.text(`Region: ${analysisResult.riskFactors.region || ''}`, 10, y);
    y += 10;
    doc.setFontSize(12);
    doc.text("Risk Factors:", 10, y);
    y += 7;
    doc.setFontSize(10);
    Object.entries(analysisResult.riskFactors).forEach(([key, value]) => {
      if (key !== 'region' && key !== 'zipCode') {
        const line = `${key.replace('Risk', '')}: ${value}`;
        const wrapped = doc.splitTextToSize(line, maxWidth);
        wrapped.forEach((wline: string) => {
          doc.text(wline, 12, y);
          y += 6;
          checkPage();
        });
      }
    });
    y += 4;
    doc.setFontSize(12);
    doc.text("Recommendations:", 10, y);
    y += 7;
    doc.setFontSize(10);
    const addRecSection = (title: string, items: string[]) => {
      if (items.length === 0) return;
      const wrappedTitle = doc.splitTextToSize(title, maxWidth);
      wrappedTitle.forEach((wline: string) => {
        doc.text(wline, 12, y);
        y += 6;
        checkPage();
      });
      items.forEach((item) => {
        const wrapped = doc.splitTextToSize(`- ${item}`, maxWidth);
        wrapped.forEach((wline: string) => {
          doc.text(wline, 14, y);
          y += 6;
          checkPage();
        });
      });
      y += 2;
      checkPage();
    };
    addRecSection("Risk Mitigation", analysisResult.recommendations.riskMitigation);
    addRecSection("Coverage Recommendations", analysisResult.recommendations.coverageRecommendations);
    addRecSection("Home Improvements", analysisResult.recommendations.homeImprovements);
    addRecSection("Emergency Preparedness", analysisResult.recommendations.emergencyPreparedness);
    addRecSection("Iowa-Specific Notes", analysisResult.recommendations.iowaSpecificNotes);
    doc.save("risk-analysis-report.pdf");
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center space-x-2">
        <AlertTriangle className="w-8 h-8 text-orange-500" />
        <div>
          <h1 className="text-3xl font-bold">Property Risk Factors</h1>
          <p className="text-gray-600">Iowa-specific risk analysis based on policy data or ZIP code</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Input Section */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <FileText className="w-5 h-5" />
              <span>Analyze by Policy or ZIP Code</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Choose Input Method</Label>
              <div className="flex space-x-4">
                <label className="flex items-center space-x-2">
                  <input type="radio" value="policy" checked={mode === 'policy'} onChange={() => setMode('policy')} />
                  <span>Choose Policy</span>
                </label>
                <label className="flex items-center space-x-2">
                  <input type="radio" value="zip" checked={mode === 'zip'} onChange={() => setMode('zip')} />
                  <span>Enter ZIP Code</span>
                </label>
              </div>
            </div>

            {mode === 'policy' && (
              <>
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
                {/* Type of Home for Policy Mode */}
                <div className="space-y-2">
                  <Label htmlFor="home-type-policy">Type of Home</Label>
                  <Select value={homeType} onValueChange={setHomeType}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select home type..." />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Single Family">Single Family</SelectItem>
                      <SelectItem value="Condo">Condo</SelectItem>
                      <SelectItem value="Townhouse">Townhouse</SelectItem>
                      <SelectItem value="Multi-Family">Multi-Family</SelectItem>
                      <SelectItem value="Mobile Home">Mobile Home</SelectItem>
                      <SelectItem value="Other">Other</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </>
            )}

            {mode === 'zip' && (
              <>
                <div className="space-y-2">
                  <Label htmlFor="zip-input">Enter ZIP Code</Label>
                  <input
                    id="zip-input"
                    type="text"
                    value={manualZip}
                    onChange={e => setManualZip(e.target.value.replace(/[^0-9]/g, '').slice(0, 5))}
                    placeholder="e.g. 50309"
                    className="w-full border rounded px-3 py-2"
                    maxLength={5}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="home-type">Type of Home</Label>
                  <Select value={homeType} onValueChange={setHomeType}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select home type..." />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Single Family">Single Family</SelectItem>
                      <SelectItem value="Condo">Condo</SelectItem>
                      <SelectItem value="Townhouse">Townhouse</SelectItem>
                      <SelectItem value="Multi-Family">Multi-Family</SelectItem>
                      <SelectItem value="Mobile Home">Mobile Home</SelectItem>
                      <SelectItem value="Other">Other</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </>
            )}

            <div className="space-y-2">
              <Label htmlFor="custom-questions">Custom Questions/Comments</Label>
              <div className="flex space-x-2">
                <input
                  id="custom-questions"
                  type="text"
                  value={newQuestion}
                  onChange={e => setNewQuestion(e.target.value)}
                  placeholder="Add a question or comment..."
                  className="w-full border rounded px-3 py-2"
                  onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); handleAddQuestion(); } }}
                />
                <Button onClick={handleAddQuestion} disabled={!newQuestion.trim()}>Add</Button>
              </div>
              {customQuestions.length > 0 && (
                <ul className="mt-2 space-y-1">
                  {customQuestions.map((q, idx) => (
                    <li
                      key={idx}
                      className={`flex items-center justify-between rounded px-3 py-1 ${isCoverageOrDeductible(q) ? 'bg-yellow-100 border border-yellow-300' : 'bg-gray-50'}`}
                    >
                      <span className="text-sm flex items-center">
                        {isCoverageOrDeductible(q) && (
                          <span className="inline-flex items-center px-2 py-0.5 mr-2 rounded bg-yellow-200 text-yellow-900 text-xs font-semibold">
                            Coverage/Deductible
                          </span>
                        )}
                        {q}
                      </span>
                      <Button size="sm" variant="ghost" onClick={() => handleRemoveQuestion(idx)} aria-label="Remove">✕</Button>
                    </li>
                  ))}
                </ul>
              )}
            </div>

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

            {/* Remove the Analyze Risk Factors button from the input card */}
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
            <Button 
              onClick={handleAnalyze} 
              disabled={(mode === 'policy' && !selectedPolicy) || (mode === 'zip' && (!manualZip.match(/^\d{5}$/) || !homeType)) || isAnalyzing}
              className="w-full mb-4"
            >
              {isAnalyzing ? "Analyzing..." : "Analyze Risk Factors"}
            </Button>
            {analysisResult ? (
              <div className="space-y-6">
                {/* Export as PDF button */}
                <Button onClick={handleExportPDF} className="mb-2" variant="outline">Export as PDF</Button>
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
                            <span className="ml-2 text-xs text-gray-500">({getRiskNumeric(level)})</span>
                          </div>
                        </Badge>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Recommendations */}
                {analysisResult.recommendations.riskMitigation.length > 0 && (
  <div>
    <h4 className="font-medium text-sm text-gray-700 mb-2">Risk Mitigation</h4>
    <ul className="space-y-1 text-sm">
      {analysisResult.recommendations.riskMitigation.map((item, index) => (
        <li key={index} className="flex items-start space-x-2 items-center">
          <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
          <span>{item}</span>
          <button
            className={`ml-2 p-1 rounded-full border ${recommendationFeedback['riskMitigation:' + item] === true ? 'bg-green-100 border-green-400' : 'bg-white border-gray-300'}`}
            onClick={() => handleRecommendationFeedback(item, 'riskMitigation', true)}
            aria-label="Upvote"
          >
            <ThumbsUp className={`w-4 h-4 ${recommendationFeedback['riskMitigation:' + item] === true ? 'text-green-600' : 'text-gray-500'}`} />
          </button>
          <button
            className={`ml-1 p-1 rounded-full border ${recommendationFeedback['riskMitigation:' + item] === false ? 'bg-red-100 border-red-400' : 'bg-white border-gray-300'}`}
            onClick={() => handleRecommendationFeedback(item, 'riskMitigation', false)}
            aria-label="Downvote"
          >
            <ThumbsDown className={`w-4 h-4 ${recommendationFeedback['riskMitigation:' + item] === false ? 'text-red-600' : 'text-gray-500'}`} />
          </button>
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
        <li key={index} className="flex items-start space-x-2 p-2 rounded bg-yellow-100 text-yellow-900 border border-yellow-300 items-center">
          <Shield className="w-4 h-4 text-blue-500 mt-0.5 flex-shrink-0" />
          <span>{item}</span>
          <button
            className={`ml-2 p-1 rounded-full border ${recommendationFeedback['coverageRecommendations:' + item] === true ? 'bg-green-100 border-green-400' : 'bg-white border-gray-300'}`}
            onClick={() => handleRecommendationFeedback(item, 'coverageRecommendations', true)}
            aria-label="Upvote"
          >
            <ThumbsUp className={`w-4 h-4 ${recommendationFeedback['coverageRecommendations:' + item] === true ? 'text-green-600' : 'text-gray-500'}`} />
          </button>
          <button
            className={`ml-1 p-1 rounded-full border ${recommendationFeedback['coverageRecommendations:' + item] === false ? 'bg-red-100 border-red-400' : 'bg-white border-gray-300'}`}
            onClick={() => handleRecommendationFeedback(item, 'coverageRecommendations', false)}
            aria-label="Downvote"
          >
            <ThumbsDown className={`w-4 h-4 ${recommendationFeedback['coverageRecommendations:' + item] === false ? 'text-red-600' : 'text-gray-500'}`} />
          </button>
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
        <li key={index} className="flex items-start space-x-2 items-center">
          <Home className="w-4 h-4 text-purple-500 mt-0.5 flex-shrink-0" />
          <span>{item}</span>
          <button
            className={`ml-2 p-1 rounded-full border ${recommendationFeedback['homeImprovements:' + item] === true ? 'bg-green-100 border-green-400' : 'bg-white border-gray-300'}`}
            onClick={() => handleRecommendationFeedback(item, 'homeImprovements', true)}
            aria-label="Upvote"
          >
            <ThumbsUp className={`w-4 h-4 ${recommendationFeedback['homeImprovements:' + item] === true ? 'text-green-600' : 'text-gray-500'}`} />
          </button>
          <button
            className={`ml-1 p-1 rounded-full border ${recommendationFeedback['homeImprovements:' + item] === false ? 'bg-red-100 border-red-400' : 'bg-white border-gray-300'}`}
            onClick={() => handleRecommendationFeedback(item, 'homeImprovements', false)}
            aria-label="Downvote"
          >
            <ThumbsDown className={`w-4 h-4 ${recommendationFeedback['homeImprovements:' + item] === false ? 'text-red-600' : 'text-gray-500'}`} />
          </button>
        </li>
      ))}
    </ul>
  </div>
)}
{analysisResult.recommendations.emergencyPreparedness.length > 0 && (
  <div>
    <h4 className="font-medium text-sm text-gray-700 mb-2">Emergency Preparedness</h4>
    <ul className="space-y-1 text-sm">
      {analysisResult.recommendations.emergencyPreparedness.map((item, index) => (
        <li key={index} className="flex items-start space-x-2 items-center">
          <Info className="w-4 h-4 text-orange-500 mt-0.5 flex-shrink-0" />
          <span>{item}</span>
          <button
            className={`ml-2 p-1 rounded-full border ${recommendationFeedback['emergencyPreparedness:' + item] === true ? 'bg-green-100 border-green-400' : 'bg-white border-gray-300'}`}
            onClick={() => handleRecommendationFeedback(item, 'emergencyPreparedness', true)}
            aria-label="Upvote"
          >
            <ThumbsUp className={`w-4 h-4 ${recommendationFeedback['emergencyPreparedness:' + item] === true ? 'text-green-600' : 'text-gray-500'}`} />
          </button>
          <button
            className={`ml-1 p-1 rounded-full border ${recommendationFeedback['emergencyPreparedness:' + item] === false ? 'bg-red-100 border-red-400' : 'bg-white border-gray-300'}`}
            onClick={() => handleRecommendationFeedback(item, 'emergencyPreparedness', false)}
            aria-label="Downvote"
          >
            <ThumbsDown className={`w-4 h-4 ${recommendationFeedback['emergencyPreparedness:' + item] === false ? 'text-red-600' : 'text-gray-500'}`} />
          </button>
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
        <li key={index} className="flex items-start space-x-2 items-center">
          <AlertTriangle className="w-4 h-4 text-orange-500 mt-0.5 flex-shrink-0" />
          <span>{item}</span>
          <button
            className={`ml-2 p-1 rounded-full border ${recommendationFeedback['iowaSpecificNotes:' + item] === true ? 'bg-green-100 border-green-400' : 'bg-white border-gray-300'}`}
            onClick={() => handleRecommendationFeedback(item, 'iowaSpecificNotes', true)}
            aria-label="Upvote"
          >
            <ThumbsUp className={`w-4 h-4 ${recommendationFeedback['iowaSpecificNotes:' + item] === true ? 'text-green-600' : 'text-gray-500'}`} />
          </button>
          <button
            className={`ml-1 p-1 rounded-full border ${recommendationFeedback['iowaSpecificNotes:' + item] === false ? 'bg-red-100 border-red-400' : 'bg-white border-gray-300'}`}
            onClick={() => handleRecommendationFeedback(item, 'iowaSpecificNotes', false)}
            aria-label="Downvote"
          >
            <ThumbsDown className={`w-4 h-4 ${recommendationFeedback['iowaSpecificNotes:' + item] === false ? 'text-red-600' : 'text-gray-500'}`} />
          </button>
        </li>
      ))}
    </ul>
  </div>
)}
                {/* Feedback Section */}
                <div className="flex flex-col items-start space-y-2 mt-6">
                  <span className="font-medium">Was this recommendation helpful?</span>
                  <div className="flex items-center space-x-4">
                    <button
                      className={`p-2 rounded-full border ${userFeedback === true ? 'bg-green-100 border-green-400' : 'bg-white border-gray-300'} transition`}
                      onClick={handleUpvote}
                      aria-label="Upvote"
                      disabled={isSubmittingFeedback}
                    >
                      <ThumbsUp className={`w-5 h-5 ${userFeedback === true ? 'text-green-600' : 'text-gray-500'}`} />
                    </button>
                    <button
                      className={`p-2 rounded-full border ${userFeedback === false ? 'bg-red-100 border-red-400' : 'bg-white border-gray-300'} transition`}
                      onClick={handleDownvote}
                      aria-label="Downvote"
                      disabled={isSubmittingFeedback}
                    >
                      <ThumbsDown className={`w-5 h-5 ${userFeedback === false ? 'text-red-600' : 'text-gray-500'}`} />
                    </button>
                  </div>
                  {/* If downvoted, show comment box and submit button */}
                  {userFeedback === false && (
                    <div className="w-full mt-2">
                      <textarea
                        className="w-full border rounded px-3 py-2 mb-2"
                        rows={2}
                        placeholder="What would you like to see improved? (Your feedback will be used to generate a new recommendation)"
                        value={feedbackComment}
                        onChange={e => setFeedbackComment(e.target.value)}
                        disabled={isSubmittingFeedback}
                      />
                      <Button
                        onClick={handleSubmitFeedback}
                        disabled={isSubmittingFeedback || !feedbackComment.trim()}
                        className="w-full"
                      >
                        {isSubmittingFeedback ? 'Submitting...' : 'Submit Feedback & Regenerate Recommendation'}
                      </Button>
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

        {/* Feedback/Analysis History Section */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <ThumbsUp className="w-5 h-5 text-green-500" />
              <ThumbsDown className="w-5 h-5 text-red-500 ml-2" />
              <span>Recent Feedback & Analysis History</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {feedbackHistory.length === 0 ? (
              <div className="text-gray-500 text-center">No feedback history yet.</div>
            ) : (
              <ul className="divide-y divide-gray-200">
                {feedbackHistory.map(entry => (
                  <li key={entry.id} className="py-3 flex flex-col space-y-1">
                    <div className="flex items-center space-x-2">
                      {entry.user_feedback === true && <ThumbsUp className="w-4 h-4 text-green-600" />}
                      {entry.user_feedback === false && <ThumbsDown className="w-4 h-4 text-red-600" />}
                      <span className="text-xs text-gray-500">{new Date(entry.created_at).toLocaleString()}</span>
                      {entry.zip_code && <span className="ml-2 text-xs text-gray-700">ZIP: {entry.zip_code}</span>}
                    </div>
                    {entry.user_query && (
                      <div className="text-sm text-gray-800"><span className="font-semibold">Query:</span> {entry.user_query}</div>
                    )}
                    {entry.feedback_comment && (
                      <div className="text-sm text-yellow-900 bg-yellow-50 rounded px-2 py-1"><span className="font-semibold">Comment:</span> {entry.feedback_comment}</div>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default PropertyRiskFactors; 