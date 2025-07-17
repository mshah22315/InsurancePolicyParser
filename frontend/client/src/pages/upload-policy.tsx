import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FileUpload } from "@/components/common/file-upload";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useFileUpload } from "@/hooks/use-file-upload";
import { useToast } from "@/hooks/use-toast";
import { useState } from "react";
import { Upload, Download, FileText, Home, Shield } from "lucide-react";

// Property features from the backend script
const PROPERTY_FEATURES = [
  { id: "monitored_alarm", label: "Monitored Alarm System", description: "24/7 monitored security system" },
  { id: "sprinkler_system", label: "Sprinkler System", description: "Fire suppression system installed" },
  { id: "impact_resistant_roof", label: "Impact Resistant Roof", description: "Roof rated for hail and wind resistance" },
  { id: "new_construction", label: "New Construction", description: "Recently built or renovated property" },
  { id: "security_camera", label: "Security Camera System", description: "Video surveillance system" },
  { id: "smart_home_system", label: "Smart Home System", description: "Automated home security and monitoring" },
  { id: "fire_extinguisher", label: "Fire Extinguisher", description: "Multiple fire extinguishers installed" },
  { id: "storm_shutters", label: "Storm Shutters", description: "Hurricane-rated window protection" },
  { id: "backup_generator", label: "Backup Generator", description: "Emergency power system" },
  { id: "water_leak_detector", label: "Water Leak Detector", description: "Automatic water leak detection system" }
];

export default function UploadPolicy() {
  const [priority, setPriority] = useState("standard");
  const [notifications, setNotifications] = useState("email_dashboard");
  const [selectedFeatures, setSelectedFeatures] = useState<string[]>([]);
  const [activeTab, setActiveTab] = useState("policy");
  const { toast } = useToast();

  const { uploadFiles: uploadPolicies, isUploading: isUploadingPolicies, uploadProgress: policyProgress } = useFileUpload({
    endpoint: "http://localhost:5001/api/policies/upload",
    acceptedTypes: ["application/pdf"],
    maxSize: 10 * 1024 * 1024, // 10MB
    onSuccess: (response) => {
      toast({
        title: "Policy Upload Successful",
        description: `Processing started with task ID: ${response.taskId}`,
      });
    },
  });

  const { uploadFiles: uploadInvoices, isUploading: isUploadingInvoices, uploadProgress: invoiceProgress } = useFileUpload({
    endpoint: "http://localhost:5001/api/roofing-invoices/upload",
    acceptedTypes: ["application/pdf"],
    maxSize: 10 * 1024 * 1024, // 10MB
    onSuccess: (response) => {
      toast({
        title: "Invoice Upload Successful",
        description: `Roofing invoice processing started with task ID: ${response.taskId}`,
      });
    },
  });

  const handlePolicyUpload = async (files: FileList) => {
    await uploadPolicies(files, {
      priority,
      notifications,
      propertyFeatures: selectedFeatures,
    });
  };

  const handleInvoiceUpload = async (files: FileList) => {
    await uploadInvoices(files, {
      priority,
      notifications,
    });
  };

  const handleFeatureToggle = (featureId: string) => {
    setSelectedFeatures(prev => 
      prev.includes(featureId) 
        ? prev.filter(id => id !== featureId)
        : [...prev, featureId]
    );
  };

  const handleDownloadTemplate = () => {
    // Create a sample policy template
    const template = `Sample Insurance Policy Template

Policy Number: SAMPLE-001
Insurer: Sample Insurance Company
Policyholder: John Doe
Property Address: 123 Main Street, Anytown, USA
Effective Date: 01/01/2024
Expiration Date: 01/01/2025
Total Premium: $1,200.00

Coverage Details:
- Dwelling Coverage: $300,000
- Personal Property: $150,000
- Liability: $300,000
- Medical Payments: $5,000

Deductibles:
- Wind/Hail: $1,000
- All Other Perils: $1,000

This is a sample template for demonstration purposes.`;
    
    const blob = new Blob([template], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'sample_policy_template.txt';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Upload Documents & Manage Features</h1>
        <p className="text-gray-600 mt-2">
          Upload insurance policies and roofing invoices, plus configure property features for better coverage
        </p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="policy" className="flex items-center gap-2">
            <Shield className="w-4 h-4" />
            Policy Documents
          </TabsTrigger>
          <TabsTrigger value="invoices" className="flex items-center gap-2">
            <FileText className="w-4 h-4" />
            Roofing Invoices
          </TabsTrigger>
          <TabsTrigger value="features" className="flex items-center gap-2">
            <Home className="w-4 h-4" />
            Property Features
          </TabsTrigger>
        </TabsList>

        <TabsContent value="policy" className="space-y-6">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Policy Document Upload</CardTitle>
                <Button variant="outline" onClick={handleDownloadTemplate}>
                  <Download className="w-4 h-4 mr-2" />
                  Download Template
                </Button>
              </div>
            </CardHeader>
            
            <CardContent className="space-y-6">
              <FileUpload
                onFileUpload={handlePolicyUpload}
                acceptedTypes={["application/pdf"]}
                maxSize={10 * 1024 * 1024}
                multiple
                isUploading={isUploadingPolicies}
                uploadProgress={policyProgress}
              />

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="priority">Processing Priority</Label>
                  <Select value={priority} onValueChange={setPriority}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select priority" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="standard">Standard</SelectItem>
                      <SelectItem value="high">High</SelectItem>
                      <SelectItem value="urgent">Urgent</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                
                <div>
                  <Label htmlFor="notifications">Notification Settings</Label>
                  <Select value={notifications} onValueChange={setNotifications}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select notifications" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="email_dashboard">Email + Dashboard</SelectItem>
                      <SelectItem value="dashboard_only">Dashboard Only</SelectItem>
                      <SelectItem value="email_only">Email Only</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="bg-blue-50 p-4 rounded-lg">
                <h3 className="font-medium text-blue-900 mb-2">Policy Processing Information</h3>
                <ul className="text-sm text-blue-800 space-y-1">
                  <li>• Documents will be processed using AI to extract key policy information</li>
                  <li>• Extracted data will be vectorized and stored in the database</li>
                  <li>• Processing typically takes 2-3 minutes per document</li>
                  <li>• You'll receive notifications when processing is complete</li>
                </ul>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="invoices" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Roofing Invoice Upload</CardTitle>
            </CardHeader>
            
            <CardContent className="space-y-6">
              <FileUpload
                onFileUpload={handleInvoiceUpload}
                acceptedTypes={["application/pdf"]}
                maxSize={10 * 1024 * 1024}
                multiple
                isUploading={isUploadingInvoices}
                uploadProgress={invoiceProgress}
              />

              <div className="bg-green-50 p-4 rounded-lg">
                <h3 className="font-medium text-green-900 mb-2">Roofing Invoice Processing</h3>
                <ul className="text-sm text-green-800 space-y-1">
                  <li>• Upload roofing invoices to calculate roof age</li>
                  <li>• AI will extract installation dates and work descriptions</li>
                  <li>• Roof age helps determine insurance rates and coverage</li>
                  <li>• Older roofs may require additional coverage or replacement</li>
                </ul>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="features" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Property Features Configuration</CardTitle>
            </CardHeader>
            
            <CardContent className="space-y-6">
              <div className="text-sm text-gray-600 mb-4">
                Select property features that may qualify you for discounts or affect your coverage:
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {PROPERTY_FEATURES.map((feature) => (
                  <div key={feature.id} className="flex items-start space-x-3 p-4 border rounded-lg">
                    <Checkbox
                      id={feature.id}
                      checked={selectedFeatures.includes(feature.id)}
                      onCheckedChange={() => handleFeatureToggle(feature.id)}
                    />
                    <div className="flex-1">
                      <Label htmlFor={feature.id} className="font-medium cursor-pointer">
                        {feature.label}
                      </Label>
                      <p className="text-sm text-gray-600 mt-1">{feature.description}</p>
                    </div>
                  </div>
                ))}
              </div>

              {selectedFeatures.length > 0 && (
                <div className="bg-yellow-50 p-4 rounded-lg">
                  <h3 className="font-medium text-yellow-900 mb-2">Selected Features</h3>
                  <div className="flex flex-wrap gap-2">
                    {selectedFeatures.map((featureId) => {
                      const feature = PROPERTY_FEATURES.find(f => f.id === featureId);
                      return (
                        <Badge key={featureId} variant="secondary" className="bg-yellow-100 text-yellow-800">
                          {feature?.label}
                        </Badge>
                      );
                    })}
                  </div>
                </div>
              )}

              <div className="bg-purple-50 p-4 rounded-lg">
                <h3 className="font-medium text-purple-900 mb-2">Feature Benefits</h3>
                <ul className="text-sm text-purple-800 space-y-1">
                  <li>• Monitored alarm systems can reduce premiums by 5-20%</li>
                  <li>• Impact resistant roofs may qualify for wind/hail discounts</li>
                  <li>• New construction often has better rates due to modern building codes</li>
                  <li>• Smart home systems can provide additional security discounts</li>
                </ul>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
