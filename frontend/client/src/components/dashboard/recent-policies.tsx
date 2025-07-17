import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useQuery } from "@tanstack/react-query";
import { Policy } from "@shared/schema";
import { useState } from "react";
import { format } from "date-fns";
import { apiClient } from "@/lib/api";

export function RecentPolicies() {
  const [selectedInsurer, setSelectedInsurer] = useState("all");
  
  // Use backend API for policies
  const { data: policiesResponse, isLoading } = useQuery({
    queryKey: ["policies"],
    queryFn: () => apiClient.getPolicies(50, 0),
  });

  const policies = policiesResponse?.data || [];

  const filteredPolicies = policies.filter(policy => 
    selectedInsurer === "all" || policy.insurerName === selectedInsurer
  );

  const uniqueInsurers = [...new Set(policies.map(p => p.insurerName))];

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

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Recent Policies</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse space-y-4">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-12 bg-gray-200 rounded" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Recent Policies</CardTitle>
          <div className="flex items-center space-x-4">
            <Select value={selectedInsurer} onValueChange={setSelectedInsurer}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="All Insurers" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Insurers</SelectItem>
                {uniqueInsurers.map(insurer => (
                  <SelectItem key={insurer} value={insurer}>{insurer}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button>Export Data</Button>
          </div>
        </div>
      </CardHeader>
      
      <CardContent>
        {filteredPolicies.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-gray-500">No policies found</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Policy Number</TableHead>
                  <TableHead>Policyholder</TableHead>
                  <TableHead>Insurer</TableHead>
                  <TableHead>Property Address</TableHead>
                  <TableHead>Premium</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredPolicies.slice(0, 10).map((policy) => (
                  <TableRow key={policy.id}>
                    <TableCell className="font-medium">{policy.policyNumber}</TableCell>
                    <TableCell>{policy.policyholderName}</TableCell>
                    <TableCell>{policy.insurerName}</TableCell>
                    <TableCell>{policy.propertyAddress}</TableCell>
                    <TableCell className="font-medium">
                      {policy.totalPremium ? `$${policy.totalPremium.toFixed(2)}` : "N/A"}
                    </TableCell>
                    <TableCell>
                      <Badge variant="secondary" className={getStatusColor(policy.processingStatus)}>
                        {policy.processingStatus}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Button variant="ghost" size="sm" className="text-blue-600 hover:text-blue-700">
                        View
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
        
        <div className="flex items-center justify-between mt-4 pt-4 border-t">
          <div className="text-sm text-gray-500">
            Showing 1-{Math.min(10, filteredPolicies.length)} of {filteredPolicies.length} policies
          </div>
          <div className="flex items-center space-x-2">
            <Button variant="outline" size="sm">Previous</Button>
            <Button variant="outline" size="sm">1</Button>
            <Button variant="outline" size="sm">2</Button>
            <Button variant="outline" size="sm">3</Button>
            <Button variant="outline" size="sm">Next</Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
