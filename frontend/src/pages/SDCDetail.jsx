import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import { API } from "@/App";
import { toast } from "sonner";
import { 
  Building2, 
  ArrowLeft, 
  Users,
  Calendar,
  DollarSign,
  FileText,
  CheckCircle,
  Clock,
  AlertTriangle,
  Plus,
  Edit
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export default function SDCDetail({ user }) {
  const { sdcId } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [sdcData, setSdcData] = useState(null);
  const [activeTab, setActiveTab] = useState("progress");
  const [showBatchDialog, setShowBatchDialog] = useState(false);
  const [showInvoiceDialog, setShowInvoiceDialog] = useState(false);

  const fetchSDCData = async () => {
    try {
      const response = await axios.get(`${API}/sdcs/${sdcId}`);
      setSdcData(response.data);
    } catch (error) {
      console.error("Error fetching SDC:", error);
      toast.error("Failed to load SDC data");
      if (error.response?.status === 403) {
        navigate("/dashboard");
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSDCData();
  }, [sdcId]);

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0
    }).format(value);
  };

  if (loading) {
    return <SDCDetailSkeleton />;
  }

  if (!sdcData) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <AlertTriangle className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
          <p className="text-muted-foreground">SDC not found</p>
          <Button variant="outline" onClick={() => navigate("/dashboard")} className="mt-4">
            Back to Dashboard
          </Button>
        </div>
      </div>
    );
  }

  const { progress, financial, job_roles, batches, invoices } = sdcData;

  return (
    <div className="min-h-screen bg-background" data-testid="sdc-detail">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-background/95 backdrop-blur-sm border-b border-border">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" onClick={() => navigate("/dashboard")} data-testid="back-btn">
              <ArrowLeft className="w-5 h-5" />
            </Button>
            <div>
              <h1 className="font-heading font-bold text-xl">{sdcData.name}</h1>
              <p className="text-sm text-muted-foreground">{sdcData.location}</p>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            {(user?.role === "ho" || user?.assigned_sdc_id === sdcId) && (
              <>
                <Dialog open={showBatchDialog} onOpenChange={setShowBatchDialog}>
                  <DialogTrigger asChild>
                    <Button variant="outline" size="sm" data-testid="add-batch-btn">
                      <Plus className="w-4 h-4 mr-1" />
                      Add Batch
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <AddBatchForm 
                      sdcId={sdcId} 
                      jobRoles={job_roles} 
                      onSuccess={() => {
                        setShowBatchDialog(false);
                        fetchSDCData();
                      }} 
                    />
                  </DialogContent>
                </Dialog>
                
                <Dialog open={showInvoiceDialog} onOpenChange={setShowInvoiceDialog}>
                  <DialogTrigger asChild>
                    <Button variant="outline" size="sm" data-testid="add-invoice-btn">
                      <Plus className="w-4 h-4 mr-1" />
                      Add Invoice
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <AddInvoiceForm 
                      sdcId={sdcId} 
                      onSuccess={() => {
                        setShowInvoiceDialog(false);
                        fetchSDCData();
                      }} 
                    />
                  </DialogContent>
                </Dialog>
              </>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Summary Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <Card className="border border-border animate-fade-in stagger-1">
            <CardContent className="p-4">
              <div className="flex items-center gap-2 mb-2">
                <Users className="w-4 h-4 text-amber-600" />
                <span className="text-sm text-muted-foreground">Mobilized</span>
              </div>
              <div className="font-mono font-bold text-2xl">{progress.mobilized}</div>
            </CardContent>
          </Card>
          
          <Card className="border border-border animate-fade-in stagger-2">
            <CardContent className="p-4">
              <div className="flex items-center gap-2 mb-2">
                <Clock className="w-4 h-4 text-blue-600" />
                <span className="text-sm text-muted-foreground">In Training</span>
              </div>
              <div className="font-mono font-bold text-2xl">{progress.in_training}</div>
            </CardContent>
          </Card>
          
          <Card className="border border-border animate-fade-in stagger-3">
            <CardContent className="p-4">
              <div className="flex items-center gap-2 mb-2">
                <FileText className="w-4 h-4 text-purple-600" />
                <span className="text-sm text-muted-foreground">Assessed</span>
              </div>
              <div className="font-mono font-bold text-2xl">{progress.assessed}</div>
            </CardContent>
          </Card>
          
          <Card className="border border-border animate-fade-in stagger-4">
            <CardContent className="p-4">
              <div className="flex items-center gap-2 mb-2">
                <CheckCircle className="w-4 h-4 text-emerald-600" />
                <span className="text-sm text-muted-foreground">Placed</span>
              </div>
              <div className="font-mono font-bold text-2xl text-emerald-600">{progress.placed}</div>
              <div className="text-xs text-muted-foreground mt-1">{progress.placement_percent}% rate</div>
            </CardContent>
          </Card>
        </div>

        {/* Progress Bar */}
        <Card className="mb-8 border border-border animate-fade-in" data-testid="progress-bar-card">
          <CardHeader className="pb-2">
            <CardTitle className="font-heading font-bold">Training Pipeline</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex h-4 rounded-full overflow-hidden bg-muted">
              <div 
                className="bg-amber-500 transition-all duration-500"
                style={{ width: `${getStagePercent(progress, 'mobilized')}%` }}
                title={`Mobilized: ${progress.mobilized}`}
              />
              <div 
                className="bg-blue-500 transition-all duration-500"
                style={{ width: `${getStagePercent(progress, 'in_training')}%` }}
                title={`In Training: ${progress.in_training}`}
              />
              <div 
                className="bg-purple-500 transition-all duration-500"
                style={{ width: `${getStagePercent(progress, 'assessed')}%` }}
                title={`Assessed: ${progress.assessed}`}
              />
              <div 
                className="bg-emerald-500 transition-all duration-500"
                style={{ width: `${getStagePercent(progress, 'placed')}%` }}
                title={`Placed: ${progress.placed}`}
              />
            </div>
            <div className="mt-3 flex flex-wrap gap-4">
              <LegendItem color="bg-amber-500" label="Mobilized" value={progress.mobilized} />
              <LegendItem color="bg-blue-500" label="Training" value={progress.in_training} />
              <LegendItem color="bg-purple-500" label="Assessed" value={progress.assessed} />
              <LegendItem color="bg-emerald-500" label="Placed" value={progress.placed} />
            </div>
          </CardContent>
        </Card>

        {/* Financial Summary */}
        <Card className="mb-8 border border-border animate-fade-in" data-testid="financial-summary">
          <CardHeader className="pb-2">
            <CardTitle className="font-heading font-bold">Financial Summary</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-6">
              <div>
                <div className="text-sm text-muted-foreground mb-1">Total Billed</div>
                <div className="font-mono font-bold text-xl">{formatCurrency(financial.total_billed)}</div>
              </div>
              <div>
                <div className="text-sm text-muted-foreground mb-1">Total Paid</div>
                <div className="font-mono font-bold text-xl text-emerald-600">{formatCurrency(financial.total_paid)}</div>
              </div>
              <div>
                <div className="text-sm text-muted-foreground mb-1">Outstanding</div>
                <div className={`font-mono font-bold text-xl ${financial.outstanding > 0 ? 'text-red-600' : 'text-emerald-600'}`}>
                  {formatCurrency(financial.outstanding)}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="animate-fade-in">
          <TabsList className="mb-6">
            <TabsTrigger value="progress" data-testid="tab-progress">Batches</TabsTrigger>
            <TabsTrigger value="jobroles" data-testid="tab-jobroles">Job Roles</TabsTrigger>
            <TabsTrigger value="billing" data-testid="tab-billing">Billing</TabsTrigger>
          </TabsList>

          <TabsContent value="progress">
            <Card className="border border-border">
              <CardHeader>
                <CardTitle className="font-heading">Active Batches</CardTitle>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="uppercase text-xs font-bold tracking-wider">Work Order</TableHead>
                      <TableHead className="uppercase text-xs font-bold tracking-wider">Start</TableHead>
                      <TableHead className="uppercase text-xs font-bold tracking-wider">End</TableHead>
                      <TableHead className="uppercase text-xs font-bold tracking-wider text-center">Mob</TableHead>
                      <TableHead className="uppercase text-xs font-bold tracking-wider text-center">Train</TableHead>
                      <TableHead className="uppercase text-xs font-bold tracking-wider text-center">Assess</TableHead>
                      <TableHead className="uppercase text-xs font-bold tracking-wider text-center">Placed</TableHead>
                      <TableHead className="uppercase text-xs font-bold tracking-wider">Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {batches?.map((batch) => (
                      <TableRow key={batch.batch_id} className="hover:bg-muted/50">
                        <TableCell className="font-mono text-sm">{batch.work_order_number}</TableCell>
                        <TableCell className="font-mono text-sm">{batch.start_date}</TableCell>
                        <TableCell className="font-mono text-sm">{batch.end_date}</TableCell>
                        <TableCell className="text-center font-mono">{batch.mobilized}</TableCell>
                        <TableCell className="text-center font-mono">{batch.in_training}</TableCell>
                        <TableCell className="text-center font-mono">{batch.assessed}</TableCell>
                        <TableCell className="text-center font-mono text-emerald-600">{batch.placed}</TableCell>
                        <TableCell>
                          <Badge variant={batch.status === "active" ? "default" : "secondary"}>
                            {batch.status}
                          </Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                    {(!batches || batches.length === 0) && (
                      <TableRow>
                        <TableCell colSpan={8} className="text-center py-8 text-muted-foreground">
                          No batches found
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="jobroles">
            <Card className="border border-border">
              <CardHeader>
                <CardTitle className="font-heading">Job Roles</CardTitle>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="uppercase text-xs font-bold tracking-wider">Code</TableHead>
                      <TableHead className="uppercase text-xs font-bold tracking-wider">Name</TableHead>
                      <TableHead className="uppercase text-xs font-bold tracking-wider">Awarding Body</TableHead>
                      <TableHead className="uppercase text-xs font-bold tracking-wider text-right">Hours</TableHead>
                      <TableHead className="uppercase text-xs font-bold tracking-wider text-right">Target</TableHead>
                      <TableHead className="uppercase text-xs font-bold tracking-wider text-right">Value</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {job_roles?.map((jr) => (
                      <TableRow key={jr.job_role_id} className="hover:bg-muted/50">
                        <TableCell className="font-mono text-sm">{jr.job_role_code}</TableCell>
                        <TableCell className="font-medium">{jr.job_role_name}</TableCell>
                        <TableCell className="text-sm text-muted-foreground">{jr.awarding_body}</TableCell>
                        <TableCell className="text-right font-mono">{jr.training_hours}</TableCell>
                        <TableCell className="text-right font-mono">{jr.target_candidates}</TableCell>
                        <TableCell className="text-right font-mono">{formatCurrency(jr.total_value)}</TableCell>
                      </TableRow>
                    ))}
                    {(!job_roles || job_roles.length === 0) && (
                      <TableRow>
                        <TableCell colSpan={6} className="text-center py-8 text-muted-foreground">
                          No job roles found
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="billing">
            <Card className="border border-border">
              <CardHeader>
                <CardTitle className="font-heading">Invoices</CardTitle>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="uppercase text-xs font-bold tracking-wider">Invoice #</TableHead>
                      <TableHead className="uppercase text-xs font-bold tracking-wider">Date</TableHead>
                      <TableHead className="uppercase text-xs font-bold tracking-wider text-right">Amount</TableHead>
                      <TableHead className="uppercase text-xs font-bold tracking-wider">Status</TableHead>
                      <TableHead className="uppercase text-xs font-bold tracking-wider">Payment Date</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {invoices?.map((inv) => (
                      <TableRow key={inv.invoice_id} className="hover:bg-muted/50">
                        <TableCell className="font-mono text-sm">{inv.invoice_number}</TableCell>
                        <TableCell className="font-mono text-sm">{inv.invoice_date}</TableCell>
                        <TableCell className="text-right font-mono">{formatCurrency(inv.amount)}</TableCell>
                        <TableCell>
                          <Badge 
                            variant={inv.status === "paid" ? "default" : "secondary"}
                            className={inv.status === "paid" ? "bg-emerald-100 text-emerald-700 border-emerald-200" : "bg-amber-100 text-amber-700 border-amber-200"}
                          >
                            {inv.status}
                          </Badge>
                        </TableCell>
                        <TableCell className="font-mono text-sm">{inv.payment_date || "-"}</TableCell>
                      </TableRow>
                    ))}
                    {(!invoices || invoices.length === 0) && (
                      <TableRow>
                        <TableCell colSpan={5} className="text-center py-8 text-muted-foreground">
                          No invoices found
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}

// Add Batch Form
const AddBatchForm = ({ sdcId, jobRoles, onSuccess }) => {
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    job_role_id: "",
    work_order_number: "",
    start_date: "",
    mobilized: 0
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await axios.post(`${API}/batches`, {
        sdc_id: sdcId,
        ...formData,
        mobilized: parseInt(formData.mobilized)
      });
      toast.success("Batch created successfully");
      onSuccess();
    } catch (error) {
      console.error("Error creating batch:", error);
      toast.error("Failed to create batch");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <DialogHeader>
        <DialogTitle>Add New Batch</DialogTitle>
      </DialogHeader>
      <form onSubmit={handleSubmit} className="space-y-4 mt-4">
        <div>
          <Label>Job Role</Label>
          <Select 
            value={formData.job_role_id} 
            onValueChange={(v) => setFormData({ ...formData, job_role_id: v })}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select job role" />
            </SelectTrigger>
            <SelectContent>
              {jobRoles?.map((jr) => (
                <SelectItem key={jr.job_role_id} value={jr.job_role_id}>
                  {jr.job_role_name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div>
          <Label>Work Order Number</Label>
          <Input 
            value={formData.work_order_number}
            onChange={(e) => setFormData({ ...formData, work_order_number: e.target.value })}
            placeholder="WO/2025/001"
            required
          />
        </div>
        <div>
          <Label>Start Date</Label>
          <Input 
            type="date"
            value={formData.start_date}
            onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
            required
          />
        </div>
        <div>
          <Label>Mobilized Candidates</Label>
          <Input 
            type="number"
            value={formData.mobilized}
            onChange={(e) => setFormData({ ...formData, mobilized: e.target.value })}
            min="0"
          />
        </div>
        <Button type="submit" className="w-full" disabled={loading}>
          {loading ? "Creating..." : "Create Batch"}
        </Button>
      </form>
    </>
  );
};

// Add Invoice Form
const AddInvoiceForm = ({ sdcId, onSuccess }) => {
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    invoice_number: "",
    invoice_date: "",
    amount: ""
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await axios.post(`${API}/invoices`, {
        sdc_id: sdcId,
        ...formData,
        amount: parseFloat(formData.amount)
      });
      toast.success("Invoice created successfully");
      onSuccess();
    } catch (error) {
      console.error("Error creating invoice:", error);
      toast.error("Failed to create invoice");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <DialogHeader>
        <DialogTitle>Add New Invoice</DialogTitle>
      </DialogHeader>
      <form onSubmit={handleSubmit} className="space-y-4 mt-4">
        <div>
          <Label>Invoice Number</Label>
          <Input 
            value={formData.invoice_number}
            onChange={(e) => setFormData({ ...formData, invoice_number: e.target.value })}
            placeholder="INV/2025/001"
            required
          />
        </div>
        <div>
          <Label>Invoice Date</Label>
          <Input 
            type="date"
            value={formData.invoice_date}
            onChange={(e) => setFormData({ ...formData, invoice_date: e.target.value })}
            required
          />
        </div>
        <div>
          <Label>Amount (₹)</Label>
          <Input 
            type="number"
            value={formData.amount}
            onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
            placeholder="100000"
            min="0"
            required
          />
        </div>
        <Button type="submit" className="w-full" disabled={loading}>
          {loading ? "Creating..." : "Create Invoice"}
        </Button>
      </form>
    </>
  );
};

// Helper Components
const LegendItem = ({ color, label, value }) => (
  <div className="flex items-center gap-2">
    <div className={`w-3 h-3 rounded-full ${color}`} />
    <span className="text-sm text-muted-foreground">{label}:</span>
    <span className="font-mono text-sm">{value}</span>
  </div>
);

const getStagePercent = (progress, stage) => {
  if (!progress) return 0;
  const total = (progress.mobilized || 0) + (progress.in_training || 0) + (progress.assessed || 0) + (progress.placed || 0);
  if (total === 0) return 0;
  return ((progress[stage] || 0) / total) * 100;
};

const SDCDetailSkeleton = () => (
  <div className="min-h-screen bg-background">
    <header className="border-b border-border">
      <div className="max-w-7xl mx-auto px-6 py-4">
        <Skeleton className="w-64 h-8" />
      </div>
    </header>
    <main className="max-w-7xl mx-auto px-6 py-8">
      <div className="grid grid-cols-4 gap-4 mb-8">
        {[1, 2, 3, 4].map(i => (
          <Skeleton key={i} className="h-24 rounded-md" />
        ))}
      </div>
      <Skeleton className="h-32 rounded-md mb-8" />
      <Skeleton className="h-64 rounded-md" />
    </main>
  </div>
);
