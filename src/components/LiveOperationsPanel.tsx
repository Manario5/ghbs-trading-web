import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { Activity, RefreshCw } from 'lucide-react';

/**
 * Live Operations summary — read-only snapshot of the last operational events
 * and the guaranteed-locked invariants. Consumes /dashboard/live-summary.
 */
export function LiveOperationsPanel() {
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    api.get('/dashboard/live-summary', { timeout: 15000 })
      .then(res => { setData(res.data); setError(null); })
      .catch(e => setError(e.response?.data?.detail || e.message || 'Failed to load'))
      .finally(() => setLoading(false));
  };
  useEffect(() => { load(); }, []);

  if (loading && !data) return <div className="bg-gray-900/70 border border-gray-800 rounded-xl p-5 text-sm text-gray-500">Loading live operations…</div>;
  if (error && !data) return (
    <div className="bg-gray-900/70 border border-gray-800 rounded-xl p-5 text-sm flex items-center justify-between">
      <span className="text-red-400">Failed to load live operations: {error}</span>
      <button onClick={load} className="ml-4 px-3 py-1.5 bg-blue-600/20 text-blue-400 rounded text-xs">Retry</button>
    </div>
  );
  if (!data) return null;

  const fmt = (t?: string) => (t ? new Date(t).toLocaleString() : 'None yet');
  const rows: [string, React.ReactNode][] = [
    ['Operating mode', data.operating_mode_label],
    ['Telegram sending', data.telegram_sending_active ? 'Active' : 'Inactive'],
    ['Scheduler', data.scheduler_enabled ? 'Enabled' : 'Disabled'],
    ['Last alert', data.last_alert ? `${data.last_alert.delivery_status} · ${data.last_alert.destination_masked || ''} · ${fmt(data.last_alert.created_at)}` : 'None yet'],
    ['Last analyze preview', data.last_analyze_preview ? fmt(data.last_analyze_preview.created_at) : 'None yet'],
    ['Last scout preview', data.last_scout_preview ? fmt(data.last_scout_preview.created_at) : 'None yet'],
  ];

  return (
    <div className="bg-gray-900/70 border border-gray-800 rounded-xl p-5">
      <div className="flex items-center justify-between border-b border-gray-800 pb-2 mb-3">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-emerald-400" />
          <h3 className="text-sm font-semibold text-gray-200">Live Operations</h3>
        </div>
        <button onClick={load} className="p-1.5 bg-black/20 text-gray-400 hover:text-white rounded">
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-1.5 text-xs">
        {rows.map(([k, v]) => (
          <div key={k} className="flex justify-between border-b border-gray-800/50 pb-1.5">
            <span className="text-gray-400">{k}</span>
            <span className="text-gray-200 text-right">{v}</span>
          </div>
        ))}
        <div className="flex justify-between border-b border-gray-800/50 pb-1.5">
          <span className="text-gray-400">Production DB write</span>
          <span className="text-emerald-400 font-medium">Impossible</span>
        </div>
        <div className="flex justify-between border-b border-gray-800/50 pb-1.5">
          <span className="text-gray-400">Trade execution</span>
          <span className="text-emerald-400 font-medium">Impossible</span>
        </div>
      </div>
    </div>
  );
}
