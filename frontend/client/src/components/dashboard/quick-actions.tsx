import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Home, Settings, FileImage, ChevronRight } from "lucide-react";
import { useState } from "react";

export function QuickActions() {
  const [activeModal, setActiveModal] = useState<string | null>(null);

  const actions = [
    {
      title: "Upload Roofing Invoice",
      icon: Home,
      description: "Calculate roof age and update policy",
      action: () => setActiveModal("roofing-invoice"),
    },
    {
      title: "Manage Property Features",
      icon: Settings,
      description: "Add or update property features",
      action: () => setActiveModal("property-features"),
    },
    {
      title: "Batch Processing",
      icon: FileImage,
      description: "Process multiple documents at once",
      action: () => setActiveModal("batch-processing"),
    },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Quick Actions</CardTitle>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {actions.map((action) => {
          const Icon = action.icon;
          
          return (
            <Button
              key={action.title}
              variant="ghost"
              onClick={action.action}
              className="w-full flex items-center justify-between p-4 h-auto bg-gray-50 hover:bg-gray-100"
            >
              <div className="flex items-center space-x-3">
                <Icon className="w-5 h-5 text-blue-600" />
                <div className="text-left">
                  <div className="font-medium text-gray-900">{action.title}</div>
                  <div className="text-sm text-gray-500">{action.description}</div>
                </div>
              </div>
              <ChevronRight className="w-5 h-5 text-gray-400" />
            </Button>
          );
        })}
      </CardContent>
    </Card>
  );
}
