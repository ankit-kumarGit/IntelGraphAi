import React from 'react';
import { 
  LayoutDashboard, 
  Cpu, 
  AlertCircle, 
  Network, 
  ShieldCheck, 
  FileText, 
  Sliders, 
  Layers,
  Building,
  X
} from 'lucide-react';

export default function Sidebar({ 
  activeNav, 
  setActiveNav, 
  actionCount = 0, 
  currentUser, 
  tenantInfo,
  mobileOpen = false,
  onCloseMobile
}) {
  const isAdmin = currentUser?.role === 'Administrator' || currentUser?.permissions?.includes('admin_manage_organizations');

  const baseNavItems = [
    { id: 'overview', label: 'Overview', icon: LayoutDashboard },
    { id: 'assets', label: 'Machines', icon: Cpu },
    { id: 'actions', label: 'Action Center', icon: AlertCircle, badge: actionCount },
    { id: 'knowledge', label: 'Knowledge', icon: Network },
    { id: 'compliance', label: 'Compliance', icon: ShieldCheck },
    { id: 'reports', label: 'Reports', icon: FileText },
  ];

  // Admin console is strictly restricted to true Platform Administrators
  const navItems = isAdmin 
    ? [...baseNavItems, { id: 'admin', label: 'Platform Administration', icon: Sliders }]
    : baseNavItems;

  return (
    <>
      {/* Mobile Backdrop */}
      {mobileOpen && (
        <div 
          className="fixed inset-0 bg-black/70 z-40 md:hidden backdrop-blur-sm animate-in fade-in duration-150"
          onClick={onCloseMobile}
        />
      )}

      <aside className={`${
        mobileOpen 
          ? 'fixed inset-y-0 left-0 z-50 flex shadow-2xl animate-in slide-in-from-left duration-200' 
          : 'hidden md:flex'
      } w-64 bg-slate-900 border-r border-slate-800 flex-col shrink-0 min-h-screen`}>
        {/* Brand Header */}
        <div className="p-5 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-brand-600/90 border border-brand-500/30 flex items-center justify-center shadow-md shadow-brand-950">
              <Layers className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="font-bold text-base text-white tracking-tight flex items-center gap-1.5">
                IntelGraph<span className="text-brand-400 text-xs px-1.5 py-0.5 rounded bg-brand-500/10 border border-brand-500/20">AI</span>
              </h1>
              <p className="text-[11px] text-slate-400 font-mono">Operations Platform</p>
            </div>
          </div>
          {mobileOpen && (
            <button
              onClick={onCloseMobile}
              className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 md:hidden"
            >
              <X className="w-5 h-5" />
            </button>
          )}
        </div>

        {/* Nav Menu */}
        <nav className="flex-1 p-3 space-y-1">
          <div className="px-3 py-2 text-[10px] font-semibold uppercase tracking-wider text-slate-400">
            Operations Platform
          </div>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeNav === item.id;
            return (
              <button
                key={item.id}
                onClick={() => {
                  setActiveNav(item.id);
                  if (onCloseMobile) onCloseMobile();
                }}
                className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-lg text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-brand-500/15 text-brand-400 border border-brand-500/30 shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`}
              >
                <div className="flex items-center gap-3">
                  <Icon className={`w-4 h-4 ${isActive ? 'text-brand-400' : 'text-slate-400'}`} />
                  <span>{item.label}</span>
                </div>
                {item.badge > 0 && (
                  <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-red-500/20 text-red-400 border border-red-500/30">
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
      </nav>

      {/* Tenant Hierarchy Footer */}
      <div className="p-3 m-3 rounded-lg bg-slate-950/70 border border-slate-800 text-[11px] text-slate-400 space-y-1">
        <div className="flex items-center justify-between font-mono text-slate-300">
          <span className="text-[10px] uppercase tracking-wider text-slate-400">Plant Scope</span>
          <span className="text-emerald-400 flex items-center gap-1 text-[11px]">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span> Active
          </span>
        </div>
        <p className="text-slate-200 font-medium truncate">
          {currentUser?.plant_scope || 'Plant A (Unit 2)'}
        </p>
        <p className="text-slate-500 text-[10px] truncate">
          {tenantInfo?.name || 'Industrial Operations'}
        </p>
      </div>
    </aside>
    </>
  );
}
