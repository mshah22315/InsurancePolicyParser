import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useToast } from "@/hooks/use-toast";
import { apiRequest } from "@/lib/queryClient";
import { Policy, PropertyFeature } from "@shared/schema";
import { AVAILABLE_FEATURES } from "@/lib/types";
import { useState } from "react";
import { Home, Settings, X, Plus } from "lucide-react";

interface PropertyFeaturesModalProps {
  isOpen: boolean;
  onClose: () => void;
  selectedPolicyId?: number;
}

export function PropertyFeaturesModal({ isOpen, onClose, selectedPolicyId }: PropertyFeaturesModalProps) {
  const [selectedPolicyIdState, setSelectedPolicyIdState] = useState<number | undefined>(selectedPolicyId);
  const [selectedFeatures, setSelectedFeatures] = useState<Set<string>>(new Set());
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const { data: policies = [] } = useQuery<Policy[]>({
    queryKey: ["/api/policies"],
    enabled: isOpen,
  });

  const { data: existingFeatures = [] } = useQuery<PropertyFeature[]>({
    queryKey: ["/api/policies", selectedPolicyIdState, "features"],
    enabled: !!selectedPolicyIdState && isOpen,
  });

  // Initialize selected features when existing features are loaded
  useState(() => {
    if (existingFeatures.length > 0) {
      setSelectedFeatures(new Set(existingFeatures.map(f => f.featureName)));
    }
  });

  const createFeatureMutation = useMutation({
    mutationFn: async (featureName: string) => {
      const feature = AVAILABLE_FEATURES.find(f => f.name === featureName);
      const response = await apiRequest("POST", `/api/policies/${selectedPolicyIdState}/features`, {
        featureName,
        featureDescription: feature?.description || "",
        discountPercentage: feature?.discountPercentage || 0,
      });
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/policies", selectedPolicyIdState, "features"] });
    },
  });

  const deleteFeatureMutation = useMutation({
    mutationFn: async (featureId: number) => {
      await apiRequest("DELETE", `/api/features/${featureId}`, undefined);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/policies", selectedPolicyIdState, "features"] });
    },
  });

  const handleFeatureToggle = async (featureName: string, checked: boolean) => {
    if (!selectedPolicyIdState) {
      toast({
        title: "Error",
        description: "Please select a policy first",
        variant: "destructive",
      });
      return;
    }

    const newSelectedFeatures = new Set(selectedFeatures);
    
    if (checked) {
      newSelectedFeatures.add(featureName);
      setSelectedFeatures(newSelectedFeatures);
      
      try {
        await createFeatureMutation.mutateAsync(featureName);
        toast({
          title: "Success",
          description: `${featureName} feature added`,
        });
      } catch (error) {
        newSelectedFeatures.delete(featureName);
        setSelectedFeatures(newSelectedFeatures);
        toast({
          title: "Error",
          description: "Failed to add feature",
          variant: "destructive",
        });
      }
    } else {
      newSelectedFeatures.delete(featureName);
      setSelectedFeatures(newSelectedFeatures);
      
      const existingFeature = existingFeatures.find(f => f.featureName === featureName);
      if (existingFeature) {
        try {
          await deleteFeatureMutation.mutateAsync(existingFeature.id);
          toast({
            title: "Success",
            description: `${featureName} feature removed`,
          });
        } catch (error) {
          newSelectedFeatures.add(featureName);
          setSelectedFeatures(newSelectedFeatures);
          toast({
            title: "Error",
            description: "Failed to remove feature",
            variant: "destructive",
          });
        }
      }
    }
  };

  const handleSaveFeatures = () => {
    toast({
      title: "Success",
      description: "Property features updated successfully",
    });
    onClose();
  };

  const selectedPolicy = policies.find(p => p.id === selectedPolicyIdState);

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Settings className="w-5 h-5" />
            Manage Property Features
          </DialogTitle>
          <DialogDescription>
            Add or remove property features that may affect insurance premiums and coverage
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Policy Selection */}
          <div>
            <Label htmlFor="policy-select">Select Policy</Label>
            <Select
              value={selectedPolicyIdState?.toString()}
              onValueChange={(value) => {
                setSelectedPolicyIdState(parseInt(value));
                setSelectedFeatures(new Set());
              }}
            >
              <SelectTrigger>
                <SelectValue placeholder="Choose a policy..." />
              </SelectTrigger>
              <SelectContent>
                {policies.map((policy) => (
                  <SelectItem key={policy.id} value={policy.id.toString()}>
                    {policy.policyNumber} - {policy.policyholderName}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Selected Policy Info */}
          {selectedPolicy && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Home className="w-4 h-4" />
                  Selected Policy Details
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-gray-600">Policy Number:</p>
                    <p className="font-medium">{selectedPolicy.policyNumber}</p>
                  </div>
                  <div>
                    <p className="text-gray-600">Policyholder:</p>
                    <p className="font-medium">{selectedPolicy.policyholderName}</p>
                  </div>
                  <div className="col-span-2">
                    <p className="text-gray-600">Property Address:</p>
                    <p className="font-medium">{selectedPolicy.propertyAddress}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Available Features */}
          {selectedPolicyIdState && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Plus className="w-4 h-4" />
                  Available Features
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {AVAILABLE_FEATURES.map((feature) => {
                    const isSelected = selectedFeatures.has(feature.name);
                    
                    return (
                      <div
                        key={feature.name}
                        className="flex items-center space-x-3 p-3 border rounded-lg hover:bg-gray-50 cursor-pointer"
                        onClick={() => handleFeatureToggle(feature.name, !isSelected)}
                      >
                        <Checkbox
                          checked={isSelected}
                          onChange={(checked) => handleFeatureToggle(feature.name, checked)}
                        />
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <span className="font-medium text-gray-900">{feature.name}</span>
                            {feature.discountPercentage && (
                              <Badge variant="secondary" className="bg-green-100 text-green-800">
                                {feature.discountPercentage}% discount
                              </Badge>
                            )}
                          </div>
                          <p className="text-sm text-gray-600">{feature.description}</p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Selected Features Summary */}
          {selectedPolicyIdState && selectedFeatures.size > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Selected Features Summary</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {Array.from(selectedFeatures).map((featureName) => {
                    const feature = AVAILABLE_FEATURES.find(f => f.name === featureName);
                    
                    return (
                      <Badge
                        key={featureName}
                        variant="secondary"
                        className="bg-blue-100 text-blue-800 flex items-center gap-1"
                      >
                        {featureName}
                        {feature?.discountPercentage && (
                          <span className="text-xs">({feature.discountPercentage}%)</span>
                        )}
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-4 w-4 p-0 hover:bg-blue-200"
                          onClick={() => handleFeatureToggle(featureName, false)}
                        >
                          <X className="w-3 h-3" />
                        </Button>
                      </Badge>
                    );
                  })}
                </div>
                
                {selectedFeatures.size > 0 && (
                  <div className="mt-4 p-3 bg-green-50 rounded-lg">
                    <p className="text-sm text-green-800">
                      <strong>Total Potential Discount:</strong>{" "}
                      {Array.from(selectedFeatures).reduce((total, featureName) => {
                        const feature = AVAILABLE_FEATURES.find(f => f.name === featureName);
                        return total + (feature?.discountPercentage || 0);
                      }, 0)}%
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Actions */}
          <div className="flex items-center justify-end space-x-4 pt-4 border-t">
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button 
              onClick={handleSaveFeatures}
              disabled={!selectedPolicyIdState}
            >
              Save Features
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
