import React, { useState } from 'react';
import { 
  Search, 
  User, 
  ChevronRight, 
  RotateCw, 
  Sparkles, 
  CheckCircle2, 
  ShieldAlert, 
  LogOut, 
  KeyRound, 
  Building2, 
  Shield, 
  Layers,
  Menu
} from 'lucide-react';
import { api } from '../../services/api';

export default function Topbar({ 
  currentUser,
  tenantInfo,
  isImpersonating = false,
  impersonationInfo = null,
  onEndImpersonation,
  onOpenLoginModal,
  onSignOut,
  onToggleMobileMenu,
  activeAsset, 
  onOpenSearch, 
  onOpenChat,
  onReseedCompleted 
}) {
  const [isReseeding, setIsReseeding] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  const handleReseed = async () => {
    if (confirm('Reset operational dataset baseline (P-101 bearing history, C-201 overhaul, P-102 standby)?')) {
      setIsReseeding(true);
      try {
        await api.reseed();
        if (onReseedCompleted) onReseedCompleted();
      } catch (e) {
        alert('Failed to reset: ' + e.message);
      } finally {
        setIsReseeding(false);
      }
    }
  };

  // Avatar initials from user's full name or email
  const getInitials = (user) => {
    if (!user) return 'OP';
    if (user.full_name) {
      const parts = user.full_name.split(' ');
      if (parts.length >= 2) return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
      return user.full_name.substring(0, 2).toUpperCase();
    }
    if (user.email) return user.email.substring(0, 2).toUpperCase();
    return 'OP';
  };

  return (
    <div className="flex flex-col sticky top-0 z-30">
      {/* HIGH-VISIBILITY SUPPORT IMPERSONATION BANNER (Enterprise Support Requirement) */}
      {isImpersonating && (
        <div className="bg-gradient-to-r from-amber-600 via-amber-700 to-amber-800 text-amber-50 px-6 py-2 border-b border-amber-500/40 flex flex-wrap items-center justify-between gap-3 shadow-md animate-in slide-in-from-top duration-200">
          <div className="flex items-center gap-2.5 text-xs font-medium">
            <ShieldAlert className="w-4 h-4 text-amber-200 shrink-0 animate-pulse" />
            <span>
              <strong className="font-bold tracking-wide uppercase">Active Support Impersonation:</strong> Acting as{' '}
              <span className="font-mono underline font-semibold text-white">{currentUser?.full_name || currentUser?.email}</span>{' '}
              ({currentUser?.role})
            </span>
            <span className="hidden md:inline text-amber-200/80">•</span>
            <span className="hidden md:inline text-amber-100 text-[11px] truncate max-w-md">
              Reason: &ldquo;{impersonationInfo?.reason || 'Support Investigation'}&rdquo;
            </span>
          </div>
          <button
            onClick={onEndImpersonation}
            className="px-3 py-1 rounded-lg bg-amber-950/80 hover:bg-amber-950 text-amber-200 hover:text-white border border-amber-400/40 text-xs font-semibold font-mono flex items-center gap-1.5 transition-all shadow-sm"
          >
            <LogOut className="w-3.5 h-3.5" />
            <span>End Support Session</span>
          </button>
        </div>
      )}

      {/* Main Topbar */}
      <header className="h-14 bg-slate-900/90 backdrop-blur-md border-b border-slate-800 px-6 flex items-center justify-between gap-4">
        {/* Dynamic Organization Hierarchy Breadcrumb */}
        <div className="flex items-center gap-2 text-xs text-slate-400 overflow-hidden truncate">
          {/* Mobile Navigation Drawer Toggle */}
          <button
            onClick={onToggleMobileMenu}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 md:hidden shrink-0 transition-colors"
            title="Toggle Navigation Menu"
            aria-label="Toggle navigation"
          >
            <Menu className="w-4 h-4" />
          </button>

          <span className="text-slate-300 font-semibold flex items-center gap-1.5 shrink-0">
            <Building2 className="w-3.5 h-3.5 text-brand-400 shrink-0" />
            <span className="truncate max-w-[180px]">{tenantInfo?.name || 'Industrial Operations'}</span>
          </span>
          <ChevronRight className="w-3.5 h-3.5 text-slate-600 shrink-0" />
          <span className="text-slate-300 font-medium truncate">
            {currentUser?.plant_scope ? currentUser.plant_scope.split('(')[0].trim() : 'Gulf Coast Operations'}
          </span>
          <ChevronRight className="w-3.5 h-3.5 text-slate-600 shrink-0" />
          <span className="text-slate-400 truncate">
            {currentUser?.plant_scope && currentUser.plant_scope.includes('(') 
              ? currentUser.plant_scope.split('(')[1].replace(')', '').trim() 
              : 'Plant A'}
          </span>
        </div>

        {/* Center/Right Operator Controls */}
        <div className="flex items-center gap-3">
          {/* Global Search Button */}
          <button
            onClick={onOpenSearch}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-800 border border-slate-700/70 text-slate-400 hover:text-slate-200 text-xs transition-all shadow-inner"
            aria-label="Global Search"
          >
            <Search className="w-3.5 h-3.5 text-slate-400" />
            <span className="hidden sm:inline">Search machines, records...</span>
            <kbd className="hidden md:inline-block px-1.5 py-0.5 text-[10px] font-mono bg-slate-900 rounded border border-slate-700 text-slate-400">
              ⌘K
            </kbd>
          </button>

          {/* AI Assistant Quick Trigger ("Ask IntelGraph AI") */}
          <button
            onClick={onOpenChat}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-brand-500/15 hover:bg-brand-500/25 border border-brand-500/30 text-brand-300 text-xs font-medium transition-all shadow-sm"
          >
            <Sparkles className="w-3.5 h-3.5 text-brand-400" />
            <span>Ask IntelGraph AI</span>
          </button>

          {/* Reseed Data Baseline */}
          <button
            onClick={handleReseed}
            disabled={isReseeding}
            title="Reset operational dataset baseline"
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-slate-200 border border-slate-700 text-xs transition-all flex items-center justify-center disabled:opacity-50"
          >
            <RotateCw className={`w-3.5 h-3.5 ${isReseeding ? 'animate-spin text-brand-400' : ''}`} />
          </button>

          {/* Authenticated Enterprise User Session Card */}
          <div className="relative">
            <button
              onClick={() => setUserMenuOpen(!userMenuOpen)}
              className="flex items-center gap-2.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-750 border border-slate-700 text-slate-200 text-xs font-medium transition-all shadow-sm"
            >
              <div className="w-6 h-6 rounded-full bg-brand-500/20 border border-brand-500/30 text-brand-400 flex items-center justify-center font-bold text-[10px] font-mono">
                {getInitials(currentUser)}
              </div>
              <div className="text-left hidden md:block">
                <div className="text-xs font-semibold text-slate-200 truncate max-w-[140px]">
                  {currentUser?.full_name || currentUser?.email || 'Authenticated User'}
                </div>
                <div className="text-[10px] font-mono text-brand-400">
                  {currentUser?.role || 'Operator'}
                </div>
              </div>
            </button>

            {/* Enterprise Account & Session Menu */}
            {userMenuOpen && (
              <div className="absolute right-0 mt-2 w-80 bg-slate-900 border border-slate-800 rounded-xl shadow-2xl p-3 z-50 animate-in fade-in zoom-in-95 duration-150">
                <div className="border-b border-slate-800 pb-3 mb-3">
                  <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-semibold">
                    Enterprise User Identity
                  </div>
                  <div className="text-sm font-bold text-white mt-1">
                    {currentUser?.full_name || 'Enterprise Operator'}
                  </div>
                  <div className="text-xs text-brand-400 font-mono mt-0.5">
                    {currentUser?.role}
                  </div>
                  <div className="text-[11px] text-slate-400 font-mono mt-1 truncate">
                    {currentUser?.email}
                  </div>
                </div>

                <div className="space-y-2 text-xs text-slate-300 pb-3 border-b border-slate-800">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Department:</span>
                    <span className="text-slate-200 font-medium truncate max-w-[170px]">
                      {currentUser?.department || 'Operations'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Scope:</span>
                    <span className="text-slate-200 font-medium truncate max-w-[170px]">
                      {currentUser?.plant_scope || 'Gulf Coast Plant'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Security Model:</span>
                    <span className="text-emerald-400 font-mono text-[11px] flex items-center gap-1">
                      <Shield className="w-3 h-3" />
                      Server-Enforced RBAC
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Active Permissions:</span>
                    <span className="text-brand-400 font-mono text-[11px]">
                      {currentUser?.permissions?.length || 0} discrete scopes
                    </span>
                  </div>
                </div>

                <div className="pt-2 space-y-1">
                  <button
                    onClick={() => {
                      setUserMenuOpen(false);
                      if (onOpenLoginModal) onOpenLoginModal();
                    }}
                    className="w-full text-left px-3 py-2 rounded-lg hover:bg-slate-800 text-slate-200 text-xs flex items-center gap-2 transition-all font-medium"
                  >
                    <KeyRound className="w-3.5 h-3.5 text-brand-400" />
                    <span>Sign In as Different User</span>
                  </button>

                  <button
                    onClick={() => {
                      setUserMenuOpen(false);
                      if (onSignOut) onSignOut();
                    }}
                    className="w-full text-left px-3 py-2 rounded-lg hover:bg-red-500/10 text-red-400 text-xs flex items-center gap-2 transition-all font-medium"
                  >
                    <LogOut className="w-3.5 h-3.5" />
                    <span>Sign Out</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </header>
    </div>
  );
}
