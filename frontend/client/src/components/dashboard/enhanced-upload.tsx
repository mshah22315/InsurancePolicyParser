import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { FileUpload } from "@/components/common/file-upload";
import { useState } from "react";
import { useFileUpload } from "@/hooks/use-file-upload";
import { useToast } from "@/hooks/use-toast";
import { Upload, FileText, Home } from "lucide-react";

interface UploadFormData {
  policyNumber: string;
  installationDate?: string;
  workDescription?: string;
  propertyFeatures: string[];
}

export function EnhancedUpload() {
  const [formData, setFormData] = useState<UploadFormData>({
    policyNumber: "",
    installationDate: "",
    workDescription: "",
    propertyFeatures: [],
  });
  const { toast } = useToast();

  const { uploadFiles, isUploading } = useFileUpload({
    endpoint: "http://localhost:5001/api/policies/upload",
    acceptedTypes: ["application/pdf"],
    maxSize: 10 * 1024 * 1024, // 10MB
    onSuccess: (response) => {
      toast({
        title: "Upload Successful",
        description: `Policy processing started with task ID: ${response.taskId}`,
      });
    },
    onError: (error) => {
      toast({
        title: "Upload Failed",
        description: error,
        variant: "destructive",
      });
    },
  });

  const handleFileUpload = async (files: FileList) => {
    const additionalData: Record<string, any> = {
      policyNumber: formData.policyNumber,
    };

    if (formData.propertyFeatures.length > 0) {
      additionalData.propertyFeatures = formData.propertyFeatures;
    }

    await uploadFiles(files, additionalData);
  };

  const propertyFeatureOptions = [
    { value: "monitored_alarm", label: "Monitored Alarm System" },
    { value: "sprinkler_system", label: "Sprinkler System" },
    { value: "fire_extinguisher", label: "Fire Extinguisher" },
    { value: "smoke_detector", label: "Smoke Detector" },
    { value: "deadbolt_locks", label: "Deadbolt Locks" },
    { value: "security_camera", label: "Security Camera" },
    { value: "storm_shutters", label: "Storm Shutters" },
    { value: "impact_windows", label: "Impact Windows" },
  ];

  const handleFeatureToggle = (feature: string) => {
    setFormData(prev => ({
      ...prev,
      propertyFeatures: prev.propertyFeatures.includes(feature)
        ? prev.propertyFeatures.filter(f => f !== feature)
        : [...prev.propertyFeatures, feature]
    }));
  };

  return (
    <Card className="col-span-2">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <FileText className="w-5 h-5" />
            Upload Policy Documents
          </CardTitle>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-6">
        {/* Policy Number Input */}
        <div>
          <Label htmlFor="policyNumber">Policy Number *</Label>
          <Input
            id="policyNumber"
            placeholder="Enter policy number (e.g., POL-2024-001)"
            value={formData.policyNumber}
            onChange={(e) => setFormData(prev => ({ ...prev, policyNumber: e.target.value }))}
            required
          />
        </div>



        {/* Property Features Selection */}
        <div>
          <Label>Property Features (Optional)</Label>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mt-2">
            {propertyFeatureOptions.map((feature) => (
              <Button
                key={feature.value}
                variant={formData.propertyFeatures.includes(feature.value) ? "default" : "outline"}
                size="sm"
                onClick={() => handleFeatureToggle(feature.value)}
                className="text-xs"
              >
                {feature.label}
              </Button>
            ))}
          </div>
        </div>

        {/* File Upload */}
        <div>
          <Label>Upload Policy Document</Label>
          <FileUpload
            onFileUpload={handleFileUpload}
            acceptedTypes={["application/pdf"]}
            maxSize={10 * 1024 * 1024}
            multiple={true}
            isUploading={isUploading}
          />
        </div>

        {/* Upload Button */}
        <Button 
          className="w-full" 
          disabled={!formData.policyNumber || isUploading}
          onClick={() => {
            // Trigger file upload if files are selected
            const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
            if (fileInput?.files) {
              handleFileUpload(fileInput.files);
            }
          }}
        >
          <Upload className="w-4 h-4 mr-2" />
          {isUploading ? "Uploading..." : "Upload Policy Document"}
        </Button>
      </CardContent>
    </Card>
  );
} 