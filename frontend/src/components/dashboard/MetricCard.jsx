import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

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

export default MetricCard;
