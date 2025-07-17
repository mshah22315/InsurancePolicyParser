import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { FileUpload } from "@/components/common/file-upload";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useToast } from "@/hooks/use-toast";
import { apiRequest } from "@/lib/queryClient";
import { Policy } from "@shared/schema";
import { useState } from "react";
import { Home, Calendar, FileText, Shield } from "lucide-react";

const roofingInvoiceSchema = z.object({
  policyId: z.number().min(1, "Please select a policy"),
  installationDate: z.string().optional(),
  workDescription: z.string().optional(),
  propertyFeatures: z.array(z.string()).optional(),
});

type RoofingInvoiceForm = z.infer<typeof roofingInvoiceSchema>;

interface RoofingInvoiceModalProps {
  isOpen: boolean;
  onClose: () => void;
  selectedPolicyId?: number;
}

// Available property features with descriptions
const PROPERTY_FEATURES = [
  { value: "monitored_alarm", label: "Monitored Alarm System", description: "24/7 monitored security system" },
  { value: "sprinkler_system", label: "Sprinkler System", description: "Fire suppression sprinkler system" },
  { value: "fire_extinguisher", label: "Fire Extinguisher", description: "Portable fire extinguishers" },
  { value: "smoke_detector", label: "Smoke Detector", description: "Smoke and fire detection system" },
  { value: "deadbolt_locks", label: "Deadbolt Locks", description: "High-security deadbolt locks" },
  { value: "security_camera", label: "Security Camera", description: "Video surveillance system" },
  { value: "storm_shutters", label: "Storm Shutters", description: "Hurricane-rated storm shutters" },
  { value: "impact_windows", label: "Impact Windows", description: "Impact-resistant windows" },
  { value: "smart_home_system", label: "Smart Home System", description: "Automated home security system" },
  { value: "backup_generator", label: "Backup Generator", description: "Emergency power generator" },
  { value: "water_leak_detector", label: "Water Leak Detector", description: "Water damage prevention system" },
  { value: "new_construction", label: "New Construction", description: "Recently built property" },
];

export function RoofingInvoiceModal({ isOpen, onClose, selectedPolicyId }: RoofingInvoiceModalProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [selectedFeatures, setSelectedFeatures] = useState<string[]>([]);
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const { data: policies = [] } = useQuery<Policy[]>({
    queryKey: ["/api/policies"],
    enabled: isOpen,
  });

  const form = useForm<RoofingInvoiceForm>({
    resolver: zodResolver(roofingInvoiceSchema),
    defaultValues: {
      policyId: selectedPolicyId || undefined,
      installationDate: "",
      workDescription: "",
      propertyFeatures: [],
    },
  });

  const uploadMutation = useMutation({
    mutationFn: async (data: RoofingInvoiceForm & { file: File }) => {
      const formData = new FormData();
      formData.append("document", data.file);
      formData.append("policyNumber", data.policyId.toString());
      if (data.installationDate) {
        formData.append("installationDate", data.installationDate);
      }
      if (data.workDescription) {
        formData.append("workDescription", data.workDescription);
      }
      // Add selected property features
      selectedFeatures.forEach(feature => {
        formData.append("propertyFeatures", feature);
      });

      const response = await apiRequest("POST", "/api/roofing-invoices/upload", formData);
      return response.json();
    },
    onSuccess: (data) => {
      toast({
        title: "Success",
        description: "Roofing invoice uploaded successfully",
      });
      queryClient.invalidateQueries({ queryKey: ["/api/roofing-invoices"] });
      queryClient.invalidateQueries({ queryKey: ["/api/policies"] });
      onClose();
      form.reset();
      setSelectedFile(null);
      setSelectedFeatures([]);
    },
    onError: (error) => {
      toast({
        title: "Upload Failed",
        description: error.message,
        variant: "destructive",
      });
    },
  });

  const handleFileUpload = (files: FileList) => {
    if (files.length > 0) {
      setSelectedFile(files[0]);
    }
  };

  const handleFeatureToggle = (featureValue: string) => {
    setSelectedFeatures(prev => 
      prev.includes(featureValue) 
        ? prev.filter(f => f !== featureValue)
        : [...prev, featureValue]
    );
  };

  const onSubmit = async (data: RoofingInvoiceForm) => {
    if (!selectedFile) {
      toast({
        title: "Error",
        description: "Please select a file to upload",
        variant: "destructive",
      });
      return;
    }

    setIsUploading(true);
    try {
      await uploadMutation.mutateAsync({ ...data, file: selectedFile });
    } finally {
      setIsUploading(false);
    }
  };

  const selectedPolicy = policies.find(p => p.id === form.watch("policyId"));

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Home className="w-5 h-5" />
            Upload Roofing Invoice
          </DialogTitle>
          <DialogDescription>
            Upload a roofing invoice to calculate roof age and update policy information
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
            {/* File Upload */}
            <FormField
              control={form.control}
              name="policyId"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Policy</FormLabel>
                  <Select onValueChange={field.onChange} defaultValue={field.value?.toString()}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Select a policy" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {policies.map((policy) => (
                        <SelectItem key={policy.id} value={policy.id.toString()}>
                          {policy.policyNumber} - {policy.policyholderName}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* File Upload */}
            <div className="space-y-2">
              <Label>Invoice Document</Label>
              <FileUpload
                onFileUpload={handleFileUpload}
                acceptedTypes={["application/pdf"]}
                maxSize={10 * 1024 * 1024}
                multiple={false}
                isUploading={isUploading}
              />
              {selectedFile && (
                <p className="text-sm text-green-600">
                  ✓ Selected: {selectedFile.name}
                </p>
              )}
            </div>

            {/* Installation Date */}
            <FormField
              control={form.control}
              name="installationDate"
              render={({ field }) => (
                <FormItem>
                  <FormLabel className="flex items-center gap-2">
                    <Calendar className="w-4 h-4" />
                    Installation Date (Optional)
                  </FormLabel>
                  <FormControl>
                    <Input
                      type="date"
                      placeholder="Select installation date"
                      {...field}
                    />
                  </FormControl>
                  <p className="text-xs text-gray-600">
                    Leave blank to auto-extract from invoice
                  </p>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Work Description */}
            <FormField
              control={form.control}
              name="workDescription"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Work Description</FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder="Brief description of roofing work..."
                      className="resize-none"
                      rows={3}
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Property Features */}
            <div className="space-y-3">
              <FormLabel className="flex items-center gap-2">
                <Shield className="w-4 h-4" />
                Property Features (Optional)
              </FormLabel>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-60 overflow-y-auto border rounded-lg p-4">
                {PROPERTY_FEATURES.map((feature) => (
                  <div
                    key={feature.value}
                    className={`flex items-start space-x-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                      selectedFeatures.includes(feature.value)
                        ? "bg-blue-50 border-blue-200"
                        : "bg-gray-50 border-gray-200 hover:bg-gray-100"
                    }`}
                    onClick={() => handleFeatureToggle(feature.value)}
                  >
                    <input
                      type="checkbox"
                      checked={selectedFeatures.includes(feature.value)}
                      onChange={() => handleFeatureToggle(feature.value)}
                      className="mt-1"
                    />
                    <div className="flex-1">
                      <p className="font-medium text-sm">{feature.label}</p>
                      <p className="text-xs text-gray-600">{feature.description}</p>
                    </div>
                  </div>
                ))}
              </div>
              <p className="text-xs text-gray-600">
                Select property features that apply to this policy. These may affect insurance rates.
              </p>
            </div>

            {/* Processing Info */}
            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="font-medium text-gray-900 mb-2">Processing Information</h4>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Roof age will be calculated automatically if installation date is provided</li>
                <li>• Invoice data will be extracted and processed using AI</li>
                <li>• Policy information will be updated with roof details and property features</li>
                <li>• Processing typically takes 1-2 minutes</li>
              </ul>
            </div>

            {/* Actions */}
            <div className="flex items-center justify-end space-x-4 pt-4 border-t">
              <Button type="button" variant="outline" onClick={onClose}>
                Cancel
              </Button>
              <Button type="submit" disabled={isUploading || !selectedFile}>
                {isUploading ? "Processing..." : "Upload & Process"}
              </Button>
            </div>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
