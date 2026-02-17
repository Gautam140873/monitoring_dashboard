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
  ClipboardList,
  Briefcase,
  GraduationCap,
  CheckCircle2
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
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
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

// Stage icons mapping
const STAGE_ICONS = {
  mobilization: Users,
  dress_distribution: ClipboardList,
  study_material: FileText,
  classroom_training: GraduationCap,
  assessment: CheckCircle2,
  ojt: Briefcase,
  placement: Building2
};

// Stage colors
const STAGE_COLORS = {
  mobilization: "bg-amber-500",
  dress_distribution: "bg-orange-500",
  study_material: "bg-yellow-500",
  classroom_training: "bg-blue-500",
  assessment: "bg-purple-500",
  ojt: "bg-indigo-500",
  placement: "bg-emerald-500"
};

export default function SDCDetail({ user }) {
  const { sdcId } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [sdcData, setSdcData] = useState(null);
  const [activeTab, setActiveTab] = useState("roadmap");
  const [showWorkOrderDialog, setShowWorkOrderDialog] = useState(false);
  const [showInvoiceDialog, setShowInvoiceDialog] = useState(false);
  const [showStartDateDialog, setShowStartDateDialog] = useState(false);
  const [selectedWorkOrder, setSelectedWorkOrder] = useState(null);

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

  const { stage_progress, financial, work_orders, invoices } = sdcData;

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
            {user?.role === "ho" && (
              <Dialog open={showWorkOrderDialog} onOpenChange={setShowWorkOrderDialog}>
                <DialogTrigger asChild>
                  <Button data-testid="add-work-order-btn">
                    <Plus className="w-4 h-4 mr-1" />
                    New Work Order
                  </Button>
                </DialogTrigger>
                <DialogContent className="max-w-2xl">
                  <AddWorkOrderForm 
                    location={sdcData.location}
                    onSuccess={() => {
                      setShowWorkOrderDialog(false);
                      fetchSDCData();
                    }} 
                  />
                </DialogContent>
              </Dialog>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Financial Summary */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
          <Card className="border border-border animate-fade-in stagger-1">
            <CardContent className="p-4">
              <div className="text-xs text-muted-foreground mb-1">Total Contract</div>
              <div className="font-mono font-bold text-lg">{formatCurrency(financial?.total_contract || 0)}</div>
            </CardContent>
          </Card>
          <Card className="border border-border animate-fade-in stagger-2">
            <CardContent className="p-4">
              <div className="text-xs text-muted-foreground mb-1">Total Billed</div>
              <div className="font-mono font-bold text-lg">{formatCurrency(financial?.total_billed || 0)}</div>
            </CardContent>
          </Card>
          <Card className="border border-border animate-fade-in stagger-3">
            <CardContent className="p-4">
              <div className="text-xs text-muted-foreground mb-1">Collected</div>
              <div className="font-mono font-bold text-lg text-emerald-600">{formatCurrency(financial?.total_paid || 0)}</div>
            </CardContent>
          </Card>
          <Card className="border border-border animate-fade-in stagger-4">
            <CardContent className="p-4">
              <div className="text-xs text-muted-foreground mb-1">Outstanding</div>
              <div className={`font-mono font-bold text-lg ${(financial?.total_outstanding || 0) > 0 ? 'text-red-600' : 'text-emerald-600'}`}>
                {formatCurrency(financial?.total_outstanding || 0)}
              </div>
            </CardContent>
          </Card>
          <Card className="border border-border animate-fade-in stagger-5">
            <CardContent className="p-4">
              <div className="text-xs text-muted-foreground mb-1">Variance</div>
              <div className={`font-mono font-bold text-lg ${(financial?.variance || 0) > 0 ? 'text-amber-600' : ''}`}>
                {formatCurrency(financial?.variance || 0)}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Training Roadmap Progress */}
        <Card className="mb-8 border border-border animate-fade-in" data-testid="roadmap-card">
          <CardHeader className="pb-2">
            <CardTitle className="font-heading font-bold">Training Roadmap</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
              {stage_progress && Object.entries(stage_progress).sort((a, b) => a[1].order - b[1].order).map(([stageId, stage]) => {
                const Icon = STAGE_ICONS[stageId] || Clock;
                const color = STAGE_COLORS[stageId] || "bg-slate-500";
                const percent = stage.target > 0 ? Math.round((stage.completed / stage.target) * 100) : 0;
                
                return (
                  <div key={stageId} className="text-center p-3 border border-border rounded-md hover:bg-muted/30 transition-colors">
                    <div className={`w-8 h-8 mx-auto mb-2 rounded-full ${color} flex items-center justify-center`}>
                      <Icon className="w-4 h-4 text-white" />
                    </div>
                    <div className="font-mono font-bold">{stage.completed}/{stage.target}</div>
                    <div className="text-xs text-muted-foreground truncate">{stage.name}</div>
                    <div className="mt-2 h-1 bg-muted rounded-full overflow-hidden">
                      <div className={`h-full ${color}`} style={{ width: `${percent}%` }} />
                    </div>
                    <div className="text-xs text-muted-foreground mt-1">{percent}%</div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="animate-fade-in">
          <TabsList className="mb-6">
            <TabsTrigger value="roadmap" data-testid="tab-roadmap">Work Orders</TabsTrigger>
            <TabsTrigger value="billing" data-testid="tab-billing">Billing</TabsTrigger>
          </TabsList>

          <TabsContent value="roadmap">
            <Card className="border border-border">
              <CardHeader>
                <CardTitle className="font-heading">Work Orders</CardTitle>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="uppercase text-xs font-bold tracking-wider">Work Order</TableHead>
                      <TableHead className="uppercase text-xs font-bold tracking-wider">Job Role</TableHead>
                      <TableHead className="uppercase text-xs font-bold tracking-wider">Students</TableHead>
                      <TableHead className="uppercase text-xs font-bold tracking-wider">Start</TableHead>
                      <TableHead className="uppercase text-xs font-bold tracking-wider">End (Calc)</TableHead>
                      <TableHead className="uppercase text-xs font-bold tracking-wider text-right">Value</TableHead>
                      <TableHead className="uppercase text-xs font-bold tracking-wider">Status</TableHead>
                      <TableHead className="uppercase text-xs font-bold tracking-wider">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {work_orders?.map((wo) => (
                      <TableRow key={wo.work_order_id} className="hover:bg-muted/50">
                        <TableCell className="font-mono text-sm">{wo.work_order_number}</TableCell>
                        <TableCell>
                          <div className="font-medium">{wo.job_role_name}</div>
                          <div className="text-xs text-muted-foreground">{wo.job_role_code}</div>
                        </TableCell>
                        <TableCell className="font-mono">{wo.num_students}</TableCell>
                        <TableCell className="font-mono text-sm">
                          {wo.start_date || (
                            <span className="text-muted-foreground">Not set</span>
                          )}
                        </TableCell>
                        <TableCell className="font-mono text-sm">
                          {wo.manual_end_date || wo.calculated_end_date || "-"}
                        </TableCell>
                        <TableCell className="text-right font-mono">{formatCurrency(wo.total_contract_value)}</TableCell>
                        <TableCell>
                          <Badge variant={wo.status === "active" ? "default" : "secondary"}>
                            {wo.status}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          {!wo.start_date && (
                            <Button 
                              variant="outline" 
                              size="sm"
                              onClick={() => {
                                setSelectedWorkOrder(wo);
                                setShowStartDateDialog(true);
                              }}
                            >
                              Set Start Date
                            </Button>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                    {(!work_orders || work_orders.length === 0) && (
                      <TableRow>
                        <TableCell colSpan={8} className="text-center py-8 text-muted-foreground">
                          No work orders found. {user?.role === "ho" && "Click 'New Work Order' to create one."}
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
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle className="font-heading">Invoices</CardTitle>
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
                      workOrders={work_orders}
                      onSuccess={() => {
                        setShowInvoiceDialog(false);
                        fetchSDCData();
                      }} 
                    />
                  </DialogContent>
                </Dialog>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="uppercase text-xs font-bold tracking-wider">Invoice #</TableHead>
                      <TableHead className="uppercase text-xs font-bold tracking-wider">Date</TableHead>
                      <TableHead className="uppercase text-xs font-bold tracking-wider text-right">Order Value</TableHead>
                      <TableHead className="uppercase text-xs font-bold tracking-wider text-right">Billed</TableHead>
                      <TableHead className="uppercase text-xs font-bold tracking-wider text-right">Variance</TableHead>
                      <TableHead className="uppercase text-xs font-bold tracking-wider text-right">Received</TableHead>
                      <TableHead className="uppercase text-xs font-bold tracking-wider text-right">Outstanding</TableHead>
                      <TableHead className="uppercase text-xs font-bold tracking-wider">Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {invoices?.map((inv) => (
                      <TableRow key={inv.invoice_id} className="hover:bg-muted/50">
                        <TableCell className="font-mono text-sm">{inv.invoice_number}</TableCell>
                        <TableCell className="font-mono text-sm">{inv.invoice_date}</TableCell>
                        <TableCell className="text-right font-mono">{formatCurrency(inv.order_value)}</TableCell>
                        <TableCell className="text-right font-mono">{formatCurrency(inv.billing_value)}</TableCell>
                        <TableCell className={`text-right font-mono ${inv.variance > 0 ? 'text-amber-600' : ''}`}>
                          {inv.variance_percent}%
                        </TableCell>
                        <TableCell className="text-right font-mono text-emerald-600">{formatCurrency(inv.payment_received)}</TableCell>
                        <TableCell className={`text-right font-mono ${inv.outstanding > 0 ? 'text-red-600' : 'text-emerald-600'}`}>
                          {formatCurrency(inv.outstanding)}
                        </TableCell>
                        <TableCell>
                          <Badge 
                            variant={inv.status === "paid" ? "default" : "secondary"}
                            className={
                              inv.status === "paid" ? "bg-emerald-100 text-emerald-700 border-emerald-200" : 
                              inv.status === "partial" ? "bg-amber-100 text-amber-700 border-amber-200" : ""
                            }
                          >
                            {inv.status}
                          </Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                    {(!invoices || invoices.length === 0) && (
                      <TableRow>
                        <TableCell colSpan={8} className="text-center py-8 text-muted-foreground">
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

        {/* Start Date Dialog */}
        <Dialog open={showStartDateDialog} onOpenChange={setShowStartDateDialog}>
          <DialogContent>
            <SetStartDateForm 
              workOrder={selectedWorkOrder}
              onSuccess={() => {
                setShowStartDateDialog(false);
                setSelectedWorkOrder(null);
                fetchSDCData();
              }} 
            />
          </DialogContent>
        </Dialog>
      </main>
    </div>
  );
}

// Add Work Order Form
const AddWorkOrderForm = ({ location, onSuccess }) => {
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    work_order_number: "",
    location: location,
    job_role_code: "",
    job_role_name: "",
    awarding_body: "",
    scheme_name: "",
    total_training_hours: 200,
    sessions_per_day: 8,
    num_students: 30,
    cost_per_student: 10000,
    manager_email: ""
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await axios.post(`${API}/work-orders`, {
        ...formData,
        total_training_hours: parseInt(formData.total_training_hours),
        sessions_per_day: parseInt(formData.sessions_per_day),
        num_students: parseInt(formData.num_students),
        cost_per_student: parseFloat(formData.cost_per_student)
      });
      toast.success("Work Order created successfully");
      onSuccess();
    } catch (error) {
      console.error("Error creating work order:", error);
      toast.error("Failed to create work order");
    } finally {
      setLoading(false);
    }
  };

  const totalValue = formData.num_students * formData.cost_per_student;

  return (
    <>
      <DialogHeader>
        <DialogTitle>Create New Work Order</DialogTitle>
      </DialogHeader>
      <form onSubmit={handleSubmit} className="space-y-4 mt-4 max-h-[70vh] overflow-y-auto pr-2">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label>Work Order Number *</Label>
            <Input 
              value={formData.work_order_number}
              onChange={(e) => setFormData({ ...formData, work_order_number: e.target.value })}
              placeholder="WO/2025/004"
              required
            />
          </div>
          <div>
            <Label>Location</Label>
            <Input 
              value={formData.location}
              onChange={(e) => setFormData({ ...formData, location: e.target.value })}
              placeholder="City name"
              required
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label>Job Role Code *</Label>
            <Input 
              value={formData.job_role_code}
              onChange={(e) => setFormData({ ...formData, job_role_code: e.target.value })}
              placeholder="CSC/Q0801"
              required
            />
          </div>
          <div>
            <Label>Job Role Name *</Label>
            <Input 
              value={formData.job_role_name}
              onChange={(e) => setFormData({ ...formData, job_role_name: e.target.value })}
              placeholder="Field Technician Computing"
              required
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label>Awarding Body *</Label>
            <Input 
              value={formData.awarding_body}
              onChange={(e) => setFormData({ ...formData, awarding_body: e.target.value })}
              placeholder="NSDC PMKVY"
              required
            />
          </div>
          <div>
            <Label>Scheme Name *</Label>
            <Input 
              value={formData.scheme_name}
              onChange={(e) => setFormData({ ...formData, scheme_name: e.target.value })}
              placeholder="PMKVY 4.0"
              required
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label>Training Hours *</Label>
            <Input 
              type="number"
              value={formData.total_training_hours}
              onChange={(e) => setFormData({ ...formData, total_training_hours: e.target.value })}
              min="1"
              required
            />
          </div>
          <div>
            <Label>Sessions/Day (hrs)</Label>
            <Input 
              type="number"
              value={formData.sessions_per_day}
              onChange={(e) => setFormData({ ...formData, sessions_per_day: e.target.value })}
              min="1"
              max="12"
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label>Number of Students *</Label>
            <Input 
              type="number"
              value={formData.num_students}
              onChange={(e) => setFormData({ ...formData, num_students: e.target.value })}
              min="1"
              required
            />
          </div>
          <div>
            <Label>Cost per Student (₹) *</Label>
            <Input 
              type="number"
              value={formData.cost_per_student}
              onChange={(e) => setFormData({ ...formData, cost_per_student: e.target.value })}
              min="0"
              required
            />
          </div>
        </div>

        <div>
          <Label>Local Manager Email</Label>
          <Input 
            type="email"
            value={formData.manager_email}
            onChange={(e) => setFormData({ ...formData, manager_email: e.target.value })}
            placeholder="manager@example.com"
          />
        </div>

        <div className="p-3 bg-muted rounded-md">
          <div className="text-sm text-muted-foreground">Total Contract Value</div>
          <div className="font-mono font-bold text-xl">
            {new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(totalValue)}
          </div>
        </div>

        <Button type="submit" className="w-full" disabled={loading}>
          {loading ? "Creating..." : "Create Work Order"}
        </Button>
      </form>
    </>
  );
};

// Set Start Date Form
const SetStartDateForm = ({ workOrder, onSuccess }) => {
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    start_date: "",
    manual_end_date: ""
  });

  if (!workOrder) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await axios.put(`${API}/work-orders/${workOrder.work_order_id}/start-date`, {
        start_date: formData.start_date,
        manual_end_date: formData.manual_end_date || null
      });
      toast.success("Start date set successfully");
      onSuccess();
    } catch (error) {
      console.error("Error setting start date:", error);
      toast.error("Failed to set start date");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <DialogHeader>
        <DialogTitle>Set Start Date</DialogTitle>
      </DialogHeader>
      <div className="text-sm text-muted-foreground mb-4">
        {workOrder.work_order_number} - {workOrder.job_role_name}
      </div>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <Label>Start Date *</Label>
          <Input 
            type="date"
            value={formData.start_date}
            onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
            required
          />
          <p className="text-xs text-muted-foreground mt-1">
            End date will be auto-calculated based on {workOrder.total_training_hours} hours at {workOrder.sessions_per_day} hrs/day, skipping Sundays and holidays.
          </p>
        </div>
        <div>
          <Label>Manual End Date (Optional Override)</Label>
          <Input 
            type="date"
            value={formData.manual_end_date}
            onChange={(e) => setFormData({ ...formData, manual_end_date: e.target.value })}
          />
          <p className="text-xs text-muted-foreground mt-1">
            Only set this if there's a local holiday or special circumstances.
          </p>
        </div>
        <Button type="submit" className="w-full" disabled={loading}>
          {loading ? "Saving..." : "Set Start Date"}
        </Button>
      </form>
    </>
  );
};

// Add Invoice Form
const AddInvoiceForm = ({ sdcId, workOrders, onSuccess }) => {
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    work_order_id: "",
    invoice_number: "",
    invoice_date: "",
    order_value: "",
    billing_value: "",
    notes: ""
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await axios.post(`${API}/invoices`, {
        sdc_id: sdcId,
        ...formData,
        order_value: parseFloat(formData.order_value),
        billing_value: parseFloat(formData.billing_value)
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

  const variance = formData.order_value && formData.billing_value 
    ? parseFloat(formData.order_value) - parseFloat(formData.billing_value)
    : 0;
  const variancePercent = formData.order_value && variance
    ? ((variance / parseFloat(formData.order_value)) * 100).toFixed(1)
    : 0;

  return (
    <>
      <DialogHeader>
        <DialogTitle>Add New Invoice</DialogTitle>
      </DialogHeader>
      <form onSubmit={handleSubmit} className="space-y-4 mt-4">
        <div>
          <Label>Work Order (Optional)</Label>
          <Select 
            value={formData.work_order_id} 
            onValueChange={(v) => setFormData({ ...formData, work_order_id: v })}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select work order" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="">None</SelectItem>
              {workOrders?.map((wo) => (
                <SelectItem key={wo.work_order_id} value={wo.work_order_id}>
                  {wo.work_order_number} - {wo.job_role_name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label>Invoice Number *</Label>
            <Input 
              value={formData.invoice_number}
              onChange={(e) => setFormData({ ...formData, invoice_number: e.target.value })}
              placeholder="INV/2025/001"
              required
            />
          </div>
          <div>
            <Label>Invoice Date *</Label>
            <Input 
              type="date"
              value={formData.invoice_date}
              onChange={(e) => setFormData({ ...formData, invoice_date: e.target.value })}
              required
            />
          </div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label>Order Value (₹) *</Label>
            <Input 
              type="number"
              value={formData.order_value}
              onChange={(e) => setFormData({ ...formData, order_value: e.target.value })}
              placeholder="100000"
              min="0"
              required
            />
          </div>
          <div>
            <Label>Billing Value (₹) *</Label>
            <Input 
              type="number"
              value={formData.billing_value}
              onChange={(e) => setFormData({ ...formData, billing_value: e.target.value })}
              placeholder="100000"
              min="0"
              required
            />
          </div>
        </div>
        
        {variance !== 0 && (
          <div className={`p-3 rounded-md ${Math.abs(variancePercent) > 10 ? 'bg-amber-50 border border-amber-200' : 'bg-muted'}`}>
            <div className="text-sm text-muted-foreground">Variance</div>
            <div className={`font-mono font-bold ${variancePercent > 10 ? 'text-amber-600' : ''}`}>
              {variancePercent}% ({new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(variance)})
            </div>
            {Math.abs(variancePercent) > 10 && (
              <div className="text-xs text-amber-600 mt-1">
                <AlertTriangle className="w-3 h-3 inline mr-1" />
                Variance exceeds 10% - will generate alert
              </div>
            )}
          </div>
        )}

        <div>
          <Label>Notes</Label>
          <Textarea 
            value={formData.notes}
            onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
            placeholder="Optional notes about billing variance..."
          />
        </div>
        <Button type="submit" className="w-full" disabled={loading}>
          {loading ? "Creating..." : "Create Invoice"}
        </Button>
      </form>
    </>
  );
};

const SDCDetailSkeleton = () => (
  <div className="min-h-screen bg-background">
    <header className="border-b border-border">
      <div className="max-w-7xl mx-auto px-6 py-4">
        <Skeleton className="w-64 h-8" />
      </div>
    </header>
    <main className="max-w-7xl mx-auto px-6 py-8">
      <div className="grid grid-cols-5 gap-4 mb-8">
        {[1, 2, 3, 4, 5].map(i => (
          <Skeleton key={i} className="h-20 rounded-md" />
        ))}
      </div>
      <Skeleton className="h-40 rounded-md mb-8" />
      <Skeleton className="h-64 rounded-md" />
    </main>
  </div>
);
