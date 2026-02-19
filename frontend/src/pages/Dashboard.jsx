import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { API } from "@/App";
import { toast } from "sonner";
import { 
  Building2, 
  BarChart3, 
  AlertTriangle, 
  TrendingUp, 
  TrendingDown,
  DollarSign,
  Users,
  ChevronRight,
  LogOut,
  Settings,
  RefreshCw,
  Bell,
  FileText,
  ClipboardList,
  Briefcase,
  GraduationCap,
  CheckCircle2,
  CheckCircle,
  Clock,
  Plus,
  Package
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { 
  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuSeparator,
  DropdownMenuTrigger 
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

// Process Stage icons (5-stage pipeline)
const PROCESS_ICONS = {
  mobilization: Users,
  training: GraduationCap,
  ojt: Briefcase,
  assessment: CheckCircle2,
  placement: Building2
};

// Process Stage colors
const PROCESS_COLORS = {
  mobilization: "bg-amber-500",
  training: "bg-blue-500",
  ojt: "bg-indigo-500",
  assessment: "bg-purple-500",
  placement: "bg-emerald-500"
};

// Deliverable items
const DELIVERABLES = [
  { id: "dress_distribution", name: "Dress Distribution", icon: ClipboardList },
  { id: "study_material", name: "Study Material", icon: FileText },
  { id: "id_card", name: "ID Card", icon: Package },
  { id: "toolkit", name: "Tool Kit", icon: Briefcase }
];

// Legacy Stage icons mapping (for backward compatibility)
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

export default function Dashboard({ user }) {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [dashboardData, setDashboardData] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [refreshing, setRefreshing] = useState(false);
  const [showWorkOrderDialog, setShowWorkOrderDialog] = useState(false);

  const fetchDashboardData = async () => {
    try {
      const [dashboardRes, alertsRes] = await Promise.all([
        axios.get(`${API}/dashboard/overview`),
        axios.get(`${API}/alerts`)
      ]);
      setDashboardData(dashboardRes.data);
      setAlerts(alertsRes.data);
    } catch (error) {
      console.error("Error fetching dashboard:", error);
      toast.error("Failed to load dashboard data");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchDashboardData();
    toast.success("Dashboard refreshed");
  };

  const handleLogout = async () => {
    try {
      await axios.post(`${API}/auth/logout`);
      navigate("/", { replace: true });
    } catch (error) {
      console.error("Logout error:", error);
      navigate("/", { replace: true });
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0
    }).format(value);
  };

  if (loading) {
    return <DashboardSkeleton />;
  }

  const { commercial_health, stage_progress, sdc_summaries } = dashboardData || {};

  // Calculate aggregated process data from stage_progress
  const processStages = [
    { id: "mobilization", name: "Mobilization", data: stage_progress?.mobilization },
    { id: "training", name: "Training", data: stage_progress?.classroom_training },
    { id: "ojt", name: "OJT", data: stage_progress?.ojt },
    { id: "assessment", name: "Assessment", data: stage_progress?.assessment },
    { id: "placement", name: "Placement", data: stage_progress?.placement }
  ];

  // Calculate overall progress
  const totalTarget = processStages.reduce((sum, s) => sum + (s.data?.target || 0), 0);
  const totalCompleted = processStages.reduce((sum, s) => sum + (s.data?.completed || 0), 0);
  const overallProgress = totalTarget > 0 ? Math.round((totalCompleted / totalTarget) * 100) : 0;

  return (
    <div className="min-h-screen bg-background" data-testid="dashboard">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-background/95 backdrop-blur-sm border-b border-border">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-primary rounded-md flex items-center justify-center">
              <Building2 className="w-6 h-6 text-primary-foreground" />
            </div>
            <span className="font-heading font-bold text-xl">SkillFlow</span>
            {user?.role === "ho" && (
              <Badge variant="secondary" className="ml-2">Head Office</Badge>
            )}
          </div>
          
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="icon"
              onClick={handleRefresh}
              disabled={refreshing}
              data-testid="refresh-btn"
            >
              <RefreshCw className={`w-5 h-5 ${refreshing ? 'animate-spin' : ''}`} />
            </Button>

            {alerts.length > 0 && (
              <Button variant="ghost" size="icon" className="relative" data-testid="alerts-btn">
                <Bell className="w-5 h-5" />
                <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
                  {alerts.length}
                </span>
              </Button>
            )}

            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="flex items-center gap-2" data-testid="user-menu">
                  <Avatar className="w-8 h-8">
                    <AvatarImage src={user?.picture} alt={user?.name} />
                    <AvatarFallback>{user?.name?.[0]}</AvatarFallback>
                  </Avatar>
                  <span className="hidden sm:block text-sm font-medium">{user?.name}</span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-48">
                {user?.role === "ho" && (
                  <>
                    <DropdownMenuItem onClick={() => navigate("/master-data")} data-testid="master-data-link">
                      <FileText className="w-4 h-4 mr-2" />
                      Master Data
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => navigate("/users")} data-testid="users-link">
                      <Users className="w-4 h-4 mr-2" />
                      User Management
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                  </>
                )}
                <DropdownMenuItem onClick={() => navigate("/settings")} data-testid="settings-link">
                  <Settings className="w-4 h-4 mr-2" />
                  Settings
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={handleLogout} data-testid="logout-btn">
                  <LogOut className="w-4 h-4 mr-2" />
                  Logout
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Page Title */}
        <div className="mb-8">
          <h1 className="font-heading font-bold text-2xl sm:text-3xl mb-2">Dashboard Overview</h1>
          <p className="text-muted-foreground">
            {user?.role === "ho" 
              ? "Monitor all Skill Development Centers" 
              : `SDC: ${user?.assigned_sdc_id || 'Not Assigned'}`}
          </p>
        </div>

        {/* Alerts Banner */}
        {alerts.length > 0 && (
          <div className="mb-8 p-4 bg-red-50 border border-red-200 rounded-md animate-fade-in" data-testid="alerts-banner">
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-red-600 mt-0.5" />
              <div>
                <h3 className="font-heading font-bold text-red-800 mb-1">Risk Alerts</h3>
                <ul className="text-sm text-red-700 space-y-1">
                  {alerts.slice(0, 3).map((alert, i) => (
                    <li key={alert.alert_id || i}>
                      <span className="font-medium">{alert.sdc_name}:</span> {alert.message}
                    </li>
                  ))}
                </ul>
                {alerts.length > 3 && (
                  <p className="text-xs text-red-600 mt-2">+{alerts.length - 3} more alerts</p>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Commercial Health Cards */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
          <MetricCard
            title="Total Portfolio"
            value={formatCurrency(commercial_health?.total_portfolio || 0)}
            icon={<DollarSign className="w-5 h-5" />}
            trend={null}
            className="animate-fade-in stagger-1"
            testId="portfolio-card"
          />
          <MetricCard
            title="Actual Billed"
            value={formatCurrency(commercial_health?.actual_billed || 0)}
            icon={<BarChart3 className="w-5 h-5" />}
            trend={null}
            className="animate-fade-in stagger-2"
            testId="billed-card"
          />
          <MetricCard
            title="Collected"
            value={formatCurrency(commercial_health?.collected || 0)}
            icon={<CheckCircle2 className="w-5 h-5" />}
            color="emerald"
            className="animate-fade-in stagger-3"
            testId="collected-card"
          />
          <MetricCard
            title="Outstanding"
            value={formatCurrency(commercial_health?.outstanding || 0)}
            icon={<TrendingDown className="w-5 h-5" />}
            trend={(commercial_health?.outstanding || 0) > 0 ? "warning" : "success"}
            className="animate-fade-in stagger-4"
            testId="outstanding-card"
          />
          <MetricCard
            title="Variance"
            value={`${commercial_health?.variance_percent || 0}%`}
            subtitle={formatCurrency(commercial_health?.variance || 0)}
            icon={<TrendingUp className="w-5 h-5" />}
            trend={(commercial_health?.variance_percent || 0) > 10 ? "warning" : "success"}
            className="animate-fade-in stagger-5"
            testId="variance-card"
          />
        </div>

        {/* Process Stages & Deliverables - Side by Side */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          {/* Process Stages - 2/3 width */}
          <Card className="border border-border animate-fade-in lg:col-span-2" data-testid="process-stages-card">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="font-heading text-base flex items-center gap-2">
                  <ClipboardList className="w-5 h-5" />
                  Process Stages (All SDCs)
                </CardTitle>
                <Badge className="text-lg px-3 py-1 bg-indigo-100 text-indigo-700">
                  {overallProgress}%
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              {/* Overall Progress Bar */}
              <Progress value={overallProgress} className="h-3 mb-6" />
              
              {/* Process Flow Timeline */}
              <div className="flex items-center justify-between mb-4">
                {processStages.map((stage, idx) => {
                  const completed = stage.data?.completed || 0;
                  const target = stage.data?.target || 0;
                  const percent = target > 0 ? Math.round((completed / target) * 100) : 0;
                  const isComplete = percent >= 100;
                  const isInProgress = percent > 0 && percent < 100;
                  
                  return (
                    <div key={stage.id} className="flex items-center">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold ${
                        isComplete ? "bg-emerald-500 text-white" :
                        isInProgress ? "bg-blue-500 text-white" :
                        "bg-gray-200 text-gray-500"
                      }`}>
                        {isComplete ? "✓" : idx + 1}
                      </div>
                      {idx < 4 && (
                        <div className={`w-8 lg:w-16 h-1 ${
                          isComplete ? "bg-emerald-500" : "bg-gray-200"
                        }`} />
                      )}
                    </div>
                  );
                })}
              </div>
              <div className="flex justify-between mb-6 text-xs text-muted-foreground">
                {processStages.map(stage => (
                  <span key={stage.id}>{stage.name}</span>
                ))}
              </div>

              {/* Stage Details */}
              <div className="space-y-3">
                {processStages.map((stage, index) => {
                  const StageIcon = PROCESS_ICONS[stage.id] || Users;
                  const color = PROCESS_COLORS[stage.id] || "bg-gray-500";
                  const completed = stage.data?.completed || 0;
                  const target = stage.data?.target || 0;
                  const percent = target > 0 ? Math.round((completed / target) * 100) : 0;
                  const isComplete = percent >= 100;
                  const isInProgress = percent > 0 && percent < 100;
                  
                  return (
                    <div 
                      key={stage.id}
                      className={`p-3 rounded-lg border transition-all ${
                        isComplete 
                          ? "border-emerald-300 bg-emerald-50" 
                          : isInProgress
                          ? "border-blue-300 bg-blue-50"
                          : "border-border bg-background"
                      }`}
                    >
                      <div className="flex items-center gap-4">
                        {/* Stage Number & Icon */}
                        <div className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 ${
                          isComplete 
                            ? "bg-emerald-500 text-white" 
                            : isInProgress
                            ? "bg-blue-500 text-white"
                            : `${color} text-white`
                        }`}>
                          {isComplete ? (
                            <CheckCircle className="w-5 h-5" />
                          ) : (
                            <StageIcon className="w-5 h-5" />
                          )}
                        </div>

                        {/* Stage Info */}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="font-semibold">{stage.name}</span>
                            <span className="text-xs text-muted-foreground">
                              (Target: {target})
                            </span>
                          </div>
                          {/* Progress Bar */}
                          <div className="flex items-center gap-2">
                            <Progress 
                              value={percent} 
                              className={`h-2 flex-1 ${isComplete ? "[&>div]:bg-emerald-500" : ""}`}
                            />
                            <span className="font-mono text-sm w-20 text-right">
                              {completed}/{target}
                            </span>
                          </div>
                        </div>

                        {/* Percentage */}
                        <div className="text-right">
                          <span className={`font-mono font-bold text-lg ${
                            isComplete ? "text-emerald-600" : 
                            isInProgress ? "text-blue-600" : "text-gray-500"
                          }`}>
                            {percent}%
                          </span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>

          {/* Deliverables - 1/3 width */}
          <Card className="border border-border animate-fade-in" data-testid="deliverables-card">
            <CardHeader className="pb-2">
              <CardTitle className="font-heading text-base flex items-center gap-2">
                <Package className="w-5 h-5" />
                Deliverables Summary
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {/* Dress Distribution */}
                <DeliverableItem 
                  name="Dress Distribution"
                  icon={ClipboardList}
                  data={stage_progress?.dress_distribution}
                />
                {/* Study Material */}
                <DeliverableItem 
                  name="Study Material"
                  icon={FileText}
                  data={stage_progress?.study_material}
                />
                {/* ID Card - estimated from mobilization */}
                <DeliverableItem 
                  name="ID Card"
                  icon={Users}
                  data={stage_progress?.mobilization}
                  label="Based on Mobilization"
                />
                {/* Tool Kit - estimated from training */}
                <DeliverableItem 
                  name="Tool Kit"
                  icon={Briefcase}
                  data={stage_progress?.classroom_training}
                  label="Based on Training"
                />
              </div>

              {/* Quick Stats */}
              <div className="mt-6 pt-4 border-t border-border">
                <h4 className="text-sm font-semibold mb-3">Quick Stats</h4>
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 rounded-lg bg-muted/50 text-center">
                    <div className="font-mono font-bold text-xl text-amber-600">
                      {stage_progress?.mobilization?.completed || 0}
                    </div>
                    <div className="text-xs text-muted-foreground">Mobilized</div>
                  </div>
                  <div className="p-3 rounded-lg bg-muted/50 text-center">
                    <div className="font-mono font-bold text-xl text-emerald-600">
                      {stage_progress?.placement?.completed || 0}
                    </div>
                    <div className="text-xs text-muted-foreground">Placed</div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* SDC Cards */}
        <div className="mb-4 flex items-center justify-between">
          <h2 className="font-heading font-bold text-xl">SDC Progress</h2>
          <div className="flex items-center gap-2">
            {user?.role === "ho" && (
              <>
                <Dialog open={showWorkOrderDialog} onOpenChange={setShowWorkOrderDialog}>
                  <DialogTrigger asChild>
                    <Button data-testid="new-work-order-btn">
                      <Plus className="w-4 h-4 mr-1" />
                      New Work Order
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
                    <NewWorkOrderForm 
                      onSuccess={() => {
                        setShowWorkOrderDialog(false);
                        fetchDashboardData();
                      }} 
                    />
                  </DialogContent>
                </Dialog>
                <Button 
                  variant="outline" 
                  onClick={() => navigate("/financial")}
                  data-testid="financial-btn"
                >
                  Financial Control
                  <ChevronRight className="w-4 h-4 ml-1" />
                </Button>
              </>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" data-testid="sdc-grid">
          {sdc_summaries?.map((sdc, index) => (
            <SDCCard
              key={sdc.sdc_id}
              sdc={sdc}
              onClick={() => navigate(`/sdc/${sdc.sdc_id}`)}
              className={`animate-fade-in stagger-${index + 1}`}
            />
          ))}
          
          {(!sdc_summaries || sdc_summaries.length === 0) && (
            <div className="col-span-full text-center py-12 text-muted-foreground">
              <Building2 className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>No SDCs found. {user?.role === "ho" ? "Create a Work Order to get started." : "Contact your administrator."}</p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

// Deliverable Item Component
const DeliverableItem = ({ name, icon: Icon, data, label }) => {
  const completed = data?.completed || 0;
  const target = data?.target || 0;
  const percent = target > 0 ? Math.round((completed / target) * 100) : 0;
  const isComplete = percent >= 100;
  
  return (
    <div 
      className={`p-3 rounded-lg border flex items-center justify-between ${
        isComplete 
          ? "border-emerald-300 bg-emerald-50" 
          : percent > 0
          ? "border-blue-200 bg-blue-50/50"
          : "border-border bg-background"
      }`}
    >
      <div className="flex items-center gap-3">
        <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
          isComplete ? "bg-emerald-500 text-white" : "bg-gray-200 text-gray-600"
        }`}>
          {isComplete ? <CheckCircle className="w-4 h-4" /> : <Icon className="w-4 h-4" />}
        </div>
        <div>
          <div className="font-medium text-sm">{name}</div>
          {label && <div className="text-xs text-muted-foreground">{label}</div>}
        </div>
      </div>
      <div className="text-right">
        <div className="font-mono text-sm font-semibold">{completed}/{target}</div>
        <div className={`text-xs ${isComplete ? "text-emerald-600" : "text-muted-foreground"}`}>
          {percent}%
        </div>
      </div>
    </div>
  );
};

// Helper Components
const MetricCard = ({ title, value, subtitle, icon, trend, color, className, testId }) => (
  <Card className={`border border-border ${className}`} data-testid={testId}>
    <CardContent className="p-4">
      <div className="flex items-start justify-between mb-3">
        <div className={`w-9 h-9 rounded-md flex items-center justify-center ${
          color === "emerald" ? "bg-emerald-100 text-emerald-700" :
          trend === "warning" ? "bg-amber-100 text-amber-700" :
          trend === "success" ? "bg-emerald-100 text-emerald-700" :
          "bg-slate-100 text-slate-700"
        }`}>
          {icon}
        </div>
        {trend && (
          <Badge variant={trend === "warning" ? "destructive" : "default"} className={`text-xs ${
            trend === "success" ? "bg-emerald-100 text-emerald-700 border-emerald-200" : ""
          }`}>
            {trend === "warning" ? "Attention" : "OK"}
          </Badge>
        )}
      </div>
      <div className="font-mono font-bold text-xl mb-1">{value}</div>
      {subtitle && <div className="text-xs text-muted-foreground font-mono">{subtitle}</div>}
      <div className="text-xs text-muted-foreground mt-1">{title}</div>
    </CardContent>
  </Card>
);

const SDCCard = ({ sdc, onClick, className }) => {
  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
      notation: 'compact'
    }).format(value);
  };

  const hasBlockers = sdc.blockers && sdc.blockers.length > 0;
  const isOverdue = sdc.overdue_count > 0;

  // Calculate 5-stage progress
  const processProgress = {
    mobilization: sdc.progress?.mobilization,
    training: sdc.progress?.classroom_training,
    ojt: sdc.progress?.ojt,
    assessment: sdc.progress?.assessment,
    placement: sdc.progress?.placement
  };

  return (
    <Card 
      className={`border border-border cursor-pointer hover:bg-muted/30 transition-colors ${className}`}
      onClick={onClick}
      data-testid={`sdc-card-${sdc.sdc_id}`}
    >
      <CardContent className="p-6">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h3 className="font-heading font-bold text-lg">{sdc.name}</h3>
            <p className="text-sm text-muted-foreground">{sdc.location}</p>
          </div>
          <div className="flex items-center gap-2">
            {isOverdue && (
              <Badge variant="destructive" className="text-xs">
                {sdc.overdue_count} Overdue
              </Badge>
            )}
            <ChevronRight className="w-5 h-5 text-muted-foreground" />
          </div>
        </div>

        {/* Blockers Alert */}
        {hasBlockers && (
          <div className="mb-4 p-2 bg-amber-50 border border-amber-200 rounded text-xs text-amber-800">
            <AlertTriangle className="w-3 h-3 inline mr-1" />
            {sdc.blockers[0]}
          </div>
        )}

        {/* Mini 5-Stage Process Flow */}
        <div className="flex items-center justify-between mb-2">
          {Object.entries(processProgress).map(([stageId, data], i) => {
            const percent = data?.target > 0 ? (data?.completed / data?.target) * 100 : 0;
            const isComplete = percent >= 100;
            const isInProgress = percent > 0 && percent < 100;
            
            return (
              <div key={stageId} className="flex items-center">
                <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                  isComplete ? "bg-emerald-500 text-white" :
                  isInProgress ? "bg-blue-500 text-white" :
                  "bg-gray-200 text-gray-500"
                }`}>
                  {isComplete ? "✓" : i + 1}
                </div>
                {i < 4 && (
                  <div className={`w-3 h-0.5 ${isComplete ? "bg-emerald-500" : "bg-gray-200"}`} />
                )}
              </div>
            );
          })}
        </div>
        <div className="flex justify-between text-[10px] text-muted-foreground mb-4">
          <span>Mob</span>
          <span>Train</span>
          <span>OJT</span>
          <span>Assess</span>
          <span>Place</span>
        </div>

        <div className="grid grid-cols-3 gap-2 text-center mb-4">
          <div>
            <div className="font-mono font-medium text-sm">{sdc.work_orders_count || 0}</div>
            <div className="text-xs text-muted-foreground">Work Orders</div>
          </div>
          <div>
            <div className="font-mono font-medium text-sm">
              {sdc.progress?.placement?.completed || 0}
            </div>
            <div className="text-xs text-muted-foreground">Placed</div>
          </div>
          <div>
            <div className={`font-mono font-medium text-sm ${sdc.financial?.outstanding > 0 ? 'text-red-600' : 'text-emerald-600'}`}>
              {formatCurrency(sdc.financial?.outstanding || 0)}
            </div>
            <div className="text-xs text-muted-foreground">Outstanding</div>
          </div>
        </div>

        <div className="flex items-center justify-between pt-4 border-t border-border">
          <div>
            <div className="text-xs text-muted-foreground">Portfolio</div>
            <div className="font-mono text-sm">{formatCurrency(sdc.financial?.portfolio || 0)}</div>
          </div>
          <div className="text-right">
            <div className="text-xs text-muted-foreground">Collected</div>
            <div className="font-mono text-sm text-emerald-600">
              {formatCurrency(sdc.financial?.paid || 0)}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

const DashboardSkeleton = () => (
  <div className="min-h-screen bg-background">
    <header className="border-b border-border">
      <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
        <Skeleton className="w-40 h-10" />
        <Skeleton className="w-32 h-10" />
      </div>
    </header>
    <main className="max-w-7xl mx-auto px-6 py-8">
      <Skeleton className="w-64 h-8 mb-8" />
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
        {[1, 2, 3, 4, 5].map(i => (
          <Skeleton key={i} className="h-28 rounded-md" />
        ))}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <Skeleton className="h-96 rounded-md lg:col-span-2" />
        <Skeleton className="h-96 rounded-md" />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {[1, 2, 3].map(i => (
          <Skeleton key={i} className="h-64 rounded-md" />
        ))}
      </div>
    </main>
  </div>
);

// New Work Order Form Component
const NewWorkOrderForm = ({ onSuccess }) => {
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    work_order_number: "",
    location: "",
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
      toast.success("Work Order created successfully! SDC has been automatically created/linked.");
      onSuccess();
    } catch (error) {
      console.error("Error creating work order:", error);
      toast.error(error.response?.data?.detail || "Failed to create work order");
    } finally {
      setLoading(false);
    }
  };

  const totalValue = formData.num_students * formData.cost_per_student;

  return (
    <>
      <DialogHeader>
        <DialogTitle className="text-xl font-heading">Create New Work Order</DialogTitle>
        <p className="text-sm text-muted-foreground mt-1">
          This will automatically create a new SDC if the location doesn't exist.
        </p>
      </DialogHeader>
      <form onSubmit={handleSubmit} className="space-y-4 mt-4" data-testid="new-work-order-form">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label>Work Order Number *</Label>
            <Input 
              value={formData.work_order_number}
              onChange={(e) => setFormData({ ...formData, work_order_number: e.target.value })}
              placeholder="WO/2025/001"
              required
              data-testid="input-wo-number"
            />
          </div>
          <div>
            <Label>Location (SDC) *</Label>
            <Input 
              value={formData.location}
              onChange={(e) => setFormData({ ...formData, location: e.target.value })}
              placeholder="e.g., Mumbai, Delhi, Jaipur"
              required
              data-testid="input-location"
            />
            <p className="text-xs text-muted-foreground mt-1">Enter city name - SDC will be auto-created</p>
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
              data-testid="input-job-code"
            />
          </div>
          <div>
            <Label>Job Role Name *</Label>
            <Input 
              value={formData.job_role_name}
              onChange={(e) => setFormData({ ...formData, job_role_name: e.target.value })}
              placeholder="e.g., Field Technician Computing"
              required
              data-testid="input-job-name"
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label>Awarding Body *</Label>
            <Input 
              value={formData.awarding_body}
              onChange={(e) => setFormData({ ...formData, awarding_body: e.target.value })}
              placeholder="e.g., NSDC, Sector Skill Council"
              required
              data-testid="input-awarding-body"
            />
          </div>
          <div>
            <Label>Scheme Name *</Label>
            <Input 
              value={formData.scheme_name}
              onChange={(e) => setFormData({ ...formData, scheme_name: e.target.value })}
              placeholder="e.g., PMKVY, DDUGKY"
              required
              data-testid="input-scheme"
            />
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4">
          <div>
            <Label>Training Hours *</Label>
            <Input 
              type="number"
              value={formData.total_training_hours}
              onChange={(e) => setFormData({ ...formData, total_training_hours: e.target.value })}
              min="1"
              required
              data-testid="input-hours"
            />
          </div>
          <div>
            <Label>Sessions/Day</Label>
            <Input 
              type="number"
              value={formData.sessions_per_day}
              onChange={(e) => setFormData({ ...formData, sessions_per_day: e.target.value })}
              min="1"
              max="12"
              data-testid="input-sessions"
            />
          </div>
          <div>
            <Label>Number of Students *</Label>
            <Input 
              type="number"
              value={formData.num_students}
              onChange={(e) => setFormData({ ...formData, num_students: e.target.value })}
              min="1"
              required
              data-testid="input-students"
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label>Cost per Student (₹) *</Label>
            <Input 
              type="number"
              value={formData.cost_per_student}
              onChange={(e) => setFormData({ ...formData, cost_per_student: e.target.value })}
              min="0"
              required
              data-testid="input-cost"
            />
          </div>
          <div>
            <Label>Manager Email</Label>
            <Input 
              type="email"
              value={formData.manager_email}
              onChange={(e) => setFormData({ ...formData, manager_email: e.target.value })}
              placeholder="manager@example.com"
              data-testid="input-manager-email"
            />
          </div>
        </div>

        {/* Total Contract Value */}
        <div className="p-4 bg-muted rounded-lg">
          <div className="flex justify-between items-center">
            <span className="text-sm text-muted-foreground">Total Contract Value:</span>
            <span className="font-mono font-bold text-xl">
              {new Intl.NumberFormat('en-IN', {
                style: 'currency',
                currency: 'INR',
                maximumFractionDigits: 0
              }).format(totalValue)}
            </span>
          </div>
          <div className="text-xs text-muted-foreground mt-1">
            {formData.num_students} students × ₹{formData.cost_per_student}/student
          </div>
        </div>

        <div className="flex justify-end gap-3 pt-4">
          <Button type="submit" disabled={loading} data-testid="submit-work-order">
            {loading ? "Creating..." : "Create Work Order"}
          </Button>
        </div>
      </form>
    </>
  );
};
