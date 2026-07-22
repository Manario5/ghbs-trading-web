import React from 'react';
import { useOperatingMode, modeStyle } from '../services/useOperatingMode';

/** Compact operating-mode badge for the sidebar / topbar. */
export function ModeBadge({ variant = 'pill' }: { variant?: 'pill' | 'block' }) {
  const { mode } = useOperatingMode(60000);
  const style = modeStyle(mode?.mode);
  const label = mode?.mode_label || '…';

  if (variant === 'block') {
    return (
      <div className={`w-full text-center py-1.5 rounded border ${style.badge}`}>
        <span className={`text-[10px] font-bold uppercase tracking-widest ${style.text}`}>{label}</span>
      </div>
    );
  }
  return (
    <div className={`px-3 py-1 rounded border flex items-center space-x-2 ${style.badge}`}>
      <div className={`w-2 h-2 rounded-full ${style.dot} ${mode?.mode === 'LOCKED_MAINTENANCE' ? '' : 'animate-pulse'}`} />
      <span className={`text-xs font-semibold tracking-wide ${style.text}`}>{label}</span>
    </div>
  );
}
