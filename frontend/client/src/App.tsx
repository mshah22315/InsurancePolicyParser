import { Switch, Route } from "wouter";
import { queryClient } from "./lib/queryClient";
import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import Dashboard from "@/pages/dashboard";
import UploadPolicy from "@/pages/upload-policy";
import PolicyLibrary from "@/pages/policy-library";
import ProcessingQueue from "@/pages/processing-queue"; 

import PolicyContext from "@/pages/policy-context";
import PropertyRiskFactors from "@/pages/property-risk-factors";
import NotFound from "@/pages/not-found";
import PolicyQueryPage from "@/pages/policy-query";
import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";

function Router() {
  return (
    <div className="min-h-screen flex bg-gray-50">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header />
        <main className="flex-1 overflow-y-auto">
          <Switch>
            <Route path="/" component={Dashboard} />
            <Route path="/upload-policy" component={UploadPolicy} />
            <Route path="/policy-library" component={PolicyLibrary} />
            <Route path="/processing-queue" component={ProcessingQueue} />

            <Route path="/policy-context" component={PolicyContext} />
            <Route path="/property-risk-factors" component={PropertyRiskFactors} />
            <Route path="/policy-query" component={PolicyQueryPage} />
            <Route component={NotFound} />
          </Switch>
        </main>
      </div>
    </div>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <Toaster />
        <Router />
      </TooltipProvider>
    </QueryClientProvider>
  );
}

export default App;
