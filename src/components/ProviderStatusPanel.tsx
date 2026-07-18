import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { Database, Lock, RefreshCw } from 'lucide-react';

const HEALTH_STYLES: Record<string, string> = {
  ready: 'text-yellow-400 bg-yellow-400/10 border-yellow-700/30',
  locked: 'text-green-400 bg-green-400/10 border-green-700/30',
  missing_key: 'text-red-400 bg-red-400/10 border-red-700/30',
  readiness_only: 'text-gray-400 bg-gray-400/10 border-gray-700/30',
};

export function ProviderStatusPanel() {
  const [health, setHealth] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get('/market-data/provider-health');
      setHealth(res.data);
    } catch (e: any) {
      setError(e.response?.data?.detail || e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  if (error) return <div className="bg-gray-800 p-6 border border-gray-700 rounded-xl text-red-400 text-sm">Failed to load provider health: {error}</div>;
  if (!health) return <div className="bg-gray-800 p-6 border border-gray-700 rounded-xl text-gray-500 text-sm">Loading provider health…</div>;

  return (
    <div className="bg-gray-800 p-6 border border-gray-700 rounded-xl space-y-4">
      <div className="flex justify-between items-center border-b border-gray-700 pb-2">
        <div className="flex items-center gap-2">
          <Database className="w-4 h-4 text-blue-400" />
          <h3 className="text-lg font-medium text-white">Provider Readiness & Fallback</h3>
        </div>
        <div className="flex items-center gap-2">
          {health.network_calls_locked && (
            <span className="inline-flex items-center gap-1 px-2 py-1 text-xs rounded font-semibold bg-green-900/30 text-green-400 border border-green-700/30">
              <Lock className="w-3 h-3" /> NETWORK LOCKED
            </span>
          )}
          <button onClick={load} disabled={loading} className="p-1.5 bg-blue-600/20 text-blue-400 hover:bg-blue-600/30 rounded transition-colors">
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {(health.providers || []).map((p: any) => (
          <div key={p.provider} className="bg-gray-900 border border-gray-700 rounded p-3 space-y-1.5">
            <div className="flex justify-between items-center">
              <span className="text-sm text-white font-medium">{p.provider}</span>
              <span className={`px-1.5 py-0.5 rounded text-[10px] font-semibold border ${HEALTH_STYLES[p.health] || HEALTH_STYLES.readiness_only}`}>
                {p.health.replace('_', ' ').toUpperCase()}
              </span>
            </div>
            <div className="text-xs text-gray-500 space-y-0.5">
              <p>Key: <span className={p.secret_masked === 'missing' ? 'text-red-400' : 'text-gray-300'}>{p.secret_masked}</span></p>
              <p>Adapter: <span className={p.adapter_implemented ? 'text-green-400' : 'text-gray-400'}>{p.adapter_implemented ? 'implemented' : 'readiness only'}</span></p>
            </div>
          </div>
        ))}
      </div>

      <div className="text-xs text-gray-400 space-y-1 border-t border-gray-700 pt-3">
        <p>
          <span className="text-gray-500">Configured fallback order:</span>{' '}
          <span className="font-mono">{(health.configured_fallback_order || []).join(' → ')}</span>
        </p>
        <p>
          <span className="text-gray-500">Effective chain (if unlocked):</span>{' '}
          <span className="font-mono text-blue-300">{(health.effective_fallback_chain || []).join(' → ') || 'none'}</span>
        </p>
        {(health.skipped_providers || []).length > 0 && (
          <p>
            <span className="text-gray-500">Skipped:</span>{' '}
            {health.skipped_providers.map((s: any) => `${s.provider} (${s.reason})`).join(', ')}
          </p>
        )}
      </div>
    </div>
  );
}
