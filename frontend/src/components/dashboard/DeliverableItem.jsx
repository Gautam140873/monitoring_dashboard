import { CheckCircle } from "lucide-react";

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

export default DeliverableItem;
