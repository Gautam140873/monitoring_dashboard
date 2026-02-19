import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { API } from "@/App";
import { toast } from "sonner";
import {
  Building2,
  Users,
  Briefcase,
  ChevronLeft,
  ChevronRight,
  Calendar as CalendarIcon,
  MapPin,
  Phone,
  Mail,
  CheckCircle,
  Clock,
  AlertTriangle,
  Filter,
  RefreshCw,
  Eye,
  Unlock,
  ArrowLeft
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";

const RESOURCE_ICONS = {
  trainer: Users,
  manager: Briefcase,
  infrastructure: Building2
};

const STATUS_COLORS = {
  available: "bg-emerald-500",
  assigned: "bg-amber-500",
  in_use: "bg-amber-500",
  on_leave: "bg-gray-400",
  maintenance: "bg-red-500"
};

const STATUS_BG_COLORS = {
  available: "bg-emerald-50 border-emerald-200",
  assigned: "bg-amber-50 border-amber-200",
  in_use: "bg-amber-50 border-amber-200",
  on_leave: "bg-gray-50 border-gray-200",
  maintenance: "bg-red-50 border-red-200"
};

export default function ResourceCalendar({ user }) {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [calendarData, setCalendarData] = useState(null);
  const [selectedType, setSelectedType] = useState("all");
  const [selectedResource, setSelectedResource] = useState(null);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  const fetchCalendarData = async () => {
    try {
      const params = selectedType !== "all" ? { resource_type: selectedType } : {};
      const response = await axios.get(`${API}/ledger/resource/calendar`, { params });
      setCalendarData(response.data);
    } catch (error) {
      console.error("Error fetching calendar data:", error);
      toast.error("Failed to load resource calendar");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchCalendarData();
  }, [selectedType]);

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchCalendarData();
    toast.success("Calendar refreshed");
  };

  const handleReleaseResource = async (resourceType, resourceId) => {
    try {
      await axios.post(`${API}/ledger/resource/release/${resourceType}/${resourceId}`);
      toast.success("Resource released successfully");
      fetchCalendarData();
      setShowDetailDialog(false);
    } catch (error) {
      console.error("Error releasing resource:", error);
      toast.error(error.response?.data?.detail || "Failed to release resource");
    }
  };

  const handleViewResource = (resource) => {
    setSelectedResource(resource);
    setShowDetailDialog(true);
  };

  if (loading) {
    return <ResourceCalendarSkeleton />;
  }

  const { grouped, summary } = calendarData || {};

  return (
    <div className="min-h-screen bg-background" data-testid="resource-calendar">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-background/95 backdrop-blur-sm border-b border-border">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" onClick={() => navigate("/dashboard")}>
              <ArrowLeft className="w-5 h-5" />
            </Button>
            <div>
              <h1 className="font-heading font-bold text-xl">Resource Calendar</h1>
              <p className="text-sm text-muted-foreground">View resource availability and assignments</p>
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            <Select value={selectedType} onValueChange={setSelectedType}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Filter by type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Resources</SelectItem>
                <SelectItem value="trainer">Trainers</SelectItem>
                <SelectItem value="manager">Managers</SelectItem>
                <SelectItem value="infrastructure">Infrastructure</SelectItem>
              </SelectContent>
            </Select>
            
            <Button variant="outline" size="icon" onClick={handleRefresh} disabled={refreshing}>
              <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <SummaryCard
            title="Trainers"
            icon={Users}
            total={summary?.trainers?.total || 0}
            available={summary?.trainers?.available || 0}
            assigned={summary?.trainers?.assigned || 0}
            color="indigo"
          />
          <SummaryCard
            title="Managers"
            icon={Briefcase}
            total={summary?.managers?.total || 0}
            available={summary?.managers?.available || 0}
            assigned={summary?.managers?.assigned || 0}
            color="purple"
          />
          <SummaryCard
            title="Infrastructure"
            icon={Building2}
            total={summary?.infrastructure?.total || 0}
            available={summary?.infrastructure?.available || 0}
            assigned={summary?.infrastructure?.in_use || 0}
            color="amber"
          />
        </div>

        {/* Resource Tabs */}
        <Tabs defaultValue="trainers" className="w-full">
          <TabsList className="grid w-full grid-cols-3 mb-6">
            <TabsTrigger value="trainers" className="flex items-center gap-2">
              <Users className="w-4 h-4" />
              Trainers ({grouped?.trainers?.length || 0})
            </TabsTrigger>
            <TabsTrigger value="managers" className="flex items-center gap-2">
              <Briefcase className="w-4 h-4" />
              Managers ({grouped?.managers?.length || 0})
            </TabsTrigger>
            <TabsTrigger value="infrastructure" className="flex items-center gap-2">
              <Building2 className="w-4 h-4" />
              Infrastructure ({grouped?.infrastructure?.length || 0})
            </TabsTrigger>
          </TabsList>

          <TabsContent value="trainers">
            <ResourceGrid 
              resources={grouped?.trainers || []} 
              type="trainer"
              onView={handleViewResource}
            />
          </TabsContent>

          <TabsContent value="managers">
            <ResourceGrid 
              resources={grouped?.managers || []} 
              type="manager"
              onView={handleViewResource}
            />
          </TabsContent>

          <TabsContent value="infrastructure">
            <ResourceGrid 
              resources={grouped?.infrastructure || []} 
              type="infrastructure"
              onView={handleViewResource}
            />
          </TabsContent>
        </Tabs>
      </main>

      {/* Resource Detail Dialog */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              {selectedResource && (
                <>
                  {(() => {
                    const Icon = RESOURCE_ICONS[selectedResource.resource_type];
                    return <Icon className="w-5 h-5" />;
                  })()}
                  {selectedResource.name}
                </>
              )}
            </DialogTitle>
          </DialogHeader>
          
          {selectedResource && (
            <div className="space-y-4">
              {/* Status */}
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Status</span>
                <Badge className={`${STATUS_COLORS[selectedResource.status]} text-white`}>
                  {selectedResource.status.replace("_", " ").toUpperCase()}
                </Badge>
              </div>

              {/* Contact Info */}
              {selectedResource.email && (
                <div className="flex items-center gap-2 text-sm">
                  <Mail className="w-4 h-4 text-muted-foreground" />
                  <span>{selectedResource.email}</span>
                </div>
              )}
              {selectedResource.phone && (
                <div className="flex items-center gap-2 text-sm">
                  <Phone className="w-4 h-4 text-muted-foreground" />
                  <span>{selectedResource.phone}</span>
                </div>
              )}
              {selectedResource.specialization && (
                <div className="flex items-center gap-2 text-sm">
                  <MapPin className="w-4 h-4 text-muted-foreground" />
                  <span>{selectedResource.specialization}</span>
                </div>
              )}

              {/* Current Assignment */}
              {selectedResource.current_assignment && (
                <div className="p-4 rounded-lg bg-amber-50 border border-amber-200">
                  <h4 className="font-semibold text-amber-800 mb-2">Current Assignment</h4>
                  <div className="space-y-1 text-sm text-amber-700">
                    <div><strong>SDC:</strong> {selectedResource.current_assignment.sdc_name}</div>
                    {selectedResource.current_assignment.work_order_number && (
                      <div><strong>Work Order:</strong> {selectedResource.current_assignment.work_order_number}</div>
                    )}
                    {selectedResource.current_assignment.start_date && (
                      <div><strong>Start:</strong> {selectedResource.current_assignment.start_date}</div>
                    )}
                    {selectedResource.current_assignment.end_date && (
                      <div><strong>Expected End:</strong> {selectedResource.current_assignment.end_date}</div>
                    )}
                  </div>
                </div>
              )}

              {/* Booking History */}
              {selectedResource.booking_history && selectedResource.booking_history.length > 0 && (
                <div>
                  <h4 className="font-semibold mb-2">Recent Bookings</h4>
                  <div className="space-y-2 max-h-40 overflow-y-auto">
                    {selectedResource.booking_history.slice(0, 5).map((booking, idx) => (
                      <div key={idx} className="p-2 rounded bg-muted/50 text-sm">
                        <div className="flex items-center justify-between">
                          <span>SDC: {booking.sdc_id}</span>
                          <Badge variant="outline" className="text-xs">
                            {booking.status}
                          </Badge>
                        </div>
                        {booking.locked_at && (
                          <div className="text-xs text-muted-foreground">
                            Since: {new Date(booking.locked_at).toLocaleDateString()}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Actions */}
              <div className="flex justify-end gap-2 pt-4 border-t">
                {selectedResource.status === "assigned" || selectedResource.status === "in_use" ? (
                  <Button
                    variant="destructive"
                    onClick={() => handleReleaseResource(
                      selectedResource.resource_type,
                      selectedResource.resource_id
                    )}
                  >
                    <Unlock className="w-4 h-4 mr-1" />
                    Release Resource
                  </Button>
                ) : (
                  <Badge className="bg-emerald-500">Available for Assignment</Badge>
                )}
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

// Summary Card Component
const SummaryCard = ({ title, icon: Icon, total, available, assigned, color }) => {
  const colorClasses = {
    indigo: "bg-indigo-50 border-indigo-200 text-indigo-700",
    purple: "bg-purple-50 border-purple-200 text-purple-700",
    amber: "bg-amber-50 border-amber-200 text-amber-700"
  };

  const iconBgClasses = {
    indigo: "bg-indigo-500",
    purple: "bg-purple-500",
    amber: "bg-amber-500"
  };

  return (
    <Card className={`border ${colorClasses[color]}`}>
      <CardContent className="p-6">
        <div className="flex items-center justify-between mb-4">
          <div className={`w-12 h-12 rounded-lg ${iconBgClasses[color]} flex items-center justify-center`}>
            <Icon className="w-6 h-6 text-white" />
          </div>
          <div className="text-right">
            <div className="font-mono font-bold text-3xl">{total}</div>
            <div className="text-sm opacity-75">Total</div>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div className="text-center p-2 rounded-lg bg-white/50">
            <div className="font-mono font-bold text-lg text-emerald-600">{available}</div>
            <div className="text-xs">Available</div>
          </div>
          <div className="text-center p-2 rounded-lg bg-white/50">
            <div className="font-mono font-bold text-lg text-amber-600">{assigned}</div>
            <div className="text-xs">Assigned</div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

// Resource Grid Component
const ResourceGrid = ({ resources, type, onView }) => {
  if (resources.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        <Building2 className="w-12 h-12 mx-auto mb-4 opacity-50" />
        <p>No {type}s found</p>
      </div>
    );
  }

  // Group by status
  const available = resources.filter(r => r.status === "available");
  const assigned = resources.filter(r => r.status === "assigned" || r.status === "in_use");
  const other = resources.filter(r => !["available", "assigned", "in_use"].includes(r.status));

  return (
    <div className="space-y-6">
      {/* Available Resources */}
      {available.length > 0 && (
        <div>
          <h3 className="font-semibold text-emerald-700 mb-3 flex items-center gap-2">
            <CheckCircle className="w-4 h-4" />
            Available ({available.length})
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {available.map(resource => (
              <ResourceCard key={resource.resource_id} resource={resource} onView={onView} />
            ))}
          </div>
        </div>
      )}

      {/* Assigned Resources */}
      {assigned.length > 0 && (
        <div>
          <h3 className="font-semibold text-amber-700 mb-3 flex items-center gap-2">
            <Clock className="w-4 h-4" />
            Currently Assigned ({assigned.length})
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {assigned.map(resource => (
              <ResourceCard key={resource.resource_id} resource={resource} onView={onView} />
            ))}
          </div>
        </div>
      )}

      {/* Other Status */}
      {other.length > 0 && (
        <div>
          <h3 className="font-semibold text-gray-700 mb-3 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4" />
            Other Status ({other.length})
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {other.map(resource => (
              <ResourceCard key={resource.resource_id} resource={resource} onView={onView} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// Resource Card Component
const ResourceCard = ({ resource, onView }) => {
  const Icon = RESOURCE_ICONS[resource.resource_type];
  const statusBg = STATUS_BG_COLORS[resource.status] || "bg-gray-50 border-gray-200";
  const statusDot = STATUS_COLORS[resource.status] || "bg-gray-400";

  return (
    <Card 
      className={`border cursor-pointer hover:shadow-md transition-shadow ${statusBg}`}
      onClick={() => onView(resource)}
      data-testid={`resource-card-${resource.resource_id}`}
    >
      <CardContent className="p-4">
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 rounded-full ${statusDot} flex items-center justify-center`}>
              <Icon className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="font-semibold">{resource.name}</div>
              {resource.specialization && (
                <div className="text-xs text-muted-foreground">{resource.specialization}</div>
              )}
            </div>
          </div>
          <div className="relative">
            {resource.status === "available" ? (
              <span className="relative flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
              </span>
            ) : (
              <span className={`inline-flex rounded-full h-3 w-3 ${statusDot}`}></span>
            )}
          </div>
        </div>

        {/* Contact Info */}
        <div className="space-y-1 text-xs text-muted-foreground mb-3">
          {resource.email && (
            <div className="flex items-center gap-1 truncate">
              <Mail className="w-3 h-3" />
              {resource.email}
            </div>
          )}
          {resource.phone && (
            <div className="flex items-center gap-1">
              <Phone className="w-3 h-3" />
              {resource.phone}
            </div>
          )}
        </div>

        {/* Current Assignment */}
        {resource.current_assignment && (
          <div className="p-2 rounded bg-white/70 text-xs">
            <div className="font-medium text-amber-800">
              {resource.current_assignment.sdc_name}
            </div>
            {resource.current_assignment.end_date && (
              <div className="text-muted-foreground">
                Until: {resource.current_assignment.end_date}
              </div>
            )}
          </div>
        )}

        {/* Action */}
        <div className="mt-3 flex justify-end">
          <Button variant="ghost" size="sm" className="text-xs">
            <Eye className="w-3 h-3 mr-1" />
            Details
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

// Skeleton Loader
const ResourceCalendarSkeleton = () => (
  <div className="min-h-screen bg-background">
    <header className="border-b border-border">
      <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
        <Skeleton className="w-48 h-10" />
        <Skeleton className="w-32 h-10" />
      </div>
    </header>
    <main className="max-w-7xl mx-auto px-6 py-8">
      <div className="grid grid-cols-3 gap-6 mb-8">
        {[1, 2, 3].map(i => (
          <Skeleton key={i} className="h-40 rounded-lg" />
        ))}
      </div>
      <Skeleton className="h-12 mb-6" />
      <div className="grid grid-cols-3 gap-4">
        {[1, 2, 3, 4, 5, 6].map(i => (
          <Skeleton key={i} className="h-48 rounded-lg" />
        ))}
      </div>
    </main>
  </div>
);
