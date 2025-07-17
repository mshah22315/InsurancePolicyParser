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
    queryKey: ["/api/policies", policyId],
    enabled: !!policyId && isOpen,
  });

  const { data: features = [] } = useQuery<PropertyFeature[]>({
    queryKey: ["/api/policies", policyId, "features"],
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

                  <div>
                    <p className="text-sm text-gray-600">Document Source</p>
                    <p className="font-medium">
                      {policy.documentSourceFilename || "N/A"}
                    </p>
                    {policy.documentSourceFilename && (
                      <Button 
                        variant="outline" 
                        size="sm" 
                        className="mt-2"
                        onClick={async () => {
                          try {
                            const response = await fetch(`http://localhost:5001/api/policies/${policyId}/download`, {
                              credentials: 'include'
                            });
                            if (response.ok) {
                              const data = await response.json();
                              // For now, just show the download URL
                              // In a real implementation, you would trigger a download
                              alert(`Download URL: ${data.downloadUrl}`);
                            } else {
                              alert('Download not available');
                            }
                          } catch (error) {
                            alert('Failed to get download link');
                          }
                        }}
                      >
                        <Download className="w-4 h-4 mr-2" />
                        Download Document
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Property Features */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Home className="w-5 h-5" />
                  Property Features
                </CardTitle>
              </CardHeader>
              <CardContent>
                {features.length === 0 ? (
                  <div className="text-center py-8">
                    <Home className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-500">No property features recorded</p>
                    <Button variant="outline" className="mt-4">
                      Add Features
                    </Button>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {features.map((feature) => (
                      <div key={feature.id} className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                        <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                        <div className="flex-1">
                          <p className="font-medium text-gray-900">{feature.featureName}</p>
                          {feature.featureDescription && (
                            <p className="text-sm text-gray-600">{feature.featureDescription}</p>
                          )}
                          {feature.discountPercentage && (
                            <p className="text-sm text-green-600 font-medium">
                              {feature.discountPercentage}% discount
                            </p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
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
                            <TableCell className="font-medium">{coverage.coverageType}</TableCell>
                            <TableCell>{formatCurrency(coverage.limit)}</TableCell>
                            <TableCell>{formatCurrency(coverage.deductible)}</TableCell>
                            <TableCell>{formatCurrency(coverage.premium)}</TableCell>
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
                        <h4 className="font-medium text-gray-900 mb-2">{deductible.coverageType}</h4>
                        <p className="text-lg font-semibold">{formatCurrency(deductible.amount)}</p>
                        <p className="text-sm text-gray-600 capitalize">{deductible.type}</p>
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
