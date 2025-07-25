import { useQuery } from "@tanstack/react-query";
import { StatsCards } from "@/components/dashboard/stats-cards";
import { EnhancedUpload } from "@/components/dashboard/enhanced-upload";
import { PolicyQuery } from "@/components/dashboard/policy-query";
import { QuickActions } from "@/components/dashboard/quick-actions";
import { ProcessingStatus } from "@/components/dashboard/processing-status";
import { RecentPolicies } from "@/components/dashboard/recent-policies";
import { ProcessingProgress } from "@/components/common/processing-progress";
import { useWebSocket } from "@/hooks/use-websocket";
import { DashboardStats } from "@/lib/types";
import { ProcessingTask } from "@shared/schema";
import { useState, useEffect } from "react";
import { apiClient } from "@/lib/api";

export default function Dashboard() {
  const [activeTask, setActiveTask] = useState<ProcessingTask | null>(null);
  
  // Use backend API for dashboard stats
  const { data: statsResponse } = useQuery({
    queryKey: ["dashboard-stats"],
    queryFn: () => apiClient.getDashboardStats(),
    refetchInterval: 30000, // Refetch every 30 seconds
  });

  const { lastMessage } = useWebSocket();

  // Handle WebSocket messages for real-time updates
  useEffect(() => {
    if (lastMessage) {
      console.log("WebSocket message:", lastMessage);
      
      if (lastMessage.type === "task_started") {
        // You could fetch task details here and set activeTask
        console.log("Task started:", lastMessage.taskId);
      }
    }
  }, [lastMessage]);

  const defaultStats: DashboardStats = {
    totalPolicies: 0,
    processingQueue: 0,
    completedToday: 0,
    avgProcessingTime: "0m",
  };

  // Extract stats from API response
  const stats = statsResponse?.data || defaultStats;

  return (
    <div className="p-6 space-y-6">
      {/* Stats Cards */}
      <StatsCards stats={stats} />
      
      {/* Main Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <QuickActions />
        <ProcessingStatus />
      </div>
      
      {/* Processing Progress Overlay */}
      {activeTask && (
        <ProcessingProgress
          task={activeTask}
          onClose={() => setActiveTask(null)}
        />
      )}
    </div>
  );
}
