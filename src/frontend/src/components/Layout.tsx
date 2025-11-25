import { ReactNode } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { TopBar } from './TopBar';

interface LayoutProps {
  children: ReactNode;
}

export function Layout({ children }: LayoutProps) {
  const location = useLocation();
  const navigate = useNavigate();
  
  // Map routes to page IDs for sidebar
  const getCurrentPage = () => {
    const path = location.pathname;
    if (path === '/') return 'dashboard';
    if (path.startsWith('/upload-data')) return 'upload';
    if (path.startsWith('/upload-audio')) return 'audio';
    if (path.startsWith('/transcripts')) return 'audio';
    if (path.startsWith('/dq')) return 'quality';
    if (path.startsWith('/compare')) return 'comparison';
    if (path.startsWith('/region-insights')) return 'regions';
    if (path.startsWith('/recommendations')) return 'recommendations';
    if (path.startsWith('/settings')) return 'settings';
    return 'dashboard';
  };

  const handleNavigate = (page: string) => {
    const routeMap: Record<string, string> = {
      dashboard: '/',
      upload: '/upload-data',
      quality: '/dq',
      audio: '/upload-audio',
      comparison: '/compare',
      regions: '/region-insights',
      recommendations: '/recommendations',
      settings: '/settings',
    };
    navigate(routeMap[page] || '/');
  };

  return (
    <div className="flex h-screen bg-slate-50 dark:bg-slate-900">
      <Sidebar currentPage={getCurrentPage()} onNavigate={handleNavigate} />
      <div className="flex-1 flex flex-col overflow-hidden">
        <TopBar />
        <main className="flex-1 overflow-y-auto bg-slate-50 dark:bg-slate-900">
          <div className="max-w-[1600px] mx-auto p-8">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
