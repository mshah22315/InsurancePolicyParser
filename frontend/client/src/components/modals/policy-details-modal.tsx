import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Separator } from "@/components/ui/separator";
import { useQuery } from "@tanstack/react-query";
import { Policy, PropertyFeature } from "@shared/schema";
import { format } from "date-fns";
import { FileText, Calendar, DollarSign, MapPin, Shield, Home, Settings, Download } from "lucide-react";

interface PolicyDetailsModalProps {
  isOpen: boolean;
  onClose: () => void;
  policyId: number | null;
}

export function PolicyDetailsModal({ isOpen, onClose, policyId }: PolicyDetailsModalProps) {
  const { data: policy, isLoading } = useQuery<Policy>({
    queryKey: [`http://localhost:5001/api/policies/${policyId}`],
    enabled: !!policyId && isOpen,
  });

  const { data: features = [] } = useQuery<PropertyFeature[]>({
    queryKey: [`http://localhost:5001/api/policies/${policyId}/features`],
    enabled: !!policyId && isOpen,
  });

  if (!policyId) return null;

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
    }).format(amount);
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

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-6xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <FileText className="w-5 h-5" />
            Policy Details
          </DialogTitle>
          <DialogDescription>
            View comprehensive policy information and coverage details
          </DialogDescription>
        </DialogHeader>

        {isLoading ? (
          <div className="animate-pulse space-y-4">
            <div className="h-32 bg-gray-200 rounded-lg" />
            <div className="h-48 bg-gray-200 rounded-lg" />
            <div className="h-32 bg-gray-200 rounded-lg" />
          </div>
        ) : !policy ? (
          <div className="text-center py-8">
            <p className="text-gray-500">Policy not found</p>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Basic Information */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Shield className="w-5 h-5" />
                    Basic Information
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-gray-600">Policy Number</p>
                      <p className="font-medium">{policy.policyNumber}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Status</p>
                      <Badge className={getStatusColor(policy.processingStatus || 'unknown')}>
                        {policy.processingStatus || 'Unknown'}
                      </Badge>
                    </div>
                  </div>
                  
                  <Separator />
                  
                  <div>
                    <p className="text-sm text-gray-600">Insurer</p>
                    <p className="font-medium">{policy.insurerName}</p>
                  </div>
                  
                  <div>
                    <p className="text-sm text-gray-600">Policyholder</p>
                    <p className="font-medium">{policy.policyholderName}</p>
                  </div>
                  
                  <div>
                    <p className="text-sm text-gray-600 flex items-center gap-1">
                      <MapPin className="w-4 h-4" />
                      Property Address
                    </p>
                    <p className="font-medium">{policy.propertyAddress}</p>
                  </div>
                  
                  <div>
                    <p className="text-sm text-gray-600 flex items-center gap-1">
                      <DollarSign className="w-4 h-4" />
                      Total Premium
                    </p>
                    <p className="font-medium text-lg">
                      {policy.totalPremium ? formatCurrency(policy.totalPremium) : "N/A"}
                    </p>
                  </div>
                </CardContent>
              </Card>

              {/* Policy Dates */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Calendar className="w-5 h-5" />
                    Policy Dates
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <p className="text-sm text-gray-600">Effective Date</p>
                    <p className="font-medium">
                      {policy.effectiveDate ? format(new Date(policy.effectiveDate), "PPP") : "N/A"}
                    </p>
                  </div>
                  
                  <div>
                    <p className="text-sm text-gray-600">Expiration Date</p>
                    <p className="font-medium">
                      {policy.expirationDate ? format(new Date(policy.expirationDate), "PPP") : "N/A"}
                    </p>
                  </div>
                  
                  <div>
                    <p className="text-sm text-gray-600">Created</p>
                    <p className="font-medium">
                      {policy.createdAt ? format(new Date(policy.createdAt), "PPP") : "N/A"}
                    </p>
                  </div>
                  
                  <div>
                    <p className="text-sm text-gray-600">Last Updated</p>
                    <p className="font-medium">
                      {policy.updatedAt ? format(new Date(policy.updatedAt), "PPP") : "N/A"}
                    </p>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Property Features */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Home className="w-5 h-5" />
                  Property Features & Roof Information
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {/* Roof Age */}
                  <div className="p-4 bg-blue-50 rounded-lg">
                    <h4 className="font-medium text-blue-900 mb-2">Roof Information</h4>
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-blue-700">Roof Age:</span>
                      <span className="font-medium text-blue-900">
                        {policy.roofAgeYears ? `${policy.roofAgeYears} years` : "Not specified"}
                      </span>
                    </div>
                  </div>

                  {/* Property Features */}
                  <div>
                    <h4 className="font-medium text-gray-900 mb-2">Property Features</h4>
                    {policy.propertyFeatures && policy.propertyFeatures.length > 0 ? (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        {policy.propertyFeatures.map((feature, index) => (
                          <div key={index} className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                            <div className="flex-1">
                              <p className="font-medium text-gray-900">{feature}</p>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-center py-4">
                        <Home className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                        <p className="text-gray-500">No property features recorded</p>
                      </div>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Coverage Details */}
            {policy.coverageDetails && policy.coverageDetails.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Shield className="w-5 h-5" />
                    Coverage Details
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="overflow-x-auto">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Coverage Type</TableHead>
                          <TableHead>Limit</TableHead>
                          <TableHead>Deductible</TableHead>
                          <TableHead>Premium</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {policy.coverageDetails.map((coverage, index) => (
                          <TableRow key={index}>
                            <TableCell className="font-medium">
                              {coverage.coverageType || coverage.coverage_type}
                            </TableCell>
                            <TableCell>
                              {coverage.limit ? formatCurrency(parseFloat(coverage.limit)) : "N/A"}
                            </TableCell>
                            <TableCell>
                              {coverage.deductible ? formatCurrency(coverage.deductible) : "N/A"}
                            </TableCell>
                            <TableCell>
                              {coverage.premium ? formatCurrency(coverage.premium) : "N/A"}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Deductibles */}
            {policy.deductibles && policy.deductibles.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <DollarSign className="w-5 h-5" />
                    Deductibles
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {policy.deductibles.map((deductible, index) => (
                      <div key={index} className="p-4 bg-gray-50 rounded-lg">
                        <h4 className="font-medium text-gray-900 mb-2">
                          {deductible.coverageType || deductible.coverage_type}
                        </h4>
                        <p className="text-lg font-semibold">
                          {deductible.amount ? formatCurrency(parseFloat(deductible.amount)) : "N/A"}
                        </p>
                        <p className="text-sm text-gray-600 capitalize">
                          {deductible.type || "per occurrence"}
                        </p>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Actions */}
            <div className="flex items-center justify-end space-x-4 pt-4 border-t">
              <Button variant="outline" onClick={onClose}>
                Close
              </Button>
              <Button>
                <Settings className="w-4 h-4 mr-2" />
                Edit Policy
              </Button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
