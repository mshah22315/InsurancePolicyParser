import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FileUpload } from "@/components/common/file-upload";
import { Button } from "@/components/ui/button";
import { useFileUpload } from "@/hooks/use-file-upload";
import { useToast } from "@/hooks/use-toast";
import { Download, Shield } from "lucide-react";

export default function UploadPolicy() {
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

  const handlePolicyUpload = async (files: FileList) => {
    await uploadPolicies(files);
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
        <h1 className="text-2xl font-bold text-gray-900">Upload Policy Documents</h1>
        <p className="text-gray-600 mt-2">
          Upload insurance policies for processing and analysis
        </p>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Shield className="w-5 h-5" />
              Policy Document Upload
            </CardTitle>
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
    </div>
  );
}
