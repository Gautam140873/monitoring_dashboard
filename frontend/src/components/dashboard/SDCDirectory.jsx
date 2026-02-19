import { useState } from "react";
import { 
  Building2, 
  AlertTriangle, 
  ChevronRight,
  ChevronDown,
  Plus,
  Search,
  Filter,
  MapPin,
  Zap,
  Eye,
  CheckCircle,
  Activity,
  Wrench
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { 
  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuTrigger 
} from "@/components/ui/dropdown-menu";
import {
  Dialog,
  DialogContent,
  DialogTrigger,
} from "@/components/ui/dialog";
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
import NewWorkOrderForm from "./NewWorkOrderForm";

// SDC Directory Component - Accordion Style
const SDCDirectory = ({ sdcSummaries, onViewSDC, user, showWorkOrderDialog, setShowWorkOrderDialog, fetchDashboardData, navigate }) => {
  const [searchQuery, setSearchQuery] = useState("");
  const [filterBy, setFilterBy] = useState("all");

  // Categorize SDCs by status
  const categorizeSDC = (sdc) => {
    const hasActiveWO = sdc.work_orders_count > 0;
    const mobilized = sdc.progress?.mobilization?.completed || 0;
    const placed = sdc.progress?.placement?.completed || 0;
    const target = sdc.progress?.mobilization?.target || 0;
    const isOverdue = sdc.overdue_count > 0;

    if ((hasActiveWO && mobilized === 0) || isOverdue) {
      return "inactive";
    }
    
    if (hasActiveWO && mobilized > 0 && (placed < target)) {
      return "engaged";
    }
    
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

export default SDCDirectory;
