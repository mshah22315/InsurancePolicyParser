import { Link, useLocation } from "wouter";
import { Shield, Upload, FileText, Clock, Home, Settings, Edit3, AlertTriangle } from "lucide-react";
import { cn } from "@/lib/utils";

const navigation = [
  { name: "Dashboard", href: "/", icon: Home },
  { name: "Upload & Manage", href: "/upload-policy", icon: Upload },
  { name: "Policy Library", href: "/policy-library", icon: FileText },
  { name: "Policy Context", href: "/policy-context", icon: Edit3 },
  { name: "Property Risk Factors", href: "/property-risk-factors", icon: AlertTriangle },
  { name: "Processing Queue", href: "/processing-queue", icon: Clock },
  { name: "Settings", href: "/settings", icon: Settings },
];

export function Sidebar() {
  const [location] = useLocation();

  return (
    <div className="w-64 bg-white shadow-lg flex flex-col">
      {/* Logo and Brand */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
            <Shield className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-lg font-semibold text-gray-900">AI Insurance Agent</h1>
            <p className="text-xs text-gray-500">Policy Processing</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-2">
        {navigation.map((item) => {
          const Icon = item.icon;
          const isActive = location === item.href;
          
          return (
            <Link 
              key={item.name} 
              href={item.href}
              className={cn(
                "flex items-center space-x-3 p-3 rounded-lg text-sm font-medium transition-colors",
                isActive
                  ? "bg-blue-600 text-white"
                  : "text-gray-700 hover:bg-blue-50 hover:text-blue-600"
              )}
            >
              <Icon className="w-5 h-5" />
              <span>{item.name}</span>
            </Link>
          );
        })}
      </nav>

      {/* User Profile */}
      <div className="p-4 border-t border-gray-200">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
            <span className="text-white text-sm font-medium">JD</span>
          </div>
          <div className="flex-1">
            <p className="text-sm font-medium text-gray-900">John Doe</p>
            <p className="text-xs text-gray-500">Insurance Agent</p>
          </div>
        </div>
      </div>
    </div>
  );
}
