import React, { useState } from 'react';
import { 
  X, 
  Lock, 
  Mail, 
  ShieldCheck, 
  Layers, 
  AlertCircle,
  RotateCw,
  KeyRound,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import { api } from '../../services/api';

export default function EnterpriseLoginModal({ isOpen, onClose, onSuccess }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);
  const [showSeedHelper, setShowSeedHelper] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    if (e) e.preventDefault();
    if (!email.trim() || !password.trim()) {
      setErrorMsg('Please enter both work email and enterprise password.');
      return;
    }

    setLoading(true);
    setErrorMsg(null);

    try {
      const res = await api.login(email.trim(), password.trim());
      if (res && res.token) {
        localStorage.setItem('intelgraph_token', res.token);
        if (onSuccess) onSuccess(res);
        if (onClose) onClose();
      } else {
        throw new Error('No authentication token received.');
      }
    } catch (err) {
      setErrorMsg(err.message || 'Authentication failed. Please verify credentials.');
    } finally {
      setLoading(false);
    }
  };

  const fillCredentials = (seedEmail, seedPwd) => {
    setEmail(seedEmail);
    setPassword(seedPwd);
    setErrorMsg(null);
  };

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-md z-50 flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md flex flex-col shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="p-6 border-b border-slate-800 bg-slate-950 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-600 to-cyan-400 flex items-center justify-center shadow-lg shadow-brand-500/20">
              <Layers className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white tracking-tight flex items-center gap-1.5">
                IntelGraph<span className="text-brand-400 text-xs px-1.5 py-0.5 rounded bg-brand-500/10 border border-brand-500/20">AI</span>
              </h3>
              <p className="text-xs text-slate-400">Enterprise Authentication</p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition-all"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4 text-xs">
          {errorMsg && (
            <div className="p-3 rounded-xl bg-red-950/30 border border-red-500/30 text-red-300 text-xs flex items-start gap-2.5">
              <AlertCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
              <span>{errorMsg}</span>
            </div>
          )}

          <div className="space-y-1.5">
            <label className="text-[11px] font-mono uppercase tracking-wider text-slate-400 font-semibold block">
              Corporate Work Email
            </label>
            <div className="relative">
              <Mail className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="operator@company.com"
                className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white placeholder-slate-600 focus:outline-none focus:border-brand-500 font-mono text-xs transition-colors"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-[11px] font-mono uppercase tracking-wider text-slate-400 font-semibold block">
              Enterprise Password
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white placeholder-slate-600 focus:outline-none focus:border-brand-500 font-mono text-xs transition-colors"
              />
            </div>
          </div>

          <div className="pt-2">
            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 rounded-xl bg-brand-500 hover:bg-brand-600 text-white font-bold text-xs flex items-center justify-center gap-2 transition-all shadow-md shadow-brand-500/20 disabled:opacity-50"
            >
              {loading ? (
                <>
                  <RotateCw className="w-4 h-4 animate-spin" />
                  <span>Authenticating Session...</span>
                </>
              ) : (
                <>
                  <ShieldCheck className="w-4 h-4" />
                  <span>Sign In with Enterprise SSO</span>
                </>
              )}
            </button>
          </div>

          {/* Development Seed Accounts Helper (For local development verification) */}
          <div className="pt-4 border-t border-slate-800/80">
            <button
              type="button"
              onClick={() => setShowSeedHelper(!showSeedHelper)}
              className="w-full flex items-center justify-between text-[11px] text-slate-400 hover:text-slate-200 transition-colors font-mono"
            >
              <span className="flex items-center gap-1.5">
                <KeyRound className="w-3.5 h-3.5 text-brand-400" />
                <span>Development Seed Accounts Reference</span>
              </span>
              {showSeedHelper ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            </button>

            {showSeedHelper && (
              <div className="mt-3 p-3 rounded-xl bg-slate-950/80 border border-slate-800 space-y-2 text-[11px]">
                <p className="text-slate-400 text-[10px]">
                  Select enterprise role profile for controlled session testing (SAML/OIDC is a deployment integration boundary):
                </p>
                <div className="space-y-1.5 font-mono">
                  <button
                    type="button"
                    onClick={() => fillCredentials('engineer@plant-ops.local', 'Password123!')}
                    className="w-full text-left p-2 rounded-lg bg-slate-900 hover:bg-slate-850 border border-slate-800 flex items-center justify-between transition-colors"
                  >
                    <div>
                      <div className="text-brand-300 font-semibold text-[11px]">Maintenance Engineer</div>
                      <div className="text-slate-400 text-[10px]">engineer@plant-ops.local</div>
                    </div>
                    <span className="text-[9px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">Fill</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => fillCredentials('manager@plant-ops.local', 'Password123!')}
                    className="w-full text-left p-2 rounded-lg bg-slate-900 hover:bg-slate-850 border border-slate-800 flex items-center justify-between transition-colors"
                  >
                    <div>
                      <div className="text-emerald-300 font-semibold text-[11px]">Plant Operations Manager</div>
                      <div className="text-slate-400 text-[10px]">manager@plant-ops.local</div>
                    </div>
                    <span className="text-[9px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">Fill</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => fillCredentials('auditor@compliance.local', 'Password123!')}
                    className="w-full text-left p-2 rounded-lg bg-slate-900 hover:bg-slate-850 border border-slate-800 flex items-center justify-between transition-colors"
                  >
                    <div>
                      <div className="text-cyan-300 font-semibold text-[11px]">Lead Compliance Auditor</div>
                      <div className="text-slate-400 text-[10px]">auditor@compliance.local</div>
                    </div>
                    <span className="text-[9px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">Fill</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => fillCredentials('admin@intelgraph.local', 'AdminPassword123!')}
                    className="w-full text-left p-2 rounded-lg bg-slate-900 hover:bg-slate-850 border border-slate-800 flex items-center justify-between transition-colors"
                  >
                    <div>
                      <div className="text-amber-300 font-semibold text-[11px]">Platform Administrator</div>
                      <div className="text-slate-400 text-[10px]">admin@intelgraph.local</div>
                    </div>
                    <span className="text-[9px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">Fill</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </form>
      </div>
    </div>
  );
}
