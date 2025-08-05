import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { useQuery } from "@tanstack/react-query";
import { ProcessingTask } from "@shared/schema";
import { Clock, FileText, AlertCircle, CheckCircle } from "lucide-react";
import { format } from "date-fns";

export default function ProcessingQueue() {
  const { data: tasks = [], isLoading } = useQuery<ProcessingTask[]>({
    queryKey: ["http://localhost:5001/api/processing-tasks"],
    refetchInterval: 2000, // Refetch every 2 seconds for real-time updates
  });

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case "processing":
        return <Clock className="w-5 h-5 text-yellow-500 animate-spin" />;
      case "failed":
        return <AlertCircle className="w-5 h-5 text-red-500" />;
      default:
        return <FileText className="w-5 h-5 text-gray-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "bg-green-100 text-green-800";
      case "processing":
        return "bg-yellow-100 text-yellow-800";
      case "failed":
        return "bg-red-100 text-red-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const getTaskTypeDisplay = (taskType: string) => {
    switch (taskType) {
      case "policy_processing":
        return "Policy Processing";
      case "roofing_invoice":
        return "Roofing Invoice";
      default:
        return taskType;
    }
  };

  const pendingTasks = tasks.filter(task => task.status === "pending");
  const processingTasks = tasks.filter(task => task.status === "processing");
  const completedTasks = tasks.filter(task => task.status === "completed");
  const failedTasks = tasks.filter(task => task.status === "failed");

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Processing Queue</h1>
        <p className="text-gray-600 mt-2">
          Monitor the status of all document processing tasks
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Pending</p>
                <p className="text-2xl font-bold text-gray-900">{pendingTasks.length}</p>
              </div>
              <Clock className="w-8 h-8 text-gray-400" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Processing</p>
                <p className="text-2xl font-bold text-yellow-600">{processingTasks.length}</p>
              </div>
              <Clock className="w-8 h-8 text-yellow-400 animate-spin" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Completed</p>
                <p className="text-2xl font-bold text-green-600">{completedTasks.length}</p>
              </div>
              <CheckCircle className="w-8 h-8 text-green-400" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Failed</p>
                <p className="text-2xl font-bold text-red-600">{failedTasks.length}</p>
              </div>
              <AlertCircle className="w-8 h-8 text-red-400" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tasks List */}
      <Card>
        <CardHeader>
          <CardTitle>All Tasks</CardTitle>
        </CardHeader>
        
        <CardContent>
          {isLoading ? (
            <div className="animate-pulse space-y-4">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="h-16 bg-gray-200 rounded" />
              ))}
            </div>
          ) : tasks.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-gray-500">No processing tasks found</p>
            </div>
          ) : (
            <div className="space-y-4">
              {tasks.map((task) => (
                <div key={task.id} className="border rounded-lg p-4 hover:bg-gray-50">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      {getStatusIcon(task.status)}
                      <div>
                        <h3 className="font-medium text-gray-900">
                          {task.filename || `${getTaskTypeDisplay(task.taskType)} Task`}
                        </h3>
                        <p className="text-sm text-gray-500">
                          Task ID: {task.taskId.slice(0, 8)}... • {getTaskTypeDisplay(task.taskType)}
                        </p>
                        <p className="text-sm text-gray-500">
                          Created: {format(new Date(task.createdAt), "PPpp")}
                        </p>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-4">
                      <div className="text-right">
                        <Badge variant="secondary" className={getStatusColor(task.status)}>
                          {task.status}
                        </Badge>
                        {task.status === "processing" && (
                          <div className="mt-2 w-32">
                            <Progress value={task.progress} className="h-2" />
                            <p className="text-xs text-gray-500 mt-1">{task.progress}%</p>
                          </div>
                        )}
                      </div>
                      
                      <Button variant="ghost" size="sm">
                        View Details
                      </Button>
                    </div>
                  </div>
                  
                  {task.errorMessage && (
                    <div className="mt-3 p-3 bg-red-50 rounded-md">
                      <p className="text-sm text-red-800">Error: {task.errorMessage}</p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
