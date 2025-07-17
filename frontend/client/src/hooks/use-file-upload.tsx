import { useState, useCallback } from "react";
import { useToast } from "@/hooks/use-toast";
import { apiRequest } from "@/lib/queryClient";
import { PolicyUploadResponse } from "@/lib/types";

interface UseFileUploadOptions {
  endpoint: string;
  acceptedTypes?: string[];
  maxSize?: number; // in bytes
  onSuccess?: (response: any) => void;
  onError?: (error: string) => void;
}

export function useFileUpload(options: UseFileUploadOptions) {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const { toast } = useToast();

  const uploadFile = useCallback(async (file: File, additionalData?: Record<string, any>) => {
    if (!file) {
      toast({
        title: "Error",
        description: "Please select a file to upload",
        variant: "destructive",
      });
      return;
    }

    // Check file type
    if (options.acceptedTypes && !options.acceptedTypes.includes(file.type)) {
      toast({
        title: "Invalid File Type",
        description: `Please upload a file of type: ${options.acceptedTypes.join(", ")}`,
        variant: "destructive",
      });
      return;
    }

    // Check file size
    if (options.maxSize && file.size > options.maxSize) {
      toast({
        title: "File Too Large",
        description: `File size must be less than ${(options.maxSize / 1024 / 1024).toFixed(1)}MB`,
        variant: "destructive",
      });
      return;
    }

    setIsUploading(true);
    setUploadProgress(0);

    try {
      const formData = new FormData();
      formData.append("document", file);
      
      // Add additional data if provided
      if (additionalData) {
        Object.keys(additionalData).forEach(key => {
          formData.append(key, additionalData[key]);
        });
      }

      // Add additional data to formData if provided
      if (additionalData) {
        Object.entries(additionalData).forEach(([key, value]) => {
          if (value !== undefined && value !== null) {
            if (Array.isArray(value)) {
              // Handle arrays (like propertyFeatures)
              formData.append(key, value.join(','));
            } else {
              formData.append(key, String(value));
            }
          }
        });
      }

      const response = await fetch(options.endpoint, {
        method: "POST",
        body: formData,
        credentials: "include",
      });

      if (!response.ok) {
        const text = await response.text();
        throw new Error(`${response.status}: ${text}`);
      }
      const result = await response.json();

      setUploadProgress(100);
      
      if (options.onSuccess) {
        options.onSuccess(result);
      }

      toast({
        title: "Success",
        description: "File uploaded successfully",
      });

      return result;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Upload failed";
      
      if (options.onError) {
        options.onError(errorMessage);
      }

      toast({
        title: "Upload Failed",
        description: errorMessage,
        variant: "destructive",
      });

      throw error;
    } finally {
      setIsUploading(false);
    }
  }, [options, toast]);

  const uploadFiles = useCallback(async (files: FileList | File[], additionalData?: Record<string, any>) => {
    const fileArray = Array.from(files);
    const results = [];

    for (const file of fileArray) {
      try {
        const result = await uploadFile(file, additionalData);
        results.push(result);
      } catch (error) {
        // Continue with other files even if one fails
        console.error(`Failed to upload ${file.name}:`, error);
      }
    }

    return results;
  }, [uploadFile]);

  return {
    uploadFile,
    uploadFiles,
    isUploading,
    uploadProgress,
  };
}
