import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { API } from "@/App";
import { toast } from "sonner";
import { 
  Building2, 
  AlertTriangle, 
  DollarSign,
  Users,
  RefreshCw,
  Bell,
  FileText,
  ClipboardList,
  Briefcase,
  GraduationCap,
  CheckCircle2,
  CheckCircle,
  Package,
  LogOut,
  Settings,
  Calendar as CalendarIcon,
  BarChart3
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

// Import extracted components
import {
  MetricCard,
  DeliverableItem,
  SDCStatusMetrics,
  BurndownDashboard,
  DashboardSkeleton,
  SDCDirectory
} from "@/components/dashboard";

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
            icon={<AlertTriangle className="w-5 h-5" />}
            trend={(commercial_health?.outstanding || 0) > 0 ? "warning" : "success"}
            className="animate-fade-in stagger-4"
            testId="outstanding-card"
          />
          <MetricCard
            title="Variance"
            value={`${commercial_health?.variance_percent || 0}%`}
            subtitle={formatCurrency(commercial_health?.variance || 0)}
            icon={<BarChart3 className="w-5 h-5" />}
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
                {processStages.map((stage) => {
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
                <DeliverableItem 
                  name="Dress Distribution"
                  icon={ClipboardList}
                  data={stage_progress?.dress_distribution}
                />
                <DeliverableItem 
                  name="Study Material"
                  icon={FileText}
                  data={stage_progress?.study_material}
                />
                <DeliverableItem 
                  name="ID Card"
                  icon={Users}
                  data={stage_progress?.mobilization}
                  label="Based on Mobilization"
                />
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
