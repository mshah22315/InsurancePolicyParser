import { Search, Bell } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useState } from "react";

export function Header() {
  const [searchQuery, setSearchQuery] = useState("");

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="flex items-center justify-between p-6">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">Policy Processing Dashboard</h1>
          <p className="text-gray-600 mt-1">Manage and analyze insurance policies with AI-powered processing</p>
        </div>
        
        <div className="flex items-center space-x-4">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-2.5 w-5 h-5 text-gray-400" />
            <Input
              type="text"
              placeholder="Search policies..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-64 pl-10"
            />
          </div>
          
          {/* Notifications */}
          <Button variant="ghost" size="icon" className="relative">
            <Bell className="w-5 h-5" />
            <span className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full"></span>
          </Button>
        </div>
      </div>
    </header>
  );
}
