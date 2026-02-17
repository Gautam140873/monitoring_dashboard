import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { API } from "@/App";
import { toast } from "sonner";
import { 
  ArrowLeft, 
  DollarSign,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  Building2,
  FileText,
  CheckCircle,
  Clock,
  Download
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

export default function FinancialControl({ user }) {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [dashboardData, setDashboardData] = useState(null);
  const [invoices, setInvoices] = useState([]);
  const [sdcs, setSdcs] = useState([]);

  useEffect(() => {
    if (user?.role !== "ho") {
      toast.error("Access denied - HO only");
      navigate("/dashboard");
      return;
    }

    const fetchData = async () => {
      try {
        const [dashboardRes, invoicesRes, sdcsRes] = await Promise.all([
          axios.get(`${API}/dashboard/overview`),
          axios.get(`${API}/invoices`),
          axios.get(`${API}/sdcs`)
        ]);
        setDashboardData(dashboardRes.data);
        setInvoices(invoicesRes.data);
        setSdcs(sdcsRes.data);
      } catch (error) {
        console.error("Error fetching data:", error);
        toast.error("Failed to load financial data");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [user, navigate]);

  const handlePaymentUpdate = async (invoiceId, newStatus) => {
    try {
      await axios.put(`${API}/invoices/${invoiceId}`, {
        status: newStatus,
        payment_date: newStatus === "paid" ? new Date().toISOString().split("T")[0] : null
      });
      toast.success("Payment status updated");
      
      // Refresh invoices
      const invoicesRes = await axios.get(`${API}/invoices`);
      setInvoices(invoicesRes.data);
      
      // Refresh dashboard
      const dashboardRes = await axios.get(`${API}/dashboard/overview`);
      setDashboardData(dashboardRes.data);
    } catch (error) {
      console.error("Error updating payment:", error);
      toast.error("Failed to update payment");
    }
  };

  const handleExport = async (type) => {
    try {
      const response = await axios.get(`${API}/export/${type}`, {
        responseType: 'blob'
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${type}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success(`${type.replace('-', ' ')} exported successfully`);
    } catch (error) {
      console.error("Export error:", error);
      toast.error("Failed to export data");
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0
    }).format(value);
  };

  const getSDCName = (sdcId) => {
    const sdc = sdcs.find(s => s.sdc_id === sdcId);
    return sdc?.name || sdcId;
  };

  if (loading) {
    return <FinancialSkeleton />;
  }

  const { commercial_health, sdc_summaries } = dashboardData || {};
  const pendingInvoices = invoices.filter(inv => inv.status === "pending");
  const paidInvoices = invoices.filter(inv => inv.status === "paid");

  return (
    <div className="min-h-screen bg-background" data-testid="financial-control">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-background/95 backdrop-blur-sm border-b border-border">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" onClick={() => navigate("/dashboard")} data-testid="back-btn">
              <ArrowLeft className="w-5 h-5" />
            </Button>
            <div>
              <h1 className="font-heading font-bold text-xl">Financial Control</h1>
              <p className="text-sm text-muted-foreground">Commercial Health & Billing Management</p>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <Card className="border border-border animate-fade-in stagger-1">
            <CardContent className="p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 bg-slate-100 rounded-md flex items-center justify-center">
                  <DollarSign className="w-5 h-5 text-slate-700" />
                </div>
                <span className="text-sm text-muted-foreground">Total Portfolio</span>
              </div>
              <div className="font-mono font-bold text-2xl">{formatCurrency(commercial_health?.total_portfolio || 0)}</div>
            </CardContent>
          </Card>

          <Card className="border border-border animate-fade-in stagger-2">
            <CardContent className="p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 bg-blue-100 rounded-md flex items-center justify-center">
                  <FileText className="w-5 h-5 text-blue-700" />
                </div>
                <span className="text-sm text-muted-foreground">Actual Billed</span>
              </div>
              <div className="font-mono font-bold text-2xl">{formatCurrency(commercial_health?.actual_billed || 0)}</div>
            </CardContent>
          </Card>

          <Card className="border border-border animate-fade-in stagger-3">
            <CardContent className="p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className={`w-10 h-10 rounded-md flex items-center justify-center ${
                  (commercial_health?.outstanding || 0) > 0 ? 'bg-red-100' : 'bg-emerald-100'
                }`}>
                  <TrendingDown className={`w-5 h-5 ${
                    (commercial_health?.outstanding || 0) > 0 ? 'text-red-700' : 'text-emerald-700'
                  }`} />
                </div>
                <span className="text-sm text-muted-foreground">Outstanding</span>
              </div>
              <div className={`font-mono font-bold text-2xl ${
                (commercial_health?.outstanding || 0) > 0 ? 'text-red-600' : 'text-emerald-600'
              }`}>
                {formatCurrency(commercial_health?.outstanding || 0)}
              </div>
            </CardContent>
          </Card>

          <Card className="border border-border animate-fade-in stagger-4">
            <CardContent className="p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className={`w-10 h-10 rounded-md flex items-center justify-center ${
                  (commercial_health?.variance_percent || 0) > 10 ? 'bg-amber-100' : 'bg-emerald-100'
                }`}>
                  <TrendingUp className={`w-5 h-5 ${
                    (commercial_health?.variance_percent || 0) > 10 ? 'text-amber-700' : 'text-emerald-700'
                  }`} />
                </div>
                <span className="text-sm text-muted-foreground">Variance</span>
              </div>
              <div className="font-mono font-bold text-2xl">{commercial_health?.variance_percent || 0}%</div>
              <div className="text-sm text-muted-foreground font-mono">{formatCurrency(commercial_health?.variance || 0)}</div>
            </CardContent>
          </Card>
        </div>

        {/* SDC Financial Summary */}
        <Card className="mb-8 border border-border animate-fade-in" data-testid="sdc-financial-table">
          <CardHeader>
            <CardTitle className="font-heading">SDC Financial Summary</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="uppercase text-xs font-bold tracking-wider">SDC</TableHead>
                  <TableHead className="uppercase text-xs font-bold tracking-wider text-right">Portfolio</TableHead>
                  <TableHead className="uppercase text-xs font-bold tracking-wider text-right">Billed</TableHead>
                  <TableHead className="uppercase text-xs font-bold tracking-wider text-right">Paid</TableHead>
                  <TableHead className="uppercase text-xs font-bold tracking-wider text-right">Outstanding</TableHead>
                  <TableHead className="uppercase text-xs font-bold tracking-wider text-right">Variance</TableHead>
                  <TableHead className="uppercase text-xs font-bold tracking-wider">Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {sdc_summaries?.map((sdc) => {
                  const variancePercent = sdc.financial.portfolio > 0 
                    ? ((sdc.financial.variance / sdc.financial.portfolio) * 100).toFixed(1)
                    : 0;
                  const hasRisk = variancePercent > 10 || sdc.financial.outstanding > 0;

                  return (
                    <TableRow key={sdc.sdc_id} className="hover:bg-muted/50">
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Building2 className="w-4 h-4 text-muted-foreground" />
                          <span className="font-medium">{sdc.name}</span>
                        </div>
                      </TableCell>
                      <TableCell className="text-right font-mono">{formatCurrency(sdc.financial.portfolio)}</TableCell>
                      <TableCell className="text-right font-mono">{formatCurrency(sdc.financial.billed)}</TableCell>
                      <TableCell className="text-right font-mono text-emerald-600">{formatCurrency(sdc.financial.paid)}</TableCell>
                      <TableCell className={`text-right font-mono ${sdc.financial.outstanding > 0 ? 'text-red-600' : ''}`}>
                        {formatCurrency(sdc.financial.outstanding)}
                      </TableCell>
                      <TableCell className={`text-right font-mono ${variancePercent > 10 ? 'text-amber-600' : ''}`}>
                        {variancePercent}%
                      </TableCell>
                      <TableCell>
                        {hasRisk ? (
                          <Badge variant="destructive" className="bg-red-100 text-red-700 border-red-200">
                            <AlertTriangle className="w-3 h-3 mr-1" />
                            Risk
                          </Badge>
                        ) : (
                          <Badge className="bg-emerald-100 text-emerald-700 border-emerald-200">
                            <CheckCircle className="w-3 h-3 mr-1" />
                            Healthy
                          </Badge>
                        )}
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        {/* Pending Invoices */}
        <Card className="mb-8 border border-border animate-fade-in" data-testid="pending-invoices">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="font-heading">
              <div className="flex items-center gap-2">
                <Clock className="w-5 h-5 text-amber-600" />
                Pending Invoices ({pendingInvoices.length})
              </div>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="uppercase text-xs font-bold tracking-wider">Invoice #</TableHead>
                  <TableHead className="uppercase text-xs font-bold tracking-wider">SDC</TableHead>
                  <TableHead className="uppercase text-xs font-bold tracking-wider">Date</TableHead>
                  <TableHead className="uppercase text-xs font-bold tracking-wider text-right">Amount</TableHead>
                  <TableHead className="uppercase text-xs font-bold tracking-wider">Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {pendingInvoices.map((inv) => (
                  <TableRow key={inv.invoice_id} className="hover:bg-muted/50">
                    <TableCell className="font-mono text-sm">{inv.invoice_number}</TableCell>
                    <TableCell>{getSDCName(inv.sdc_id)}</TableCell>
                    <TableCell className="font-mono text-sm">{inv.invoice_date}</TableCell>
                    <TableCell className="text-right font-mono">{formatCurrency(inv.amount)}</TableCell>
                    <TableCell>
                      <Button 
                        size="sm" 
                        onClick={() => handlePaymentUpdate(inv.invoice_id, "paid")}
                        className="bg-emerald-600 hover:bg-emerald-700"
                        data-testid={`mark-paid-${inv.invoice_id}`}
                      >
                        <CheckCircle className="w-4 h-4 mr-1" />
                        Mark Paid
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
                {pendingInvoices.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={5} className="text-center py-8 text-muted-foreground">
                      No pending invoices
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        {/* Paid Invoices */}
        <Card className="border border-border animate-fade-in" data-testid="paid-invoices">
          <CardHeader>
            <CardTitle className="font-heading">
              <div className="flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-emerald-600" />
                Paid Invoices ({paidInvoices.length})
              </div>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="uppercase text-xs font-bold tracking-wider">Invoice #</TableHead>
                  <TableHead className="uppercase text-xs font-bold tracking-wider">SDC</TableHead>
                  <TableHead className="uppercase text-xs font-bold tracking-wider">Invoice Date</TableHead>
                  <TableHead className="uppercase text-xs font-bold tracking-wider text-right">Amount</TableHead>
                  <TableHead className="uppercase text-xs font-bold tracking-wider">Payment Date</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {paidInvoices.slice(0, 10).map((inv) => (
                  <TableRow key={inv.invoice_id} className="hover:bg-muted/50">
                    <TableCell className="font-mono text-sm">{inv.invoice_number}</TableCell>
                    <TableCell>{getSDCName(inv.sdc_id)}</TableCell>
                    <TableCell className="font-mono text-sm">{inv.invoice_date}</TableCell>
                    <TableCell className="text-right font-mono text-emerald-600">{formatCurrency(inv.amount)}</TableCell>
                    <TableCell className="font-mono text-sm">{inv.payment_date}</TableCell>
                  </TableRow>
                ))}
                {paidInvoices.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={5} className="text-center py-8 text-muted-foreground">
                      No paid invoices
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </main>
    </div>
  );
}

const FinancialSkeleton = () => (
  <div className="min-h-screen bg-background">
    <header className="border-b border-border">
      <div className="max-w-7xl mx-auto px-6 py-4">
        <Skeleton className="w-64 h-8" />
      </div>
    </header>
    <main className="max-w-7xl mx-auto px-6 py-8">
      <div className="grid grid-cols-4 gap-4 mb-8">
        {[1, 2, 3, 4].map(i => (
          <Skeleton key={i} className="h-32 rounded-md" />
        ))}
      </div>
      <Skeleton className="h-64 rounded-md mb-8" />
      <Skeleton className="h-64 rounded-md" />
    </main>
  </div>
);
