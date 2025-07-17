import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { X } from "lucide-react";
import { ProcessingTask } from "@shared/schema";
import { cn } from "@/lib/utils";

interface ProcessingProgressProps {
  task: ProcessingTask;
  onClose: () => void;
}

const processingSteps = [
  { name: "Document Upload", key: "upload" },
  { name: "AI Processing", key: "processing" },
  { name: "Vectorization", key: "vectorization" },
  { name: "Database Storage", key: "storage" },
];

export function ProcessingProgress({ task, onClose }: ProcessingProgressProps) {
  const getCurrentStep = () => {
    if (task.progress >= 100) return 4;
    if (task.progress >= 75) return 3;
    if (task.progress >= 50) return 2;
    if (task.progress >= 25) return 1;
    return 0;
  };

  const currentStep = getCurrentStep();

  const getStepStatus = (index: number) => {
    if (index < currentStep) return "completed";
    if (index === currentStep) return "processing";
    return "pending";
  };

  const getStepColor = (status: string) => {
    switch (status) {
      case "completed":
        return "bg-green-500";
      case "processing":
        return "bg-yellow-500 animate-pulse";
      default:
        return "bg-gray-300";
    }
  };

  const getStepDescription = (index: number) => {
    const status = getStepStatus(index);
    switch (status) {
      case "completed":
        return "Completed";
      case "processing":
        return "Processing...";
      default:
        return "Pending";
    }
  };

  return (
    <div className="fixed bottom-4 right-4 w-80 z-50">
      <Card className="shadow-lg">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg">Processing Documents</CardTitle>
            <Button variant="ghost" size="sm" onClick={onClose}>
              <X className="w-4 h-4" />
            </Button>
          </div>
        </CardHeader>
        
        <CardContent className="space-y-4">
          {/* Processing Steps */}
          <div className="space-y-3">
            {processingSteps.map((step, index) => {
              const status = getStepStatus(index);
              
              return (
                <div key={step.key} className="flex items-center space-x-3">
                  <div className={cn("w-2 h-2 rounded-full", getStepColor(status))} />
                  <div className="flex-1">
                    <div className="text-sm font-medium text-gray-900">{step.name}</div>
                    <div className="text-xs text-gray-500">{getStepDescription(index)}</div>
                  </div>
                </div>
              );
            })}
          </div>
          
          {/* Progress Bar */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600">Progress</span>
              <span className="font-medium text-gray-900">{task.progress}%</span>
            </div>
            <Progress value={task.progress} className="h-2" />
          </div>
          
          {/* Task Info */}
          <div className="text-xs text-gray-500">
            {task.filename && <div>File: {task.filename}</div>}
            <div>Task ID: {task.taskId.slice(0, 8)}...</div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
