import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { API } from "@/App";
import { toast } from "sonner";
import { 
  Building2, 
  ArrowLeft,
  Plus,
  Edit2,
  Trash2,
  FileText,
  Users,
  DollarSign,
  Clock,
  ChevronRight,
  Search,
  Filter,
  MoreVertical,
  CheckCircle2,
  AlertTriangle,
  Database,
  Layers
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogDescription,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

// Category rates
const CATEGORY_RATES = {
  "A": 46,
  "B": 42
};

export default function MasterData({ user }) {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("job-roles");
  const [jobRoles, setJobRoles] = useState([]);
  const [masterWorkOrders, setMasterWorkOrders] = useState([]);
  const [summary, setSummary] = useState(null);
  const [showJobRoleDialog, setShowJobRoleDialog] = useState(false);
  const [showWorkOrderDialog, setShowWorkOrderDialog] = useState(false);
  const [showSDCDialog, setShowSDCDialog] = useState(false);
  const [selectedMasterWO, setSelectedMasterWO] = useState(null);
  const [editingJobRole, setEditingJobRole] = useState(null);

  // Redirect if not HO
  useEffect(() => {
    if (user?.role !== "ho") {
      toast.error("Access denied. Head Office role required.");
      navigate("/dashboard");
    }
  }, [user, navigate]);

  const fetchData = async () => {
    try {
      const [jobRolesRes, workOrdersRes, summaryRes] = await Promise.all([
        axios.get(`${API}/master/job-roles`),
        axios.get(`${API}/master/work-orders`),
        axios.get(`${API}/master/summary`)
      ]);
      setJobRoles(jobRolesRes.data);
      setMasterWorkOrders(workOrdersRes.data);
      setSummary(summaryRes.data);
    } catch (error) {
      console.error("Error fetching master data:", error);
      toast.error("Failed to load master data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0
    }).format(value);
  };

  if (user?.role !== "ho") {
    return null;
  }

  if (loading) {
    return <MasterDataSkeleton />;
  }

  return (
    <div className="min-h-screen bg-background" data-testid="master-data-page">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-background/95 backdrop-blur-sm border-b border-border">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" onClick={() => navigate("/dashboard")} data-testid="back-btn">
              <ArrowLeft className="w-5 h-5" />
            </Button>
            <div>
              <h1 className="font-heading font-bold text-xl flex items-center gap-2">
                <Database className="w-5 h-5" />
                Master Data
              </h1>
              <p className="text-sm text-muted-foreground">Manage Job Roles, Work Orders & SDC Configuration</p>
            </div>
          </div>
          <Badge variant="secondary" className="bg-amber-100 text-amber-700 border-amber-200">
            HO Admin Only
          </Badge>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <Card className="border border-border">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-md bg-blue-100 flex items-center justify-center">
                  <FileText className="w-5 h-5 text-blue-600" />
                </div>
                <div>
                  <div className="font-mono font-bold text-xl">{summary?.job_roles?.total || 0}</div>
                  <div className="text-xs text-muted-foreground">Job Roles</div>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card className="border border-border">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-md bg-purple-100 flex items-center justify-center">
                  <Layers className="w-5 h-5 text-purple-600" />
                </div>
                <div>
                  <div className="font-mono font-bold text-xl">{summary?.work_orders?.total || 0}</div>
                  <div className="text-xs text-muted-foreground">Work Orders</div>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card className="border border-border">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-md bg-emerald-100 flex items-center justify-center">
                  <Users className="w-5 h-5 text-emerald-600" />
                </div>
                <div>
                  <div className="font-mono font-bold text-xl">{summary?.financials?.total_students || 0}</div>
                  <div className="text-xs text-muted-foreground">Total Students</div>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card className="border border-border">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-md bg-amber-100 flex items-center justify-center">
                  <DollarSign className="w-5 h-5 text-amber-600" />
                </div>
                <div>
                  <div className="font-mono font-bold text-xl">{formatCurrency(summary?.financials?.total_contract_value || 0)}</div>
                  <div className="text-xs text-muted-foreground">Total Contract Value</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="mb-6">
            <TabsTrigger value="job-roles" data-testid="tab-job-roles">
              <FileText className="w-4 h-4 mr-2" />
              Job Roles
            </TabsTrigger>
            <TabsTrigger value="work-orders" data-testid="tab-work-orders">
              <Layers className="w-4 h-4 mr-2" />
              Work Orders
            </TabsTrigger>
          </TabsList>

          {/* Job Roles Tab */}
          <TabsContent value="job-roles">
            <Card className="border border-border">
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle className="font-heading">Job Role Master</CardTitle>
                  <CardDescription>Define job roles with categories and rates</CardDescription>
                </div>
                <Dialog open={showJobRoleDialog} onOpenChange={setShowJobRoleDialog}>
                  <DialogTrigger asChild>
                    <Button data-testid="add-job-role-btn" onClick={() => setEditingJobRole(null)}>
                      <Plus className="w-4 h-4 mr-1" />
                      Add Job Role
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="max-w-xl">
                    <JobRoleForm 
                      editData={editingJobRole}
                      onSuccess={() => {
                        setShowJobRoleDialog(false);
                        setEditingJobRole(null);
                        fetchData();
                      }} 
                    />
                  </DialogContent>
                </Dialog>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="uppercase text-xs font-bold">Job Role Code</TableHead>
                      <TableHead className="uppercase text-xs font-bold">Job Role Name</TableHead>
                      <TableHead className="uppercase text-xs font-bold">Category</TableHead>
                      <TableHead className="uppercase text-xs font-bold text-right">Rate/Hr</TableHead>
                      <TableHead className="uppercase text-xs font-bold text-right">Hours</TableHead>
                      <TableHead className="uppercase text-xs font-bold">Scheme</TableHead>
                      <TableHead className="uppercase text-xs font-bold">Status</TableHead>
                      <TableHead className="uppercase text-xs font-bold">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {jobRoles.map((jr) => (
                      <TableRow key={jr.job_role_id} className="hover:bg-muted/50">
                        <TableCell className="font-mono text-sm">{jr.job_role_code}</TableCell>
                        <TableCell className="font-medium">{jr.job_role_name}</TableCell>
                        <TableCell>
                          <Badge variant={jr.category === "A" ? "default" : jr.category === "B" ? "secondary" : "outline"}>
                            Cat {jr.category}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right font-mono">₹{jr.rate_per_hour}</TableCell>
                        <TableCell className="text-right font-mono">{jr.total_training_hours}</TableCell>
                        <TableCell className="text-sm text-muted-foreground">{jr.scheme_name}</TableCell>
                        <TableCell>
                          <Badge variant={jr.is_active ? "default" : "secondary"} className={jr.is_active ? "bg-emerald-100 text-emerald-700" : ""}>
                            {jr.is_active ? "Active" : "Inactive"}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="icon">
                                <MoreVertical className="w-4 h-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuItem onClick={() => {
                                setEditingJobRole(jr);
                                setShowJobRoleDialog(true);
                              }}>
                                <Edit2 className="w-4 h-4 mr-2" />
                                Edit
                              </DropdownMenuItem>
                              <DropdownMenuItem 
                                className="text-red-600"
                                onClick={async () => {
                                  try {
                                    await axios.delete(`${API}/master/job-roles/${jr.job_role_id}`);
                                    toast.success("Job Role deactivated");
                                    fetchData();
                                  } catch (error) {
                                    toast.error("Failed to deactivate job role");
                                  }
                                }}
                              >
                                <Trash2 className="w-4 h-4 mr-2" />
                                Deactivate
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </TableCell>
                      </TableRow>
                    ))}
                    {jobRoles.length === 0 && (
                      <TableRow>
                        <TableCell colSpan={8} className="text-center py-8 text-muted-foreground">
                          <FileText className="w-8 h-8 mx-auto mb-2 opacity-50" />
                          No job roles defined. Click "Add Job Role" to create one.
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Work Orders Tab */}
          <TabsContent value="work-orders">
            <Card className="border border-border">
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle className="font-heading">Master Work Orders</CardTitle>
                  <CardDescription>Create work orders and allocate SDCs</CardDescription>
                </div>
                <Dialog open={showWorkOrderDialog} onOpenChange={setShowWorkOrderDialog}>
                  <DialogTrigger asChild>
                    <Button data-testid="add-work-order-btn" disabled={jobRoles.filter(jr => jr.is_active).length === 0}>
                      <Plus className="w-4 h-4 mr-1" />
                      New Work Order
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="max-w-xl">
                    <MasterWorkOrderForm 
                      jobRoles={jobRoles.filter(jr => jr.is_active)}
                      onSuccess={() => {
                        setShowWorkOrderDialog(false);
                        fetchData();
                      }} 
                    />
                  </DialogContent>
                </Dialog>
              </CardHeader>
              <CardContent>
                {masterWorkOrders.length === 0 ? (
                  <div className="text-center py-12 text-muted-foreground">
                    <Layers className="w-12 h-12 mx-auto mb-4 opacity-50" />
                    <p>No work orders created yet.</p>
                    <p className="text-sm mt-1">First add Job Roles, then create Work Orders.</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {masterWorkOrders.map((mwo) => (
                      <Card key={mwo.master_wo_id} className="border border-border hover:bg-muted/30 transition-colors">
                        <CardContent className="p-4">
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <div className="flex items-center gap-3 mb-2">
                                <h3 className="font-heading font-bold text-lg">{mwo.work_order_number}</h3>
                                <Badge variant={mwo.category === "A" ? "default" : "secondary"}>
                                  Cat {mwo.category} - ₹{mwo.rate_per_hour}/hr
                                </Badge>
                                <Badge variant="outline">{mwo.status}</Badge>
                              </div>
                              <p className="text-sm text-muted-foreground mb-3">
                                {mwo.job_role_name} ({mwo.job_role_code}) • {mwo.total_training_hours} hours • {mwo.scheme_name}
                              </p>
                              
                              {/* SDCs List */}
                              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-3">
                                {mwo.sdcs?.map((sdc) => (
                                  <div key={sdc.sdc_id} className="p-3 bg-muted/50 rounded-md">
                                    <div className="flex items-center justify-between">
                                      <span className="font-medium text-sm">{sdc.name}</span>
                                      <Badge variant="outline" className="text-xs">{sdc.target_students || 0} students</Badge>
                                    </div>
                                  </div>
                                ))}
                                {(!mwo.sdcs || mwo.sdcs.length === 0) && (
                                  <div className="p-3 bg-amber-50 border border-amber-200 rounded-md col-span-full">
                                    <p className="text-sm text-amber-700">No SDCs allocated yet. Click "Add SDC" to allocate.</p>
                                  </div>
                                )}
                              </div>

                              {/* Totals */}
                              <div className="flex items-center gap-6 text-sm">
                                <div>
                                  <span className="text-muted-foreground">SDCs:</span>
                                  <span className="font-mono font-medium ml-1">{mwo.sdc_count || 0}</span>
                                </div>
                                <div>
                                  <span className="text-muted-foreground">Students:</span>
                                  <span className="font-mono font-medium ml-1">{mwo.total_target_students || 0}</span>
                                </div>
                                <div>
                                  <span className="text-muted-foreground">Contract Value:</span>
                                  <span className="font-mono font-bold text-emerald-600 ml-1">{formatCurrency(mwo.total_contract_value || 0)}</span>
                                </div>
                              </div>
                            </div>

                            <div className="flex items-center gap-2">
                              <Dialog open={showSDCDialog && selectedMasterWO?.master_wo_id === mwo.master_wo_id} onOpenChange={(open) => {
                                setShowSDCDialog(open);
                                if (!open) setSelectedMasterWO(null);
                              }}>
                                <DialogTrigger asChild>
                                  <Button variant="outline" size="sm" onClick={() => setSelectedMasterWO(mwo)}>
                                    <Plus className="w-4 h-4 mr-1" />
                                    Add SDC
                                  </Button>
                                </DialogTrigger>
                                <DialogContent>
                                  <SDCFromMasterForm 
                                    masterWO={mwo}
                                    onSuccess={() => {
                                      setShowSDCDialog(false);
                                      setSelectedMasterWO(null);
                                      fetchData();
                                    }} 
                                  />
                                </DialogContent>
                              </Dialog>
                              <Button variant="ghost" size="icon" onClick={() => navigate(`/sdc/${mwo.sdcs?.[0]?.sdc_id || ''}`)}>
                                <ChevronRight className="w-4 h-4" />
                              </Button>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}

// Job Role Form Component
const JobRoleForm = ({ editData, onSuccess }) => {
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    job_role_code: editData?.job_role_code || "",
    job_role_name: editData?.job_role_name || "",
    category: editData?.category || "A",
    rate_per_hour: editData?.rate_per_hour || CATEGORY_RATES["A"],
    total_training_hours: editData?.total_training_hours || 400,
    awarding_body: editData?.awarding_body || "NSDC",
    scheme_name: editData?.scheme_name || "PMKVY 4.0",
    default_daily_hours: editData?.default_daily_hours || 8,
    default_batch_size: editData?.default_batch_size || 30
  });

  const handleCategoryChange = (value) => {
    setFormData({
      ...formData,
      category: value,
      rate_per_hour: CATEGORY_RATES[value] || formData.rate_per_hour
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      if (editData) {
        await axios.put(`${API}/master/job-roles/${editData.job_role_id}`, formData);
        toast.success("Job Role updated successfully");
      } else {
        await axios.post(`${API}/master/job-roles`, formData);
        toast.success("Job Role created successfully");
      }
      onSuccess();
    } catch (error) {
      console.error("Error saving job role:", error);
      toast.error(error.response?.data?.detail || "Failed to save job role");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <DialogHeader>
        <DialogTitle>{editData ? "Edit Job Role" : "Add New Job Role"}</DialogTitle>
        <DialogDescription>
          Define job role configuration with category-based rates
        </DialogDescription>
      </DialogHeader>
      <form onSubmit={handleSubmit} className="space-y-4 mt-4" data-testid="job-role-form">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label>Job Role Code *</Label>
            <Input 
              value={formData.job_role_code}
              onChange={(e) => setFormData({ ...formData, job_role_code: e.target.value })}
              placeholder="CSC/Q0801"
              required
              disabled={!!editData}
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
            <Label>Category *</Label>
            <Select value={formData.category} onValueChange={handleCategoryChange}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="A">Category A (₹46/hr)</SelectItem>
                <SelectItem value="B">Category B (₹42/hr)</SelectItem>
                <SelectItem value="CUSTOM">Custom Rate</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label>Rate Per Hour (₹) *</Label>
            <Input 
              type="number"
              value={formData.rate_per_hour}
              onChange={(e) => setFormData({ ...formData, rate_per_hour: parseFloat(e.target.value) })}
              min="0"
              step="0.01"
              required
              disabled={formData.category !== "CUSTOM"}
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label>Total Training Hours *</Label>
            <Input 
              type="number"
              value={formData.total_training_hours}
              onChange={(e) => setFormData({ ...formData, total_training_hours: parseInt(e.target.value) })}
              min="1"
              required
            />
          </div>
          <div>
            <Label>Default Daily Hours</Label>
            <Select value={String(formData.default_daily_hours)} onValueChange={(v) => setFormData({ ...formData, default_daily_hours: parseInt(v) })}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="4">4 hours/day</SelectItem>
                <SelectItem value="6">6 hours/day</SelectItem>
                <SelectItem value="8">8 hours/day</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label>Awarding Body *</Label>
            <Input 
              value={formData.awarding_body}
              onChange={(e) => setFormData({ ...formData, awarding_body: e.target.value })}
              placeholder="NSDC"
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

        <div>
          <Label>Default Batch Size</Label>
          <Input 
            type="number"
            value={formData.default_batch_size}
            onChange={(e) => setFormData({ ...formData, default_batch_size: parseInt(e.target.value) })}
            min="1"
            max="100"
          />
        </div>

        <div className="p-3 bg-muted rounded-md">
          <div className="text-sm text-muted-foreground">Cost Per Student (calculated)</div>
          <div className="font-mono font-bold text-lg">
            {new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(formData.total_training_hours * formData.rate_per_hour)}
          </div>
          <p className="text-xs text-muted-foreground mt-1">
            {formData.total_training_hours} hrs × ₹{formData.rate_per_hour}/hr
          </p>
        </div>

        <Button type="submit" className="w-full" disabled={loading}>
          {loading ? "Saving..." : (editData ? "Update Job Role" : "Create Job Role")}
        </Button>
      </form>
    </>
  );
};

// Master Work Order Form Component
const MasterWorkOrderForm = ({ jobRoles, onSuccess }) => {
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    work_order_number: "",
    job_role_id: ""
  });
  const [selectedJobRole, setSelectedJobRole] = useState(null);

  const handleJobRoleChange = (value) => {
    const jr = jobRoles.find(j => j.job_role_id === value);
    setSelectedJobRole(jr);
    setFormData({ ...formData, job_role_id: value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await axios.post(`${API}/master/work-orders`, formData);
      toast.success("Master Work Order created successfully");
      onSuccess();
    } catch (error) {
      console.error("Error creating work order:", error);
      toast.error(error.response?.data?.detail || "Failed to create work order");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <DialogHeader>
        <DialogTitle>Create Master Work Order</DialogTitle>
        <DialogDescription>
          Create a work order from an existing job role
        </DialogDescription>
      </DialogHeader>
      <form onSubmit={handleSubmit} className="space-y-4 mt-4" data-testid="master-wo-form">
        <div>
          <Label>Work Order Number *</Label>
          <Input 
            value={formData.work_order_number}
            onChange={(e) => setFormData({ ...formData, work_order_number: e.target.value })}
            placeholder="WO/2025/001"
            required
          />
        </div>

        <div>
          <Label>Select Job Role *</Label>
          <Select value={formData.job_role_id} onValueChange={handleJobRoleChange} required>
            <SelectTrigger>
              <SelectValue placeholder="Select a job role..." />
            </SelectTrigger>
            <SelectContent>
              {jobRoles.map((jr) => (
                <SelectItem key={jr.job_role_id} value={jr.job_role_id}>
                  {jr.job_role_code} - {jr.job_role_name} (Cat {jr.category})
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {selectedJobRole && (
          <div className="p-4 bg-muted rounded-md space-y-2">
            <h4 className="font-medium text-sm">Selected Job Role Details:</h4>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div>
                <span className="text-muted-foreground">Category:</span>
                <span className="ml-2 font-medium">Cat {selectedJobRole.category}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Rate:</span>
                <span className="ml-2 font-mono">₹{selectedJobRole.rate_per_hour}/hr</span>
              </div>
              <div>
                <span className="text-muted-foreground">Duration:</span>
                <span className="ml-2 font-mono">{selectedJobRole.total_training_hours} hrs</span>
              </div>
              <div>
                <span className="text-muted-foreground">Scheme:</span>
                <span className="ml-2">{selectedJobRole.scheme_name}</span>
              </div>
            </div>
            <div className="pt-2 border-t border-border mt-2">
              <span className="text-muted-foreground text-sm">Cost Per Student:</span>
              <span className="ml-2 font-mono font-bold">
                {new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(selectedJobRole.total_training_hours * selectedJobRole.rate_per_hour)}
              </span>
            </div>
          </div>
        )}

        <Button type="submit" className="w-full" disabled={loading || !formData.job_role_id}>
          {loading ? "Creating..." : "Create Work Order"}
        </Button>
      </form>
    </>
  );
};

// SDC From Master Form Component
const SDCFromMasterForm = ({ masterWO, onSuccess }) => {
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    location: "",
    target_students: 30,
    daily_hours: 8,
    manager_email: ""
  });

  const contractValue = formData.target_students * masterWO.total_training_hours * masterWO.rate_per_hour;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await axios.post(`${API}/master/work-orders/${masterWO.master_wo_id}/sdcs`, {
        master_wo_id: masterWO.master_wo_id,
        ...formData
      });
      toast.success("SDC created and linked to Work Order successfully!");
      onSuccess();
    } catch (error) {
      console.error("Error creating SDC:", error);
      toast.error(error.response?.data?.detail || "Failed to create SDC");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <DialogHeader>
        <DialogTitle>Add SDC to {masterWO.work_order_number}</DialogTitle>
        <DialogDescription>
          Allocate a new Skill Development Center to this work order
        </DialogDescription>
      </DialogHeader>
      <form onSubmit={handleSubmit} className="space-y-4 mt-4" data-testid="sdc-from-master-form">
        <div className="p-3 bg-blue-50 border border-blue-200 rounded-md text-sm">
          <div className="font-medium text-blue-800">{masterWO.job_role_name}</div>
          <div className="text-blue-600">
            Cat {masterWO.category} • ₹{masterWO.rate_per_hour}/hr • {masterWO.total_training_hours} hrs
          </div>
        </div>

        <div>
          <Label>SDC Location *</Label>
          <Input 
            value={formData.location}
            onChange={(e) => setFormData({ ...formData, location: e.target.value })}
            placeholder="e.g., Delhi, Mumbai, Jaipur"
            required
          />
          <p className="text-xs text-muted-foreground mt-1">Enter city name - SDC will be auto-created if not exists</p>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label>Target Students *</Label>
            <Input 
              type="number"
              value={formData.target_students}
              onChange={(e) => setFormData({ ...formData, target_students: parseInt(e.target.value) })}
              min="1"
              required
            />
          </div>
          <div>
            <Label>Daily Session Hours</Label>
            <Select value={String(formData.daily_hours)} onValueChange={(v) => setFormData({ ...formData, daily_hours: parseInt(v) })}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="4">4 hours/day</SelectItem>
                <SelectItem value="6">6 hours/day</SelectItem>
                <SelectItem value="8">8 hours/day</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        <div>
          <Label>Manager Email (Optional)</Label>
          <Input 
            type="email"
            value={formData.manager_email}
            onChange={(e) => setFormData({ ...formData, manager_email: e.target.value })}
            placeholder="manager@example.com"
          />
        </div>

        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-md">
          <div className="text-sm text-emerald-600">SDC Contract Value</div>
          <div className="font-mono font-bold text-2xl text-emerald-700">
            {new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(contractValue)}
          </div>
          <p className="text-xs text-emerald-600 mt-1">
            {formData.target_students} students × {masterWO.total_training_hours} hrs × ₹{masterWO.rate_per_hour}/hr
          </p>
        </div>

        <Button type="submit" className="w-full" disabled={loading}>
          {loading ? "Creating..." : "Create SDC & Allocate"}
        </Button>
      </form>
    </>
  );
};

// Skeleton
const MasterDataSkeleton = () => (
  <div className="min-h-screen bg-background">
    <header className="border-b border-border">
      <div className="max-w-7xl mx-auto px-6 py-4">
        <Skeleton className="w-64 h-8" />
      </div>
    </header>
    <main className="max-w-7xl mx-auto px-6 py-8">
      <div className="grid grid-cols-4 gap-4 mb-8">
        {[1, 2, 3, 4].map(i => (
          <Skeleton key={i} className="h-20 rounded-md" />
        ))}
      </div>
      <Skeleton className="h-12 w-64 mb-6" />
      <Skeleton className="h-96 rounded-md" />
    </main>
  </div>
);
