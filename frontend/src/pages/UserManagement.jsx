import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { API } from "@/App";
import { toast } from "sonner";
import { 
  ArrowLeft, 
  Users,
  Shield,
  Building2
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
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

export default function UserManagement({ user }) {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [users, setUsers] = useState([]);
  const [sdcs, setSdcs] = useState([]);
  const [editingUser, setEditingUser] = useState(null);

  useEffect(() => {
    if (user?.role !== "ho") {
      toast.error("Access denied - HO only");
      navigate("/dashboard");
      return;
    }

    const fetchData = async () => {
      try {
        const [usersRes, sdcsRes] = await Promise.all([
          axios.get(`${API}/users`),
          axios.get(`${API}/sdcs`)
        ]);
        setUsers(usersRes.data);
        setSdcs(sdcsRes.data);
      } catch (error) {
        console.error("Error fetching data:", error);
        toast.error("Failed to load users");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [user, navigate]);

  const handleUpdateRole = async (userId, role, assignedSdcId) => {
    try {
      await axios.put(`${API}/users/${userId}/role`, {
        role,
        assigned_sdc_id: role === "sdc" ? assignedSdcId : null
      });
      toast.success("User role updated");
      
      // Refresh users
      const usersRes = await axios.get(`${API}/users`);
      setUsers(usersRes.data);
      setEditingUser(null);
    } catch (error) {
      console.error("Error updating role:", error);
      toast.error("Failed to update role");
    }
  };

  const getSDCName = (sdcId) => {
    const sdc = sdcs.find(s => s.sdc_id === sdcId);
    return sdc?.name || sdcId || "Not Assigned";
  };

  if (loading) {
    return <UserManagementSkeleton />;
  }

  return (
    <div className="min-h-screen bg-background" data-testid="user-management">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-background/95 backdrop-blur-sm border-b border-border">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" onClick={() => navigate("/dashboard")} data-testid="back-btn">
              <ArrowLeft className="w-5 h-5" />
            </Button>
            <div>
              <h1 className="font-heading font-bold text-xl">User Management</h1>
              <p className="text-sm text-muted-foreground">Manage user roles and SDC assignments</p>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        <Card className="border border-border animate-fade-in">
          <CardHeader>
            <CardTitle className="font-heading flex items-center gap-2">
              <Users className="w-5 h-5" />
              All Users ({users.length})
            </CardTitle>
            <CardDescription>
              Assign roles and SDC access to users. HO users have full access, SDC users only see their assigned center.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="uppercase text-xs font-bold tracking-wider">User</TableHead>
                  <TableHead className="uppercase text-xs font-bold tracking-wider">Email</TableHead>
                  <TableHead className="uppercase text-xs font-bold tracking-wider">Role</TableHead>
                  <TableHead className="uppercase text-xs font-bold tracking-wider">Assigned SDC</TableHead>
                  <TableHead className="uppercase text-xs font-bold tracking-wider">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {users.map((u) => (
                  <TableRow key={u.user_id} className="hover:bg-muted/50">
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <Avatar className="w-8 h-8">
                          <AvatarImage src={u.picture} alt={u.name} />
                          <AvatarFallback>{u.name?.[0]}</AvatarFallback>
                        </Avatar>
                        <span className="font-medium">{u.name}</span>
                      </div>
                    </TableCell>
                    <TableCell className="font-mono text-sm">{u.email}</TableCell>
                    <TableCell>
                      <Badge variant={u.role === "ho" ? "default" : "secondary"}>
                        {u.role === "ho" ? (
                          <><Shield className="w-3 h-3 mr-1" /> Head Office</>
                        ) : (
                          <><Building2 className="w-3 h-3 mr-1" /> SDC</>
                        )}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {u.role === "sdc" ? (
                        <span className="text-sm">{getSDCName(u.assigned_sdc_id)}</span>
                      ) : (
                        <span className="text-muted-foreground text-sm">All SDCs</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <Dialog 
                        open={editingUser?.user_id === u.user_id} 
                        onOpenChange={(open) => setEditingUser(open ? u : null)}
                      >
                        <DialogTrigger asChild>
                          <Button variant="outline" size="sm" data-testid={`edit-user-${u.user_id}`}>
                            Edit Role
                          </Button>
                        </DialogTrigger>
                        <DialogContent>
                          <EditRoleForm 
                            user={u}
                            sdcs={sdcs}
                            onSave={handleUpdateRole}
                            onCancel={() => setEditingUser(null)}
                          />
                        </DialogContent>
                      </Dialog>
                    </TableCell>
                  </TableRow>
                ))}
                {users.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={5} className="text-center py-8 text-muted-foreground">
                      No users found
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        {/* Role Legend */}
        <Card className="mt-6 border border-border">
          <CardHeader>
            <CardTitle className="font-heading text-lg">Role Permissions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-2 gap-6">
              <div className="p-4 border border-border rounded-md">
                <div className="flex items-center gap-2 mb-3">
                  <Shield className="w-5 h-5 text-primary" />
                  <span className="font-heading font-bold">Head Office (HO)</span>
                </div>
                <ul className="text-sm text-muted-foreground space-y-1">
                  <li>• View all SDCs and their data</li>
                  <li>• Access Financial Control dashboard</li>
                  <li>• Manage users and roles</li>
                  <li>• Create/delete SDCs, job roles</li>
                  <li>• Generate risk alerts</li>
                  <li>• Seed sample data</li>
                </ul>
              </div>
              <div className="p-4 border border-border rounded-md">
                <div className="flex items-center gap-2 mb-3">
                  <Building2 className="w-5 h-5 text-muted-foreground" />
                  <span className="font-heading font-bold">SDC User</span>
                </div>
                <ul className="text-sm text-muted-foreground space-y-1">
                  <li>• View only assigned SDC data</li>
                  <li>• Track training progress</li>
                  <li>• Add batches and invoices</li>
                  <li>• Update batch progress</li>
                  <li>• View job roles and billing</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  );
}

// Edit Role Form
const EditRoleForm = ({ user, sdcs, onSave, onCancel }) => {
  const [role, setRole] = useState(user.role);
  const [assignedSdcId, setAssignedSdcId] = useState(user.assigned_sdc_id || "");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    await onSave(user.user_id, role, assignedSdcId);
    setLoading(false);
  };

  return (
    <>
      <DialogHeader>
        <DialogTitle>Edit User Role</DialogTitle>
        <DialogDescription>
          Change role for {user.name} ({user.email})
        </DialogDescription>
      </DialogHeader>
      <form onSubmit={handleSubmit} className="space-y-4 mt-4">
        <div>
          <Label>Role</Label>
          <Select value={role} onValueChange={setRole}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ho">Head Office (Full Access)</SelectItem>
              <SelectItem value="sdc">SDC (Limited Access)</SelectItem>
            </SelectContent>
          </Select>
        </div>
        
        {role === "sdc" && (
          <div>
            <Label>Assigned SDC</Label>
            <Select value={assignedSdcId} onValueChange={setAssignedSdcId}>
              <SelectTrigger>
                <SelectValue placeholder="Select SDC" />
              </SelectTrigger>
              <SelectContent>
                {sdcs.map((sdc) => (
                  <SelectItem key={sdc.sdc_id} value={sdc.sdc_id}>
                    {sdc.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}

        <div className="flex gap-2">
          <Button type="button" variant="outline" onClick={onCancel} className="flex-1">
            Cancel
          </Button>
          <Button type="submit" className="flex-1" disabled={loading}>
            {loading ? "Saving..." : "Save Changes"}
          </Button>
        </div>
      </form>
    </>
  );
};

const UserManagementSkeleton = () => (
  <div className="min-h-screen bg-background">
    <header className="border-b border-border">
      <div className="max-w-7xl mx-auto px-6 py-4">
        <Skeleton className="w-64 h-8" />
      </div>
    </header>
    <main className="max-w-7xl mx-auto px-6 py-8">
      <Skeleton className="h-64 rounded-md" />
    </main>
  </div>
);
