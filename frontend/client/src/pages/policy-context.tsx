import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useToast } from "@/hooks/use-toast";
import { apiClient } from "@/lib/api";
import { Policy } from "@shared/schema";
import { Home, Calendar, Shield, CheckCircle, AlertCircle } from "lucide-react";

// Available property features with descriptions
const PROPERTY_FEATURES = [
  { value: "monitored_alarm", label: "Monitored Alarm System", description: "24/7 monitored security system" },
  { value: "sprinkler_system", label: "Sprinkler System", description: "Fire suppression sprinkler system" },
  { value: "fire_extinguisher", label: "Fire Extinguisher", description: "Portable fire extinguishers" },
  { value: "smoke_detector", label: "Smoke Detector", description: "Smoke and fire detection system" },
  { value: "deadbolt_locks", label: "Deadbolt Locks", description: "High-security deadbolt locks" },
  { value: "security_camera", label: "Security Camera", description: "Video surveillance system" },
  { value: "storm_shutters", label: "Storm Shutters", description: "Hurricane-rated storm shutters" },
  { value: "impact_windows", label: "Impact Windows", description: "Impact-resistant windows" },
  { value: "smart_home_system", label: "Smart Home System", description: "Automated home security system" },
  { value: "backup_generator", label: "Backup Generator", description: "Emergency power generator" },
  { value: "water_leak_detector", label: "Water Leak Detector", description: "Water damage prevention system" },
  { value: "new_construction", label: "New Construction", description: "Recently built property" },
];

export default function PolicyContext() {
  const [selectedPolicyId, setSelectedPolicyId] = useState<string>("");
  const [installationDate, setInstallationDate] = useState<string>("");
  const [renewalDate, setRenewalDate] = useState<string>("");
  const [selectedFeatures, setSelectedFeatures] = useState<string[]>([]);
  const [isUpdating, setIsUpdating] = useState(false);
  const [updatedPolicyData, setUpdatedPolicyData] = useState<any>(null);
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const { data: policies = [] } = useQuery({
    queryKey: ["policies"],
    queryFn: async (): Promise<Policy[]> => {
      const result = await apiClient.getPolicies();
      return (result.data as Policy[]) || [];
    },
  });

  const selectedPolicy = policies.find(p => p.id.toString() === selectedPolicyId);
  
  // Use updated data if available, otherwise use the policy from the list
  const displayPolicy = updatedPolicyData && updatedPolicyData.policyId === selectedPolicyId 
    ? {
        ...selectedPolicy,
        roofAgeYears: updatedPolicyData.roofAgeYears,
        propertyFeatures: updatedPolicyData.propertyFeatures
      }
    : selectedPolicy;

  // Clear updated data when policy selection changes
  useEffect(() => {
    setUpdatedPolicyData(null);
  }, [selectedPolicyId]);

  const updatePolicyMutation = useMutation({
    mutationFn: async (data: {
      policyId: string;
      installationDate?: string;
      renewalDate?: string;
      propertyFeatures: string[];
    }) => {
      const response = await apiClient.updatePolicyContext(data.policyId, {
        installationDate: data.installationDate,
        renewalDate: data.renewalDate,
        propertyFeatures: data.propertyFeatures,
      });
      return response;
    },
    onSuccess: (data) => {
      toast({
        title: "Success",
        description: "Policy context updated successfully",
      });
      // Store the updated data to display immediately
      // The API client wraps responses in { data: ... }
      if (data.data) {
        setUpdatedPolicyData(data.data);
      }
      // Invalidate and refetch policies to get fresh data
      queryClient.invalidateQueries({ queryKey: ["policies"] });
      queryClient.refetchQueries({ queryKey: ["policies"] });
      // Reset form
      setInstallationDate("");
      setRenewalDate("");
      setSelectedFeatures([]);
    },
    onError: (error) => {
      toast({
        title: "Update Failed",
        description: error.message,
        variant: "destructive",
      });
    },
  });

  const handleFeatureToggle = (featureValue: string) => {
    setSelectedFeatures(prev => 
      prev.includes(featureValue) 
        ? prev.filter(f => f !== featureValue)
        : [...prev, featureValue]
    );
  };

  const handleSubmit = async () => {
    if (!selectedPolicyId) {
      toast({
        title: "Error",
        description: "Please select a policy",
        variant: "destructive",
      });
      return;
    }

    setIsUpdating(true);
    try {
      await updatePolicyMutation.mutateAsync({
        policyId: selectedPolicyId,
        installationDate: installationDate || undefined,
        renewalDate: renewalDate || undefined,
        propertyFeatures: selectedFeatures,
      });
    } finally {
      setIsUpdating(false);
    }
  };

  const calculateRoofAge = (installationDate: string) => {
    if (!installationDate) return null;
    const installDate = new Date(installationDate);
    const currentDate = new Date();
    let age = currentDate.getFullYear() - installDate.getFullYear();
    
    // Adjust for partial years
    if (currentDate.getMonth() < installDate.getMonth() || 
        (currentDate.getMonth() === installDate.getMonth() && currentDate.getDate() < installDate.getDate())) {
      age -= 1;
    }
    
    return Math.max(0, age);
  };

  const roofAge = installationDate ? calculateRoofAge(installationDate) : null;

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Policy Context Update</h1>
        <p className="text-gray-600 mt-2">
          Update roof age and property features for insurance policies
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Policy Selection */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Home className="w-5 h-5" />
              Select Policy
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Policy</Label>
              <Select value={selectedPolicyId} onValueChange={setSelectedPolicyId}>
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

            {displayPolicy && (
              <div className="p-4 bg-blue-50 rounded-lg">
                <h4 className="font-medium text-blue-900 mb-2">Selected Policy</h4>
                <div className="space-y-1 text-sm">
                  <p><span className="font-medium">Policy Number:</span> {displayPolicy.policyNumber}</p>
                  <p><span className="font-medium">Policyholder:</span> {displayPolicy.policyholderName}</p>
                  <p><span className="font-medium">Address:</span> {displayPolicy.propertyAddress}</p>
                  <p><span className="font-medium">Current Roof Age:</span> {displayPolicy.roofAgeYears || 'Not set'} years</p>
                  <p><span className="font-medium">Property Features:</span> {displayPolicy.propertyFeatures?.length || 0} features</p>
                  <p><span className="font-medium">Renewal Date:</span> {displayPolicy.renewalDate ? new Date(displayPolicy.renewalDate).toLocaleDateString() : 'Not set'}</p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Installation Date */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calendar className="w-5 h-5" />
              Roof Installation Date
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Installation Date</Label>
              <Input
                type="date"
                value={installationDate}
                onChange={(e) => setInstallationDate(e.target.value)}
                placeholder="Select installation date"
              />
              <p className="text-xs text-gray-600">
                Enter the date when the roof was installed or last replaced
              </p>
            </div>

            {roofAge !== null && (
              <div className="p-4 bg-green-50 rounded-lg">
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-600" />
                  <span className="font-medium text-green-900">Calculated Roof Age</span>
                </div>
                <p className="text-2xl font-bold text-green-700 mt-1">{roofAge} years</p>
                <p className="text-xs text-green-600 mt-1">
                  Based on installation date: {new Date(installationDate).toLocaleDateString()}
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Renewal Date */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calendar className="w-5 h-5" />
              Renewal Date
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Renewal Date</Label>
              <Input
                type="date"
                value={renewalDate}
                onChange={(e) => setRenewalDate(e.target.value)}
                placeholder="Select renewal date"
              />
              <p className="text-xs text-gray-600">
                Set the policy renewal date (defaults to expiration date)
              </p>
            </div>

            {renewalDate && (
              <div className="p-4 bg-yellow-50 rounded-lg">
                <div className="flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 text-yellow-600" />
                  <span className="font-medium text-yellow-900">Renewal Reminder</span>
                </div>
                <p className="text-sm text-yellow-700 mt-1">
                  Policy will need renewal on: {new Date(renewalDate).toLocaleDateString()}
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Property Features */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="w-5 h-5" />
              Property Features
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Select Features</Label>
              <div className="max-h-60 overflow-y-auto border rounded-lg p-3 space-y-2">
                {PROPERTY_FEATURES.map((feature) => (
                  <div
                    key={feature.value}
                    className={`flex items-start space-x-3 p-2 rounded-lg border cursor-pointer transition-colors ${
                      selectedFeatures.includes(feature.value)
                        ? "bg-blue-50 border-blue-200"
                        : "bg-gray-50 border-gray-200 hover:bg-gray-100"
                    }`}
                    onClick={() => handleFeatureToggle(feature.value)}
                  >
                    <input
                      type="checkbox"
                      checked={selectedFeatures.includes(feature.value)}
                      onChange={() => handleFeatureToggle(feature.value)}
                      className="mt-1"
                    />
                    <div className="flex-1">
                      <p className="font-medium text-sm">{feature.label}</p>
                      <p className="text-xs text-gray-600">{feature.description}</p>
                    </div>
                  </div>
                ))}
              </div>
              <p className="text-xs text-gray-600">
                Selected features may affect insurance rates and coverage
              </p>
            </div>

            {selectedFeatures.length > 0 && (
              <div className="p-3 bg-blue-50 rounded-lg">
                <p className="text-sm font-medium text-blue-900 mb-1">Selected Features ({selectedFeatures.length})</p>
                <div className="flex flex-wrap gap-1">
                  {selectedFeatures.map((feature) => {
                    const featureInfo = PROPERTY_FEATURES.find(f => f.value === feature);
                    return (
                      <span
                        key={feature}
                        className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                      >
                        {featureInfo?.label}
                      </span>
                    );
                  })}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Update Button */}
      <div className="mt-6 flex justify-end">
        <Button
          onClick={handleSubmit}
          disabled={isUpdating || !selectedPolicyId}
          className="min-w-[200px]"
        >
          {isUpdating ? "Updating..." : "Update Policy Context"}
        </Button>
      </div>

      {/* Information Panel */}
      <Card className="mt-6">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertCircle className="w-5 h-5" />
            Information
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div>
              <h4 className="font-medium mb-2">Roof Age Calculation</h4>
              <ul className="space-y-1 text-gray-600">
                <li>• Roof age is calculated from installation date to current date</li>
                <li>• Older roofs may require additional coverage</li>
                <li>• Roof age affects insurance rates and coverage options</li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium mb-2">Property Features</h4>
              <ul className="space-y-1 text-gray-600">
                <li>• Security features may qualify for discounts</li>
                <li>• Safety features can improve coverage options</li>
                <li>• Features are stored with the policy for future reference</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
} 