import { useState } from "react";
import axios from "axios";
import { API } from "@/App";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

// Category rates
const CATEGORY_RATES = {
  "A": 46,
  "B": 42
};

const JobRoleForm = ({ editData, onSuccess }) => {
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    job_role_code: editData?.job_role_code || "",
    job_role_name: editData?.job_role_name || "",
    category: editData?.category || "A",
    rate_per_hour: editData?.rate_per_hour || CATEGORY_RATES["A"],
    total_training_hours: editData?.total_training_hours || 400,
    awarding_body: editData?.awarding_body || "NSDC",
    scheme_name: editData?.scheme_name || "PMKVY 4.0",
    default_daily_hours: editData?.default_daily_hours || 8,
    default_batch_size: editData?.default_batch_size || 30
  });

  const handleCategoryChange = (value) => {
    setFormData({
      ...formData,
      category: value,
      rate_per_hour: CATEGORY_RATES[value] || formData.rate_per_hour
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      if (editData) {
        await axios.put(`${API}/master/job-roles/${editData.job_role_id}`, formData);
        toast.success("Job Role updated successfully");
      } else {
        await axios.post(`${API}/master/job-roles`, formData);
        toast.success("Job Role created successfully");
      }
      onSuccess();
    } catch (error) {
      console.error("Error saving job role:", error);
      toast.error(error.response?.data?.detail || "Failed to save job role");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <DialogHeader>
        <DialogTitle>{editData ? "Edit Job Role" : "Add New Job Role"}</DialogTitle>
        <DialogDescription>
          Define job role configuration with category-based rates
        </DialogDescription>
      </DialogHeader>
      <form onSubmit={handleSubmit} className="space-y-4 mt-4" data-testid="job-role-form">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label>Job Role Code *</Label>
            <Input 
              value={formData.job_role_code}
              onChange={(e) => setFormData({ ...formData, job_role_code: e.target.value })}
              placeholder="CSC/Q0801"
              required
              disabled={!!editData}
            />
          </div>
          <div>
            <Label>Job Role Name *</Label>
            <Input 
              value={formData.job_role_name}
              onChange={(e) => setFormData({ ...formData, job_role_name: e.target.value })}
              placeholder="Field Technician Computing"
              required
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label>Category *</Label>
            <Select value={formData.category} onValueChange={handleCategoryChange}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="A">Category A (INR 46/hr)</SelectItem>
                <SelectItem value="B">Category B (INR 42/hr)</SelectItem>
                <SelectItem value="CUSTOM">Custom Rate</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label>Rate Per Hour (INR) *</Label>
            <Input 
              type="number"
              value={formData.rate_per_hour}
              onChange={(e) => setFormData({ ...formData, rate_per_hour: parseFloat(e.target.value) })}
              min="0"
              step="0.01"
              required
              disabled={formData.category !== "CUSTOM"}
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label>Total Training Hours *</Label>
            <Input 
              type="number"
              value={formData.total_training_hours}
              onChange={(e) => setFormData({ ...formData, total_training_hours: parseInt(e.target.value) })}
              min="1"
              required
            />
          </div>
          <div>
            <Label>Default Daily Hours</Label>
            <Select value={String(formData.default_daily_hours)} onValueChange={(v) => setFormData({ ...formData, default_daily_hours: parseInt(v) })}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="4">4 hours/day</SelectItem>
                <SelectItem value="6">6 hours/day</SelectItem>
                <SelectItem value="8">8 hours/day</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label>Awarding Body *</Label>
            <Input 
              value={formData.awarding_body}
              onChange={(e) => setFormData({ ...formData, awarding_body: e.target.value })}
              placeholder="NSDC"
              required
            />
          </div>
          <div>
            <Label>Scheme Name *</Label>
            <Input 
              value={formData.scheme_name}
              onChange={(e) => setFormData({ ...formData, scheme_name: e.target.value })}
              placeholder="PMKVY 4.0"
              required
            />
          </div>
        </div>

        <div className="p-3 bg-muted rounded-md">
          <div className="text-sm text-muted-foreground">Cost Per Student (calculated)</div>
          <div className="font-mono font-bold text-lg">
            {new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(formData.total_training_hours * formData.rate_per_hour)}
          </div>
          <p className="text-xs text-muted-foreground mt-1">
            {formData.total_training_hours} hrs x INR {formData.rate_per_hour}/hr
          </p>
        </div>

        <Button type="submit" className="w-full" disabled={loading}>
          {loading ? "Saving..." : (editData ? "Update Job Role" : "Create Job Role")}
        </Button>
      </form>
    </>
  );
};

export default JobRoleForm;
export { CATEGORY_RATES };
