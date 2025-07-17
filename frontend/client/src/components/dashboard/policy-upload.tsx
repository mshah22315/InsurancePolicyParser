import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { FileUpload } from "@/components/common/file-upload";
import { useState } from "react";
import { useFileUpload } from "@/hooks/use-file-upload";
import { useToast } from "@/hooks/use-toast";

export function PolicyUpload() {
  const [priority, setPriority] = useState("standard");
  const [notifications, setNotifications] = useState("email_dashboard");
  const { toast } = useToast();

  const { uploadFiles, isUploading } = useFileUpload({
    endpoint: "http://localhost:5001/api/policies/upload",
    acceptedTypes: ["application/pdf"],
    maxSize: 10 * 1024 * 1024, // 10MB
    onSuccess: (response) => {
      toast({
        title: "Upload Successful",
        description: `Processing started with task ID: ${response.taskId}`,
      });
    },
  });

  const handleFileUpload = async (files: FileList) => {
    await uploadFiles(files, {
      priority,
      notifications,
    });
  };

  return (
    <Card className="col-span-2">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Upload Policy Documents</CardTitle>
          <Button variant="outline" size="sm">
            View All Uploads
          </Button>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-6">
        <FileUpload
          onFileUpload={handleFileUpload}
          acceptedTypes={["application/pdf"]}
          maxSize={10 * 1024 * 1024}
          multiple
          isUploading={isUploading}
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
      </CardContent>
    </Card>
  );
}
