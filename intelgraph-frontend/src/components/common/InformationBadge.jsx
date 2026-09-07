import React from 'react';
import { ShieldCheck, UserCheck, Sparkles } from 'lucide-react';

export default function InformationBadge({ type = 'verified', label, size = 'sm' }) {
  const isSm = size === 'sm';
  const sizeClasses = isSm ? 'text-xs px-2 py-0.5' : 'text-sm px-3 py-1';

  if (type === 'verified' || type === 'Verified Record') {
    return (
      <span className={`inline-flex items-center gap-1.5 font-medium rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 ${sizeClasses}`}>
        <ShieldCheck className={isSm ? 'w-3 h-3' : 'w-4 h-4'} />
        {label || 'Verified Record'}
      </span>
    );
  }

  if (type === 'human' || type === 'Human Input') {
    return (
      <span className={`inline-flex items-center gap-1.5 font-medium rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/30 ${sizeClasses}`}>
        <UserCheck className={isSm ? 'w-3 h-3' : 'w-4 h-4'} />
        {label || 'Human Input'}
      </span>
    );
  }

  return (
    <span className={`inline-flex items-center gap-1.5 font-medium rounded-full bg-purple-500/10 text-purple-400 border border-purple-500/30 ${sizeClasses}`}>
      <Sparkles className={isSm ? 'w-3 h-3' : 'w-4 h-4'} />
      {label || 'AI-Assisted Insight'}
    </span>
  );
}
