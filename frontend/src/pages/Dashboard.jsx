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
  Clock
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { 
  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuSeparator,
  DropdownMenuTrigger 
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Skeleton } from "@/components/ui/skeleton";

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

export default function Dashboard({ user }) {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [dashboardData, setDashboardData] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [refreshing, setRefreshing] = useState(false);

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
                <DropdownMenuItem onClick={() => navigate("/settings")} data-testid="settings-link">
                  <Settings className="w-4 h-4 mr-2" />
                  Settings
                </DropdownMenuItem>
                {user?.role === "ho" && (
                  <DropdownMenuItem onClick={() => navigate("/users")} data-testid="users-link">
                    <Users className="w-4 h-4 mr-2" />
                    User Management
                  </DropdownMenuItem>
                )}
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
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mb-8">
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

        {/* Training Roadmap Progress */}
        <Card className="mb-8 border border-border animate-fade-in" data-testid="roadmap-progress">
          <CardHeader className="pb-2">
            <CardTitle className="font-heading font-bold text-lg">Training Roadmap Progress</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
              {stage_progress && Object.entries(stage_progress).map(([stageId, stage]) => {
                const Icon = STAGE_ICONS[stageId] || Clock;
                const color = STAGE_COLORS[stageId] || "bg-slate-500";
                const percent = stage.target > 0 ? Math.round((stage.completed / stage.target) * 100) : 0;
                
                return (
                  <div key={stageId} className="text-center p-4 border border-border rounded-md">
                    <div className={`w-10 h-10 mx-auto mb-2 rounded-full ${color} flex items-center justify-center`}>
                      <Icon className="w-5 h-5 text-white" />
                    </div>
                    <div className="font-mono font-bold text-lg">{stage.completed}</div>
                    <div className="text-xs text-muted-foreground">{stage.name}</div>
                    <div className="mt-2 h-1.5 bg-muted rounded-full overflow-hidden">
                      <div 
                        className={`h-full ${color} transition-all duration-500`}
                        style={{ width: `${percent}%` }}
                      />
                    </div>
                    <div className="text-xs text-muted-foreground mt-1">{percent}%</div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* SDC Cards */}
        <div className="mb-4 flex items-center justify-between">
          <h2 className="font-heading font-bold text-xl">SDC Progress</h2>
          {user?.role === "ho" && (
            <Button 
              variant="outline" 
              onClick={() => navigate("/financial")}
              data-testid="financial-btn"
            >
              Financial Control
              <ChevronRight className="w-4 h-4 ml-1" />
            </Button>
          )}
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

        {/* Mini Progress - Training Stages */}
        <div className="flex h-2 rounded-full overflow-hidden bg-muted mb-4">
          {sdc.progress && Object.entries(sdc.progress).map(([stageId, data], i) => {
            const color = STAGE_COLORS[stageId] || "bg-slate-400";
            const width = data.target > 0 ? (data.completed / data.target) * (100 / 7) : 0;
            return (
              <div 
                key={stageId}
                className={color}
                style={{ width: `${width}%` }}
                title={`${stageId}: ${data.completed}/${data.target}`}
              />
            );
          })}
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
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-8">
        {[1, 2, 3, 4, 5].map(i => (
          <Skeleton key={i} className="h-28 rounded-md" />
        ))}
      </div>
      <Skeleton className="h-48 rounded-md mb-8" />
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {[1, 2, 3].map(i => (
          <Skeleton key={i} className="h-64 rounded-md" />
        ))}
      </div>
    </main>
  </div>
);
