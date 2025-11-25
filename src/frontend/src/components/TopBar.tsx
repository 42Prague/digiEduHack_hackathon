import { useState, useEffect } from 'react';
import { Search, Bell, User, Sun, Moon } from 'lucide-react';
import { Input } from './ui/input';
import { Button } from './ui/button';
import { Avatar, AvatarFallback } from './ui/avatar';

export function TopBar() {
  const [darkMode, setDarkMode] = useState(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('darkMode') === 'true';
    }
    return false;
  });

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('darkMode', 'true');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('darkMode', 'false');
    }
  }, [darkMode]);

  return (
    <div className="h-16 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-700 flex items-center justify-between px-6">
      <div className="flex-1 max-w-md">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 dark:text-slate-500" />
          <Input 
            placeholder="Search schools, regions, or data..." 
            className="pl-10 dark:bg-slate-800 dark:border-slate-700 dark:text-white"
          />
        </div>
      </div>

      <div className="flex items-center gap-3">
        <Button 
          variant="ghost" 
          size="icon" 
          onClick={() => setDarkMode(!darkMode)}
          className="dark:hover:bg-slate-800"
        >
          {darkMode ? (
            <Sun className="w-5 h-5" />
          ) : (
            <Moon className="w-5 h-5" />
          )}
        </Button>
        
        <Button variant="ghost" size="icon" className="relative dark:hover:bg-slate-800">
          <Bell className="w-5 h-5" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-blue-600 rounded-full"></span>
        </Button>
        
        <div className="flex items-center gap-2 pl-3 border-l border-slate-200 dark:border-slate-700">
          <Avatar>
            <AvatarFallback className="bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-300">
              <User className="w-4 h-4" />
            </AvatarFallback>
          </Avatar>
          <div>
            <div className="text-sm dark:text-white">Foundation Staff</div>
            <div className="text-xs text-slate-500 dark:text-slate-400">Coordinator</div>
          </div>
        </div>
      </div>
    </div>
  );
}
