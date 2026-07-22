import React from 'react';
import { Outlet, Navigate, Link, useLocation } from 'react-router-dom';
import { useAuth } from '../services/auth';
import { LayoutDashboard, User, Briefcase, Activity, Target, Search, Clock, Settings, LogOut, Calendar, BookOpen, Bell, BarChart2 } from 'lucide-react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { ModeBadge } from '../components/ModeBadge';

function cx(...inputs: (string | undefined | null | false)[]) {
  return twMerge(clsx(inputs));
}

export function ProtectedRoute() {
  const { token, loading } = useAuth();
  
  if (loading) return <div className="min-h-screen bg-gray-900 flex items-center justify-center text-white">Loading...</div>;
  if (!token) return <Navigate to="/login" replace />;
  
  return <Layout />;
}

function Layout() {
  const { logout, user } = useAuth();
  const location = useLocation();

  const navItems = [
    { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
    { name: 'Action Plan', path: '/action-plan', icon: Calendar },
    { name: 'Scout', path: '/scout', icon: Target },
    { name: 'Analyze', path: '/analyze', icon: Search },
    { name: 'Portfolio', path: '/portfolio', icon: Briefcase },
    { name: 'Journal', path: '/journal', icon: BookOpen },
    { name: 'Alerts', path: '/alerts', icon: Bell },
    { name: 'Market Data', path: '/market-data', icon: BarChart2 },
    { name: 'Performance', path: '/performance', icon: Activity },
    { name: 'Account', path: '/account', icon: User },
    { name: 'History', path: '/history', icon: Clock },
    { name: 'Settings', path: '/settings', icon: Settings },
  ];

  return (
    <div className="min-h-screen flex text-gray-300 bg-gray-900 font-sans">
      {/* Sidebar */}
      <aside className="w-64 bg-gray-950 border-r border-gray-800 flex flex-col">
        <div className="h-16 flex items-center px-6 border-b border-gray-800">
          <h1 className="text-xl font-bold text-white tracking-tight">GHBS Trading</h1>
        </div>
        <nav className="flex-1 px-4 py-6 space-y-1 overflow-y-auto">
          {navItems.map(item => {
            const Icon = item.icon;
            const isActive = location.pathname.startsWith(item.path);
            return (
              <Link
                key={item.path}
                to={item.path}
                className={cx(
                  "flex items-center px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
                  isActive ? "bg-blue-600/10 text-blue-500" : "hover:bg-gray-800 hover:text-white text-gray-400"
                )}
              >
                <Icon className={cx("w-5 h-5 mr-3", isActive ? "text-blue-500" : "text-gray-500")} />
                {item.name}
              </Link>
            )
          })}
        </nav>
        <div className="p-4 border-t border-gray-800">
          <div className="flex items-center justify-between mb-2">
             <span className="text-sm font-medium text-gray-300 truncate">{user?.username}</span>
             <button onClick={logout} className="text-gray-500 hover:text-white" title="Logout">
               <LogOut className="w-4 h-4" />
             </button>
          </div>
          <ModeBadge variant="block" />
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col h-screen overflow-hidden bg-[#0A0A0A]">
        {/* Topbar */}
        <header className="h-16 flex items-center justify-between px-8 border-b border-gray-800 bg-gray-950/50 backdrop-blur">
          <h2 className="text-sm font-medium text-gray-400 uppercase tracking-wider">TASI Quant Command Center</h2>
          <div className="flex items-center space-x-4">
             <ModeBadge />
          </div>
        </header>
        
        {/* App Content */}
        <div className="flex-1 overflow-auto p-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
