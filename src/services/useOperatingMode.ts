import { useState, useEffect } from 'react';
import { api } from './api';

export interface OperatingMode {
  mode: string;
  mode_label: string;
  description?: string;
  safety_state?: string;
  warning_reasons?: string[];
  unsafe_reasons?: string[];
  capabilities?: Record<string, boolean>;
  automation?: { scheduler_enabled: boolean; scheduler_dry_run_only: boolean };
  telegram_sending_active?: boolean;
  live_preview_read_only?: boolean;
  production_db_write_possible?: boolean;
  trade_execution_possible?: boolean;
  blocked?: Record<string, boolean>;
  uses_sandbox_db?: boolean;
  db_path?: string;
}

export const MODE_STYLES: Record<string, { badge: string; dot: string; text: string }> = {
  PRIVATE_LIVE:       { badge: 'bg-emerald-900/30 border-emerald-700/50', dot: 'bg-emerald-400', text: 'text-emerald-400' },
  AUTOMATED_ALERTS:   { badge: 'bg-indigo-900/30 border-indigo-700/50',   dot: 'bg-indigo-400',  text: 'text-indigo-400' },
  LOCKED_MAINTENANCE: { badge: 'bg-slate-800/60 border-slate-600/50',     dot: 'bg-slate-400',   text: 'text-slate-300' },
  RESTRICTED:         { badge: 'bg-red-900/30 border-red-700/50',         dot: 'bg-red-400',     text: 'text-red-400' },
};

export function modeStyle(mode?: string) {
  return MODE_STYLES[mode || ''] || MODE_STYLES.LOCKED_MAINTENANCE;
}

export function useOperatingMode(pollMs = 0) {
  const [mode, setMode] = useState<OperatingMode | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = () => {
    api.get('/system/operating-mode', { timeout: 15000 })
      .then(res => { setMode(res.data); setError(null); })
      .catch(e => setError(e.response?.data?.detail || e.message || 'Failed to load mode'));
  };

  useEffect(() => {
    load();
    if (pollMs > 0) {
      const id = setInterval(load, pollMs);
      return () => clearInterval(id);
    }
  }, [pollMs]);

  return { mode, error, reload: load };
}
