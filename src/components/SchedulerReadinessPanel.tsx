import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { Clock, Lock, Play, RefreshCw } from 'lucide-react';

export function SchedulerReadinessPanel() {
  const [readiness, setReadiness] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get('/scheduler/readiness');
      setReadiness(res.data);
    } catch (e: any) {
      setError(e.response?.data?.detail || e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  if (error) return <div className="bg-gray-800 p-6 border border-gray-700 rounded-xl text-red-400 text-sm">Failed to load scheduler readiness: {error}</div>;
  if (!readiness) return <div className="bg-gray-800 p-6 border border-gray-700 rounded-xl text-gray-500 text-sm">Loading scheduler readiness…</div>;

  const g = readiness.gates || {};
  const locked = g.scheduled_send_gate_status !== 'open';

  return (
    <div className="bg-gray-800 p-6 border border-gray-700 rounded-xl space-y-4">
      <div className="flex justify-between items-center border-b border-gray-700 pb-2">
        <div className="flex items-center gap-2">
          <Clock className="w-4 h-4 text-purple-400" />
          <h3 className="text-lg font-medium text-white">Scheduled Alerts Readiness</h3>
        </div>
        <div className="flex items-center gap-2">
          <span className={`inline-flex items-center gap-1 px-2 py-1 text-xs rounded font-semibold ${readiness.is_running ? 'bg-yellow-900/30 text-yellow-400 border border-yellow-700/30' : 'bg-gray-700 text-gray-300'}`}>
            {readiness.is_running ? <Play className="w-3 h-3" /> : <Lock className="w-3 h-3" />}
            {readiness.is_running ? 'DRY-RUN LOOP RUNNING' : 'NOT RUNNING'}
          </span>
          <span className={`px-2 py-1 text-xs rounded font-semibold ${locked ? 'bg-green-900/30 text-green-400 border border-green-700/30' : 'bg-yellow-900/30 text-yellow-400 border border-yellow-700/30'}`}>
            SCHEDULED SENDS {locked ? 'LOCKED' : 'OPEN'}
          </span>
          <button onClick={load} disabled={loading} className="p-1.5 bg-blue-600/20 text-blue-400 hover:bg-blue-600/30 rounded transition-colors">
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
        <div className="space-y-1">
          <p className="text-gray-400 font-semibold uppercase">Gate Status</p>
          {(g.blocked_reasons || []).length > 0 ? (
            <ul className="text-gray-400 list-disc list-inside space-y-0.5">
              {g.blocked_reasons.map((r: string, i: number) => <li key={i}>{r}</li>)}
            </ul>
          ) : (
            <p className="text-yellow-400">All scheduled-send gates open — verify this is intentional.</p>
          )}
          <p className="pt-1">
            <span className="text-gray-500">Real scheduled sends implemented:</span>{' '}
            <span className={readiness.real_scheduled_sends_implemented ? 'text-yellow-400' : 'text-green-400'}>
              {String(!!readiness.real_scheduled_sends_implemented)}
            </span>
          </p>
        </div>
        <div className="space-y-1">
          <p className="text-gray-400 font-semibold uppercase">Defined Jobs ({readiness.jobs_defined})</p>
          <ul className="space-y-1">
            {(readiness.job_definitions || []).map((j: any) => (
              <li key={j.job_id} className="flex justify-between bg-gray-900 border border-gray-700 rounded px-2 py-1">
                <span className="text-gray-300">{j.job_id}</span>
                <span className="text-gray-500">{j.category} · every {j.default_interval_seconds}s</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
