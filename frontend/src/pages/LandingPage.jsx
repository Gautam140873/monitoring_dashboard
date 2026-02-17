import { Button } from "@/components/ui/button";
import { Building2, BarChart3, Shield, Users, ArrowRight } from "lucide-react";

export default function LandingPage() {
  // REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
  const handleLogin = () => {
    const redirectUrl = window.location.origin + '/dashboard';
    window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-primary rounded-md flex items-center justify-center">
              <Building2 className="w-6 h-6 text-primary-foreground" />
            </div>
            <span className="font-heading font-bold text-xl">SkillFlow</span>
          </div>
          <Button 
            onClick={handleLogin}
            className="bg-primary text-primary-foreground hover:bg-primary/90 rounded-md px-6"
            data-testid="login-button"
          >
            Sign In with Google
            <ArrowRight className="w-4 h-4 ml-2" />
          </Button>
        </div>
      </header>

      {/* Hero Section */}
      <main className="max-w-7xl mx-auto px-6 py-16">
        <div className="grid lg:grid-cols-2 gap-16 items-center">
          <div className="animate-fade-in">
            <h1 className="font-heading font-black text-4xl sm:text-5xl lg:text-6xl leading-tight mb-6">
              Skill Development
              <span className="block text-muted-foreground">CRM & Billing</span>
              Controller
            </h1>
            <p className="text-lg text-muted-foreground mb-8 max-w-lg">
              Monitor training progress, manage finances, and track placements across all your Skill Development Centers in one unified dashboard.
            </p>
            <div className="flex flex-wrap gap-4">
              <Button 
                onClick={handleLogin}
                size="lg"
                className="bg-primary text-primary-foreground hover:bg-primary/90 rounded-md px-8"
                data-testid="hero-login-button"
              >
                Get Started
                <ArrowRight className="w-5 h-5 ml-2" />
              </Button>
            </div>
          </div>

          {/* Feature Cards */}
          <div className="grid grid-cols-2 gap-4 animate-fade-in stagger-2">
            <FeatureCard
              icon={<BarChart3 className="w-6 h-6" />}
              title="Commercial Health"
              description="Track portfolio, billing & outstanding amounts"
              color="bg-blue-50 text-blue-700"
            />
            <FeatureCard
              icon={<Users className="w-6 h-6" />}
              title="SDC Progress"
              description="Monitor Mobilization to Placement pipeline"
              color="bg-emerald-50 text-emerald-700"
            />
            <FeatureCard
              icon={<Building2 className="w-6 h-6" />}
              title="Multi-Center"
              description="Manage multiple SDCs from one dashboard"
              color="bg-amber-50 text-amber-700"
            />
            <FeatureCard
              icon={<Shield className="w-6 h-6" />}
              title="Role-Based Access"
              description="SDC & HO level permissions"
              color="bg-purple-50 text-purple-700"
            />
          </div>
        </div>

        {/* Stats Section */}
        <div className="mt-24 grid grid-cols-2 md:grid-cols-4 gap-8 border-t border-border pt-16">
          <StatItem value="4" label="Training Stages" />
          <StatItem value="Real-time" label="Progress Tracking" />
          <StatItem value="Automated" label="End Date Calculation" />
          <StatItem value="Role-Based" label="Access Control" />
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-border mt-16">
        <div className="max-w-7xl mx-auto px-6 py-8 text-center text-muted-foreground text-sm">
          <p>SkillFlow CRM &copy; 2025. Skill Development Project Management.</p>
        </div>
      </footer>
    </div>
  );
}

const FeatureCard = ({ icon, title, description, color }) => (
  <div className="border border-border rounded-md p-6 hover:bg-muted/30 transition-colors">
    <div className={`w-12 h-12 rounded-md flex items-center justify-center mb-4 ${color}`}>
      {icon}
    </div>
    <h3 className="font-heading font-bold text-lg mb-2">{title}</h3>
    <p className="text-sm text-muted-foreground">{description}</p>
  </div>
);

const StatItem = ({ value, label }) => (
  <div className="text-center animate-fade-in">
    <div className="font-heading font-black text-3xl mb-2">{value}</div>
    <div className="text-sm text-muted-foreground">{label}</div>
  </div>
);
