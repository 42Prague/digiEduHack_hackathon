import { 
  LayoutDashboard, 
  Upload, 
  CheckCircle2, 
  Mic, 
  GitCompare, 
  MapPin, 
  Lightbulb, 
  Settings 
} from 'lucide-react';

interface SidebarProps {
  currentPage: string;
  onNavigate: (page: string) => void;
}

export function Sidebar({ currentPage, onNavigate }: SidebarProps) {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'upload', label: 'Upload Data', icon: Upload },
    { id: 'quality', label: 'Data Quality', icon: CheckCircle2 },
    { id: 'audio', label: 'Audio Analysis', icon: Mic },
    { id: 'comparison', label: 'School Comparison', icon: GitCompare },
    { id: 'regions', label: 'Region Insights', icon: MapPin },
    { id: 'recommendations', label: 'Recommendations', icon: Lightbulb },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  return (
    <div className="w-64 bg-white border-r border-slate-200 flex flex-col">
      <div className="p-6 border-b border-slate-200">
        <h1 className="text-blue-600">SchoolInsights</h1>
        <p className="text-slate-500 text-sm mt-1">Analytics Platform</p>
      </div>
      
      <nav className="flex-1 p-4">
        <ul className="space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentPage === item.id;
            
            return (
              <li key={item.id}>
                <button
                  onClick={() => onNavigate(item.id)}
                  className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors ${
                    isActive 
                      ? 'bg-blue-50 text-blue-600' 
                      : 'text-slate-600 hover:bg-slate-50'
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  <span>{item.label}</span>
                </button>
              </li>
            );
          })}
        </ul>
      </nav>

      <div className="p-4 border-t border-slate-200">
        <div className="text-xs text-slate-500">
          Powered by Nadace The Foundation
        </div>
      </div>
    </div>
  );
}
