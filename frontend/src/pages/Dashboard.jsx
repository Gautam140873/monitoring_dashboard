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
  Package,
  FolderOpen,
  Activity,
  PauseCircle,
  Wrench,
  Search,
  Filter,
  ChevronDown,
  MapPin,
  Calendar as CalendarIcon,
  Zap,
  Eye
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
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";

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
                    <DropdownMenuItem onClick={() => navigate("/resource-calendar")} data-testid="resource-calendar-link">
                      <CalendarIcon className="w-4 h-4 mr-2" />
                      Resource Calendar
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

        {/* SDC Status Metrics */}
        <SDCStatusMetrics sdcSummaries={sdc_summaries} />

        {/* Burn-down Dashboard */}
        <BurndownDashboard />

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

        {/* SDC Directory - Accordion Style */}
        <SDCDirectory 
          sdcSummaries={sdc_summaries} 
          onViewSDC={(sdcId) => navigate(`/sdc/${sdcId}`)}
          user={user}
          showWorkOrderDialog={showWorkOrderDialog}
          setShowWorkOrderDialog={setShowWorkOrderDialog}
          fetchDashboardData={fetchDashboardData}
          navigate={navigate}
        />
      </main>
    </div>
  );
}

// SDC Directory Component - Accordion Style
const SDCDirectory = ({ sdcSummaries, onViewSDC, user, showWorkOrderDialog, setShowWorkOrderDialog, fetchDashboardData, navigate }) => {
  const [searchQuery, setSearchQuery] = useState("");
  const [filterBy, setFilterBy] = useState("all"); // all, location, capability
  const [expandedGroups, setExpandedGroups] = useState(["available", "engaged"]);

  // Categorize SDCs by status
  const categorizeSDC = (sdc) => {
    const hasActiveWO = sdc.work_orders_count > 0;
    const mobilized = sdc.progress?.mobilization?.completed || 0;
    const placed = sdc.progress?.placement?.completed || 0;
    const target = sdc.progress?.mobilization?.target || 0;
    const isOverdue = sdc.overdue_count > 0;

    // Inactive/Maintenance: No progress started or overdue issues
    if ((hasActiveWO && mobilized === 0) || isOverdue) {
      return "inactive";
    }
    
    // Engaged/Busy: Active work orders with progress in between
    if (hasActiveWO && mobilized > 0 && (placed < target)) {
      return "engaged";
    }
    
    // Available: No work orders or completed all
    return "available";
  };

  // Filter and group SDCs
  const filteredSDCs = sdcSummaries?.filter(sdc => {
    const matchesSearch = searchQuery === "" || 
      sdc.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      sdc.location.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesSearch;
  }) || [];

  const groupedSDCs = {
    available: filteredSDCs.filter(sdc => categorizeSDC(sdc) === "available"),
    engaged: filteredSDCs.filter(sdc => categorizeSDC(sdc) === "engaged"),
    inactive: filteredSDCs.filter(sdc => categorizeSDC(sdc) === "inactive")
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
      notation: 'compact'
    }).format(value);
  };

  const StatusDot = ({ status }) => {
    if (status === "available") {
      return (
        <span className="relative flex h-3 w-3">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
          <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
        </span>
      );
    }
    if (status === "engaged") {
      return <span className="inline-flex rounded-full h-3 w-3 bg-amber-500"></span>;
    }
    return <span className="inline-flex rounded-full h-3 w-3 bg-gray-400"></span>;
  };

  const SDCRow = ({ sdc, status }) => {
    const [isExpanded, setIsExpanded] = useState(false);
    
    return (
      <Collapsible open={isExpanded} onOpenChange={setIsExpanded}>
        <CollapsibleTrigger asChild>
          <div 
            className={`flex items-center justify-between p-4 hover:bg-muted/50 cursor-pointer border-b border-border last:border-b-0 transition-colors ${
              isExpanded ? "bg-muted/30" : ""
            }`}
          >
            <div className="flex items-center gap-4">
              <StatusDot status={status} />
              <div>
                <div className="font-semibold">{sdc.name}</div>
                <div className="text-sm text-muted-foreground flex items-center gap-1">
                  <MapPin className="w-3 h-3" />
                  {sdc.location}
                </div>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <div className="text-right hidden md:block">
                <div className="text-sm font-mono">{sdc.work_orders_count || 0} WOs</div>
                <div className="text-xs text-muted-foreground">
                  {sdc.progress?.placement?.completed || 0} placed
                </div>
              </div>
              <ChevronDown className={`w-5 h-5 text-muted-foreground transition-transform ${isExpanded ? "rotate-180" : ""}`} />
            </div>
          </div>
        </CollapsibleTrigger>
        <CollapsibleContent>
          <div className="p-4 bg-muted/20 border-b border-border">
            {/* SDC Details */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              {/* Progress */}
              <div className="space-y-2">
                <div className="text-sm font-medium">Process Progress</div>
                <div className="flex items-center gap-2">
                  {["mobilization", "classroom_training", "ojt", "assessment", "placement"].map((stage, i) => {
                    const data = sdc.progress?.[stage];
                    const percent = data?.target > 0 ? (data?.completed / data?.target) * 100 : 0;
                    return (
                      <div key={stage} className="flex items-center">
                        <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                          percent >= 100 ? "bg-emerald-500 text-white" :
                          percent > 0 ? "bg-blue-500 text-white" :
                          "bg-gray-200 text-gray-500"
                        }`}>
                          {percent >= 100 ? "✓" : i + 1}
                        </div>
                        {i < 4 && <div className={`w-2 h-0.5 ${percent >= 100 ? "bg-emerald-500" : "bg-gray-200"}`} />}
                      </div>
                    );
                  })}
                </div>
                <div className="flex justify-between text-[10px] text-muted-foreground">
                  <span>Mob</span>
                  <span>Train</span>
                  <span>OJT</span>
                  <span>Assess</span>
                  <span>Place</span>
                </div>
              </div>

              {/* Financial */}
              <div className="space-y-2">
                <div className="text-sm font-medium">Financial Summary</div>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <span className="text-muted-foreground">Portfolio:</span>
                    <span className="font-mono ml-1">{formatCurrency(sdc.financial?.portfolio || 0)}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Collected:</span>
                    <span className="font-mono ml-1 text-emerald-600">{formatCurrency(sdc.financial?.paid || 0)}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Outstanding:</span>
                    <span className={`font-mono ml-1 ${sdc.financial?.outstanding > 0 ? "text-red-600" : "text-emerald-600"}`}>
                      {formatCurrency(sdc.financial?.outstanding || 0)}
                    </span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Variance:</span>
                    <span className="font-mono ml-1">{formatCurrency(sdc.financial?.variance || 0)}</span>
                  </div>
                </div>
              </div>

              {/* Actions */}
              <div className="space-y-2">
                <div className="text-sm font-medium">Quick Actions</div>
                <div className="flex flex-wrap gap-2">
                  <Button 
                    size="sm" 
                    variant="outline"
                    onClick={() => onViewSDC(sdc.sdc_id)}
                  >
                    <Eye className="w-4 h-4 mr-1" />
                    View Details
                  </Button>
                  {user?.role === "ho" && (
                    <Button 
                      size="sm" 
                      variant={status === "available" ? "default" : "secondary"}
                      disabled={status !== "available"}
                      title={status !== "available" ? "SDC is not available for new assignments" : "Assign new work order"}
                    >
                      <Zap className="w-4 h-4 mr-1" />
                      Assign
                    </Button>
                  )}
                </div>
                {status !== "available" && user?.role === "ho" && (
                  <p className="text-xs text-muted-foreground">
                    {status === "engaged" ? "Currently executing tasks" : "Requires attention before assignment"}
                  </p>
                )}
              </div>
            </div>

            {/* Blockers */}
            {sdc.blockers && sdc.blockers.length > 0 && (
              <div className="mt-2 p-2 bg-amber-50 border border-amber-200 rounded text-sm text-amber-800">
                <AlertTriangle className="w-4 h-4 inline mr-1" />
                <span className="font-medium">Blocker:</span> {sdc.blockers[0]}
              </div>
            )}

            {/* Overdue Warning */}
            {sdc.overdue_count > 0 && (
              <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-800">
                <AlertTriangle className="w-4 h-4 inline mr-1" />
                <span className="font-medium">{sdc.overdue_count} Overdue Work Order(s)</span>
              </div>
            )}
          </div>
        </CollapsibleContent>
      </Collapsible>
    );
  };

  const GroupHeader = ({ status, count, icon: Icon, color, bgColor, borderColor }) => (
    <div className={`flex items-center justify-between p-3 ${bgColor} ${borderColor} border-b`}>
      <div className="flex items-center gap-3">
        <div className={`w-8 h-8 rounded-full ${color} flex items-center justify-center`}>
          <Icon className="w-4 h-4 text-white" />
        </div>
        <span className="font-semibold capitalize">{status.replace("_", " ")}</span>
      </div>
      <Badge variant="secondary" className="font-mono">{count}</Badge>
    </div>
  );

  return (
    <Card className="border border-border animate-fade-in" data-testid="sdc-directory">
      <CardHeader className="pb-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <CardTitle className="font-heading text-lg flex items-center gap-2">
            <Building2 className="w-5 h-5" />
            SDC Directory
          </CardTitle>
          
          <div className="flex items-center gap-2">
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input
                placeholder="Search SDCs..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9 w-48"
                data-testid="sdc-search"
              />
            </div>

            {/* Filter Dropdown */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="sm">
                  <Filter className="w-4 h-4 mr-1" />
                  Filter
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => setFilterBy("all")}>
                  All SDCs
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => setFilterBy("location")}>
                  By Location
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => setFilterBy("capability")}>
                  By Capability
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>

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
      </CardHeader>
      
      <CardContent className="p-0">
        {/* Available Group */}
        <Accordion type="multiple" defaultValue={["available", "engaged"]} className="w-full">
          <AccordionItem value="available" className="border-0">
            <AccordionTrigger className="px-0 py-0 hover:no-underline">
              <GroupHeader 
                status="Available" 
                count={groupedSDCs.available.length}
                icon={CheckCircle}
                color="bg-emerald-500"
                bgColor="bg-emerald-50"
                borderColor="border-emerald-200"
              />
            </AccordionTrigger>
            <AccordionContent className="pb-0">
              {groupedSDCs.available.length > 0 ? (
                groupedSDCs.available.map(sdc => (
                  <SDCRow key={sdc.sdc_id} sdc={sdc} status="available" />
                ))
              ) : (
                <div className="p-4 text-center text-muted-foreground text-sm">
                  No available SDCs
                </div>
              )}
            </AccordionContent>
          </AccordionItem>

          <AccordionItem value="engaged" className="border-0">
            <AccordionTrigger className="px-0 py-0 hover:no-underline">
              <GroupHeader 
                status="Engaged / Busy" 
                count={groupedSDCs.engaged.length}
                icon={Activity}
                color="bg-amber-500"
                bgColor="bg-amber-50"
                borderColor="border-amber-200"
              />
            </AccordionTrigger>
            <AccordionContent className="pb-0">
              {groupedSDCs.engaged.length > 0 ? (
                groupedSDCs.engaged.map(sdc => (
                  <SDCRow key={sdc.sdc_id} sdc={sdc} status="engaged" />
                ))
              ) : (
                <div className="p-4 text-center text-muted-foreground text-sm">
                  No SDCs currently engaged
                </div>
              )}
            </AccordionContent>
          </AccordionItem>

          <AccordionItem value="inactive" className="border-0">
            <AccordionTrigger className="px-0 py-0 hover:no-underline">
              <GroupHeader 
                status="Inactive / Maintenance" 
                count={groupedSDCs.inactive.length}
                icon={Wrench}
                color="bg-red-500"
                bgColor="bg-red-50"
                borderColor="border-red-200"
              />
            </AccordionTrigger>
            <AccordionContent className="pb-0">
              {groupedSDCs.inactive.length > 0 ? (
                groupedSDCs.inactive.map(sdc => (
                  <SDCRow key={sdc.sdc_id} sdc={sdc} status="inactive" />
                ))
              ) : (
                <div className="p-4 text-center text-muted-foreground text-sm">
                  No inactive SDCs
                </div>
              )}
            </AccordionContent>
          </AccordionItem>
        </Accordion>

        {(!sdcSummaries || sdcSummaries.length === 0) && (
          <div className="p-8 text-center text-muted-foreground">
            <Building2 className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>No SDCs found. {user?.role === "ho" ? "Create a Work Order to get started." : "Contact your administrator."}</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

// SDC Status Metrics Component
const SDCStatusMetrics = ({ sdcSummaries }) => {
  // Calculate SDC status counts based on work orders and activity
  const totalRegistered = sdcSummaries?.length || 0;
  
  // Active & Available: SDCs with no active work orders or completed all
  const activeAvailable = sdcSummaries?.filter(sdc => {
    const hasActiveWO = sdc.work_orders_count > 0;
    const placementComplete = sdc.progress?.placement?.completed > 0;
    return !hasActiveWO || (placementComplete && sdc.progress?.placement?.completed >= sdc.progress?.placement?.target);
  }).length || 0;
  
  // Engaged/Busy: SDCs with active work orders in progress
  const engagedBusy = sdcSummaries?.filter(sdc => {
    const hasActiveWO = sdc.work_orders_count > 0;
    const mobilized = sdc.progress?.mobilization?.completed || 0;
    const placed = sdc.progress?.placement?.completed || 0;
    const target = sdc.progress?.mobilization?.target || 0;
    return hasActiveWO && mobilized > 0 && (placed < target);
  }).length || 0;
  
  // Inactive/Maintenance: SDCs with no progress or overdue
  const inactiveMaintenance = sdcSummaries?.filter(sdc => {
    const hasActiveWO = sdc.work_orders_count > 0;
    const mobilized = sdc.progress?.mobilization?.completed || 0;
    const isOverdue = sdc.overdue_count > 0;
    return (hasActiveWO && mobilized === 0) || isOverdue;
  }).length || 0;

  return (
    <Card className="mb-8 border border-border animate-fade-in" data-testid="sdc-status-metrics">
      <CardHeader className="pb-2">
        <CardTitle className="font-heading text-base flex items-center gap-2">
          <Building2 className="w-5 h-5" />
          SDC Status Overview
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {/* Total Registered - Blue */}
          <div className="p-4 rounded-lg bg-blue-50 border border-blue-200">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 rounded-full bg-blue-500 flex items-center justify-center">
                <FolderOpen className="w-5 h-5 text-white" />
              </div>
              <div>
                <div className="font-mono font-bold text-2xl text-blue-700">{totalRegistered}</div>
              </div>
            </div>
            <div className="text-sm font-medium text-blue-800">Total Registered</div>
            <div className="text-xs text-blue-600">Total SDCs in ecosystem</div>
          </div>

          {/* Active & Available - Green */}
          <div className="p-4 rounded-lg bg-emerald-50 border border-emerald-200">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 rounded-full bg-emerald-500 flex items-center justify-center">
                <CheckCircle className="w-5 h-5 text-white" />
              </div>
              <div>
                <div className="font-mono font-bold text-2xl text-emerald-700">{activeAvailable}</div>
              </div>
            </div>
            <div className="text-sm font-medium text-emerald-800">Active & Available</div>
            <div className="text-xs text-emerald-600">Ready for new assignments</div>
          </div>

          {/* Engaged/Busy - Amber */}
          <div className="p-4 rounded-lg bg-amber-50 border border-amber-200">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 rounded-full bg-amber-500 flex items-center justify-center">
                <Activity className="w-5 h-5 text-white" />
              </div>
              <div>
                <div className="font-mono font-bold text-2xl text-amber-700">{engagedBusy}</div>
              </div>
            </div>
            <div className="text-sm font-medium text-amber-800">Engaged / Busy</div>
            <div className="text-xs text-amber-600">Currently executing tasks</div>
          </div>

          {/* Inactive/Maintenance - Red */}
          <div className="p-4 rounded-lg bg-red-50 border border-red-200">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 rounded-full bg-red-500 flex items-center justify-center">
                <Wrench className="w-5 h-5 text-white" />
              </div>
              <div>
                <div className="font-mono font-bold text-2xl text-red-700">{inactiveMaintenance}</div>
              </div>
            </div>
            <div className="text-sm font-medium text-red-800">Inactive / Maintenance</div>
            <div className="text-xs text-red-600">Offline or needs attention</div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

// Burn-down Dashboard Component
const BurndownDashboard = () => {
  const [burndownData, setBurndownData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedWO, setSelectedWO] = useState(null);

  useEffect(() => {
    const fetchBurndown = async () => {
      try {
        const response = await axios.get(`${API}/ledger/burndown`);
        setBurndownData(response.data);
      } catch (error) {
        console.error("Error fetching burndown data:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchBurndown();
  }, []);

  if (loading) {
    return (
      <Card className="mb-8 border border-border animate-fade-in">
        <CardContent className="p-6">
          <Skeleton className="h-32 w-full" />
        </CardContent>
      </Card>
    );
  }

  if (!burndownData || burndownData.work_orders?.length === 0) {
    return null; // Don't show if no data
  }

  const { overall, work_orders } = burndownData;
  const displayData = selectedWO 
    ? work_orders.find(wo => wo.master_wo_id === selectedWO) 
    : {
        pipeline: {
          unallocated: overall?.total_unallocated || 0,
          mobilized: overall?.total_mobilized || 0,
          placed: overall?.total_placed || 0,
          in_training: (overall?.total_mobilized || 0) - (overall?.total_placed || 0)
        },
        total_target: overall?.total_target || 0,
        summary: {
          total_allocated: overall?.total_allocated || 0,
          total_mobilized: overall?.total_mobilized || 0,
          total_placed: overall?.total_placed || 0,
          completion_percent: overall?.overall_completion || 0
        }
      };

  // Calculate pipeline stages for visualization
  const pipelineStages = [
    { id: "unallocated", name: "Unallocated", value: displayData?.pipeline?.unallocated || 0, color: "bg-gray-400" },
    { id: "allocated", name: "Allocated", value: (displayData?.summary?.total_allocated || 0) - (displayData?.pipeline?.mobilized || 0), color: "bg-blue-400" },
    { id: "mobilized", name: "Mobilized", value: displayData?.pipeline?.awaiting_training || displayData?.pipeline?.mobilized || 0, color: "bg-amber-500" },
    { id: "training", name: "In Training", value: displayData?.pipeline?.in_training || 0, color: "bg-indigo-500" },
    { id: "placed", name: "Placed", value: displayData?.summary?.total_placed || 0, color: "bg-emerald-500" }
  ];

  const totalTarget = displayData?.total_target || overall?.total_target || 1;

  return (
    <Card className="mb-8 border border-border animate-fade-in" data-testid="burndown-dashboard">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="font-heading text-base flex items-center gap-2">
            <BarChart3 className="w-5 h-5" />
            Work Order Burn-down
          </CardTitle>
          <div className="flex items-center gap-2">
            <select
              className="text-sm border rounded-md px-2 py-1 bg-background"
              value={selectedWO || ""}
              onChange={(e) => setSelectedWO(e.target.value || null)}
            >
              <option value="">All Work Orders</option>
              {work_orders?.map(wo => (
                <option key={wo.master_wo_id} value={wo.master_wo_id}>
                  {wo.work_order_number}
                </option>
              ))}
            </select>
            <Badge variant="outline" className="font-mono">
              {displayData?.summary?.completion_percent || 0}% Complete
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {/* Pipeline Visualization */}
        <div className="mb-6">
          <div className="flex h-8 rounded-lg overflow-hidden">
            {pipelineStages.map((stage, idx) => {
              const width = totalTarget > 0 ? (stage.value / totalTarget) * 100 : 0;
              if (width === 0) return null;
              return (
                <div
                  key={stage.id}
                  className={`${stage.color} flex items-center justify-center text-xs text-white font-medium transition-all`}
                  style={{ width: `${Math.max(width, 5)}%` }}
                  title={`${stage.name}: ${stage.value}`}
                >
                  {width > 10 && stage.value}
                </div>
              );
            })}
          </div>
          {/* Legend */}
          <div className="flex flex-wrap gap-4 mt-3 text-xs">
            {pipelineStages.map(stage => (
              <div key={stage.id} className="flex items-center gap-1">
                <div className={`w-3 h-3 rounded ${stage.color}`} />
                <span className="text-muted-foreground">{stage.name}:</span>
                <span className="font-mono font-medium">{stage.value}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Summary Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-3 rounded-lg bg-gray-50 border border-gray-200 text-center">
            <div className="font-mono font-bold text-xl text-gray-700">
              {displayData?.pipeline?.unallocated || 0}
            </div>
            <div className="text-xs text-gray-600">Unallocated</div>
          </div>
          <div className="p-3 rounded-lg bg-amber-50 border border-amber-200 text-center">
            <div className="font-mono font-bold text-xl text-amber-700">
              {displayData?.summary?.total_mobilized || 0}
            </div>
            <div className="text-xs text-amber-600">Mobilized</div>
          </div>
          <div className="p-3 rounded-lg bg-indigo-50 border border-indigo-200 text-center">
            <div className="font-mono font-bold text-xl text-indigo-700">
              {displayData?.pipeline?.in_training || 0}
            </div>
            <div className="text-xs text-indigo-600">In Training</div>
          </div>
          <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-center">
            <div className="font-mono font-bold text-xl text-emerald-700">
              {displayData?.summary?.total_placed || 0}
            </div>
            <div className="text-xs text-emerald-600">Placed</div>
          </div>
        </div>

        {/* Target Progress */}
        <div className="mt-4 pt-4 border-t border-border">
          <div className="flex justify-between text-sm mb-2">
            <span className="text-muted-foreground">Overall Target Progress</span>
            <span className="font-mono">
              {displayData?.summary?.total_placed || 0} / {totalTarget} placed
            </span>
          </div>
          <Progress 
            value={(displayData?.summary?.total_placed || 0) / totalTarget * 100} 
            className="h-2" 
          />
        </div>
      </CardContent>
    </Card>
  );
};

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
