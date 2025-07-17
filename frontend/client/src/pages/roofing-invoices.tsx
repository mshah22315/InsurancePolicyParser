import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useQuery } from "@tanstack/react-query";
import { RoofingInvoice } from "@shared/schema";
import { Upload, FileText, Calendar } from "lucide-react";
import { format } from "date-fns";

export default function RoofingInvoices() {
  const { data: invoices = [], isLoading } = useQuery<RoofingInvoice[]>({
    queryKey: ["/api/roofing-invoices"],
  });

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

  const calculateRoofAge = (installationDate: Date) => {
    const currentDate = new Date();
    const years = currentDate.getFullYear() - installationDate.getFullYear();
    return years;
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Roofing Invoices</h1>
        <p className="text-gray-600 mt-2">
          Upload and manage roofing invoices to calculate roof age for insurance policies
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Invoices</p>
                <p className="text-2xl font-bold text-gray-900">{invoices.length}</p>
              </div>
              <FileText className="w-8 h-8 text-gray-400" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Processed</p>
                <p className="text-2xl font-bold text-green-600">
                  {invoices.filter(i => i.processingStatus === "completed").length}
                </p>
              </div>
              <FileText className="w-8 h-8 text-green-400" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Avg Roof Age</p>
                <p className="text-2xl font-bold text-blue-600">
                  {invoices.length > 0 
                    ? Math.round(invoices.reduce((sum, inv) => sum + (inv.roofAgeYears || 0), 0) / invoices.length)
                    : 0
                  } years
                </p>
              </div>
              <Calendar className="w-8 h-8 text-blue-400" />
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Roofing Invoices</CardTitle>
            <Button>
              <Upload className="w-4 h-4 mr-2" />
              Upload Invoice
            </Button>
          </div>
        </CardHeader>
        
        <CardContent>
          {isLoading ? (
            <div className="animate-pulse space-y-4">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="h-12 bg-gray-200 rounded" />
              ))}
            </div>
          ) : invoices.length === 0 ? (
            <div className="text-center py-8">
              <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500 mb-2">No roofing invoices found</p>
              <p className="text-sm text-gray-400">Upload your first roofing invoice to get started</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Filename</TableHead>
                    <TableHead>Policy ID</TableHead>
                    <TableHead>Installation Date</TableHead>
                    <TableHead>Roof Age</TableHead>
                    <TableHead>Work Description</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {invoices.map((invoice) => (
                    <TableRow key={invoice.id}>
                      <TableCell className="font-medium">{invoice.filename}</TableCell>
                      <TableCell>{invoice.policyId}</TableCell>
                      <TableCell>
                        {invoice.installationDate 
                          ? format(new Date(invoice.installationDate), "PPP")
                          : "N/A"
                        }
                      </TableCell>
                      <TableCell className="font-medium">
                        {invoice.roofAgeYears ? `${invoice.roofAgeYears} years` : "N/A"}
                      </TableCell>
                      <TableCell className="max-w-xs truncate">
                        {invoice.workDescription || "N/A"}
                      </TableCell>
                      <TableCell>
                        <Badge variant="secondary" className={getStatusColor(invoice.processingStatus)}>
                          {invoice.processingStatus}
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
        </CardContent>
      </Card>
    </div>
  );
}
