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
  ChevronDown,
  MoreVertical,
  MapPin,
  Layers,
  Database,
  X,
  GraduationCap,
  UserCog,
  Home,
  Phone,
  Mail,
  Award,
  CheckCircle,
  AlertCircle,
  BarChart3
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Checkbox } from "@/components/ui/checkbox";
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
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

// Category rates
const CATEGORY_RATES = {
  "A": 46,
  "B": 42
};

export default function MasterData({ user }) {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("work-orders");
  const [jobRoles, setJobRoles] = useState([]);
  const [masterWorkOrders, setMasterWorkOrders] = useState([]);
  const [summary, setSummary] = useState(null);
  const [showJobRoleDialog, setShowJobRoleDialog] = useState(false);
  const [showWorkOrderDialog, setShowWorkOrderDialog] = useState(false);
  const [showSDCDialog, setShowSDCDialog] = useState(false);
  const [selectedMasterWO, setSelectedMasterWO] = useState(null);
  const [editingJobRole, setEditingJobRole] = useState(null);
  const [expandedWO, setExpandedWO] = useState(null);
  
  // Resources state
  const [trainers, setTrainers] = useState([]);
  const [managers, setManagers] = useState([]);
  const [infrastructure, setInfrastructure] = useState([]);
  const [resourcesSummary, setResourcesSummary] = useState(null);
  const [showTrainerDialog, setShowTrainerDialog] = useState(false);
  const [showManagerDialog, setShowManagerDialog] = useState(false);
  const [showInfraDialog, setShowInfraDialog] = useState(false);
  const [editingTrainer, setEditingTrainer] = useState(null);
  const [editingManager, setEditingManager] = useState(null);
  const [editingInfra, setEditingInfra] = useState(null);

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

  const fetchResources = async () => {
    try {
      const [trainersRes, managersRes, infraRes, summaryRes] = await Promise.all([
        axios.get(`${API}/resources/trainers`),
        axios.get(`${API}/resources/managers`),
        axios.get(`${API}/resources/infrastructure`),
        axios.get(`${API}/resources/summary`)
      ]);
      setTrainers(trainersRes.data);
      setManagers(managersRes.data);
      setInfrastructure(infraRes.data);
      setResourcesSummary(summaryRes.data);
    } catch (error) {
      console.error("Error fetching resources:", error);
    }
  };

  useEffect(() => {
    fetchData();
    fetchResources();
  }, []);

  // Fetch resources when switching to resources tab
  useEffect(() => {
    if (activeTab === "resources") {
      fetchResources();
    }
  }, [activeTab]);

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
              <p className="text-sm text-muted-foreground">Manage Work Orders, Job Roles & SDC Configuration</p>
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
                <div className="w-10 h-10 rounded-md bg-purple-100 flex items-center justify-center">
                  <Layers className="w-5 h-5 text-purple-600" />
                </div>
                <div>
                  <div className="font-mono font-bold text-xl">{masterWorkOrders.length}</div>
                  <div className="text-xs text-muted-foreground">Work Orders</div>
                </div>
              </div>
            </CardContent>
          </Card>
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
                <div className="w-10 h-10 rounded-md bg-emerald-100 flex items-center justify-center">
                  <Users className="w-5 h-5 text-emerald-600" />
                </div>
                <div>
                  <div className="font-mono font-bold text-xl">{summary?.financials?.total_students || 0}</div>
                  <div className="text-xs text-muted-foreground">Total Target</div>
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
                  <div className="text-xs text-muted-foreground">Contract Value</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="mb-6">
            <TabsTrigger value="work-orders" data-testid="tab-work-orders">
              <Layers className="w-4 h-4 mr-2" />
              Work Orders
            </TabsTrigger>
            <TabsTrigger value="job-roles" data-testid="tab-job-roles">
              <FileText className="w-4 h-4 mr-2" />
              Job Roles
            </TabsTrigger>
            <TabsTrigger value="resources" data-testid="tab-resources">
              <Users className="w-4 h-4 mr-2" />
              Resources
            </TabsTrigger>
          </TabsList>

          {/* Work Orders Tab */}
          <TabsContent value="work-orders">
            <Card className="border border-border">
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle className="font-heading">Master Work Orders</CardTitle>
                  <CardDescription>Create work orders with multiple job roles and SDC districts</CardDescription>
                </div>
                <Dialog open={showWorkOrderDialog} onOpenChange={setShowWorkOrderDialog}>
                  <DialogTrigger asChild>
                    <Button data-testid="add-work-order-btn" disabled={jobRoles.filter(jr => jr.is_active).length === 0}>
                      <Plus className="w-4 h-4 mr-1" />
                      New Work Order
                    </Button>
                  </DialogTrigger>
                  <DialogContent 
                    className="max-w-3xl max-h-[90vh] overflow-y-auto"
                    onInteractOutside={(e) => e.preventDefault()}
                    onEscapeKeyDown={(e) => e.preventDefault()}
                  >
                    <MasterWorkOrderForm 
                      jobRoles={jobRoles.filter(jr => jr.is_active)}
                      onSuccess={() => {
                        setShowWorkOrderDialog(false);
                        fetchData();
                      }} 
                      onCancel={() => setShowWorkOrderDialog(false)}
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
                      <Collapsible 
                        key={mwo.master_wo_id} 
                        open={expandedWO === mwo.master_wo_id}
                        onOpenChange={(open) => setExpandedWO(open ? mwo.master_wo_id : null)}
                      >
                        <Card className="border border-border">
                          <CardContent className="p-4">
                            <CollapsibleTrigger className="w-full">
                              <div className="flex items-start justify-between">
                                <div className="flex-1 text-left">
                                  <div className="flex items-center gap-3 mb-2">
                                    <h3 className="font-heading font-bold text-lg">{mwo.work_order_number}</h3>
                                    <Badge variant="outline">{mwo.status}</Badge>
                                    {expandedWO === mwo.master_wo_id ? 
                                      <ChevronDown className="w-4 h-4" /> : 
                                      <ChevronRight className="w-4 h-4" />
                                    }
                                  </div>
                                  <p className="text-sm text-muted-foreground mb-2">
                                    {mwo.awarding_body} • {mwo.scheme_name}
                                  </p>
                                  
                                  {/* Job Roles Summary */}
                                  <div className="flex flex-wrap gap-2 mb-3">
                                    {mwo.job_roles?.map((jr, idx) => (
                                      <Badge key={idx} variant="secondary" className="text-xs">
                                        {jr.job_role_code}: {jr.target} students (Cat {jr.category})
                                      </Badge>
                                    ))}
                                  </div>
                                  
                                  {/* SDC Districts Summary */}
                                  <div className="flex flex-wrap gap-2 mb-3">
                                    {mwo.sdc_districts?.map((dist, idx) => (
                                      <Badge key={idx} variant="outline" className="text-xs">
                                        <MapPin className="w-3 h-3 mr-1" />
                                        {dist.district_name} ({dist.sdc_count} SDC{dist.sdc_count > 1 ? 's' : ''})
                                      </Badge>
                                    ))}
                                  </div>

                                  {/* Totals */}
                                  <div className="flex items-center gap-6 text-sm">
                                    <div>
                                      <span className="text-muted-foreground">Total Target:</span>
                                      <span className="font-mono font-medium ml-1">{mwo.total_training_target}</span>
                                    </div>
                                    <div>
                                      <span className="text-muted-foreground">SDCs Created:</span>
                                      <span className="font-mono font-medium ml-1">{mwo.sdcs_created_count || 0}/{mwo.num_sdcs}</span>
                                    </div>
                                    <div>
                                      <span className="text-muted-foreground">Contract Value:</span>
                                      <span className="font-mono font-bold text-emerald-600 ml-1">{formatCurrency(mwo.total_contract_value || 0)}</span>
                                    </div>
                                  </div>
                                </div>
                              </div>
                            </CollapsibleTrigger>

                            <CollapsibleContent>
                              <div className="mt-4 pt-4 border-t border-border">
                                {/* SDCs Created */}
                                <div className="mb-4">
                                  <h4 className="font-medium text-sm mb-2 flex items-center gap-2">
                                    <Building2 className="w-4 h-4" />
                                    SDCs Created
                                  </h4>
                                  {mwo.sdcs_created?.length > 0 ? (
                                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                                      {mwo.sdcs_created.map((sdc) => (
                                        <div 
                                          key={sdc.sdc_id} 
                                          className="p-3 bg-muted/50 rounded-md cursor-pointer hover:bg-muted transition-colors"
                                          onClick={() => navigate(`/sdc/${sdc.sdc_id}`)}
                                        >
                                          <div className="flex items-center justify-between">
                                            <span className="font-medium text-sm">{sdc.name}</span>
                                            <ChevronRight className="w-4 h-4 text-muted-foreground" />
                                          </div>
                                          <div className="text-xs text-muted-foreground mt-1">
                                            {sdc.target_students || 0} students
                                          </div>
                                        </div>
                                      ))}
                                    </div>
                                  ) : (
                                    <p className="text-sm text-muted-foreground">No SDCs created yet</p>
                                  )}
                                </div>

                                {/* Create SDC Button */}
                                <div className="flex items-center gap-2">
                                  <Dialog open={showSDCDialog && selectedMasterWO?.master_wo_id === mwo.master_wo_id} onOpenChange={(open) => {
                                    setShowSDCDialog(open);
                                    if (!open) setSelectedMasterWO(null);
                                  }}>
                                    <DialogTrigger asChild>
                                      <Button variant="outline" size="sm" onClick={() => setSelectedMasterWO(mwo)} disabled={mwo.status === "completed"}>
                                        <Plus className="w-4 h-4 mr-1" />
                                        Create SDC
                                      </Button>
                                    </DialogTrigger>
                                    <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto" onInteractOutside={(e) => e.preventDefault()}>
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

                                  {/* Complete Work Order Button */}
                                  {mwo.status === "active" && (
                                    <Button 
                                      variant="outline" 
                                      size="sm" 
                                      className="text-emerald-600 border-emerald-300 hover:bg-emerald-50"
                                      onClick={async () => {
                                        if (window.confirm(`Are you sure you want to mark "${mwo.work_order_number}" as completed? This will release all assigned resources (trainers, managers, centers).`)) {
                                          try {
                                            const res = await axios.post(`${API}/master/work-orders/${mwo.master_wo_id}/complete`);
                                            toast.success(`Work Order completed! Released: ${res.data.released_resources.trainers} trainers, ${res.data.released_resources.managers} managers, ${res.data.released_resources.infrastructure} centers`);
                                            fetchData();
                                            fetchResources();
                                          } catch (error) {
                                            toast.error(error.response?.data?.detail || "Failed to complete work order");
                                          }
                                        }
                                      }}
                                    >
                                      <CheckCircle className="w-4 h-4 mr-1" />
                                      Complete & Release Resources
                                    </Button>
                                  )}
                                  
                                  {mwo.status === "completed" && (
                                    <Badge variant="default" className="bg-emerald-100 text-emerald-700">
                                      <CheckCircle className="w-3 h-3 mr-1" />
                                      Completed
                                    </Badge>
                                  )}
                                </div>
                              </div>
                            </CollapsibleContent>
                          </CardContent>
                        </Card>
                      </Collapsible>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

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

          {/* Resources Tab */}
          <TabsContent value="resources">
            {/* Resources Summary */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              <Card className="border border-border">
                <CardContent className="p-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-md bg-blue-100 flex items-center justify-center">
                      <GraduationCap className="w-5 h-5 text-blue-600" />
                    </div>
                    <div>
                      <div className="font-mono font-bold text-xl">{resourcesSummary?.trainers?.total || 0}</div>
                      <div className="text-xs text-muted-foreground">
                        Trainers ({resourcesSummary?.trainers?.available || 0} available)
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
              <Card className="border border-border">
                <CardContent className="p-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-md bg-purple-100 flex items-center justify-center">
                      <UserCog className="w-5 h-5 text-purple-600" />
                    </div>
                    <div>
                      <div className="font-mono font-bold text-xl">{resourcesSummary?.managers?.total || 0}</div>
                      <div className="text-xs text-muted-foreground">
                        Center Managers ({resourcesSummary?.managers?.available || 0} available)
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
              <Card className="border border-border">
                <CardContent className="p-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-md bg-emerald-100 flex items-center justify-center">
                      <Home className="w-5 h-5 text-emerald-600" />
                    </div>
                    <div>
                      <div className="font-mono font-bold text-xl">{resourcesSummary?.infrastructure?.total || 0}</div>
                      <div className="text-xs text-muted-foreground">
                        SDC/Centers ({resourcesSummary?.infrastructure?.available || 0} available)
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Trainers Section */}
            <Card className="border border-border mb-6">
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle className="font-heading flex items-center gap-2">
                    <GraduationCap className="w-5 h-5" />
                    Trainers
                  </CardTitle>
                  <CardDescription>Manage trainer details and availability</CardDescription>
                </div>
                <Dialog open={showTrainerDialog} onOpenChange={setShowTrainerDialog}>
                  <DialogTrigger asChild>
                    <Button data-testid="add-trainer-btn" onClick={() => setEditingTrainer(null)}>
                      <Plus className="w-4 h-4 mr-1" />
                      Add Trainer
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="max-w-xl" onInteractOutside={(e) => e.preventDefault()}>
                    <TrainerForm 
                      editData={editingTrainer}
                      jobRoles={jobRoles}
                      onSuccess={() => {
                        setShowTrainerDialog(false);
                        setEditingTrainer(null);
                        fetchResources();
                      }}
                      onCancel={() => setShowTrainerDialog(false)}
                    />
                  </DialogContent>
                </Dialog>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="uppercase text-xs font-bold">Name</TableHead>
                      <TableHead className="uppercase text-xs font-bold">Contact</TableHead>
                      <TableHead className="uppercase text-xs font-bold">Domain</TableHead>
                      <TableHead className="uppercase text-xs font-bold">Specialization</TableHead>
                      <TableHead className="uppercase text-xs font-bold">Experience</TableHead>
                      <TableHead className="uppercase text-xs font-bold">Status</TableHead>
                      <TableHead className="uppercase text-xs font-bold">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {trainers.map((trainer) => (
                      <TableRow key={trainer.trainer_id} className="hover:bg-muted/50">
                        <TableCell>
                          <div className="font-medium">{trainer.name}</div>
                          <div className="text-xs text-muted-foreground">{trainer.qualification}</div>
                        </TableCell>
                        <TableCell>
                          <div className="text-sm">{trainer.phone}</div>
                          <div className="text-xs text-muted-foreground">{trainer.email}</div>
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline" className="text-xs">{trainer.domain || 'General'}</Badge>
                          {trainer.nsqf_level && <div className="text-xs text-muted-foreground mt-1">NSQF {trainer.nsqf_level}</div>}
                        </TableCell>
                        <TableCell className="font-mono text-sm">{trainer.specialization}</TableCell>
                        <TableCell>{trainer.experience_years} years</TableCell>
                        <TableCell>
                          <Badge variant={trainer.status === "available" ? "default" : "secondary"} 
                            className={trainer.status === "available" ? "bg-emerald-100 text-emerald-700" : ""}>
                            {trainer.status}
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
                                setEditingTrainer(trainer);
                                setShowTrainerDialog(true);
                              }}>
                                <Edit2 className="w-4 h-4 mr-2" />
                                Edit
                              </DropdownMenuItem>
                              {trainer.status === "assigned" && (
                                <DropdownMenuItem onClick={async () => {
                                  try {
                                    await axios.post(`${API}/resources/trainers/${trainer.trainer_id}/release`);
                                    toast.success("Trainer released");
                                    fetchResources();
                                  } catch (error) {
                                    toast.error("Failed to release trainer");
                                  }
                                }}>
                                  <CheckCircle className="w-4 h-4 mr-2" />
                                  Release
                                </DropdownMenuItem>
                              )}
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </TableCell>
                      </TableRow>
                    ))}
                    {trainers.length === 0 && (
                      <TableRow>
                        <TableCell colSpan={7} className="text-center py-8 text-muted-foreground">
                          <GraduationCap className="w-8 h-8 mx-auto mb-2 opacity-50" />
                          No trainers added. Click "Add Trainer" to create one.
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>

            {/* Center Managers Section */}
            <Card className="border border-border mb-6">
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle className="font-heading flex items-center gap-2">
                    <UserCog className="w-5 h-5" />
                    Center Managers
                  </CardTitle>
                  <CardDescription>Manage center manager details and assignments</CardDescription>
                </div>
                <Dialog open={showManagerDialog} onOpenChange={setShowManagerDialog}>
                  <DialogTrigger asChild>
                    <Button data-testid="add-manager-btn" onClick={() => setEditingManager(null)}>
                      <Plus className="w-4 h-4 mr-1" />
                      Add Manager
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="max-w-xl" onInteractOutside={(e) => e.preventDefault()}>
                    <ManagerForm 
                      editData={editingManager}
                      onSuccess={() => {
                        setShowManagerDialog(false);
                        setEditingManager(null);
                        fetchResources();
                      }}
                      onCancel={() => setShowManagerDialog(false)}
                    />
                  </DialogContent>
                </Dialog>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="uppercase text-xs font-bold">Name</TableHead>
                      <TableHead className="uppercase text-xs font-bold">Contact</TableHead>
                      <TableHead className="uppercase text-xs font-bold">Experience</TableHead>
                      <TableHead className="uppercase text-xs font-bold">Location</TableHead>
                      <TableHead className="uppercase text-xs font-bold">Status</TableHead>
                      <TableHead className="uppercase text-xs font-bold">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {managers.map((manager) => (
                      <TableRow key={manager.manager_id} className="hover:bg-muted/50">
                        <TableCell>
                          <div className="font-medium">{manager.name}</div>
                          <div className="text-xs text-muted-foreground">{manager.qualification}</div>
                        </TableCell>
                        <TableCell>
                          <div className="text-sm">{manager.phone}</div>
                          <div className="text-xs text-muted-foreground">{manager.email}</div>
                        </TableCell>
                        <TableCell>{manager.experience_years} years</TableCell>
                        <TableCell className="text-sm">{manager.city}, {manager.state}</TableCell>
                        <TableCell>
                          <Badge variant={manager.status === "available" ? "default" : "secondary"} 
                            className={manager.status === "available" ? "bg-emerald-100 text-emerald-700" : ""}>
                            {manager.status}
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
                                setEditingManager(manager);
                                setShowManagerDialog(true);
                              }}>
                                <Edit2 className="w-4 h-4 mr-2" />
                                Edit
                              </DropdownMenuItem>
                              {manager.status === "assigned" && (
                                <DropdownMenuItem onClick={async () => {
                                  try {
                                    await axios.post(`${API}/resources/managers/${manager.manager_id}/release`);
                                    toast.success("Manager released");
                                    fetchResources();
                                  } catch (error) {
                                    toast.error("Failed to release manager");
                                  }
                                }}>
                                  <CheckCircle className="w-4 h-4 mr-2" />
                                  Release
                                </DropdownMenuItem>
                              )}
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </TableCell>
                      </TableRow>
                    ))}
                    {managers.length === 0 && (
                      <TableRow>
                        <TableCell colSpan={6} className="text-center py-8 text-muted-foreground">
                          <UserCog className="w-8 h-8 mx-auto mb-2 opacity-50" />
                          No managers added. Click "Add Manager" to create one.
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>

            {/* SDC/Center Infrastructure Section */}
            <Card className="border border-border">
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle className="font-heading flex items-center gap-2">
                    <Home className="w-5 h-5" />
                    SDC/Center Infrastructure
                  </CardTitle>
                  <CardDescription>Manage training center details and facilities</CardDescription>
                </div>
                <Dialog open={showInfraDialog} onOpenChange={setShowInfraDialog}>
                  <DialogTrigger asChild>
                    <Button data-testid="add-infra-btn" onClick={() => setEditingInfra(null)}>
                      <Plus className="w-4 h-4 mr-1" />
                      Add Center
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto" onInteractOutside={(e) => e.preventDefault()}>
                    <InfrastructureForm 
                      editData={editingInfra}
                      onSuccess={() => {
                        setShowInfraDialog(false);
                        setEditingInfra(null);
                        fetchResources();
                      }}
                      onCancel={() => setShowInfraDialog(false)}
                    />
                  </DialogContent>
                </Dialog>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="uppercase text-xs font-bold">Center</TableHead>
                      <TableHead className="uppercase text-xs font-bold">Location</TableHead>
                      <TableHead className="uppercase text-xs font-bold">Capacity</TableHead>
                      <TableHead className="uppercase text-xs font-bold">Facilities</TableHead>
                      <TableHead className="uppercase text-xs font-bold">Status</TableHead>
                      <TableHead className="uppercase text-xs font-bold">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {infrastructure.map((infra) => (
                      <TableRow key={infra.infra_id} className="hover:bg-muted/50">
                        <TableCell>
                          <div className="font-medium">{infra.center_name}</div>
                          <div className="text-xs text-muted-foreground font-mono">{infra.center_code}</div>
                        </TableCell>
                        <TableCell>
                          <div className="text-sm">{infra.city}, {infra.district}</div>
                          <div className="text-xs text-muted-foreground">{infra.state} - {infra.pincode}</div>
                        </TableCell>
                        <TableCell>
                          <div className="font-mono">{infra.total_capacity} students</div>
                          <div className="text-xs text-muted-foreground">
                            {infra.num_classrooms} classroom{infra.num_classrooms > 1 ? 's' : ''}
                            {infra.num_computer_labs > 0 && `, ${infra.num_computer_labs} lab${infra.num_computer_labs > 1 ? 's' : ''}`}
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="flex flex-wrap gap-1">
                            {infra.has_projector && <Badge variant="outline" className="text-xs">Projector</Badge>}
                            {infra.has_ac && <Badge variant="outline" className="text-xs">AC</Badge>}
                            {infra.has_library && <Badge variant="outline" className="text-xs">Library</Badge>}
                            {infra.has_biometric && <Badge variant="outline" className="text-xs bg-blue-50">Biometric</Badge>}
                            {infra.has_internet && <Badge variant="outline" className="text-xs bg-green-50">Internet</Badge>}
                            {infra.has_fire_safety && <Badge variant="outline" className="text-xs bg-red-50">Fire Safety</Badge>}
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant={infra.status === "available" ? "default" : infra.status === "in_use" ? "secondary" : "destructive"} 
                            className={infra.status === "available" ? "bg-emerald-100 text-emerald-700" : ""}>
                            {infra.status}
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
                                setEditingInfra(infra);
                                setShowInfraDialog(true);
                              }}>
                                <Edit2 className="w-4 h-4 mr-2" />
                                Edit
                              </DropdownMenuItem>
                              {infra.status === "in_use" && (
                                <DropdownMenuItem onClick={async () => {
                                  try {
                                    await axios.post(`${API}/resources/infrastructure/${infra.infra_id}/release`);
                                    toast.success("Center released");
                                    fetchResources();
                                  } catch (error) {
                                    toast.error("Failed to release center");
                                  }
                                }}>
                                  <CheckCircle className="w-4 h-4 mr-2" />
                                  Release
                                </DropdownMenuItem>
                              )}
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </TableCell>
                      </TableRow>
                    ))}
                    {infrastructure.length === 0 && (
                      <TableRow>
                        <TableCell colSpan={6} className="text-center py-8 text-muted-foreground">
                          <Home className="w-8 h-8 mx-auto mb-2 opacity-50" />
                          No centers added. Click "Add Center" to create one.
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

// Master Work Order Form Component - Step-by-step with target validation
const MasterWorkOrderForm = ({ jobRoles, onSuccess, onCancel }) => {
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState(1); // Step 1: Basic info, Step 2: Job roles, Step 3: Districts
  const [selectKey, setSelectKey] = useState(0); // Key to force Select remount after selection
  const [formData, setFormData] = useState({
    work_order_number: "",
    awarding_body: "NSDC",
    scheme_name: "PMKVY 4.0",
    total_training_target: 150,
    num_job_roles: 2
  });
  const [selectedJobRoles, setSelectedJobRoles] = useState([]);
  const [sdcDistricts, setSdcDistricts] = useState([]);
  const [newDistrict, setNewDistrict] = useState({ name: "", count: 1 });

  // Available job roles (not yet selected)
  const availableJobRoles = jobRoles.filter(jr => !selectedJobRoles.find(s => s.job_role_id === jr.job_role_id));

  // Calculate totals
  const allocatedTarget = selectedJobRoles.reduce((sum, jr) => sum + (jr.target || 0), 0);
  const remainingTarget = formData.total_training_target - allocatedTarget;
  const totalValue = selectedJobRoles.reduce((sum, jr) => 
    sum + ((jr.target || 0) * jr.total_training_hours * jr.rate_per_hour), 0
  );

  // Check if target is fully allocated
  const isTargetFullyAllocated = allocatedTarget === formData.total_training_target;
  const isOverAllocated = allocatedTarget > formData.total_training_target;

  const addJobRole = (jobRoleId) => {
    if (!jobRoleId) return;
    
    if (selectedJobRoles.length >= formData.num_job_roles) {
      toast.error(`Maximum ${formData.num_job_roles} job roles allowed`);
      return;
    }
    const jr = jobRoles.find(j => j.job_role_id === jobRoleId);
    if (jr && !selectedJobRoles.find(s => s.job_role_id === jobRoleId)) {
      // Set default target as remaining or 0
      const defaultTarget = Math.min(remainingTarget, 30);
      setSelectedJobRoles([...selectedJobRoles, { ...jr, target: defaultTarget > 0 ? defaultTarget : 0 }]);
      // Force Select to remount and clear selection
      setSelectKey(prev => prev + 1);
    }
  };

  const updateJobRoleTarget = (jobRoleId, targetValue) => {
    const newTarget = parseInt(targetValue) || 0;
    
    // Calculate what the new total would be
    const otherTargets = selectedJobRoles
      .filter(jr => jr.job_role_id !== jobRoleId)
      .reduce((sum, jr) => sum + (jr.target || 0), 0);
    
    const newTotal = otherTargets + newTarget;
    
    // Don't allow exceeding total target
    if (newTotal > formData.total_training_target) {
      toast.error(`Cannot exceed total target of ${formData.total_training_target}`);
      return;
    }
    
    setSelectedJobRoles(selectedJobRoles.map(jr => 
      jr.job_role_id === jobRoleId ? { ...jr, target: newTarget } : jr
    ));
  };

  const removeJobRole = (jobRoleId) => {
    setSelectedJobRoles(selectedJobRoles.filter(jr => jr.job_role_id !== jobRoleId));
  };

  const addDistrict = () => {
    if (newDistrict.name.trim()) {
      setSdcDistricts([...sdcDistricts, { 
        district_name: newDistrict.name.trim(), 
        sdc_count: newDistrict.count 
      }]);
      setNewDistrict({ name: "", count: 1 });
    }
  };

  const removeDistrict = (index) => {
    setSdcDistricts(sdcDistricts.filter((_, i) => i !== index));
  };

  const canProceedToStep2 = formData.work_order_number && formData.total_training_target > 0 && formData.num_job_roles > 0;
  const canProceedToStep3 = selectedJobRoles.length === formData.num_job_roles && isTargetFullyAllocated;

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!isTargetFullyAllocated) {
      toast.error(`Job role targets must equal total target (${formData.total_training_target})`);
      return;
    }
    
    if (sdcDistricts.length === 0) {
      toast.error("Please add at least one SDC district");
      return;
    }

    setLoading(true);
    try {
      await axios.post(`${API}/master/work-orders`, {
        work_order_number: formData.work_order_number,
        awarding_body: formData.awarding_body,
        scheme_name: formData.scheme_name,
        total_training_target: formData.total_training_target,
        job_roles: selectedJobRoles.map(jr => ({
          job_role_id: jr.job_role_id,
          target: jr.target
        })),
        sdc_districts: sdcDistricts
      });
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
      <DialogHeader className="flex flex-row items-start justify-between">
        <div>
          <DialogTitle>Create Master Work Order</DialogTitle>
          <DialogDescription>
            Step {step} of 3: {step === 1 ? "Basic Information" : step === 2 ? "Job Roles & Targets" : "SDC Districts"}
          </DialogDescription>
        </div>
        <Button variant="ghost" size="icon" onClick={onCancel} className="h-8 w-8" type="button">
          <X className="w-4 h-4" />
        </Button>
      </DialogHeader>

      {/* Progress Indicator */}
      <div className="flex items-center gap-2 my-4">
        {[1, 2, 3].map((s) => (
          <div key={s} className="flex items-center">
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
              s < step ? "bg-emerald-500 text-white" : 
              s === step ? "bg-primary text-primary-foreground" : 
              "bg-muted text-muted-foreground"
            }`}>
              {s < step ? "✓" : s}
            </div>
            {s < 3 && <div className={`w-12 h-1 ${s < step ? "bg-emerald-500" : "bg-muted"}`} />}
          </div>
        ))}
      </div>

      <form onSubmit={handleSubmit} className="space-y-4" data-testid="master-wo-form">
        {/* Step 1: Basic Info */}
        {step === 1 && (
          <div className="space-y-4">
            <div>
              <Label>Work Order Number *</Label>
              <Input 
                value={formData.work_order_number}
                onChange={(e) => setFormData({ ...formData, work_order_number: e.target.value })}
                placeholder="WO/2025/001"
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Total Training Target *</Label>
                <Input 
                  type="number"
                  value={formData.total_training_target}
                  onChange={(e) => setFormData({ ...formData, total_training_target: parseInt(e.target.value) || 0 })}
                  min="1"
                  required
                />
                <p className="text-xs text-muted-foreground mt-1">Total students to be trained</p>
              </div>
              <div>
                <Label>Number of Job Roles *</Label>
                <Select 
                  value={String(formData.num_job_roles)} 
                  onValueChange={(v) => {
                    setFormData({ ...formData, num_job_roles: parseInt(v) });
                    setSelectedJobRoles([]); // Reset selected job roles
                  }}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {[1, 2, 3, 4, 5].map(n => (
                      <SelectItem key={n} value={String(n)}>{n} Job Role{n > 1 ? 's' : ''}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Awarding Body</Label>
                <Input 
                  value={formData.awarding_body}
                  onChange={(e) => setFormData({ ...formData, awarding_body: e.target.value })}
                />
              </div>
              <div>
                <Label>Scheme Name</Label>
                <Input 
                  value={formData.scheme_name}
                  onChange={(e) => setFormData({ ...formData, scheme_name: e.target.value })}
                />
              </div>
            </div>

            <div className="p-4 bg-blue-50 border border-blue-200 rounded-md">
              <div className="text-sm text-blue-600 font-medium">Configuration Summary</div>
              <div className="mt-2 grid grid-cols-2 gap-4 text-sm">
                <div>Total Target: <span className="font-mono font-bold">{formData.total_training_target}</span></div>
                <div>Job Roles: <span className="font-mono font-bold">{formData.num_job_roles}</span></div>
              </div>
            </div>

            <Button 
              type="button" 
              className="w-full" 
              onClick={() => setStep(2)}
              disabled={!canProceedToStep2}
            >
              Next: Select Job Roles
            </Button>
          </div>
        )}

        {/* Step 2: Job Roles */}
        {step === 2 && (
          <div className="space-y-4">
            {/* Target Progress Bar */}
            <div className="p-4 border border-border rounded-md">
              <div className="flex justify-between text-sm mb-2">
                <span>Target Allocation</span>
                <span className={`font-mono font-bold ${isOverAllocated ? 'text-red-600' : isTargetFullyAllocated ? 'text-emerald-600' : ''}`}>
                  {allocatedTarget} / {formData.total_training_target}
                </span>
              </div>
              <div className="w-full bg-muted rounded-full h-3">
                <div 
                  className={`h-3 rounded-full transition-all ${
                    isOverAllocated ? 'bg-red-500' : 
                    isTargetFullyAllocated ? 'bg-emerald-500' : 'bg-blue-500'
                  }`}
                  style={{ width: `${Math.min((allocatedTarget / formData.total_training_target) * 100, 100)}%` }}
                />
              </div>
              {remainingTarget > 0 && !isOverAllocated && (
                <p className="text-xs text-muted-foreground mt-2">
                  Remaining to allocate: <span className="font-mono font-bold">{remainingTarget}</span>
                </p>
              )}
              {isTargetFullyAllocated && (
                <p className="text-xs text-emerald-600 mt-2 font-medium">✓ Target fully allocated</p>
              )}
            </div>

            {/* Add Job Role */}
            <div>
              <Label>Select Job Roles ({selectedJobRoles.length}/{formData.num_job_roles})</Label>
              <Select 
                key={selectKey}
                onValueChange={(value) => {
                  if (value) {
                    addJobRole(value);
                  }
                }}
                disabled={selectedJobRoles.length >= formData.num_job_roles}
              >
                <SelectTrigger className="mt-1" data-testid="job-role-select">
                  <SelectValue placeholder={
                    selectedJobRoles.length >= formData.num_job_roles 
                      ? "Maximum job roles selected" 
                      : `Select job role to add... (${availableJobRoles.length} available)`
                  } />
                </SelectTrigger>
                <SelectContent>
                  {availableJobRoles.length === 0 ? (
                    <div className="p-2 text-sm text-muted-foreground text-center">
                      {jobRoles.length === 0 ? "No job roles defined" : "All job roles selected"}
                    </div>
                  ) : (
                    availableJobRoles.map((jr) => (
                      <SelectItem key={jr.job_role_id} value={jr.job_role_id} data-testid={`job-role-option-${jr.job_role_id}`}>
                        {jr.job_role_code} - {jr.job_role_name} (Cat {jr.category}, ₹{jr.rate_per_hour}/hr)
                      </SelectItem>
                    ))
                  )}
                </SelectContent>
              </Select>
              {jobRoles.length === 0 && (
                <p className="text-xs text-red-500 mt-1">No job roles available. Please create job roles first in the Job Roles tab.</p>
              )}
            </div>

            {/* Selected Job Roles */}
            <div className="space-y-2">
              {selectedJobRoles.map((jr, idx) => (
                <div key={jr.job_role_id} className="p-3 border border-border rounded-md">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="font-medium text-sm">
                        {idx + 1}. {jr.job_role_code} - {jr.job_role_name}
                      </div>
                      <div className="text-xs text-muted-foreground mt-1">
                        Cat {jr.category} • ₹{jr.rate_per_hour}/hr • {jr.total_training_hours} hrs
                      </div>
                    </div>
                    <Button 
                      type="button" 
                      variant="ghost" 
                      size="icon" 
                      className="h-8 w-8"
                      onClick={() => removeJobRole(jr.job_role_id)}
                    >
                      <X className="w-4 h-4" />
                    </Button>
                  </div>
                  <div className="mt-3 flex items-center gap-3">
                    <Label className="text-xs whitespace-nowrap">Target Students:</Label>
                    <Input 
                      type="number"
                      value={jr.target}
                      onChange={(e) => updateJobRoleTarget(jr.job_role_id, e.target.value)}
                      className="w-24 h-8"
                      min="0"
                      max={formData.total_training_target}
                    />
                    <span className="text-xs text-muted-foreground">
                      Value: {new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(jr.target * jr.total_training_hours * jr.rate_per_hour)}
                    </span>
                  </div>
                </div>
              ))}
              
              {selectedJobRoles.length === 0 && (
                <p className="text-sm text-muted-foreground text-center py-4">
                  Select {formData.num_job_roles} job role{formData.num_job_roles > 1 ? 's' : ''} from the dropdown above
                </p>
              )}
            </div>

            {/* Validation Messages */}
            {!canProceedToStep3 && selectedJobRoles.length > 0 && (
              <div className="p-3 bg-amber-50 border border-amber-200 rounded-md text-sm text-amber-700">
                <strong>To proceed:</strong>
                <ul className="list-disc list-inside mt-1">
                  {selectedJobRoles.length < formData.num_job_roles && (
                    <li>Select {formData.num_job_roles - selectedJobRoles.length} more job role(s) ({selectedJobRoles.length}/{formData.num_job_roles} selected)</li>
                  )}
                  {!isTargetFullyAllocated && (
                    <li>Allocate targets to equal {formData.total_training_target} (currently: {allocatedTarget})</li>
                  )}
                </ul>
              </div>
            )}

            {/* Navigation */}
            <div className="flex gap-2">
              <Button type="button" variant="outline" onClick={() => setStep(1)} className="flex-1">
                Back
              </Button>
              <Button 
                type="button" 
                className="flex-1" 
                onClick={() => setStep(3)}
                disabled={!canProceedToStep3}
              >
                Next: SDC Districts
              </Button>
            </div>
          </div>
        )}

        {/* Step 3: SDC Districts */}
        {step === 3 && (
          <div className="space-y-4">
            {/* Summary */}
            <div className="p-4 bg-muted/50 rounded-md">
              <div className="text-sm font-medium mb-2">Work Order Summary</div>
              <div className="text-xs space-y-1">
                <div><span className="text-muted-foreground">WO Number:</span> {formData.work_order_number}</div>
                <div><span className="text-muted-foreground">Total Target:</span> {formData.total_training_target} students</div>
                <div><span className="text-muted-foreground">Job Roles:</span> {selectedJobRoles.map(jr => `${jr.job_role_code} (${jr.target})`).join(', ')}</div>
              </div>
            </div>

            {/* Add District */}
            <div>
              <Label>SDC Districts</Label>
              <div className="flex gap-2 mt-1">
                <Input 
                  placeholder="District name (e.g., Udaipur)"
                  value={newDistrict.name}
                  onChange={(e) => setNewDistrict({ ...newDistrict, name: e.target.value })}
                  className="flex-1"
                />
                <Select 
                  value={String(newDistrict.count)} 
                  onValueChange={(v) => setNewDistrict({ ...newDistrict, count: parseInt(v) })}
                >
                  <SelectTrigger className="w-32">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {[1, 2, 3, 4, 5].map(n => (
                      <SelectItem key={n} value={String(n)}>{n} SDC{n > 1 ? 's' : ''}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Button type="button" variant="outline" onClick={addDistrict}>
                  <Plus className="w-4 h-4" />
                </Button>
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                Add districts where training will be conducted
              </p>
            </div>

            {/* Added Districts */}
            {sdcDistricts.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {sdcDistricts.map((dist, idx) => (
                  <Badge key={idx} variant="secondary" className="px-3 py-2">
                    <MapPin className="w-3 h-3 mr-1" />
                    {dist.district_name} ({dist.sdc_count} SDC{dist.sdc_count > 1 ? 's' : ''})
                    <button 
                      type="button"
                      className="ml-2 hover:text-red-500"
                      onClick={() => removeDistrict(idx)}
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </Badge>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground text-center py-4">No districts added yet</p>
            )}

            {/* Final Summary */}
            <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-md">
              <div className="grid grid-cols-3 gap-4 text-center">
                <div>
                  <div className="text-sm text-emerald-600">Total Target</div>
                  <div className="font-mono font-bold text-xl">{formData.total_training_target}</div>
                </div>
                <div>
                  <div className="text-sm text-emerald-600">Total SDCs</div>
                  <div className="font-mono font-bold text-xl">{sdcDistricts.reduce((sum, d) => sum + d.sdc_count, 0)}</div>
                </div>
                <div>
                  <div className="text-sm text-emerald-600">Contract Value</div>
                  <div className="font-mono font-bold text-xl text-emerald-700">
                    {new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(totalValue)}
                  </div>
                </div>
              </div>
            </div>

            {/* Navigation */}
            <div className="flex gap-2">
              <Button type="button" variant="outline" onClick={() => setStep(2)} className="flex-1">
                Back
              </Button>
              <Button 
                type="submit" 
                className="flex-1" 
                disabled={loading || sdcDistricts.length === 0}
              >
                {loading ? "Creating..." : "Create Work Order"}
              </Button>
            </div>
          </div>
        )}
      </form>
    </>
  );
};

// SDC From Master Form Component
const SDCFromMasterForm = ({ masterWO, onSuccess }) => {
  const [loading, setLoading] = useState(false);
  const [availableInfra, setAvailableInfra] = useState([]);
  const [availableManagers, setAvailableManagers] = useState([]);
  const [allocationStatus, setAllocationStatus] = useState(null);
  const [selectedInfra, setSelectedInfra] = useState(null);
  const [selectedManager, setSelectedManager] = useState(null);
  const [formData, setFormData] = useState({
    district_name: "",
    sdc_suffix: "",
    job_role_id: masterWO.job_roles?.[0]?.job_role_id || "",
    target_students: 30,
    daily_hours: 8,
    manager_email: "",
    infra_id: "",
    address_line1: "",
    address_line2: "",
    city: "",
    state: "",
    pincode: ""
  });

  // Fetch available infrastructure, managers, and allocation status
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [infraRes, managersRes, allocationRes] = await Promise.all([
          axios.get(`${API}/resources/infrastructure/available`),
          axios.get(`${API}/resources/managers/available`),
          axios.get(`${API}/master/work-orders/${masterWO.master_wo_id}/allocation-status`)
        ]);
        setAvailableInfra(infraRes.data);
        setAvailableManagers(managersRes.data);
        setAllocationStatus(allocationRes.data);
        
        // Auto-set target students based on remaining allocation for first job role
        if (allocationRes.data?.job_roles?.length > 0) {
          const firstJR = allocationRes.data.job_roles[0];
          const numSDCs = masterWO.num_sdcs || 1;
          const suggestedTarget = Math.ceil(firstJR.remaining / Math.max(1, numSDCs - allocationRes.data.sdcs_created));
          setFormData(prev => ({
            ...prev,
            target_students: Math.min(suggestedTarget, firstJR.remaining) || 30
          }));
        }
      } catch (error) {
        console.error("Error fetching data:", error);
      }
    };
    fetchData();
  }, [masterWO.master_wo_id, masterWO.num_sdcs]);

  // Get allocation info for selected job role
  const selectedJobRoleAllocation = allocationStatus?.job_roles?.find(
    jr => jr.job_role_id === formData.job_role_id
  );
  
  // Calculate suggested target based on remaining SDCs
  const remainingSDCs = Math.max(1, (masterWO.num_sdcs || 1) - (allocationStatus?.sdcs_created || 0));
  const suggestedTargetPerSDC = selectedJobRoleAllocation 
    ? Math.ceil(selectedJobRoleAllocation.remaining / remainingSDCs)
    : 30;

  // Get all unique districts from available infrastructure
  const availableDistricts = [...new Set(availableInfra.map(i => i.district))];
  
  // Filter infrastructure by selected district (if any)
  const filteredInfra = formData.district_name 
    ? availableInfra.filter(infra => infra.district.toLowerCase() === formData.district_name.toLowerCase())
    : availableInfra;

  const selectedJobRole = masterWO.job_roles?.find(jr => jr.job_role_id === formData.job_role_id);
  const contractValue = selectedJobRole 
    ? formData.target_students * selectedJobRole.total_training_hours * selectedJobRole.rate_per_hour 
    : 0;

  // Validate target doesn't exceed remaining allocation
  const isTargetValid = selectedJobRoleAllocation 
    ? formData.target_students <= selectedJobRoleAllocation.remaining 
    : true;

  // Generate SDC name preview
  const sdcNamePreview = formData.district_name 
    ? `SDC_${formData.district_name.toUpperCase().replace(/\s/g, '_')}${formData.sdc_suffix || ''}`
    : '';

  // Handle job role change - update target to suggested value
  const handleJobRoleChange = (jobRoleId) => {
    const jrAllocation = allocationStatus?.job_roles?.find(jr => jr.job_role_id === jobRoleId);
    const suggested = jrAllocation 
      ? Math.min(Math.ceil(jrAllocation.remaining / remainingSDCs), jrAllocation.remaining)
      : 30;
    setFormData({ 
      ...formData, 
      job_role_id: jobRoleId,
      target_students: suggested || 30
    });
  };

  // Handle infrastructure selection - auto-fill ALL details
  const handleInfraSelect = (infraId) => {
    const infra = availableInfra.find(i => i.infra_id === infraId);
    if (infra) {
      setSelectedInfra(infra);
      setFormData({
        ...formData,
        infra_id: infraId,
        district_name: infra.district,
        address_line1: infra.address_line1 || "",
        address_line2: infra.address_line2 || "",
        city: infra.city || "",
        state: infra.state || "",
        pincode: infra.pincode || "",
        target_students: Math.min(formData.target_students, infra.total_capacity || 30)
      });
    }
  };

  // Handle manager selection
  const handleManagerSelect = (managerId) => {
    const manager = availableManagers.find(m => m.manager_id === managerId);
    if (manager) {
      setSelectedManager(manager);
      setFormData({
        ...formData,
        manager_email: manager.email
      });
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      // Create the SDC
      const response = await axios.post(`${API}/master/work-orders/${masterWO.master_wo_id}/sdcs`, {
        master_wo_id: masterWO.master_wo_id,
        ...formData
      });
      
      const createdSdcId = response.data.sdc_id;
      
      // If infrastructure was selected, mark it as in_use
      if (formData.infra_id) {
        try {
          await axios.post(`${API}/resources/infrastructure/${formData.infra_id}/assign`, null, {
            params: { work_order_id: masterWO.master_wo_id }
          });
        } catch (infraError) {
          console.warn("Infrastructure assignment failed:", infraError);
        }
      }
      
      // If manager was selected, assign to this SDC
      if (selectedManager) {
        try {
          await axios.post(`${API}/resources/managers/${selectedManager.manager_id}/assign`, null, {
            params: { sdc_id: createdSdcId }
          });
        } catch (managerError) {
          console.warn("Manager assignment failed:", managerError);
        }
      }
      
      toast.success(`SDC ${sdcNamePreview} created successfully!`);
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
        <DialogTitle>Create SDC for {masterWO.work_order_number}</DialogTitle>
        <DialogDescription>
          Select a center from Resource Masters - all details will be auto-filled
        </DialogDescription>
      </DialogHeader>
      <form onSubmit={handleSubmit} className="space-y-4 mt-4 max-h-[60vh] overflow-y-auto pr-2" data-testid="sdc-from-master-form">
        
        {/* STEP 1: Select Center (Primary Selection) */}
        <div className="border-2 border-primary/30 rounded-lg p-4 bg-primary/5">
          <Label className="text-base font-semibold flex items-center gap-2 mb-3">
            <Home className="w-5 h-5 text-primary" />
            Step 1: Select Center from Resource Masters *
          </Label>
          <Badge variant="outline" className="text-xs mb-3">
            {availableInfra.length} centers available
          </Badge>
          
          <Select value={formData.infra_id} onValueChange={handleInfraSelect}>
            <SelectTrigger className="w-full">
              <SelectValue placeholder="Select a center..." />
            </SelectTrigger>
            <SelectContent className="max-h-60">
              {availableInfra.map((infra) => (
                <SelectItem key={infra.infra_id} value={infra.infra_id}>
                  <div className="flex flex-col py-1">
                    <span className="font-medium">{infra.center_name}</span>
                    <span className="text-xs text-muted-foreground">
                      {infra.district} • {infra.city}, {infra.state} • Capacity: {infra.total_capacity}
                    </span>
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          
          {availableInfra.length === 0 && (
            <p className="text-sm text-amber-600 mt-2">
              No centers available. Please add centers in Resources tab first.
            </p>
          )}
        </div>

        {/* Selected Center Details (Auto-filled) */}
        {selectedInfra && (
          <div className="border border-emerald-200 rounded-lg p-4 bg-emerald-50">
            <div className="flex items-center gap-2 mb-3">
              <CheckCircle className="w-5 h-5 text-emerald-600" />
              <span className="font-semibold text-emerald-700">Center Selected - Details Auto-filled</span>
            </div>
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div>
                <span className="text-muted-foreground">Center:</span>
                <span className="ml-2 font-medium">{selectedInfra.center_name}</span>
              </div>
              <div>
                <span className="text-muted-foreground">District:</span>
                <span className="ml-2 font-medium">{selectedInfra.district}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Address:</span>
                <span className="ml-2">{selectedInfra.address_line1}, {selectedInfra.city}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Capacity:</span>
                <span className="ml-2 font-medium">{selectedInfra.total_capacity} students</span>
              </div>
              <div className="col-span-2 flex gap-2 mt-1">
                {selectedInfra.has_biometric && <Badge variant="outline" className="text-xs bg-blue-50">Biometric</Badge>}
                {selectedInfra.has_internet && <Badge variant="outline" className="text-xs bg-green-50">Internet</Badge>}
                {selectedInfra.has_fire_safety && <Badge variant="outline" className="text-xs bg-red-50">Fire Safety</Badge>}
                {selectedInfra.has_ac && <Badge variant="outline" className="text-xs">AC</Badge>}
              </div>
            </div>
          </div>
        )}

        {/* SDC Name Preview */}
        {sdcNamePreview && (
          <div className="p-3 bg-blue-50 border border-blue-200 rounded-md">
            <div className="text-sm text-blue-600">SDC Name (auto-generated)</div>
            <div className="font-mono font-bold text-blue-800">{sdcNamePreview}</div>
          </div>
        )}

        {/* SDC Suffix (for multiple SDCs in same district) */}
        <div>
          <Label>SDC Suffix (for multiple SDCs in same district)</Label>
          <Input 
            value={formData.sdc_suffix}
            onChange={(e) => setFormData({ ...formData, sdc_suffix: e.target.value })}
            placeholder="e.g., 1, 2, A, B"
          />
          <p className="text-xs text-muted-foreground mt-1">Leave empty for single SDC in district</p>
        </div>

        {/* Select Center Manager from Resources */}
        <div className="border border-border rounded-md p-4 bg-muted/30">
          <div className="flex items-center justify-between mb-3">
            <Label className="text-base font-medium flex items-center gap-2">
              <UserCog className="w-4 h-4" />
              Step 2: Select Center Manager
            </Label>
            <Badge variant="outline" className="text-xs">
              {availableManagers.length} available
            </Badge>
          </div>
          
          {availableManagers.length > 0 ? (
            <Select onValueChange={handleManagerSelect}>
              <SelectTrigger>
                <SelectValue placeholder="Select available manager..." />
              </SelectTrigger>
              <SelectContent>
                {availableManagers.map((manager) => (
                  <SelectItem key={manager.manager_id} value={manager.manager_id}>
                    <div className="flex flex-col">
                      <span className="font-medium">{manager.name}</span>
                      <span className="text-xs text-muted-foreground">
                        {manager.phone} • {manager.city || "N/A"}
                      </span>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          ) : (
            <p className="text-sm text-muted-foreground py-2">
              No available managers. Add managers in Resources tab.
            </p>
          )}

          {selectedManager && (
            <div className="mt-3 p-3 bg-purple-50 border border-purple-200 rounded-md">
              <div className="flex items-center gap-2 text-purple-700 font-medium text-sm">
                <CheckCircle className="w-4 h-4" />
                Selected: {selectedManager.name}
              </div>
              <div className="text-xs text-purple-600 mt-1">
                {selectedManager.email} • {selectedManager.phone}
              </div>
            </div>
          )}
        </div>

        {/* Allocation Summary */}
        {allocationStatus && (
          <div className="border border-indigo-200 rounded-lg p-4 bg-indigo-50">
            <div className="flex items-center justify-between mb-3">
              <Label className="text-base font-semibold flex items-center gap-2">
                <BarChart3 className="w-5 h-5 text-indigo-600" />
                Allocation Status
              </Label>
              <Badge variant={allocationStatus.is_fully_allocated ? "default" : "outline"} 
                className={allocationStatus.is_fully_allocated ? "bg-emerald-100 text-emerald-700" : ""}>
                {allocationStatus.sdcs_created}/{masterWO.num_sdcs || 0} SDCs Created
              </Badge>
            </div>
            <div className="grid grid-cols-3 gap-4 text-center text-sm">
              <div>
                <div className="font-bold text-lg text-indigo-700">{allocationStatus.total_training_target}</div>
                <div className="text-muted-foreground">Total Target</div>
              </div>
              <div>
                <div className="font-bold text-lg text-amber-600">{allocationStatus.total_allocated}</div>
                <div className="text-muted-foreground">Allocated</div>
              </div>
              <div>
                <div className="font-bold text-lg text-emerald-600">{allocationStatus.total_remaining}</div>
                <div className="text-muted-foreground">Remaining</div>
              </div>
            </div>
          </div>
        )}

        {/* Job Role Selection with Allocation Info */}
        <div className="border border-border rounded-lg p-4">
          <Label className="text-base font-semibold mb-3 block">Step 3: Select Job Role & Allocation *</Label>
          <Select value={formData.job_role_id} onValueChange={handleJobRoleChange}>
            <SelectTrigger>
              <SelectValue placeholder="Select job role..." />
            </SelectTrigger>
            <SelectContent>
              {allocationStatus?.job_roles?.map((jr) => (
                <SelectItem 
                  key={jr.job_role_id} 
                  value={jr.job_role_id}
                  disabled={jr.remaining === 0}
                >
                  <div className="flex flex-col py-1">
                    <span className="font-medium">{jr.job_role_code} - {jr.job_role_name}</span>
                    <span className={`text-xs ${jr.remaining === 0 ? 'text-red-500' : 'text-muted-foreground'}`}>
                      Target: {jr.target} | Allocated: {jr.allocated} | 
                      <span className={jr.remaining > 0 ? 'text-emerald-600 font-medium' : 'text-red-500'}>
                        {' '}Remaining: {jr.remaining}
                      </span>
                    </span>
                  </div>
                </SelectItem>
              )) || masterWO.job_roles?.map((jr) => (
                <SelectItem key={jr.job_role_id} value={jr.job_role_id}>
                  {jr.job_role_code} - {jr.job_role_name} (Target: {jr.target})
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          
          {/* Selected Job Role Allocation Details */}
          {selectedJobRoleAllocation && (
            <div className="mt-3 p-3 bg-slate-50 border border-slate-200 rounded-md">
              <div className="grid grid-cols-4 gap-2 text-center text-sm">
                <div>
                  <div className="font-semibold">{selectedJobRoleAllocation.target}</div>
                  <div className="text-xs text-muted-foreground">Total</div>
                </div>
                <div>
                  <div className="font-semibold text-amber-600">{selectedJobRoleAllocation.allocated}</div>
                  <div className="text-xs text-muted-foreground">Allocated</div>
                </div>
                <div>
                  <div className="font-semibold text-emerald-600">{selectedJobRoleAllocation.remaining}</div>
                  <div className="text-xs text-muted-foreground">Remaining</div>
                </div>
                <div>
                  <div className="font-semibold text-indigo-600">{suggestedTargetPerSDC}</div>
                  <div className="text-xs text-muted-foreground">Suggested/SDC</div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Target & Hours */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label>Target Students for this SDC *</Label>
            <Input 
              type="number"
              value={formData.target_students}
              onChange={(e) => setFormData({ ...formData, target_students: parseInt(e.target.value) || 0 })}
              min="1"
              max={selectedJobRoleAllocation?.remaining || selectedInfra?.total_capacity || 999}
              required
              className={!isTargetValid ? "border-red-500" : ""}
            />
            <div className="flex justify-between mt-1">
              {selectedInfra && (
                <p className="text-xs text-muted-foreground">
                  Center capacity: {selectedInfra.total_capacity}
                </p>
              )}
              {selectedJobRoleAllocation && (
                <p className={`text-xs ${isTargetValid ? 'text-emerald-600' : 'text-red-500 font-medium'}`}>
                  {isTargetValid 
                    ? `Available: ${selectedJobRoleAllocation.remaining}` 
                    : `Exceeds available (${selectedJobRoleAllocation.remaining})!`
                  }
                </p>
              )}
            </div>
            {/* Quick allocation buttons */}
            {selectedJobRoleAllocation && selectedJobRoleAllocation.remaining > 0 && (
              <div className="flex gap-2 mt-2">
                <Button 
                  type="button" 
                  variant="outline" 
                  size="sm"
                  onClick={() => setFormData({ ...formData, target_students: suggestedTargetPerSDC })}
                >
                  Suggested ({suggestedTargetPerSDC})
                </Button>
                <Button 
                  type="button" 
                  variant="outline" 
                  size="sm"
                  onClick={() => setFormData({ ...formData, target_students: selectedJobRoleAllocation.remaining })}
                >
                  All Remaining ({selectedJobRoleAllocation.remaining})
                </Button>
              </div>
            )}
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

        {/* Contract Value */}
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-md">
          <div className="text-sm text-emerald-600">SDC Contract Value</div>
          <div className="font-mono font-bold text-2xl text-emerald-700">
            {new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(contractValue)}
          </div>
          {selectedJobRole && (
            <p className="text-xs text-emerald-600 mt-1">
              {formData.target_students} students × {selectedJobRole.total_training_hours} hrs × ₹{selectedJobRole.rate_per_hour}/hr
            </p>
          )}
        </div>

        {/* Validation Messages */}
        {!selectedInfra && (
          <div className="p-3 bg-amber-50 border border-amber-200 rounded-md text-sm text-amber-700">
            <strong>Please select a Center</strong> from Resource Masters to proceed. 
            If no centers are available, add them in the Resources tab first.
          </div>
        )}
        
        {!isTargetValid && selectedJobRoleAllocation && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-md text-sm text-red-700">
            <strong>Target exceeds available allocation!</strong> 
            {' '}Maximum available for this job role: {selectedJobRoleAllocation.remaining}
          </div>
        )}
        
        {selectedJobRoleAllocation?.remaining === 0 && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-md text-sm text-red-700">
            <strong>This job role is fully allocated.</strong> 
            {' '}Please select a different job role or complete/adjust existing SDCs.
          </div>
        )}

        <Button 
          type="submit" 
          className="w-full" 
          disabled={loading || !selectedInfra || !formData.job_role_id || !isTargetValid || selectedJobRoleAllocation?.remaining === 0}
        >
          {loading ? "Creating SDC..." : "Create SDC"}
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

// ==================== RESOURCE FORM COMPONENTS ====================

// Trainer Form
const TrainerForm = ({ editData, jobRoles, onSuccess, onCancel }) => {
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    name: editData?.name || "",
    email: editData?.email || "",
    phone: editData?.phone || "",
    qualification: editData?.qualification || "",
    specialization: editData?.specialization || "",
    experience_years: editData?.experience_years || 0,
    certifications: editData?.certifications?.join(", ") || "",
    address: editData?.address || "",
    city: editData?.city || "",
    state: editData?.state || ""
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const payload = {
        ...formData,
        experience_years: parseInt(formData.experience_years) || 0,
        certifications: formData.certifications.split(",").map(c => c.trim()).filter(Boolean)
      };
      
      if (editData) {
        await axios.put(`${API}/resources/trainers/${editData.trainer_id}`, payload);
        toast.success("Trainer updated successfully");
      } else {
        await axios.post(`${API}/resources/trainers`, payload);
        toast.success("Trainer added successfully");
      }
      onSuccess();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to save trainer");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <DialogHeader className="flex flex-row items-start justify-between">
        <div>
          <DialogTitle>{editData ? "Edit Trainer" : "Add New Trainer"}</DialogTitle>
          <DialogDescription>Enter trainer details and qualifications</DialogDescription>
        </div>
        <Button variant="ghost" size="icon" onClick={onCancel} className="h-8 w-8" type="button">
          <X className="w-4 h-4" />
        </Button>
      </DialogHeader>
      <form onSubmit={handleSubmit} className="space-y-4 mt-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label>Full Name *</Label>
            <Input 
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="Rajesh Kumar"
              required
            />
          </div>
          <div>
            <Label>Phone *</Label>
            <Input 
              value={formData.phone}
              onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
              placeholder="9876543210"
              required
            />
          </div>
        </div>

        <div>
          <Label>Email *</Label>
          <Input 
            type="email"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            placeholder="trainer@example.com"
            required
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label>Qualification *</Label>
            <Input 
              value={formData.qualification}
              onChange={(e) => setFormData({ ...formData, qualification: e.target.value })}
              placeholder="B.Tech Computer Science"
              required
            />
          </div>
          <div>
            <Label>Experience (Years)</Label>
            <Input 
              type="number"
              value={formData.experience_years}
              onChange={(e) => setFormData({ ...formData, experience_years: e.target.value })}
              min="0"
            />
          </div>
        </div>

        <div>
          <Label>Specialization (Job Role Code) *</Label>
          <Select 
            value={formData.specialization} 
            onValueChange={(v) => setFormData({ ...formData, specialization: v })}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select job role specialization..." />
            </SelectTrigger>
            <SelectContent>
              {jobRoles.filter(jr => jr.is_active).map((jr) => (
                <SelectItem key={jr.job_role_id} value={jr.job_role_code}>
                  {jr.job_role_code} - {jr.job_role_name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div>
          <Label>Certifications (comma-separated)</Label>
          <Input 
            value={formData.certifications}
            onChange={(e) => setFormData({ ...formData, certifications: e.target.value })}
            placeholder="TOT, NSDC Certified, ITI"
          />
        </div>

        <div className="grid grid-cols-3 gap-4">
          <div>
            <Label>Address</Label>
            <Input 
              value={formData.address}
              onChange={(e) => setFormData({ ...formData, address: e.target.value })}
              placeholder="Street address"
            />
          </div>
          <div>
            <Label>City</Label>
            <Input 
              value={formData.city}
              onChange={(e) => setFormData({ ...formData, city: e.target.value })}
              placeholder="Jaipur"
            />
          </div>
          <div>
            <Label>State</Label>
            <Input 
              value={formData.state}
              onChange={(e) => setFormData({ ...formData, state: e.target.value })}
              placeholder="Rajasthan"
            />
          </div>
        </div>

        <div className="flex gap-2 pt-4">
          <Button type="button" variant="outline" onClick={onCancel} className="flex-1">
            Cancel
          </Button>
          <Button type="submit" className="flex-1" disabled={loading}>
            {loading ? "Saving..." : (editData ? "Update Trainer" : "Add Trainer")}
          </Button>
        </div>
      </form>
    </>
  );
};

// Manager Form
const ManagerForm = ({ editData, onSuccess, onCancel }) => {
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    name: editData?.name || "",
    email: editData?.email || "",
    phone: editData?.phone || "",
    qualification: editData?.qualification || "",
    experience_years: editData?.experience_years || 0,
    address: editData?.address || "",
    city: editData?.city || "",
    state: editData?.state || ""
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const payload = {
        ...formData,
        experience_years: parseInt(formData.experience_years) || 0
      };
      
      if (editData) {
        await axios.put(`${API}/resources/managers/${editData.manager_id}`, payload);
        toast.success("Manager updated successfully");
      } else {
        await axios.post(`${API}/resources/managers`, payload);
        toast.success("Manager added successfully");
      }
      onSuccess();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to save manager");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <DialogHeader className="flex flex-row items-start justify-between">
        <div>
          <DialogTitle>{editData ? "Edit Center Manager" : "Add Center Manager"}</DialogTitle>
          <DialogDescription>Enter manager details</DialogDescription>
        </div>
        <Button variant="ghost" size="icon" onClick={onCancel} className="h-8 w-8" type="button">
          <X className="w-4 h-4" />
        </Button>
      </DialogHeader>
      <form onSubmit={handleSubmit} className="space-y-4 mt-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label>Full Name *</Label>
            <Input 
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="Amit Verma"
              required
            />
          </div>
          <div>
            <Label>Phone *</Label>
            <Input 
              value={formData.phone}
              onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
              placeholder="9876543210"
              required
            />
          </div>
        </div>

        <div>
          <Label>Email *</Label>
          <Input 
            type="email"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            placeholder="manager@example.com"
            required
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label>Qualification</Label>
            <Input 
              value={formData.qualification}
              onChange={(e) => setFormData({ ...formData, qualification: e.target.value })}
              placeholder="MBA, B.Com"
            />
          </div>
          <div>
            <Label>Experience (Years)</Label>
            <Input 
              type="number"
              value={formData.experience_years}
              onChange={(e) => setFormData({ ...formData, experience_years: e.target.value })}
              min="0"
            />
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4">
          <div>
            <Label>Address</Label>
            <Input 
              value={formData.address}
              onChange={(e) => setFormData({ ...formData, address: e.target.value })}
              placeholder="Street address"
            />
          </div>
          <div>
            <Label>City</Label>
            <Input 
              value={formData.city}
              onChange={(e) => setFormData({ ...formData, city: e.target.value })}
              placeholder="Jaipur"
            />
          </div>
          <div>
            <Label>State</Label>
            <Input 
              value={formData.state}
              onChange={(e) => setFormData({ ...formData, state: e.target.value })}
              placeholder="Rajasthan"
            />
          </div>
        </div>

        <div className="flex gap-2 pt-4">
          <Button type="button" variant="outline" onClick={onCancel} className="flex-1">
            Cancel
          </Button>
          <Button type="submit" className="flex-1" disabled={loading}>
            {loading ? "Saving..." : (editData ? "Update Manager" : "Add Manager")}
          </Button>
        </div>
      </form>
    </>
  );
};

// Infrastructure Form
const InfrastructureForm = ({ editData, onSuccess, onCancel }) => {
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    center_name: editData?.center_name || "",
    center_code: editData?.center_code || "",
    district: editData?.district || "",
    address_line1: editData?.address_line1 || "",
    address_line2: editData?.address_line2 || "",
    city: editData?.city || "",
    state: editData?.state || "",
    pincode: editData?.pincode || "",
    contact_phone: editData?.contact_phone || "",
    contact_email: editData?.contact_email || "",
    total_capacity: editData?.total_capacity || 30,
    num_classrooms: editData?.num_classrooms || 1,
    num_computer_labs: editData?.num_computer_labs || 0,
    has_projector: editData?.has_projector ?? true,
    has_ac: editData?.has_ac ?? false,
    has_library: editData?.has_library ?? false
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const payload = {
        ...formData,
        total_capacity: parseInt(formData.total_capacity) || 30,
        num_classrooms: parseInt(formData.num_classrooms) || 1,
        num_computer_labs: parseInt(formData.num_computer_labs) || 0
      };
      
      if (editData) {
        await axios.put(`${API}/resources/infrastructure/${editData.infra_id}`, payload);
        toast.success("Center updated successfully");
      } else {
        await axios.post(`${API}/resources/infrastructure`, payload);
        toast.success("Center added successfully");
      }
      onSuccess();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to save center");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <DialogHeader className="flex flex-row items-start justify-between">
        <div>
          <DialogTitle>{editData ? "Edit SDC/Center" : "Add New SDC/Center"}</DialogTitle>
          <DialogDescription>Enter center details, address and facilities</DialogDescription>
        </div>
        <Button variant="ghost" size="icon" onClick={onCancel} className="h-8 w-8" type="button">
          <X className="w-4 h-4" />
        </Button>
      </DialogHeader>
      <form onSubmit={handleSubmit} className="space-y-4 mt-4">
        {/* Basic Info */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label>Center Name *</Label>
            <Input 
              value={formData.center_name}
              onChange={(e) => setFormData({ ...formData, center_name: e.target.value })}
              placeholder="Skill Center Jaipur"
              required
            />
          </div>
          <div>
            <Label>Center Code *</Label>
            <Input 
              value={formData.center_code}
              onChange={(e) => setFormData({ ...formData, center_code: e.target.value })}
              placeholder="SDC-JAI-001"
              required
              disabled={!!editData}
            />
          </div>
        </div>

        <div>
          <Label>District *</Label>
          <Input 
            value={formData.district}
            onChange={(e) => setFormData({ ...formData, district: e.target.value })}
            placeholder="Jaipur"
            required
          />
        </div>

        {/* Address */}
        <div className="border border-border rounded-md p-4">
          <Label className="text-base font-medium mb-3 block">Address Details</Label>
          <div className="space-y-3">
            <div>
              <Label className="text-sm">Address Line 1 *</Label>
              <Input 
                value={formData.address_line1}
                onChange={(e) => setFormData({ ...formData, address_line1: e.target.value })}
                placeholder="123, Industrial Area"
                required
              />
            </div>
            <div>
              <Label className="text-sm">Address Line 2</Label>
              <Input 
                value={formData.address_line2}
                onChange={(e) => setFormData({ ...formData, address_line2: e.target.value })}
                placeholder="Near Bus Stand"
              />
            </div>
            <div className="grid grid-cols-3 gap-3">
              <div>
                <Label className="text-sm">City *</Label>
                <Input 
                  value={formData.city}
                  onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                  placeholder="Jaipur"
                  required
                />
              </div>
              <div>
                <Label className="text-sm">State *</Label>
                <Input 
                  value={formData.state}
                  onChange={(e) => setFormData({ ...formData, state: e.target.value })}
                  placeholder="Rajasthan"
                  required
                />
              </div>
              <div>
                <Label className="text-sm">Pincode *</Label>
                <Input 
                  value={formData.pincode}
                  onChange={(e) => setFormData({ ...formData, pincode: e.target.value })}
                  placeholder="302001"
                  required
                />
              </div>
            </div>
          </div>
        </div>

        {/* Contact */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label>Contact Phone</Label>
            <Input 
              value={formData.contact_phone}
              onChange={(e) => setFormData({ ...formData, contact_phone: e.target.value })}
              placeholder="0141-2345678"
            />
          </div>
          <div>
            <Label>Contact Email</Label>
            <Input 
              type="email"
              value={formData.contact_email}
              onChange={(e) => setFormData({ ...formData, contact_email: e.target.value })}
              placeholder="center@example.com"
            />
          </div>
        </div>

        {/* Capacity */}
        <div className="grid grid-cols-3 gap-4">
          <div>
            <Label>Total Capacity *</Label>
            <Input 
              type="number"
              value={formData.total_capacity}
              onChange={(e) => setFormData({ ...formData, total_capacity: e.target.value })}
              min="1"
              required
            />
          </div>
          <div>
            <Label>Classrooms</Label>
            <Input 
              type="number"
              value={formData.num_classrooms}
              onChange={(e) => setFormData({ ...formData, num_classrooms: e.target.value })}
              min="0"
            />
          </div>
          <div>
            <Label>Computer Labs</Label>
            <Input 
              type="number"
              value={formData.num_computer_labs}
              onChange={(e) => setFormData({ ...formData, num_computer_labs: e.target.value })}
              min="0"
            />
          </div>
        </div>

        {/* Facilities */}
        <div className="border border-border rounded-md p-4">
          <Label className="text-base font-medium mb-3 block">Facilities</Label>
          <div className="flex flex-wrap gap-6">
            <label className="flex items-center gap-2 cursor-pointer">
              <Checkbox 
                checked={formData.has_projector}
                onCheckedChange={(checked) => setFormData({ ...formData, has_projector: checked })}
              />
              <span className="text-sm">Projector</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <Checkbox 
                checked={formData.has_ac}
                onCheckedChange={(checked) => setFormData({ ...formData, has_ac: checked })}
              />
              <span className="text-sm">Air Conditioning</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <Checkbox 
                checked={formData.has_library}
                onCheckedChange={(checked) => setFormData({ ...formData, has_library: checked })}
              />
              <span className="text-sm">Library</span>
            </label>
          </div>
        </div>

        <div className="flex gap-2 pt-4">
          <Button type="button" variant="outline" onClick={onCancel} className="flex-1">
            Cancel
          </Button>
          <Button type="submit" className="flex-1" disabled={loading}>
            {loading ? "Saving..." : (editData ? "Update Center" : "Add Center")}
          </Button>
        </div>
      </form>
    </>
  );
};
