import { useState, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import axios from "axios";
import { API } from "@/App";
import { toast } from "sonner";
import { 
  ArrowLeft, 
  Building2,
  Plus,
  Calendar,
  Trash2,
  Database,
  AlertTriangle,
  RefreshCw,
  Mail,
  CheckCircle2,
  Send,
  ExternalLink
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogDescription,
} from "@/components/ui/dialog";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

export default function Settings({ user }) {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [loading, setLoading] = useState(true);
  const [sdcs, setSdcs] = useState([]);
  const [holidays, setHolidays] = useState([]);
  const [showSDCDialog, setShowSDCDialog] = useState(false);
  const [showHolidayDialog, setShowHolidayDialog] = useState(false);
  const [seeding, setSeeding] = useState(false);
  const [generatingAlerts, setGeneratingAlerts] = useState(false);
  
  // Gmail state
  const [gmailStatus, setGmailStatus] = useState({ connected: false });
  const [connectingGmail, setConnectingGmail] = useState(false);
  const [showEmailDialog, setShowEmailDialog] = useState(false);
  const [emailLogs, setEmailLogs] = useState([]);

  const fetchData = async () => {
    try {
      const promises = [
        axios.get(`${API}/sdcs`),
        axios.get(`${API}/holidays`)
      ];
      
      // Fetch Gmail status if HO
      if (user?.role === "ho") {
        promises.push(axios.get(`${API}/gmail/status`).catch(() => ({ data: { connected: false } })));
        promises.push(axios.get(`${API}/email-logs`).catch(() => ({ data: [] })));
      }
      
      const results = await Promise.all(promises);
      setSdcs(results[0].data);
      setHolidays(results[1].data);
      
      if (user?.role === "ho") {
        setGmailStatus(results[2].data);
        setEmailLogs(results[3].data || []);
      }
    } catch (error) {
      console.error("Error fetching data:", error);
      toast.error("Failed to load settings data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    
    // Check for Gmail connection status from URL params
    const gmailParam = searchParams.get("gmail");
    if (gmailParam === "connected") {
      toast.success("Gmail connected successfully!");
      setGmailStatus({ connected: true });
    } else if (gmailParam === "error") {
      toast.error("Failed to connect Gmail. Please try again.");
    }
  }, [searchParams]);

  const handleConnectGmail = async () => {
    setConnectingGmail(true);
    try {
      const response = await axios.get(`${API}/gmail/auth`);
      // Redirect to Google OAuth
      window.location.href = response.data.authorization_url;
    } catch (error) {
      console.error("Error starting Gmail auth:", error);
      toast.error("Failed to start Gmail authorization");
      setConnectingGmail(false);
    }
  };

  const handleSeedData = async () => {
    if (user?.role !== "ho") {
      toast.error("HO access required");
      return;
    }
    
    setSeeding(true);
    try {
      await axios.post(`${API}/seed-data`);
      toast.success("Sample data seeded successfully!");
      fetchData();
    } catch (error) {
      console.error("Error seeding data:", error);
      toast.error("Failed to seed data");
    } finally {
      setSeeding(false);
    }
  };

  const handleGenerateAlerts = async () => {
    if (user?.role !== "ho") {
      toast.error("HO access required");
      return;
    }
    
    setGeneratingAlerts(true);
    try {
      const response = await axios.post(`${API}/alerts/generate`);
      toast.success(`Generated ${response.data.alerts?.length || 0} alerts`);
    } catch (error) {
      console.error("Error generating alerts:", error);
      toast.error("Failed to generate alerts");
    } finally {
      setGeneratingAlerts(false);
    }
  };

  const handleDeleteSDC = async (sdcId) => {
    try {
      await axios.delete(`${API}/sdcs/${sdcId}`);
      toast.success("SDC deleted successfully");
      fetchData();
    } catch (error) {
      console.error("Error deleting SDC:", error);
      toast.error("Failed to delete SDC");
    }
  };

  const handleDeleteHoliday = async (holidayId) => {
    try {
      await axios.delete(`${API}/holidays/${holidayId}`);
      toast.success("Holiday deleted successfully");
      fetchData();
    } catch (error) {
      console.error("Error deleting holiday:", error);
      toast.error("Failed to delete holiday");
    }
  };

  if (loading) {
    return <SettingsSkeleton />;
  }

  return (
    <div className="min-h-screen bg-background" data-testid="settings-page">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-background/95 backdrop-blur-sm border-b border-border">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" onClick={() => navigate("/dashboard")} data-testid="back-btn">
              <ArrowLeft className="w-5 h-5" />
            </Button>
            <div>
              <h1 className="font-heading font-bold text-xl">Settings</h1>
              <p className="text-sm text-muted-foreground">Manage SDCs, holidays, and system data</p>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        <Tabs defaultValue="sdcs" className="animate-fade-in">
          <TabsList className="mb-6">
            <TabsTrigger value="sdcs" data-testid="tab-sdcs">SDCs</TabsTrigger>
            <TabsTrigger value="holidays" data-testid="tab-holidays">Holidays</TabsTrigger>
            <TabsTrigger value="system" data-testid="tab-system">System</TabsTrigger>
          </TabsList>

          {/* SDCs Tab */}
          <TabsContent value="sdcs">
            <Card className="border border-border">
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle className="font-heading">Skill Development Centers</CardTitle>
                  <CardDescription>Manage SDC locations</CardDescription>
                </div>
                {user?.role === "ho" && (
                  <Dialog open={showSDCDialog} onOpenChange={setShowSDCDialog}>
                    <DialogTrigger asChild>
                      <Button data-testid="add-sdc-btn">
                        <Plus className="w-4 h-4 mr-2" />
                        Add SDC
                      </Button>
                    </DialogTrigger>
                    <DialogContent>
                      <AddSDCForm onSuccess={() => {
                        setShowSDCDialog(false);
                        fetchData();
                      }} />
                    </DialogContent>
                  </Dialog>
                )}
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="uppercase text-xs font-bold tracking-wider">SDC ID</TableHead>
                      <TableHead className="uppercase text-xs font-bold tracking-wider">Name</TableHead>
                      <TableHead className="uppercase text-xs font-bold tracking-wider">Location</TableHead>
                      {user?.role === "ho" && (
                        <TableHead className="uppercase text-xs font-bold tracking-wider">Actions</TableHead>
                      )}
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {sdcs.map((sdc) => (
                      <TableRow key={sdc.sdc_id} className="hover:bg-muted/50">
                        <TableCell className="font-mono text-sm">{sdc.sdc_id}</TableCell>
                        <TableCell className="font-medium">{sdc.name}</TableCell>
                        <TableCell className="text-muted-foreground">{sdc.location}</TableCell>
                        {user?.role === "ho" && (
                          <TableCell>
                            <AlertDialog>
                              <AlertDialogTrigger asChild>
                                <Button variant="ghost" size="sm" className="text-red-600 hover:text-red-700 hover:bg-red-50">
                                  <Trash2 className="w-4 h-4" />
                                </Button>
                              </AlertDialogTrigger>
                              <AlertDialogContent>
                                <AlertDialogHeader>
                                  <AlertDialogTitle>Delete SDC?</AlertDialogTitle>
                                  <AlertDialogDescription>
                                    This will permanently delete {sdc.name} and all associated data including job roles, batches, and invoices.
                                  </AlertDialogDescription>
                                </AlertDialogHeader>
                                <AlertDialogFooter>
                                  <AlertDialogCancel>Cancel</AlertDialogCancel>
                                  <AlertDialogAction 
                                    onClick={() => handleDeleteSDC(sdc.sdc_id)}
                                    className="bg-red-600 hover:bg-red-700"
                                  >
                                    Delete
                                  </AlertDialogAction>
                                </AlertDialogFooter>
                              </AlertDialogContent>
                            </AlertDialog>
                          </TableCell>
                        )}
                      </TableRow>
                    ))}
                    {sdcs.length === 0 && (
                      <TableRow>
                        <TableCell colSpan={user?.role === "ho" ? 4 : 3} className="text-center py-8 text-muted-foreground">
                          No SDCs found. {user?.role === "ho" && "Click 'Add SDC' to create one."}
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Holidays Tab */}
          <TabsContent value="holidays">
            <Card className="border border-border">
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle className="font-heading">Public Holidays</CardTitle>
                  <CardDescription>Holidays are excluded from training end date calculations</CardDescription>
                </div>
                {user?.role === "ho" && (
                  <Dialog open={showHolidayDialog} onOpenChange={setShowHolidayDialog}>
                    <DialogTrigger asChild>
                      <Button data-testid="add-holiday-btn">
                        <Plus className="w-4 h-4 mr-2" />
                        Add Holiday
                      </Button>
                    </DialogTrigger>
                    <DialogContent>
                      <AddHolidayForm onSuccess={() => {
                        setShowHolidayDialog(false);
                        fetchData();
                      }} />
                    </DialogContent>
                  </Dialog>
                )}
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="uppercase text-xs font-bold tracking-wider">Date</TableHead>
                      <TableHead className="uppercase text-xs font-bold tracking-wider">Name</TableHead>
                      <TableHead className="uppercase text-xs font-bold tracking-wider">Year</TableHead>
                      {user?.role === "ho" && (
                        <TableHead className="uppercase text-xs font-bold tracking-wider">Actions</TableHead>
                      )}
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {holidays.map((holiday) => (
                      <TableRow key={holiday.holiday_id} className="hover:bg-muted/50">
                        <TableCell className="font-mono text-sm">{holiday.date}</TableCell>
                        <TableCell className="font-medium">{holiday.name}</TableCell>
                        <TableCell className="font-mono">{holiday.year}</TableCell>
                        {user?.role === "ho" && (
                          <TableCell>
                            <Button 
                              variant="ghost" 
                              size="sm" 
                              className="text-red-600 hover:text-red-700 hover:bg-red-50"
                              onClick={() => handleDeleteHoliday(holiday.holiday_id)}
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </TableCell>
                        )}
                      </TableRow>
                    ))}
                    {holidays.length === 0 && (
                      <TableRow>
                        <TableCell colSpan={user?.role === "ho" ? 4 : 3} className="text-center py-8 text-muted-foreground">
                          No holidays found. {user?.role === "ho" && "Click 'Add Holiday' to create one."}
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          {/* System Tab */}
          <TabsContent value="system">
            <div className="grid gap-6">
              {user?.role === "ho" && (
                <>
                  <Card className="border border-border">
                    <CardHeader>
                      <CardTitle className="font-heading flex items-center gap-2">
                        <Database className="w-5 h-5" />
                        Sample Data
                      </CardTitle>
                      <CardDescription>
                        Seed the database with sample SDCs, job roles, batches, and invoices for demo purposes.
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <Button 
                        onClick={handleSeedData} 
                        disabled={seeding}
                        data-testid="seed-data-btn"
                      >
                        {seeding ? (
                          <>
                            <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                            Seeding...
                          </>
                        ) : (
                          <>
                            <Database className="w-4 h-4 mr-2" />
                            Seed Sample Data
                          </>
                        )}
                      </Button>
                      <p className="text-xs text-muted-foreground mt-2">
                        Warning: This will replace all existing data.
                      </p>
                    </CardContent>
                  </Card>

                  <Card className="border border-border">
                    <CardHeader>
                      <CardTitle className="font-heading flex items-center gap-2">
                        <AlertTriangle className="w-5 h-5" />
                        Risk Alerts
                      </CardTitle>
                      <CardDescription>
                        Generate risk alerts based on current data (overdue batches, billing variance > 10%).
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <Button 
                        onClick={handleGenerateAlerts} 
                        disabled={generatingAlerts}
                        variant="outline"
                        data-testid="generate-alerts-btn"
                      >
                        {generatingAlerts ? (
                          <>
                            <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                            Generating...
                          </>
                        ) : (
                          <>
                            <AlertTriangle className="w-4 h-4 mr-2" />
                            Generate Alerts
                          </>
                        )}
                      </Button>
                    </CardContent>
                  </Card>
                </>
              )}

              <Card className="border border-border">
                <CardHeader>
                  <CardTitle className="font-heading">Account Info</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between py-2 border-b border-border">
                    <span className="text-muted-foreground">Email</span>
                    <span className="font-mono text-sm">{user?.email}</span>
                  </div>
                  <div className="flex items-center justify-between py-2 border-b border-border">
                    <span className="text-muted-foreground">Role</span>
                    <Badge variant={user?.role === "ho" ? "default" : "secondary"}>
                      {user?.role === "ho" ? "Head Office" : "SDC"}
                    </Badge>
                  </div>
                  {user?.assigned_sdc_id && (
                    <div className="flex items-center justify-between py-2 border-b border-border">
                      <span className="text-muted-foreground">Assigned SDC</span>
                      <span className="font-mono text-sm">{user.assigned_sdc_id}</span>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}

// Add SDC Form
const AddSDCForm = ({ onSuccess }) => {
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    location: ""
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await axios.post(`${API}/sdcs`, formData);
      toast.success("SDC created successfully");
      onSuccess();
    } catch (error) {
      console.error("Error creating SDC:", error);
      toast.error("Failed to create SDC");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <DialogHeader>
        <DialogTitle>Add New SDC</DialogTitle>
        <DialogDescription>Create a new Skill Development Center</DialogDescription>
      </DialogHeader>
      <form onSubmit={handleSubmit} className="space-y-4 mt-4">
        <div>
          <Label>Name</Label>
          <Input 
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            placeholder="SDC Mumbai"
            required
          />
        </div>
        <div>
          <Label>Location</Label>
          <Input 
            value={formData.location}
            onChange={(e) => setFormData({ ...formData, location: e.target.value })}
            placeholder="Mumbai, Maharashtra"
            required
          />
        </div>
        <Button type="submit" className="w-full" disabled={loading}>
          {loading ? "Creating..." : "Create SDC"}
        </Button>
      </form>
    </>
  );
};

// Add Holiday Form
const AddHolidayForm = ({ onSuccess }) => {
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    date: "",
    name: "",
    year: new Date().getFullYear()
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await axios.post(`${API}/holidays`, {
        ...formData,
        year: parseInt(formData.year)
      });
      toast.success("Holiday added successfully");
      onSuccess();
    } catch (error) {
      console.error("Error creating holiday:", error);
      toast.error("Failed to add holiday");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <DialogHeader>
        <DialogTitle>Add Holiday</DialogTitle>
        <DialogDescription>Add a public holiday to exclude from training calculations</DialogDescription>
      </DialogHeader>
      <form onSubmit={handleSubmit} className="space-y-4 mt-4">
        <div>
          <Label>Date</Label>
          <Input 
            type="date"
            value={formData.date}
            onChange={(e) => {
              const date = e.target.value;
              setFormData({ 
                ...formData, 
                date,
                year: date ? new Date(date).getFullYear() : formData.year
              });
            }}
            required
          />
        </div>
        <div>
          <Label>Holiday Name</Label>
          <Input 
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            placeholder="Republic Day"
            required
          />
        </div>
        <div>
          <Label>Year</Label>
          <Input 
            type="number"
            value={formData.year}
            onChange={(e) => setFormData({ ...formData, year: e.target.value })}
            min="2020"
            max="2030"
            required
          />
        </div>
        <Button type="submit" className="w-full" disabled={loading}>
          {loading ? "Adding..." : "Add Holiday"}
        </Button>
      </form>
    </>
  );
};

const SettingsSkeleton = () => (
  <div className="min-h-screen bg-background">
    <header className="border-b border-border">
      <div className="max-w-7xl mx-auto px-6 py-4">
        <Skeleton className="w-64 h-8" />
      </div>
    </header>
    <main className="max-w-7xl mx-auto px-6 py-8">
      <Skeleton className="w-48 h-10 mb-6" />
      <Skeleton className="h-64 rounded-md" />
    </main>
  </div>
);
