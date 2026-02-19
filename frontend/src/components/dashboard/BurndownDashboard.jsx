import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "@/App";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { BarChart3 } from "lucide-react";

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
            {pipelineStages.map((stage) => {
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

export default BurndownDashboard;
