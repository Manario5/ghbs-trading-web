import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { ShieldCheck, ShieldAlert, Lock, Unlock, RefreshCw } from 'lucide-react';

function Flag({ label, value, goodWhen }: { label: string; value: boolean; goodWhen: boolean }) {
  const good = value === goodWhen;
  return (
    <span className="text-xs space-x-1">
      <span className="text-gray-500">{label}:</span>
      <span className={good ? 'text-green-400' : 'text-yellow-400'}>{value ? 'true' : 'false'}</span>
    </span>
  );
}

export function TelegramStatusPanel() {
  const [status, setStatus] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get('/alerts/telegram/status', { timeout: 15000 });
      setStatus(res.data || {});
    } catch (e: any) {
      setError(e.response?.data?.detail || e.message || 'Request failed');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  if (loading && !status) {
    return <div className="bg-gray-800 p-6 border border-gray-700 rounded-xl text-gray-500 text-sm">Loading Telegram status…</div>;
  }
  if (error && !status) {
    return (
      <div className="bg-gray-800 p-6 border border-gray-700 rounded-xl text-sm flex items-center justify-between">
        <span className="text-red-400">Failed to load Telegram status: {error}</span>
        <button onClick={load} className="ml-4 px-3 py-1.5 bg-blue-600/20 text-blue-400 hover:bg-blue-600/30 rounded text-xs">Retry</button>
      </div>
    );
  }
  if (!status) {
    return (
      <div className="bg-gray-800 p-6 border border-gray-700 rounded-xl text-sm flex items-center justify-between">
        <span className="text-gray-500">No Telegram status data.</span>
        <button onClick={load} className="ml-4 px-3 py-1.5 bg-blue-600/20 text-blue-400 hover:bg-blue-600/30 rounded text-xs">Retry</button>
      </div>
    );
  }

  const r = status.readiness || {};
  const g = status.gates || {};
  const last = status.last_attempt;
  const locked = g.test_send_gate_status !== 'open';

  return (
    <div className="bg-gray-800 p-6 border border-gray-700 rounded-xl space-y-4">
      <div className="flex justify-between items-center border-b border-gray-700 pb-2">
        <h3 className="text-lg font-medium text-white">Telegram Readiness & Gates</h3>
        <div className="flex items-center gap-2">
          <span className={`inline-flex items-center gap-1 px-2 py-1 text-xs rounded font-semibold ${locked ? 'bg-gray-700 text-gray-300' : 'bg-yellow-900/30 text-yellow-400 border border-yellow-700/30'}`}>
            {locked ? <Lock className="w-3 h-3" /> : <Unlock className="w-3 h-3" />}
            {locked ? 'TEST-SEND LOCKED' : 'TEST-SEND OPEN'}
          </span>
          <span className={`inline-flex items-center gap-1 px-2 py-1 text-xs rounded font-semibold ${r.safety_state === 'SAFE' ? 'bg-green-900/30 text-green-400 border border-green-700/30' : 'bg-yellow-900/30 text-yellow-400 border border-yellow-700/30'}`}>
            {r.safety_state === 'SAFE' ? <ShieldCheck className="w-3 h-3" /> : <ShieldAlert className="w-3 h-3" />}
            {r.safety_state || 'UNKNOWN'}
          </span>
          <button onClick={load} disabled={loading} className="p-1.5 bg-blue-600/20 text-blue-400 hover:bg-blue-600/30 rounded transition-colors">
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
        {/* Readiness */}
        <div className="space-y-1.5">
          <p className="text-gray-400 text-xs font-semibold uppercase">Readiness</p>
          <div className="flex flex-col gap-1">
            <span className="text-xs space-x-1">
              <span className="text-gray-500">Token:</span>
              <span className={r.telegram_bot_token_configured ? 'text-green-400' : 'text-red-400'}>{r.telegram_bot_token_masked}</span>
              {r.telegram_token_source && r.telegram_token_source !== 'missing' && (
                <span className="text-gray-500">({r.telegram_token_source})</span>
              )}
            </span>
            <span className="text-xs space-x-1">
              <span className="text-gray-500">Chat ID:</span>
              <span className={r.telegram_chat_id_configured ? 'text-green-400' : 'text-red-400'}>{r.telegram_chat_id_masked}</span>
            </span>
            <span className="text-xs space-x-1">
              <span className="text-gray-500">Authorized IDs:</span>
              <span className={r.authorized_user_ids_configured ? 'text-green-400' : 'text-red-400'}>
                {r.authorized_user_ids_masked} ({r.authorized_user_ids_count ?? 0})
              </span>
            </span>
          </div>
        </div>

        {/* Flags */}
        <div className="space-y-1.5">
          <p className="text-gray-400 text-xs font-semibold uppercase">Send / Test Flags</p>
          <div className="flex flex-col gap-1">
            <Flag label="ENABLE_TELEGRAM_SEND" value={!!r.telegram_send_enabled} goodWhen={false} />
            <Flag label="ENABLE_TELEGRAM_TEST_SEND" value={!!r.telegram_test_send_enabled} goodWhen={false} />
            <Flag label="ENABLE_ALERT_SCHEDULER" value={!!r.alert_scheduler_enabled} goodWhen={false} />
            <Flag label="Dry run" value={!!r.telegram_dry_run_enabled} goodWhen={true} />
            <Flag label="Network calls locked" value={!!r.telegram_network_calls_locked} goodWhen={true} />
          </div>
        </div>

        {/* Gate status */}
        <div className="space-y-1.5">
          <p className="text-gray-400 text-xs font-semibold uppercase">Test-Send Gate</p>
          <div className="flex flex-col gap-1">
            <span className="text-xs space-x-1">
              <span className="text-gray-500">can_run_test_send:</span>
              <span className={g.can_run_test_send ? 'text-yellow-400' : 'text-green-400'}>{String(!!g.can_run_test_send)}</span>
            </span>
            {(g.blocked_reasons || []).length > 0 && (
              <ul className="text-xs text-gray-400 list-disc list-inside space-y-0.5">
                {g.blocked_reasons.map((reason: string, i: number) => (
                  <li key={i}>{reason}</li>
                ))}
              </ul>
            )}
            {(g.blocked_reasons || []).length === 0 && (
              <span className="text-xs text-yellow-400">All gates open — manual test-send is possible.</span>
            )}
          </div>
        </div>
      </div>

      {/* Last attempt */}
      <div className="border-t border-gray-700 pt-3">
        <p className="text-gray-400 text-xs font-semibold uppercase mb-1.5">Last Dry-Run / Test-Send Attempt</p>
        {last ? (
          <div className="flex flex-wrap gap-4 text-xs">
            <span><span className="text-gray-500">Time:</span> <span className="text-gray-300">{new Date(last.timestamp).toLocaleString()}</span></span>
            <span><span className="text-gray-500">Kind:</span> <span className="text-gray-300">{last.kind}</span></span>
            <span><span className="text-gray-500">Outcome:</span> <span className={last.outcome === 'sent' ? 'text-green-400' : last.outcome === 'failed' ? 'text-red-400' : 'text-gray-300'}>{last.outcome}</span></span>
            <span><span className="text-gray-500">Network call:</span> <span className={last.network_call_made ? 'text-yellow-400' : 'text-green-400'}>{String(!!last.network_call_made)}</span></span>
            {last.target_chat_masked && <span><span className="text-gray-500">Target:</span> <span className="font-mono text-gray-400">{last.target_chat_masked}</span></span>}
          </div>
        ) : (
          <span className="text-xs text-gray-500">No attempts recorded yet.</span>
        )}
      </div>
    </div>
  );
}
