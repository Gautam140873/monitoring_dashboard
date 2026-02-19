import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { 
  Building2, 
  FolderOpen, 
  CheckCircle, 
  Activity, 
  Wrench 
} from "lucide-react";

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

export default SDCStatusMetrics;
