import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { Upload, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";

interface FileUploadProps {
  onFileUpload: (files: FileList) => void;
  acceptedTypes?: string[];
  maxSize?: number;
  multiple?: boolean;
  isUploading?: boolean;
  uploadProgress?: number;
  className?: string;
}

export function FileUpload({
  onFileUpload,
  acceptedTypes = ["application/pdf"],
  maxSize = 10 * 1024 * 1024, // 10MB
  multiple = false,
  isUploading = false,
  uploadProgress = 0,
  className,
}: FileUploadProps) {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    setSelectedFiles(acceptedFiles);
    
    // Create a FileList-like object
    const fileList = {
      length: acceptedFiles.length,
      item: (index: number) => acceptedFiles[index],
      ...acceptedFiles.reduce((acc, file, index) => ({ ...acc, [index]: file }), {}),
    } as FileList;
    
    onFileUpload(fileList);
  }, [onFileUpload]);

  const {
    getRootProps,
    getInputProps,
    isDragActive,
    isDragReject,
  } = useDropzone({
    onDrop,
    accept: acceptedTypes.reduce((acc, type) => ({ ...acc, [type]: [] }), {}),
    maxSize,
    multiple,
  });

  const removeFile = (index: number) => {
    setSelectedFiles(files => files.filter((_, i) => i !== index));
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  const getAcceptText = () => {
    if (acceptedTypes.includes("application/pdf")) {
      return "PDF files";
    }
    return acceptedTypes.join(", ");
  };

  return (
    <div className={cn("space-y-4", className)}>
      <div
        {...getRootProps()}
        className={cn(
          "border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors",
          isDragActive && !isDragReject ? "border-blue-500 bg-blue-50" : "border-gray-300",
          isDragReject ? "border-red-500 bg-red-50" : "",
          isUploading ? "pointer-events-none opacity-50" : "hover:border-blue-400 hover:bg-gray-50"
        )}
      >
        <input {...getInputProps()} />
        
        <Upload className="w-16 h-16 text-gray-400 mx-auto mb-4" />
        
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          {isDragActive ? "Drop your files here" : "Drop your documents here"}
        </h3>
        
        <p className="text-gray-600 mb-4">
          or click to browse files
        </p>
        
        <p className="text-sm text-gray-500 mb-4">
          Supports {getAcceptText()} up to {(maxSize / 1024 / 1024).toFixed(0)}MB
        </p>
        
        <Button type="button" disabled={isUploading}>
          {isUploading ? "Uploading..." : "Choose Files"}
        </Button>
      </div>

      {/* Selected Files */}
      {selectedFiles.length > 0 && (
        <div className="space-y-2">
          <h4 className="font-medium text-gray-900">Selected Files:</h4>
          {selectedFiles.map((file, index) => (
            <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex-1">
                <p className="font-medium text-gray-900">{file.name}</p>
                <p className="text-sm text-gray-500">{formatFileSize(file.size)}</p>
              </div>
              {!isUploading && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => removeFile(index)}
                  className="text-red-600 hover:text-red-700"
                >
                  <X className="w-4 h-4" />
                </Button>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Upload Progress */}
      {isUploading && (
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-600">Uploading...</span>
            <span className="font-medium text-gray-900">{uploadProgress}%</span>
          </div>
          <Progress value={uploadProgress} className="h-2" />
        </div>
      )}
    </div>
  );
}
