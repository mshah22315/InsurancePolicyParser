import { Card, CardContent } from "@/components/ui/card";
import { FileText, Clock, CheckCircle, Zap } from "lucide-react";
import { DashboardStats } from "@/lib/types";

interface StatsCardsProps {
  stats: DashboardStats;
}

const statCards = [
  {
    title: "Total Policies",
    key: "totalPolicies" as keyof DashboardStats,
    icon: FileText,
    color: "blue",
    change: "+12%",
    changeLabel: "from last month",
  },
  {
    title: "Processing Queue",
    key: "processingQueue" as keyof DashboardStats,
    icon: Clock,
    color: "yellow",
    change: "Processing",
    changeLabel: "avg 2.5 min",
  },
  {
    title: "Completed Today",
    key: "completedToday" as keyof DashboardStats,
    icon: CheckCircle,
    color: "green",
    change: "100%",
    changeLabel: "success rate",
  },
  {
    title: "Avg Processing Time",
    key: "avgProcessingTime" as keyof DashboardStats,
    icon: Zap,
    color: "purple",
    change: "-15%",
    changeLabel: "improved",
  },
];

const colorClasses = {
  blue: "bg-blue-50 text-blue-600",
  yellow: "bg-yellow-50 text-yellow-600",
  green: "bg-green-50 text-green-600",
  purple: "bg-purple-50 text-purple-600",
};

export function StatsCards({ stats }: StatsCardsProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {statCards.map((card) => {
        const Icon = card.icon;
        const value = stats[card.key];
        
        return (
          <Card key={card.title} className="hover:shadow-md transition-shadow">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-600 text-sm font-medium">{card.title}</p>
                  <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
                </div>
                <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${colorClasses[card.color]}`}>
                  <Icon className="w-6 h-6" />
                </div>
              </div>
              <div className="mt-4 flex items-center text-sm">
                <span className="text-green-600 font-medium">{card.change}</span>
                <span className="text-gray-500 ml-2">{card.changeLabel}</span>
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
