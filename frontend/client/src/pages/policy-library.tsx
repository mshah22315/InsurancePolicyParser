import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useQuery } from "@tanstack/react-query";
import { Policy } from "@shared/schema";
import { Search, Download, Eye } from "lucide-react";
import { useState } from "react";
import { PolicyDetailsModal } from "@/components/modals/policy-details-modal";

export default function PolicyLibrary() {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedInsurer, setSelectedInsurer] = useState("all");
  const [selectedStatus, setSelectedStatus] = useState("all");
  const [selectedPolicyId, setSelectedPolicyId] = useState<number | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  
  const { data: policies = [], isLoading } = useQuery<Policy[]>({
    queryKey: ["http://localhost:5001/api/policies"],
  });

  const { data: searchResults = [] } = useQuery<Policy[]>({
    queryKey: ["http://localhost:5001/api/policies/search", searchQuery],
    enabled: searchQuery.length > 2,
  });

  const displayPolicies = searchQuery.length > 2 ? searchResults : policies;

  const filteredPolicies = displayPolicies.filter(policy => {
    const matchesInsurer = selectedInsurer === "all" || policy.insurerName === selectedInsurer;
    const matchesStatus = selectedStatus === "all" || policy.processingStatus === selectedStatus;
    return matchesInsurer && matchesStatus;
  });

  const uniqueInsurers = [...new Set(policies.map(p => p.insurerName))];
  const uniqueStatuses = [...new Set(policies.map(p => p.processingStatus))];

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

  const handleViewPolicy = (policyId: number) => {
    setSelectedPolicyId(policyId);
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setSelectedPolicyId(null);
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Policy Library</h1>
        <p className="text-gray-600 mt-2">
          Browse and search through all processed insurance policies
        </p>
      </div>

      <Card>
        <CardHeader>
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <CardTitle>All Policies</CardTitle>
            
            <div className="flex items-center gap-4">
              {/* Search */}
              <div className="relative">
                <Search className="absolute left-3 top-2.5 w-4 h-4 text-gray-400" />
                <Input
                  placeholder="Search policies..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10 w-64"
                />
              </div>
              
              {/* Filters */}
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
              
              <Select value={selectedStatus} onValueChange={setSelectedStatus}>
                <SelectTrigger className="w-40">
                  <SelectValue placeholder="All Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  {uniqueStatuses.map(status => (
                    <SelectItem key={status} value={status}>{status}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              
              <Button>
                <Download className="w-4 h-4 mr-2" />
                Export
              </Button>
            </div>
          </div>
        </CardHeader>
        
        <CardContent>
          {isLoading ? (
            <div className="animate-pulse space-y-4">
              {[...Array(10)].map((_, i) => (
                <div key={i} className="h-12 bg-gray-200 rounded" />
              ))}
            </div>
          ) : filteredPolicies.length === 0 ? (
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
                    <TableHead>Effective Date</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredPolicies.map((policy) => (
                    <TableRow key={policy.id}>
                      <TableCell className="font-medium">{policy.policyNumber}</TableCell>
                      <TableCell>{policy.policyholderName}</TableCell>
                      <TableCell>{policy.insurerName}</TableCell>
                      <TableCell className="max-w-xs truncate">{policy.propertyAddress}</TableCell>
                      <TableCell className="font-medium">
                        {policy.totalPremium ? `$${policy.totalPremium.toFixed(2)}` : "N/A"}
                      </TableCell>
                      <TableCell>
                        {policy.effectiveDate ? new Date(policy.effectiveDate).toLocaleDateString() : "N/A"}
                      </TableCell>
                      <TableCell>
                        <Badge variant="secondary" className={getStatusColor(policy.processingStatus)}>
                          {policy.processingStatus}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Button 
                          variant="ghost" 
                          size="sm" 
                          className="text-blue-600 hover:text-blue-700"
                          onClick={() => handleViewPolicy(policy.id)}
                        >
                          <Eye className="w-4 h-4 mr-1" />
                          View
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Policy Details Modal */}
      <PolicyDetailsModal
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        policyId={selectedPolicyId}
      />
    </div>
  );
}
