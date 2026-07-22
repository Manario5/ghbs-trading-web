/// <reference types="vite/client" />
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../services/api';
import { TradeTicket } from '../components/TradeTicket';
import { OperatingModePanel } from '../components/OperatingModePanel';
import { ModeBadge } from '../components/ModeBadge';
import { ChartCard, EmptyState, LineChart, BarChart, HBarChart, Funnel, Donut } from '../components/charts/Charts';

function useFetch<T>(url: string) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchData = () => {
    setLoading(true);
    api.get(url)
      .then(res => {
        setData(res.data);
        setError('');
      })
      .catch(err => {
        setError(err.message || 'Error loading data');
      })
      .finally(() => {
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchData();
  }, [url]);

  return { data, loading, error, refresh: fetchData };
}

const Loading = () => (
  <div className="flex items-center justify-center p-12">
    <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
  </div>
);

const ErrorMsg = ({ message }: { message: string }) => (
  <div className="text-red-500 bg-red-900/20 p-4 rounded-md border border-red-500/20 text-sm">
    {message}
  </div>
);

const StatCard = ({ title, value, className = '' }: { title: string; value: React.ReactNode; className?: string }) => (
  <div className={`bg-gray-800 p-6 rounded-xl border border-gray-700 ${className}`}>
    <div className="text-sm font-medium text-gray-400 mb-2">{title}</div>
    <div className="text-2xl font-bold text-white tracking-tight">{value}</div>
  </div>
);

const ProviderHealthCards = ({ providers }: { providers: any[] }) => {
  const styles: Record<string, string> = {
    ready: 'text-amber-400 border-amber-700/40',
    locked: 'text-emerald-400 border-emerald-700/40',
    missing_key: 'text-red-400 border-red-700/40',
    readiness_only: 'text-gray-400 border-gray-700/40',
  };
  if (!providers?.length) return <EmptyState message="No providers configured." />;
  return (
    <div className="grid grid-cols-2 gap-2">
      {providers.map((p: any) => (
        <div key={p.provider} className={`bg-gray-900 border rounded-lg p-3 ${styles[p.health] || styles.readiness_only}`}>
          <div className="flex justify-between items-center">
            <span className="text-sm font-medium text-gray-200">{p.provider}</span>
            <span className="text-[10px] font-semibold uppercase">{(p.health || '').replace('_', ' ')}</span>
          </div>
          <div className="text-[11px] text-gray-500 mt-1">
            Key: {p.secret_masked} · {p.adapter_implemented ? 'adapter ready' : 'readiness only'}
          </div>
        </div>
      ))}
    </div>
  );
};

export function Dashboard() {
  const { data: summary } = useFetch<any>('/dashboard/summary');
  const { data: live } = useFetch<any>('/dashboard/live-summary');
  const { data: charts, loading } = useFetch<any>('/dashboard/charts');
  const { data: funnel } = useFetch<any>('/dashboard/scout-funnel');
  const { data: activity } = useFetch<any>('/dashboard/alert-activity');
  const { data: providers } = useFetch<any>('/dashboard/provider-health');

  const risk = live?.risk_snapshot;

  const setupItems = (charts?.setup_distribution?.items || []).map((i: any) => ({ label: i.setup_type, value: i.count }));
  const symbolItems = (charts?.symbol_strength?.items || []).map((i: any) => ({ label: i.ticker, value: i.score }));
  const previewItems = (charts?.live_preview_outcomes?.items || []).map((i: any) => ({ label: i.label, value: i.count }));
  const activitySeries = (activity?.series || []).map((s: any) => ({ label: (s.day || '').slice(5), value: s.sent + s.failed }));

  return (
    <div className="space-y-6 max-w-7xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Command Center</h1>
          <p className="text-sm text-gray-500 mt-0.5">GHBS Trading — TASI Quant Command Center</p>
        </div>
        <ModeBadge />
      </div>

      <OperatingModePanel />

      {/* Risk / exposure snapshot */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard title="Equity (SAR)" value={summary ? summary.equity?.toLocaleString() : '—'} />
        <StatCard title="Open Positions" value={summary?.open_positions ?? '—'} />
        <StatCard title="Portfolio Heat" value={risk ? `${risk.portfolio_heat_pct}%` : '—'} />
        <StatCard title="Exposure" value={risk?.exposure_pct != null ? `${risk.exposure_pct}%` : 'n/a'} />
      </div>

      {loading && <Loading />}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <ChartCard title="Market Regime Trend" subtitle="Average regime score over time (setup log)">
          {charts?.regime_trend?.available
            ? <LineChart points={charts.regime_trend.points} />
            : <EmptyState message={charts?.regime_trend?.message || 'No history yet.'} />}
        </ChartCard>

        <ChartCard title="Setup Signal Distribution" subtitle="Counts by setup type">
          {setupItems.length ? <Donut data={setupItems} /> : <EmptyState message={charts?.setup_distribution?.message || 'No signals yet.'} />}
        </ChartCard>

        <ChartCard title="Scout Funnel" subtitle={funnel?.available ? `Latest scout run · ${funnel.provider || ''}` : 'Latest scout preview run'}>
          <Funnel stages={funnel?.stages || []} />
        </ChartCard>

        <ChartCard title="Symbol Strength Ranking" subtitle="Top symbols by avg confidence">
          <HBarChart data={symbolItems.map((s: any) => ({ label: s.label, value: s.value }))} />
        </ChartCard>

        <ChartCard title="Alert Activity Timeline" subtitle="Alerts by day (manual + scheduled)">
          {activitySeries.length ? <BarChart data={activitySeries} /> : <EmptyState message={activity?.message || 'No alert activity yet.'} />}
        </ChartCard>

        <ChartCard title="Provider Health" subtitle={providers?.network_calls_locked ? 'Network locked' : 'Network unlocked'}>
          <ProviderHealthCards providers={providers?.providers || []} />
        </ChartCard>

        <ChartCard title="Live Preview Outcomes" subtitle="Trade executions are always 0 (impossible)">
          <BarChart data={previewItems} />
        </ChartCard>

        <ChartCard title="Live Operations" subtitle="Latest activity & guarantees">
          <div className="space-y-2 text-xs">
            <OpRow label="Operating mode" value={live?.operating_mode_label} />
            <OpRow label="Telegram sending" value={live?.telegram_sending_active ? 'Active' : 'Inactive'} />
            <OpRow label="Scheduler" value={live?.scheduler_enabled ? 'Enabled' : 'Disabled'} />
            <OpRow label="Last alert" value={live?.last_alert ? `${live.last_alert.delivery_status} · ${new Date(live.last_alert.created_at).toLocaleString()}` : 'None yet'} />
            <OpRow label="Last analyze preview" value={live?.last_analyze_preview ? new Date(live.last_analyze_preview.created_at).toLocaleString() : 'None yet'} />
            <OpRow label="Last scout preview" value={live?.last_scout_preview ? new Date(live.last_scout_preview.created_at).toLocaleString() : 'None yet'} />
            <OpRow label="Production DB write" value="Impossible" good />
            <OpRow label="Trade execution" value="Impossible" good />
          </div>
        </ChartCard>
      </div>
    </div>
  );
}

const OpRow = ({ label, value, good }: { label: string; value?: React.ReactNode; good?: boolean }) => (
  <div className="flex items-center justify-between border-b border-gray-800/60 pb-1.5">
    <span className="text-gray-400">{label}</span>
    <span className={good ? 'text-emerald-400 font-medium' : 'text-gray-300'}>{value ?? '—'}</span>
  </div>
);

export function Account() {
  const { data, loading, error } = useFetch<any>('/account/summary');

  return (
    <div className="space-y-6 max-w-5xl">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white tracking-tight">Account Summary</h1>
        <ModeBadge />
      </div>
      {loading && <Loading />}
      {error && <ErrorMsg message={error} />}
      {data && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <StatCard title="Starting Equity" value={`$${data.starting_equity?.toLocaleString()}`} />
          <StatCard title="Current Equity" value={`$${data.current_equity?.toLocaleString()}`} />
          <StatCard 
            title="Net PnL" 
            value={
              <span className={data.net_pnl >= 0 ? "text-green-500" : "text-red-500"}>
                {data.net_pnl >= 0 ? '+' : ''}{data.net_pnl?.toLocaleString()}
              </span>
            } 
          />
          <StatCard title="Win Rate" value={`${(data.win_rate).toFixed(1)}%`} />
          <StatCard title="Total Trades" value={data.total_trades} />
        </div>
      )}
    </div>
  );
}

export function Portfolio() {
  const { data, loading, error, refresh } = useFetch<any[]>('/positions/open');
  const [sellTicket, setSellTicket] = useState<{ ticker: string; qty: number } | null>(null);

  return (
    <div className="space-y-6 max-w-6xl">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white tracking-tight">Open Portfolio</h1>
        <ModeBadge />
      </div>
      {loading && <Loading />}
      {error && <ErrorMsg message={error} />}
      {data && data.length === 0 && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-8 text-center space-y-3">
          <div className="text-gray-500 text-lg">No open positions.</div>
          <p className="text-sm text-gray-600">Simulate a buy in Scout or Analyze to see it here.</p>
        </div>
      )}
      {data && data.length > 0 && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
          <table className="w-full text-left text-sm text-gray-300">
            <thead className="bg-gray-800 text-gray-400 uppercase text-xs">
              <tr>
                <th className="px-6 py-4 font-semibold uppercase">Ticker</th>
                <th className="px-6 py-4 font-semibold uppercase">Qty</th>
                <th className="px-6 py-4 font-semibold uppercase">Avg Entry</th>
                <th className="px-6 py-4 font-semibold uppercase">Stop</th>
                <th className="px-6 py-4 font-semibold uppercase">TP1</th>
                <th className="px-6 py-4 font-semibold uppercase">State</th>
                <th className="px-6 py-4 font-semibold uppercase text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800/50">
              {data.map((pos: any, i: number) => (
                <tr key={i} className="hover:bg-gray-800/30 transition-colors">
                  <td className="px-6 py-4 whitespace-nowrap font-medium text-white">{pos.ticker}</td>
                  <td className="px-6 py-4 whitespace-nowrap">{pos.current_position_size ?? 'N/A'}</td>
                  <td className="px-6 py-4 whitespace-nowrap">{pos.avg_cost ? `$${pos.avg_cost.toFixed(2)}` : 'N/A'}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-red-400">N/A</td>
                  <td className="px-6 py-4 whitespace-nowrap text-green-400">{pos.tp1_price ? `$${pos.tp1_price.toFixed(2)}` : 'N/A'}</td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-500/10 text-blue-400 border border-blue-500/20">
                      {pos.position_state}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right space-x-2">
                    <Link to="/journal" className="text-xs bg-gray-800 hover:bg-gray-700 text-white px-3 py-1.5 rounded transition-colors font-semibold">Note</Link>
                    <button 
                      onClick={() => setSellTicket({ ticker: pos.ticker, qty: pos.current_position_size || 0 })}
                      className="text-xs bg-red-600/10 hover:bg-red-600/20 text-red-500 px-3 py-1.5 rounded transition-colors font-semibold"
                    >
                      Sell (Sbox)
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {sellTicket && (
        <TradeTicket 
          type="SELL"
          initialTicker={sellTicket.ticker}
          initialQty={sellTicket.qty}
          onClose={() => setSellTicket(null)}
          onSuccess={refresh}
        />
      )}
    </div>
  );
}

export function Performance() {

  const { data, loading, error } = useFetch<any>('/performance/summary');

  return (
    <div className="space-y-6 max-w-5xl">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white tracking-tight">Performance Metrics</h1>
        <ModeBadge />
      </div>
      {loading && <Loading />}
      {error && <ErrorMsg message={error} />}
      {data && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <StatCard title="Total Trades" value={data.total_trades} />
          <StatCard title="Winners" value={data.winners} />
          <StatCard 
            title="Total PnL" 
            value={
              <span className={data.total_pnl >= 0 ? "text-green-500" : "text-red-500"}>
                {data.total_pnl >= 0 ? '+' : ''}{data.total_pnl?.toLocaleString()}
              </span>
            } 
          />
          <StatCard title="Avg R" value={data.avg_r ? `${data.avg_r.toFixed(2)}R` : '-'} />
          <StatCard title="Best Trade" value={data.best_r ? <span className="text-green-500">{data.best_r.toFixed(2)}R</span> : '-'} />
          <StatCard title="Worst Trade" value={data.worst_r && data.worst_r < 0 ? <span className="text-red-500">{data.worst_r.toFixed(2)}R</span> : <span className="text-gray-400">N/A</span>} />
        </div>
      )}
    </div>
  );
}

export function History() {
  const { data, loading, error } = useFetch<any[]>('/history/transactions');

  const exportCsv = () => {
    if (!data || data.length === 0) return;
    const headers = ['Date', 'Ticker', 'Type', 'Qty', 'Price', 'Notional'];
    const rows = data.map(tx => [
      new Date(tx.execution_time).toISOString(),
      tx.ticker,
      tx.transaction_type,
      tx.quantity,
      tx.fill_price,
      tx.quantity * tx.fill_price
    ]);
    const csvContent = "data:text/csv;charset=utf-8," 
      + headers.join(',') + '\n' 
      + rows.map(e => e.join(',')).join('\n');
      
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", "sandbox_transactions.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="space-y-6 max-w-6xl">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white tracking-tight">Transaction History</h1>
        <div className="flex gap-3">
          <button onClick={exportCsv} disabled={!data || data.length === 0} className="px-4 py-2 bg-gray-800 hover:bg-gray-700 disabled:opacity-50 text-white rounded-lg font-bold text-sm transition-colors border border-gray-700">Export CSV</button>
          <ModeBadge />
        </div>
      </div>
      {loading && <Loading />}
      {error && <ErrorMsg message={error} />}
      {data && data.length === 0 && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-8 text-center space-y-3">
          <div className="text-gray-500 text-lg">No simulated transactions yet.</div>
          <p className="text-sm text-gray-600">Execute a sandbox trade to start filling your history.</p>
        </div>
      )}
      {data && data.length > 0 && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
          <table className="w-full text-left text-sm text-gray-300">
            <thead className="bg-gray-800 text-gray-400 uppercase text-xs">
              <tr>
                <th className="px-6 py-4 font-semibold uppercase">Date</th>
                <th className="px-6 py-4 font-semibold uppercase">Ticker</th>
                <th className="px-6 py-4 font-semibold uppercase">Type</th>
                <th className="px-6 py-4 font-semibold uppercase">Qty</th>
                <th className="px-6 py-4 font-semibold uppercase">Price</th>
                <th className="px-6 py-4 font-semibold uppercase">Notional</th>
                <th className="px-6 py-4 font-semibold uppercase text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800/50">
              {data.map((tx: any, i: number) => (
                <tr key={i} className="hover:bg-gray-800/30 transition-colors">
                  <td className="px-6 py-4 whitespace-nowrap text-gray-400">
                    {new Date(tx.execution_time).toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap font-medium text-white">{tx.ticker}</td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${
                      tx.transaction_type === 'BUY' 
                        ? 'bg-green-500/10 text-green-400 border-green-500/20' 
                        : 'bg-red-500/10 text-red-400 border-red-500/20'
                    }`}>
                      {tx.transaction_type}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">{tx.quantity ?? 'N/A'}</td>
                  <td className="px-6 py-4 whitespace-nowrap">{tx.fill_price ? `$${tx.fill_price.toFixed(2)}` : 'N/A'}</td>
                  <td className="px-6 py-4 whitespace-nowrap">{tx.quantity && tx.fill_price ? `$${(tx.quantity * tx.fill_price).toFixed(2)}` : 'N/A'}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-right">
                    <Link to="/journal" className="text-xs bg-gray-800 hover:bg-gray-700 text-white px-3 py-1.5 rounded transition-colors font-semibold">Note</Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export function Settings() {
  const { data: health, loading: healthLoading } = useFetch<any>('/system/health');
  const { data: version, loading: versionLoading } = useFetch<any>('/system/version');
  const { data: config, loading: configLoading } = useFetch<any>('/system/config');
  const { data: integrations, loading: integrationsLoading } = useFetch<any>('/integrations/status');
  const { data: safety, loading: safetyLoading } = useFetch<any>('/system/safety-matrix');
  const { data: secretStatus, loading: secretLoading } = useFetch<any>('/system/secret-status');
  const { data: dbGate, loading: dbGateLoading } = useFetch<any>('/system/db-gate-status');
  const { data: livePreview, loading: livePreviewLoading } = useFetch<any>('/system/live-preview-status');
  const { data: providerStatus, loading: providerLoading } = useFetch<any>('/system/provider-readiness-status');
  
  const [testStatus, setTestStatus] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<{
    target: string; ok: boolean; message: string; timestamp: string;
  } | null>(null);
  const [testingTarget, setTestingTarget] = useState<string | null>(null);

  const loading = healthLoading || versionLoading || configLoading || integrationsLoading || safetyLoading || secretLoading || dbGateLoading || livePreviewLoading || providerLoading;

  const testIntegration = async (target: string) => {
    setTestingTarget(target);
    setTestResult(null);
    setTestStatus(null);
    const label = target.charAt(0).toUpperCase() + target.slice(1);
    try {
      const res = await api.post(`/integrations/${target}/test`);
      // Backend returns 200 with { success, message } even on a handled failure.
      const ok = res.data?.success !== false;
      setTestResult({
        target,
        ok,
        message: res.data?.message || (ok ? `${label} test passed.` : `${label} test failed.`),
        timestamp: new Date().toLocaleString(),
      });
    } catch (err: any) {
      setTestResult({
        target,
        ok: false,
        message: err.response?.data?.detail || err.message || `${label} test failed.`,
        timestamp: new Date().toLocaleString(),
      });
    } finally {
      setTestingTarget(null);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white tracking-tight">System &amp; Settings</h1>
        <ModeBadge />
      </div>

      <OperatingModePanel />

      {loading && <Loading />}

      {!loading && (
        <div className="space-y-6">
          {testStatus && (
            <div className="bg-blue-900/30 border border-blue-700/50 p-4 rounded-xl text-blue-200">
              {testStatus}
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-gray-800 p-6 border border-gray-700 hover:border-gray-600 rounded-xl space-y-4 md:col-span-2">
              <div className="flex items-center justify-between border-b border-gray-700 pb-2">
                <h3 className="text-lg font-medium text-white">Safety Matrix <span className="text-xs font-normal text-gray-500">(engineering diagnostics)</span></h3>
                <span className="text-[10px] uppercase tracking-wider text-gray-500">Raw internal state — see Operating Mode above for product status</span>
              </div>
              <p className="text-xs text-gray-400">This panel is read-only. It does not enable or disable features. Change environment flags only on the VPS. A WARNING here simply means live gates are enabled; the product operating mode is shown in the Operating Mode panel above.</p>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm mt-3">
                 <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-gray-400">Production DB Access</span>
                      <span className={safety?.allow_production_db ? "text-red-400 font-bold" : "text-green-400 font-bold"}>{safety?.allow_production_db ? "Enabled" : "Disabled"}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Database Path</span>
                      <span className="text-gray-300 font-mono text-xs">{safety?.db_path || '-'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Live Analyze Preview</span>
                      <span className={safety?.live_analyze_preview_enabled ? "text-blue-400 font-bold" : "text-gray-500 font-bold"}>{safety?.live_analyze_preview_enabled ? "Enabled" : "Disabled"}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Live Scout Preview</span>
                      <span className={safety?.live_scout_preview_enabled ? "text-blue-400 font-bold" : "text-gray-500 font-bold"}>{safety?.live_scout_preview_enabled ? "Enabled" : "Disabled"}</span>
                    </div>
                 </div>
                 
                 <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-gray-400">Alert Scheduler</span>
                      <span className={safety?.alert_scheduler_enabled ? "text-blue-400 font-bold" : "text-gray-500 font-bold"}>{safety?.alert_scheduler_enabled ? "Enabled" : "Disabled"}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Provider Coverage Scan</span>
                      <span className={safety?.provider_coverage_scan_enabled ? "text-blue-400 font-bold" : "text-gray-500 font-bold"}>{safety?.provider_coverage_scan_enabled ? "Enabled" : "Disabled"}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Telegram Bot</span>
                      <span className="text-gray-300 font-mono text-xs">{safety?.telegram_configured_masked || '-'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Anthropic AI</span>
                      <span className="text-gray-300 font-mono text-xs">{safety?.anthropic_configured_masked || '-'}</span>
                    </div>
                 </div>
              </div>
              
              <div className={`mt-4 p-3 rounded font-bold text-center border overflow-hidden ${
                  safety?.safety_state === 'SAFE' ? 'bg-green-900/30 text-green-400 border-green-700/50' :
                  safety?.safety_state === 'WARNING' ? 'bg-yellow-900/40 text-yellow-500 border-yellow-700/50' :
                  'bg-red-900/40 text-red-500 border-red-700/50'
              }`}>
                 Safety State: {safety?.safety_state || 'UNKNOWN'}
                 {safety?.mode_label && safety.mode_label !== safety.safety_state && (
                   <span className="ml-2 text-xs font-normal opacity-80">({safety.mode_label})</span>
                 )}
                 {safety?.safety_state === 'WARNING' && (
                   <div className="text-xs font-normal mt-1 text-yellow-600/90">
                     {(safety?.warning_reasons?.length ? safety.warning_reasons : ['One or more live-UAT gates are enabled.']).map((r: string, i: number) => (
                       <div key={i}>• {r}</div>
                     ))}
                   </div>
                 )}
                 {safety?.safety_state === 'UNSAFE' && (
                   <div className="text-xs font-normal mt-1 text-red-600/90">
                     {(safety?.unsafe_reasons?.length ? safety.unsafe_reasons : ['Production capabilities or paths are enabled.']).map((r: string, i: number) => (
                       <div key={i}>• {r}</div>
                     ))}
                   </div>
                 )}
              </div>
            </div>

            <div className="bg-gray-800 p-6 border border-gray-700 rounded-xl space-y-4">
              <h3 className="text-lg font-medium text-white border-b border-gray-700 pb-2">Status & Version</h3>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between items-center">
                  <span className="text-gray-400">System Health</span>
                  <span className="flex items-center text-green-400">
                    <span className="w-2 h-2 rounded-full bg-green-500 mr-2"></span>
                    {health?.status || 'Unknown'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">GHBS Server</span>
                  <span className="text-white font-mono">{version?.ghbs_version || '-'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">TASI Engine</span>
                  <span className="text-white font-mono">{version?.tasi_version || '-'}</span>
                </div>
              </div>
            </div>
            
            <div className="bg-gray-800 p-6 border border-gray-700 rounded-xl space-y-4">
              <h3 className="text-lg font-medium text-white border-b border-gray-700 pb-2">Secret Status (Phase 6S)</h3>
              <p className="text-xs text-gray-400">
                Configured only means the value exists in .env. Operational use remains disabled until later phases.
              </p>
              <div className="space-y-3 text-sm mt-3">
                <div className="flex justify-between">
                  <span className="text-gray-400">Anthropic API Key</span>
                  <span className={secretStatus?.anthropic?.configured ? "text-green-400 font-bold" : "text-gray-500"}>
                    {secretStatus?.anthropic?.configured ? "Configured" : "Missing"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Telegram Bot Token</span>
                  <span className={secretStatus?.telegram?.bot_token_configured ? "text-green-400 font-bold" : "text-gray-500"}>
                    {secretStatus?.telegram?.bot_token_configured ? "Configured" : "Missing"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Telegram Chat ID</span>
                  <span className={secretStatus?.telegram?.chat_id_configured ? "text-green-400 font-bold" : "text-gray-500"}>
                    {secretStatus?.telegram?.chat_id_configured ? "Configured" : "Missing"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">TwelveData API Key</span>
                  <span className={secretStatus?.market_data?.twelvedata_configured ? "text-green-400 font-bold" : "text-gray-500"}>
                    {secretStatus?.market_data?.twelvedata_configured ? "Configured" : "Missing"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">SahmK API Key</span>
                  <span className={secretStatus?.market_data?.sahmk_configured ? "text-green-400 font-bold" : "text-gray-500"}>
                    {secretStatus?.market_data?.sahmk_configured ? "Configured" : "Missing"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">TradingView API Key</span>
                  <span className={secretStatus?.market_data?.tradingview_configured ? "text-green-400 font-bold" : "text-gray-500"}>
                    {secretStatus?.market_data?.tradingview_configured ? "Configured" : "Missing"}
                  </span>
                </div>
              </div>
            </div>

            <div className="bg-gray-800 p-6 border border-gray-700 rounded-xl space-y-4">
              <h3 className="text-lg font-medium text-white border-b border-gray-700 pb-2">DB Gate Status (Phase 6T)</h3>
              <p className="text-xs text-gray-400">
                This gate verifies read-only access only. The application database remains sandbox unless a later phase explicitly changes it.
              </p>
              <div className="space-y-3 text-sm mt-3">
                <div className="flex justify-between">
                  <span className="text-gray-400">Production DB Gate</span>
                  <span className={dbGate?.gate_enabled ? "text-green-400 font-bold" : "text-gray-500"}>
                    {dbGate?.gate_enabled ? "Enabled" : "Locked"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Production DB Path</span>
                  <span className={dbGate?.production_db_path_configured ? "text-green-400 font-bold" : "text-gray-500"}>
                    {dbGate?.production_db_path_configured ? "Configured" : "Missing"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Read-only Required</span>
                  <span className={dbGate?.readonly_required ? "text-green-400 font-bold" : "text-red-500 font-bold"}>
                    {dbGate?.readonly_required ? "Yes" : "No"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Read-only Connection</span>
                  <span className={
                    dbGate?.readonly_connection_ok ? "text-green-400 font-bold" : 
                    dbGate?.gate_locked ? "text-gray-500" : "text-red-500 font-bold"
                  }>
                    {dbGate?.readonly_connection_ok ? "OK" : dbGate?.gate_locked ? "Not attempted" : "Failed"}
                  </span>
                </div>
                {dbGate?.readonly_connection_ok && (
                  <div className="bg-gray-900/50 p-3 rounded mt-2">
                    <span className="text-gray-400 text-xs block mb-1">Detected Legacy Tables ({dbGate.detected_tables_count} total):</span>
                    <span className="text-gray-300 font-mono text-xs">{dbGate.detected_known_legacy_tables?.join(", ") || "None"}</span>
                  </div>
                )}
              </div>
            </div>

            <div className="bg-gray-800 p-6 border border-gray-700 rounded-xl space-y-4">
              <h3 className="text-lg font-medium text-white border-b border-gray-700 pb-2">Live Preview Status (Phase 6U)</h3>
              <p className="text-xs text-gray-400">
                Live Preview is manual-only. It does not execute trades, send Telegram alerts, run scheduled scans, or write to production DB.
              </p>
              <div className="space-y-3 text-sm mt-3">
                <div className="flex justify-between">
                  <span className="text-gray-400">Live Analyze Preview</span>
                  <span className={livePreview?.live_analyze_preview_enabled ? "text-blue-400 font-bold" : "text-gray-500 font-bold"}>
                    {livePreview?.live_analyze_preview_enabled ? "Enabled" : "Locked"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Live Scout Preview</span>
                  <span className={livePreview?.live_scout_preview_enabled ? "text-blue-400 font-bold" : "text-gray-500 font-bold"}>
                    {livePreview?.live_scout_preview_enabled ? "Enabled" : "Locked"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Scheduler</span>
                  <span className={livePreview?.scheduler_enabled ? "text-red-400 font-bold" : "text-green-400 font-bold"}>
                    {livePreview?.scheduler_enabled ? "Enabled" : "Disabled"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Provider Coverage Scan</span>
                  <span className={livePreview?.provider_coverage_scan_enabled ? "text-red-400 font-bold" : "text-green-400 font-bold"}>
                    {livePreview?.provider_coverage_scan_enabled ? "Enabled" : "Disabled"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Execution</span>
                  <span className={livePreview?.broker_execution_enabled ? "text-red-400 font-bold" : "text-green-400 font-bold"}>
                    {livePreview?.broker_execution_enabled ? "Enabled" : "Disabled"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Telegram Sending</span>
                  <span className={livePreview?.telegram_send_enabled ? "text-red-400 font-bold" : "text-green-400 font-bold"}>
                    {livePreview?.telegram_send_enabled ? "Enabled" : "Disabled"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Production DB Write</span>
                  <span className={livePreview?.production_db_write_enabled ? "text-red-400 font-bold" : "text-green-400 font-bold"}>
                    {livePreview?.production_db_write_enabled ? "Enabled" : "Disabled"}
                  </span>
                </div>
                <div className="flex justify-between border-t border-gray-700/50 pt-2 mt-2">
                  <span className="text-gray-400">Safety State</span>
                  <span className={livePreview?.safety_state === 'SAFE' ? "text-green-400 font-bold" : "text-red-500 font-bold"}>
                    {livePreview?.safety_state}
                  </span>
                </div>
              </div>
            </div>

            <div className="bg-gray-800 p-6 border border-gray-700 rounded-xl space-y-4">
              <h3 className="text-lg font-medium text-white border-b border-gray-700 pb-2">Provider Readiness (Phase 6V)</h3>
              <p className="text-xs text-gray-400">
                Shows configured providers and active fallback order. API keys are masked.
              </p>
              <div className="space-y-3 text-sm mt-3">
                <div className="flex justify-between">
                  <span className="text-gray-400">Provider Calls Locked</span>
                  <span className={providerStatus?.provider_calls_locked ? "text-green-400 font-bold" : "text-yellow-500 font-bold"}>
                    {providerStatus?.provider_calls_locked ? "Locked" : "Unlocked"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Smoke Tests</span>
                  <span className={providerStatus?.market_data_smoke_tests_enabled ? "text-yellow-500 font-bold" : "text-gray-500"}>
                    {providerStatus?.market_data_smoke_tests_enabled ? "Enabled" : "Locked"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Coverage Scan</span>
                  <span className={providerStatus?.provider_coverage_scan_enabled ? "text-red-500 font-bold" : "text-gray-500"}>
                    {providerStatus?.provider_coverage_scan_enabled ? "Enabled" : "Locked"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Default Provider</span>
                  <span className="text-white font-mono text-xs">{providerStatus?.default_provider}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Fallback Order</span>
                  <span className="text-gray-300 font-mono text-xs">{providerStatus?.fallback_order?.join(" > ")}</span>
                </div>
                <div className="border-t border-gray-700/50 pt-2 mt-2">
                  <span className="text-gray-400 text-xs block mb-1">Provider Config Status:</span>
                  <div className="space-y-1">
                    {providerStatus?.providers && Object.entries(providerStatus.providers).map(([name, p]: [string, any]) => (
                      <div key={name} className="flex justify-between text-xs pl-2">
                        <span className="text-gray-300 capitalize">{name}</span>
                        <span className={p.configured ? "text-blue-400" : "text-gray-500"}>{p.configured ? "Configured" : "Missing"}</span>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="flex justify-between border-t border-gray-700/50 pt-2 mt-2">
                  <span className="text-gray-400">Safety State</span>
                  <span className={providerStatus?.safety_state === 'SAFE' ? "text-green-400 font-bold" : providerStatus?.safety_state === 'WARNING' ? "text-yellow-500 font-bold" : "text-red-500 font-bold"}>
                    {providerStatus?.safety_state}
                  </span>
                </div>
              </div>
            </div>

            <div className="bg-gray-800 p-6 border border-gray-700 rounded-xl space-y-4">
              <h3 className="text-lg font-medium text-white border-b border-gray-700 pb-2">Backend Config (Masked)</h3>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-400">Environment</span>
                  <span className="text-yellow-500 font-semibold">{config?.environment || 'sandbox'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Database Path</span>
                  <span className="text-gray-500 font-mono text-xs">{config?.db_path?.includes('test') ? config.db_path : 'Sandbox database (masked)'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Max Portfolio Heat</span>
                  <span className="text-white">{(config?.max_portfolio_heat * 100)?.toFixed(0) || 5}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Risk per Trade</span>
                  <span className="text-white">{(config?.risk_per_trade_pct * 100)?.toFixed(2) || 1.0}%</span>
                </div>
              </div>
            </div>
            
            <div className="bg-gray-800 p-6 border border-gray-700 rounded-xl space-y-4">
              <h3 className="text-lg font-medium text-white border-b border-gray-700 pb-2">Integration Status</h3>
              <div className="space-y-4 text-sm">
                <div className="space-y-2 pb-3 border-b border-gray-700/50">
                  <div className="flex justify-between">
                    <span className="text-gray-400">Anthropic AI</span>
                    <span className={integrations?.anthropic?.configured ? "text-green-400" : "text-gray-500"}>
                      {integrations?.anthropic?.status_text || 'Unknown'}
                    </span>
                  </div>
                  <button onClick={() => testIntegration('anthropic')} disabled={testingTarget === 'anthropic'} className="w-full py-2 bg-gray-700 hover:bg-gray-600 disabled:opacity-50 rounded text-xs font-semibold text-white transition-colors">
                    {testingTarget === 'anthropic' ? 'Testing Anthropic…' : 'Test Anthropic'}
                  </button>
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-gray-400">Telegram Alert Bot</span>
                    <span className={integrations?.telegram_alert_bot?.configured ? "text-green-400" : "text-gray-500"}>
                      {integrations?.telegram_alert_bot?.status_text || 'Unknown'}
                    </span>
                  </div>
                  {integrations?.telegram_alert_bot?.token_source && integrations.telegram_alert_bot.token_source !== 'missing' && (
                    <div className="flex justify-between text-xs">
                      <span className="text-gray-500">Token source</span>
                      <span className="text-gray-400 font-mono">{integrations.telegram_alert_bot.token_source}</span>
                    </div>
                  )}
                  <button onClick={() => testIntegration('telegram')} disabled={testingTarget === 'telegram'} className="w-full py-2 bg-gray-700 hover:bg-gray-600 disabled:opacity-50 rounded text-xs font-semibold text-white transition-colors">
                    {testingTarget === 'telegram' ? 'Testing Telegram…' : 'Test Telegram'}
                  </button>
                  <p className="text-xs text-gray-500 text-center mt-2">Smoke test only. No trading action will occur.</p>
                </div>

                {testResult && (
                  <div className={`mt-2 p-3 rounded border text-xs space-y-1 ${
                      testResult.ok ? 'bg-green-900/20 border-green-700/40 text-green-300'
                                    : 'bg-red-900/20 border-red-700/40 text-red-300'
                  }`}>
                    <div className="flex justify-between font-semibold">
                      <span>{testResult.target.charAt(0).toUpperCase() + testResult.target.slice(1)} test</span>
                      <span>{testResult.ok ? 'SUCCESS' : 'FAILED'}</span>
                    </div>
                    <div className="break-words">{testResult.message}</div>
                    <div className="text-gray-500">{testResult.timestamp}</div>
                  </div>
                )}
              </div>
            </div>

            <div className="bg-gray-800 p-6 border border-gray-700 rounded-xl space-y-4">
              <h3 className="text-lg font-medium text-white border-b border-gray-700 pb-2">Manual Alerts</h3>
              <div className="space-y-4 text-sm">
                <p className="text-gray-400">Send a manual Telegram notification to verify alert delivery pipeline.</p>
                <div className="bg-blue-900/20 border border-blue-700/30 p-3 rounded text-blue-300 text-xs text-center">
                  Manual notification test only. No trading action, no scheduler, and no live signal execution.
                </div>
                <button 
                  onClick={async () => {
                    setTestStatus('Sending manual alert...');
                    try {
                      const res = await api.post('/alerts/manual-test');
                      setTestStatus(res.data.message || 'Manual alert sent successfully.');
                    } catch (err: any) {
                      setTestStatus(`Manual alert failed: ${err.response?.data?.detail || err.message}`);
                    }
                  }}
                  className="w-full py-2 bg-blue-600 hover:bg-blue-500 rounded text-xs font-semibold text-white transition-colors"
                >
                  Send Manual Telegram Alert
                </button>
              </div>
            </div>

          </div>
        </div>
      )}
    </div>
  );
}
