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
} from "@/components/ui/dialog";

const NewWorkOrderForm = ({ onSuccess }) => {
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    work_order_number: "",
    location: "",
    job_role_code: "",
    job_role_name: "",
    awarding_body: "",
    scheme_name: "",
    total_training_hours: 200,
    sessions_per_day: 8,
    num_students: 30,
    cost_per_student: 10000,
    manager_email: ""
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await axios.post(`${API}/work-orders`, {
        ...formData,
        total_training_hours: parseInt(formData.total_training_hours),
        sessions_per_day: parseInt(formData.sessions_per_day),
        num_students: parseInt(formData.num_students),
        cost_per_student: parseFloat(formData.cost_per_student)
      });
      toast.success("Work Order created successfully! SDC has been automatically created/linked.");
      onSuccess();
    } catch (error) {
      console.error("Error creating work order:", error);
      toast.error(error.response?.data?.detail || "Failed to create work order");
    } finally {
      setLoading(false);
    }
  };

  const totalValue = formData.num_students * formData.cost_per_student;

  return (
    <>
      <DialogHeader>
        <DialogTitle className="text-xl font-heading">Create New Work Order</DialogTitle>
        <p className="text-sm text-muted-foreground mt-1">
          This will automatically create a new SDC if the location doesn't exist.
        </p>
      </DialogHeader>
      <form onSubmit={handleSubmit} className="space-y-4 mt-4" data-testid="new-work-order-form">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label>Work Order Number *</Label>
            <Input 
              value={formData.work_order_number}
              onChange={(e) => setFormData({ ...formData, work_order_number: e.target.value })}
              placeholder="WO/2025/001"
              required
              data-testid="input-wo-number"
            />
          </div>
          <div>
            <Label>Location (SDC) *</Label>
            <Input 
              value={formData.location}
              onChange={(e) => setFormData({ ...formData, location: e.target.value })}
              placeholder="e.g., Mumbai, Delhi, Jaipur"
              required
              data-testid="input-location"
            />
            <p className="text-xs text-muted-foreground mt-1">Enter city name - SDC will be auto-created</p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label>Job Role Code *</Label>
            <Input 
              value={formData.job_role_code}
              onChange={(e) => setFormData({ ...formData, job_role_code: e.target.value })}
              placeholder="CSC/Q0801"
              required
              data-testid="input-job-code"
            />
          </div>
          <div>
            <Label>Job Role Name *</Label>
            <Input 
              value={formData.job_role_name}
              onChange={(e) => setFormData({ ...formData, job_role_name: e.target.value })}
              placeholder="e.g., Field Technician Computing"
              required
              data-testid="input-job-name"
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label>Awarding Body *</Label>
            <Input 
              value={formData.awarding_body}
              onChange={(e) => setFormData({ ...formData, awarding_body: e.target.value })}
              placeholder="e.g., NSDC, Sector Skill Council"
              required
              data-testid="input-awarding-body"
            />
          </div>
          <div>
            <Label>Scheme Name *</Label>
            <Input 
              value={formData.scheme_name}
              onChange={(e) => setFormData({ ...formData, scheme_name: e.target.value })}
              placeholder="e.g., PMKVY, DDUGKY"
              required
              data-testid="input-scheme"
            />
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4">
          <div>
            <Label>Training Hours *</Label>
            <Input 
              type="number"
              value={formData.total_training_hours}
              onChange={(e) => setFormData({ ...formData, total_training_hours: e.target.value })}
              min="1"
              required
              data-testid="input-hours"
            />
          </div>
          <div>
            <Label>Sessions/Day</Label>
            <Input 
              type="number"
              value={formData.sessions_per_day}
              onChange={(e) => setFormData({ ...formData, sessions_per_day: e.target.value })}
              min="1"
              max="12"
              data-testid="input-sessions"
            />
          </div>
          <div>
            <Label>Number of Students *</Label>
            <Input 
              type="number"
              value={formData.num_students}
              onChange={(e) => setFormData({ ...formData, num_students: e.target.value })}
              min="1"
              required
              data-testid="input-students"
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label>Cost per Student (INR) *</Label>
            <Input 
              type="number"
              value={formData.cost_per_student}
              onChange={(e) => setFormData({ ...formData, cost_per_student: e.target.value })}
              min="0"
              required
              data-testid="input-cost"
            />
          </div>
          <div>
            <Label>Manager Email</Label>
            <Input 
              type="email"
              value={formData.manager_email}
              onChange={(e) => setFormData({ ...formData, manager_email: e.target.value })}
              placeholder="manager@example.com"
              data-testid="input-manager-email"
            />
          </div>
        </div>

        {/* Total Contract Value */}
        <div className="p-4 bg-muted rounded-lg">
          <div className="flex justify-between items-center">
            <span className="text-sm text-muted-foreground">Total Contract Value:</span>
            <span className="font-mono font-bold text-xl">
              {new Intl.NumberFormat('en-IN', {
                style: 'currency',
                currency: 'INR',
                maximumFractionDigits: 0
              }).format(totalValue)}
            </span>
          </div>
        </div>

        <Button type="submit" className="w-full" disabled={loading}>
          {loading ? "Creating..." : "Create Work Order"}
        </Button>
      </form>
    </>
  );
};

export default NewWorkOrderForm;
