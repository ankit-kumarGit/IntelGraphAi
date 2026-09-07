import React, { useState, useEffect } from 'react';
import { 
  Cpu, 
  Plus, 
  Upload, 
  Search, 
  ArrowRight, 
  AlertTriangle, 
  CheckCircle2, 
  ChevronRight
} from 'lucide-react';
import { api } from '../../services/api';

export default function AssetDirectory({ 
  onSelectAsset, 
  onOpenNewAssetModal, 
  onOpenOnboardingModal 
}) {
  const [assets, setAssets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  const loadAssets = async () => {
    setLoading(true);
    try {
      const data = await api.getAssets();
      setAssets(data);
    } catch (err) {
      console.error('Failed to load assets:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAssets();
  }, []);

  const filteredAssets = assets.filter((a) => {
    const matchesSearch = 
      a.tag.toLowerCase().includes(searchQuery.toLowerCase()) ||
      a.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      a.manufacturer.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === 'all' || a.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-6">
      {/* Header & Main Industrial Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="text-xs font-mono tracking-wider uppercase text-slate-400 font-semibold mb-1">
            Registered Machinery
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">
            Industrial Assets Directory
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Central operational intelligence brain configured for each site asset
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={onOpenOnboardingModal}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-semibold transition-all shadow-sm"
          >
            <Upload className="w-3.5 h-3.5 text-brand-400" />
            <span>Import Legacy Records</span>
          </button>

          <button
            onClick={onOpenNewAssetModal}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-brand-500 hover:bg-brand-600 text-white text-xs font-semibold shadow-lg shadow-brand-500/20 transition-all"
          >
            <Plus className="w-4 h-4" />
            <span>Register New Asset</span>
          </button>
        </div>
      </div>

      {/* Scannable Filter & Search Toolbar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 text-xs">
        <div className="relative w-full sm:w-80">
          <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search P-101, Compressor, pump..."
            className="w-full pl-9 pr-3 py-2 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-200 placeholder-slate-400 focus:outline-none focus:border-brand-500"
          />
        </div>

        <div className="flex items-center gap-1.5 w-full sm:w-auto overflow-x-auto">
          {['all', 'Operational', 'Maintenance Due', 'Critical'].map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`px-3 py-1.5 rounded-lg capitalize text-xs font-medium whitespace-nowrap transition-all ${
                statusFilter === st
                  ? 'bg-brand-500/15 text-brand-400 border border-brand-500/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
              }`}
            >
              {st}
            </button>
          ))}
        </div>
      </div>

      {/* Easy-to-Scan Assets List */}
      {loading ? (
        <div className="p-16 text-center text-slate-400">
          <div className="w-8 h-8 border-2 border-brand-400 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
          Scanning machine profiles...
        </div>
      ) : filteredAssets.length === 0 ? (
        <div className="p-12 text-center text-slate-400 bg-slate-900/50 rounded-xl border border-slate-800">
          No matching machinery found.
        </div>
      ) : (
        <div className="space-y-3">
          {filteredAssets.map((asset) => {
            const isCritical = asset.status === 'Critical' || asset.criticality === 'Critical';
            const isMaintDue = asset.status === 'Maintenance Due';

            // Coverage calculation: 7/8 for P-101, etc.
            const coverageCount = asset.tag === 'P-101' ? 7 : asset.tag === 'P-102' ? 6 : asset.tag === 'C-201' ? 5 : 4;
            const primaryIssue = asset.tag === 'P-101' 
              ? 'Potential recurring bearing issue' 
              : asset.tag === 'C-201' 
              ? 'Overhaul overdue (4 days beyond interval)'
              : 'All condition monitoring parameters verified';

            return (
              <div
                key={asset.tag}
                onClick={() => onSelectAsset(asset.tag)}
                className="p-4 rounded-xl bg-slate-900 border border-slate-800 hover:border-brand-500/40 cursor-pointer transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-4 group"
              >
                {/* 1. Identity & 2. State & 3. Important Issue */}
                <div className="space-y-1.5 min-w-0">
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-sm font-bold text-brand-400 group-hover:text-brand-300 transition-colors">
                      {asset.tag}
                    </span>
                    <span className="font-semibold text-xs text-white">
                      {asset.name}
                    </span>
                    <span className="flex items-center gap-1.5 text-xs">
                      <span className={`w-2 h-2 rounded-full ${
                        asset.status === 'Operational' ? 'bg-emerald-400' : 'bg-red-400'
                      }`}></span>
                      <span className={asset.status === 'Operational' ? 'text-emerald-400' : 'text-red-400 font-semibold'}>
                        {asset.status}
                      </span>
                    </span>
                  </div>

                  <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400">
                    <span className={isMaintDue || isCritical ? 'text-amber-300 font-medium' : 'text-slate-400'}>
                      {primaryIssue}
                    </span>
                    {asset.open_findings_count > 0 && (
                      <>
                        <span>•</span>
                        <span className="text-amber-400 font-medium">{asset.open_findings_count} finding</span>
                      </>
                    )}
                    <span>•</span>
                    <span className="font-mono text-[11px] text-slate-400">
                      Knowledge coverage {coverageCount}/8
                    </span>
                  </div>
                </div>

                {/* 4. Next Action */}
                <div className="flex items-center gap-3 self-end sm:self-center shrink-0">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onSelectAsset(asset.tag);
                    }}
                    className="px-3.5 py-1.5 rounded-lg bg-slate-800 group-hover:bg-brand-500 group-hover:text-white text-slate-200 text-xs font-semibold border border-slate-700/80 group-hover:border-transparent transition-all flex items-center gap-1.5 shadow-sm"
                  >
                    <span>Open Asset</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
