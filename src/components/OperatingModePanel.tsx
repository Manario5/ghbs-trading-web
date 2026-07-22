import React from 'react';
import { useOperatingMode, modeStyle } from '../services/useOperatingMode';
import { Check, X, Lock, Radio, RefreshCw } from 'lucide-react';

function Row({ label, on, goodWhenOn = true }: { label: string; on: boolean; goodWhenOn?: boolean }) {
  const good = on === goodWhenOn;
  return (
    <div className="flex items-center justify-between py-1 text-xs">
      <span className="text-gray-400">{label}</span>
      <span className={`flex items-center gap-1 font-medium ${good ? 'text-emerald-400' : 'text-gray-500'}`}>
        {on ? <Check className="w-3 h-3" /> : <X className="w-3 h-3" />}
        {on ? 'Enabled' : 'Off'}
      </span>
    </div>
  );
}

function Locked({ label }: { label: string }) {
  return (
    <div className="flex items-center justify-between py-1 text-xs">
      <span className="text-gray-400">{label}</span>
      <span className="flex items-center gap-1 font-medium text-slate-400">
        <Lock className="w-3 h-3" /> Impossible
      </span>
    </div>
  );
}

export function OperatingModePanel() {
  const { mode, error, reload } = useOperatingMode();
  const style = modeStyle(mode?.mode);

  if (error && !mode) {
    return (
      <div className="bg-gray-900/70 border border-gray-800 rounded-xl p-5 text-sm flex items-center justify-between">
        <span className="text-red-400">Failed to load operating mode: {error}</span>
        <button onClick={reload} className="ml-4 px-3 py-1.5 bg-blue-600/20 text-blue-400 rounded text-xs">Retry</button>
      </div>
    );
  }
  if (!mode) return <div className="bg-gray-900/70 border border-gray-800 rounded-xl p-5 text-sm text-gray-500">Loading operating mode…</div>;

  const cap = mode.capabilities || {};

  return (
    <div className={`rounded-xl p-5 border ${style.badge}`}>
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <Radio className={`w-5 h-5 ${style.text}`} />
          <div>
            <h3 className={`text-base font-bold ${style.text}`}>{mode.mode_label}</h3>
            <p className="text-xs text-gray-400 mt-0.5 max-w-xl">{mode.description}</p>
          </div>
        </div>
        <button onClick={reload} className="p-1.5 bg-black/20 text-gray-400 hover:text-white rounded">
          <RefreshCw className="w-3.5 h-3.5" />
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-x-6 gap-y-1 mt-4">
        <div>
          <p className="text-[10px] uppercase tracking-wider text-gray-500 mb-1 font-semibold">Live capabilities</p>
          <Row label="Market data provider" on={!!cap.market_data_provider_usage} />
          <Row label="OHLCV diagnostics" on={!!cap.ohlcv_diagnostics} />
          <Row label="Provider coverage scan" on={!!cap.provider_coverage_scan} />
          <Row label="Live Analyze preview" on={!!cap.live_analyze_preview} />
          <Row label="Live Scout preview" on={!!cap.live_scout_preview} />
        </div>
        <div>
          <p className="text-[10px] uppercase tracking-wider text-gray-500 mb-1 font-semibold">Alerts & automation</p>
          <Row label="Manual Telegram alerts" on={!!cap.manual_telegram_alerts} />
          <Row label="Telegram test-send" on={!!cap.telegram_test_send} />
          <Row label="Telegram sending active" on={!!mode.telegram_sending_active} />
          <Row label="Scheduler enabled" on={!!mode.automation?.scheduler_enabled} />
          <Row label="Anthropic assistant ready" on={!!cap.anthropic_ready} />
        </div>
        <div>
          <p className="text-[10px] uppercase tracking-wider text-gray-500 mb-1 font-semibold">Guaranteed locked</p>
          <Locked label="Trade execution" />
          <Locked label="Broker execution" />
          <Locked label="Production DB write" />
          <Locked label="Public exposure" />
          <div className="flex items-center justify-between py-1 text-xs">
            <span className="text-gray-400">Live preview mode</span>
            <span className="text-emerald-400 font-medium">Read-only</span>
          </div>
        </div>
      </div>

      {mode.uses_sandbox_db && (
        <p className="text-[11px] text-gray-500 mt-3 border-t border-gray-800 pt-2">
          Data store: sandbox DB (<span className="font-mono">tasi_ledger_test.db</span>) — production DB writes are impossible.
        </p>
      )}
    </div>
  );
}
