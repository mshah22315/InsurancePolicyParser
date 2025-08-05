import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useQuery } from "@tanstack/react-query";
import { ProcessingTask } from "@shared/schema";
import { cn } from "@/lib/utils";

const statusColors = {
  pending: "bg-gray-100 text-gray-800",
  processing: "bg-yellow-100 text-yellow-800",
  completed: "bg-green-100 text-green-800",
  failed: "bg-red-100 text-red-800",
};

const statusDots = {
  pending: "bg-gray-400",
  processing: "bg-yellow-400 animate-pulse",
  completed: "bg-green-400",
  failed: "bg-red-400",
};

export function ProcessingStatus() {
  const { data: tasks = [], isLoading } = useQuery<ProcessingTask[]>({
    queryKey: ["http://localhost:5001/api/processing-tasks"],
    refetchInterval: 2000, // Refetch every 2 seconds for real-time updates
  });

  const recentTasks = tasks.slice(0, 5);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Processing Status</CardTitle>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {recentTasks.length === 0 ? (
          <p className="text-gray-500 text-center py-4">No processing tasks</p>
        ) : (
          recentTasks.map((task) => (
            <div
              key={task.id}
              className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
            >
              <div className="flex items-center space-x-3">
                <div className={cn("w-2 h-2 rounded-full", statusDots[task.status])} />
                <span className="text-sm font-medium text-gray-900">
                  {task.filename || `Task ${task.taskId.slice(0, 8)}`}
                </span>
              </div>
              <Badge variant="secondary" className={statusColors[task.status]}>
                {task.status}
              </Badge>
            </div>
          ))
        )}
        
        <Button variant="ghost" className="w-full text-blue-600 hover:text-blue-700">
          View All Tasks
        </Button>
      </CardContent>
    </Card>
  );
}
