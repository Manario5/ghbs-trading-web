import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../services/api';
import { TradeTicket } from '../components/TradeTicket';

import { ActionPlanDrawer } from '../components/ActionPlanDrawer';

function LivePreviewAuditLog() {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchLogs();
  }, []);

  const [selectedLog, setSelectedLog] = useState<any>(null);
  const [detailsLoading, setDetailsLoading] = useState(false);
  const [actionPlanCandidate, setActionPlanCandidate] = useState<any>(null);

  const fetchLogDetails = async (id: number) => {
    setDetailsLoading(true);
    try {
      const res = await api.get(`/live-preview/runs/${id}`);
      setSelectedLog(res.data);
    } catch (e) {
      console.error(e);
      alert('Failed to load log details.');
    } finally {
      setDetailsLoading(false);
    }
  };

  const closeDetails = () => setSelectedLog(null);

  const fetchLogs = async () => {
    try {
      const res = await api.get('/live-preview/runs');
      setLogs(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const exportCsv = () => {
    if (logs.length === 0) return;
    const headers = ["ID", "Created At", "Type", "Provider", "Requested Ticker", "Scanned", "Eligible", "Blocked", "Data Failures"];
    const csvContent = "data:text/csv;charset=utf-8," + 
      headers.join(",") + "\n" +
      logs.map(log => {
        return [
          log.id,
          log.created_at,
          log.preview_type,
          log.provider,
          log.requested_ticker || "N/A",
          log.scanned_count,
          log.eligible_count,
          log.blocked_count,
          log.data_failures
        ].join(",");
      }).join("\n");
      
    const encodeUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodeUri);
    link.setAttribute("download", "live_preview_audit_logs.csv");
    document.body.appendChild(link);
    link.click();
    link.remove();
  };

  return (
    <div className="mt-12 bg-gray-900 border border-gray-800 rounded-lg p-6 space-y-4 relative overflow-hidden">
        <h2 className="text-xl font-bold text-gray-300">Live Preview Audit Log</h2>
        <p className="text-sm text-gray-500 mb-4">
          Read-only preview audit only. These logs are not trades, alerts, action plans, or execution records.
        </p>

        <div className="flex gap-4 mb-4">
          <button 
            onClick={fetchLogs}
            className="px-4 py-2 bg-gray-800 hover:bg-gray-700 text-white rounded-md text-sm transition-all"
          >
            Refresh
          </button>
          <button 
            onClick={exportCsv}
            disabled={logs.length === 0}
            className="px-4 py-2 bg-indigo-600/20 hover:bg-indigo-600/40 text-indigo-400 rounded-md text-sm disabled:opacity-50 transition-all font-semibold"
          >
            Export CSV
          </button>
        </div>

        {loading ? (
          <div className="text-gray-500 py-4">Loading logs...</div>
        ) : logs.length === 0 ? (
          <div className="text-gray-500 py-4">No audit logs found.</div>
        ) : (
          <div className="overflow-x-auto border border-gray-800 rounded-xl">
            <table className="w-full text-left text-sm text-gray-400 whitespace-nowrap">
              <thead className="bg-gray-900/50 text-xs uppercase font-bold text-gray-500 border-b border-gray-800">
                <tr>
                  <th className="px-4 py-3">ID</th>
                  <th className="px-4 py-3">Time</th>
                  <th className="px-4 py-3">Type</th>
                  <th className="px-4 py-3">Provider</th>
                  <th className="px-4 py-3">Requested Ticker</th>
                  <th className="px-4 py-3 text-right">Scanned</th>
                  <th className="px-4 py-3 text-right">Eligible</th>
                  <th className="px-4 py-3 text-right">Blocked</th>
                  <th className="px-4 py-3 text-right">Failures</th>
                  <th className="px-4 py-3"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800/50">
                {logs.map((log) => (
                  <tr key={log.id} className="hover:bg-gray-800/20">
                    <td className="px-4 py-3 text-gray-500">{log.id}</td>
                    <td className="px-4 py-3 font-mono text-xs">{new Date(log.created_at).toLocaleString()}</td>
                    <td className="px-4 py-3 text-blue-400 font-bold uppercase text-[10px]">{log.preview_type}</td>
                    <td className="px-4 py-3 text-xs">{log.provider}</td>
                    <td className="px-4 py-3 font-bold text-white">{log.requested_ticker || '—'}</td>
                    <td className="px-4 py-3 text-right text-gray-300">{log.scanned_count}</td>
                    <td className="px-4 py-3 text-right text-green-400 font-bold">{log.eligible_count}</td>
                    <td className="px-4 py-3 text-right text-red-400">{log.blocked_count}</td>
                    <td className="px-4 py-3 text-right text-orange-400">{log.data_failures}</td>
                    <td className="px-4 py-3 text-right">
                      <button className="text-xs text-indigo-400 hover:text-indigo-300 bg-indigo-500/10 hover:bg-indigo-500/20 px-2 py-1 rounded" onClick={() => fetchLogDetails(log.id)}>
                        {detailsLoading && selectedLog?.id === log.id ? 'Loading...' : 'Details'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {selectedLog && (
          <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4">
            <div className="bg-gray-900 border border-gray-700 rounded-lg shadow-xl w-full max-w-5xl max-h-[90vh] flex flex-col">
              {/* Header Summary */}
              <div className="p-4 border-b border-gray-800 flex justify-between items-center bg-gray-800/50">
                <div className="flex items-center gap-4">
                  <h3 className="text-lg font-bold text-white">Audit Details</h3>
                  <span className="text-xs font-mono text-gray-500">ID: {selectedLog.id}</span>
                  <span className={`px-2 py-0.5 rounded text-[10px] uppercase font-bold ${
                    selectedLog.status === 'success' ? 'bg-green-500/20 text-green-400' :
                    selectedLog.status === 'failed' ? 'bg-red-500/20 text-red-400' :
                    'bg-yellow-500/20 text-yellow-400'
                  }`}>
                    {selectedLog.status || 'UNKNOWN'}
                  </span>
                  <span className="px-2 py-0.5 rounded bg-blue-500/20 text-blue-400 text-[10px] uppercase font-bold">
                    {selectedLog.event_type || selectedLog.preview_type || 'TEST'}
                  </span>
                </div>
                <button onClick={closeDetails} className="text-gray-500 hover:text-gray-300">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                </button>
              </div>

              <div className="p-6 overflow-y-auto space-y-8 flex-1 text-sm">
                {/* Meta Overview */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pb-6 border-b border-gray-800 text-sm">
                   <div><div className="text-xs text-gray-500 uppercase font-bold mb-1">Provider</div> <div className="text-white">{selectedLog.provider || 'N/A'}</div></div>
                   <div><div className="text-xs text-gray-500 uppercase font-bold mb-1">Created At</div> <div className="text-white">{selectedLog.created_at ? new Date(selectedLog.created_at).toLocaleString() : 'N/A'}</div></div>
                   <div><div className="text-xs text-gray-500 uppercase font-bold mb-1">Requested Ticker</div> <div className="text-white">{selectedLog.requested_ticker || '—'}</div></div>
                   <div><div className="text-xs text-gray-500 uppercase font-bold mb-1">Market Regime</div> <div className="text-blue-400 font-bold">{selectedLog.summary?.regime || 'NEUTRAL'}</div></div>
                </div>

                {/* Scan Summary */}
                <div>
                   <h4 className="text-sm font-bold text-gray-300 mb-3 flex items-center gap-2">
                     <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>
                     Scan Summary
                   </h4>
                   <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-4">
                     <div className="bg-gray-800/40 border border-gray-700/50 p-3 rounded-lg text-center">
                       <div className="text-[10px] text-gray-500 uppercase font-bold">Fetched</div>
                       <div className="text-lg font-bold text-white">{selectedLog.summary?.fetched || selectedLog.scanned_count || 0}</div>
                     </div>
                     <div className="bg-gray-800/40 border border-gray-700/50 p-3 rounded-lg text-center">
                       <div className="text-[10px] text-gray-500 uppercase font-bold">Actionable</div>
                       <div className="text-lg font-bold text-green-400">{selectedLog.summary?.actionable || selectedLog.eligible_count || 0}</div>
                     </div>
                     <div className="bg-gray-800/40 border border-gray-700/50 p-3 rounded-lg text-center">
                       <div className="text-[10px] text-gray-500 uppercase font-bold">Blocked</div>
                       <div className="text-lg font-bold text-gray-400">{selectedLog.summary?.blocked || selectedLog.blocked_count || 0}</div>
                     </div>
                     <div className="bg-gray-800/40 border border-gray-700/50 p-3 rounded-lg text-center">
                       <div className="text-[10px] text-gray-500 uppercase font-bold">Signals</div>
                       <div className="text-lg font-bold text-indigo-400">{selectedLog.summary?.signals || 0}</div>
                     </div>
                     <div className="bg-red-900/10 border border-red-900/30 p-3 rounded-lg text-center">
                       <div className="text-[10px] text-red-500/70 uppercase font-bold">Failed</div>
                       <div className="text-lg font-bold text-red-400">{selectedLog.summary?.failed || selectedLog.data_failures || 0}</div>
                     </div>
                     <div className="bg-gray-800/40 border border-gray-700/50 p-3 rounded-lg text-center">
                       <div className="text-[10px] text-gray-500 uppercase font-bold">Claude Calls</div>
                       <div className="text-lg font-bold text-purple-400">{selectedLog.summary?.claude_calls || 0}</div>
                     </div>
                   </div>
                </div>

                {/* Filters Applied */}
                <div>
                   <h4 className="text-sm font-bold text-gray-300 mb-3 flex items-center gap-2">
                     <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" /></svg>
                     Filters Applied
                   </h4>
                   {(!selectedLog.filters_applied || Object.keys(selectedLog.filters_applied).length === 0) ? (
                     <div className="text-xs text-gray-600 italic">No filters applied.</div>
                   ) : (
                     <div className="flex flex-wrap gap-2">
                        {Object.entries(selectedLog.filters_applied).map(([key, val]) => (
                          <div key={key} className="bg-gray-800 border border-gray-700 px-3 py-1.5 rounded-full text-xs flex items-center gap-2">
                            <span className="text-gray-500">{key.replace('_', ' ')}</span>
                            <span className="text-gray-200 font-bold">{val === null || val === undefined || val === '' ? 'Not applied' : String(val)}</span>
                          </div>
                        ))}
                     </div>
                   )}
                </div>

                {/* Warnings Section */}
                {selectedLog.warnings && selectedLog.warnings.length > 0 && (
                  <div className="bg-orange-500/10 border border-orange-500/20 p-4 rounded-lg">
                    <h4 className="text-sm font-bold text-orange-400 mb-2 flex items-center gap-2">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
                      Warnings & Data Failures
                    </h4>
                    <ul className="list-disc list-inside text-xs text-orange-300/80 space-y-1">
                      {selectedLog.warnings.map((w: string, i: number) => <li key={i}>{w}</li>)}
                    </ul>
                  </div>
                )}

                {/* Results Table */}
                {selectedLog.candidates && selectedLog.candidates.length > 0 && (
                  <div>
                    <h4 className="text-sm font-bold text-gray-300 mb-3 flex items-center gap-2">
                      <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                      Candidate Results
                    </h4>
                    <div className="overflow-x-auto border border-gray-800 rounded-lg">
                      <table className="w-full text-left text-xs whitespace-nowrap">
                        <thead className="bg-gray-800/50 text-gray-500 uppercase font-bold border-b border-gray-800">
                           <tr>
                             <th className="px-4 py-3">Ticker</th>
                             <th className="px-4 py-3">Tier / Segment</th>
                             <th className="px-4 py-3">Setup Type</th>
                             <th className="px-4 py-3">Claude Signal</th>
                             <th className="px-4 py-3">Actionable</th>
                             <th className="px-4 py-3">Signal</th>
                             <th className="px-4 py-3 text-right">Actions</th>
                           </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-800/50">
                          {selectedLog.candidates.map((c: any, i: number) => {
                            // Link complete details from raw_payload if available
                            let fullCandidate = c;
                            if (selectedLog.raw_payload) {
                               if (selectedLog.preview_type === 'analyze' && selectedLog.raw_payload.ticker === c.ticker) {
                                  fullCandidate = { ...selectedLog.raw_payload, ...c };
                               } else if (selectedLog.raw_payload.results) {
                                  const rawMatch = selectedLog.raw_payload.results.find((r:any) => r.ticker === c.ticker);
                                  if (rawMatch) fullCandidate = { ...rawMatch, ...c };
                               }
                            }
                            
                            return (
                              <tr key={i} className="hover:bg-gray-800/20">
                                <td className="px-4 py-3 font-bold text-white">{c.ticker || '—'}</td>
                                <td className="px-4 py-3 text-gray-400">{c.tier} <span className="opacity-50">/</span> {c.segment}</td>
                                <td className="px-4 py-3 text-indigo-300">{c.setup_type || '—'}</td>
                                <td className="px-4 py-3 text-gray-500">{c.claude_signal || '—'}</td>
                                <td className="px-4 py-3">
                                  {c.actionable ? 
                                    <span className="text-green-400 bg-green-400/10 px-2 py-0.5 rounded text-[10px] uppercase font-bold">Yes</span> :
                                    <span className="text-gray-500 bg-gray-800 px-2 py-0.5 rounded text-[10px] uppercase font-bold" title={c.mechanical_reason}>No</span>
                                  }
                                </td>
                                <td className="px-4 py-3">
                                  {c.signal === 'BUY' ? <span className="text-green-400 font-bold uppercase">{c.signal}</span> :
                                   c.signal === 'SELL' ? <span className="text-red-400 font-bold uppercase">{c.signal}</span> :
                                   <span className="text-gray-500 font-bold uppercase">{c.signal || 'HOLD'}</span>}
                                </td>
                                <td className="px-4 py-3 text-right">
                                  <button onClick={() => setActionPlanCandidate(fullCandidate)} className="text-xs bg-green-600/20 hover:bg-green-600/40 text-green-400 font-semibold px-2 py-1 rounded transition-colors">Action Plan</button>
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {actionPlanCandidate && (
                  <ActionPlanDrawer candidate={actionPlanCandidate} onClose={() => setActionPlanCandidate(null)} />
                )}

                {/* Collapsed Raw Payload */}
                <details className="group border border-gray-800 rounded-lg bg-gray-900/50">
                   <summary className="px-4 py-3 text-xs font-bold text-gray-500 uppercase cursor-pointer hover:text-gray-300 flex items-center justify-between">
                     Advanced: Raw Payload
                     <svg className="w-4 h-4 transition-transform group-open:rotate-180" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
                   </summary>
                   <div className="p-4 border-t border-gray-800">
                     <pre className="bg-gray-950 p-4 rounded text-[10px] text-gray-400 overflow-x-auto">
                       {JSON.stringify(selectedLog.raw_payload || {}, null, 2)}
                     </pre>
                   </div>
                </details>

              </div>
            </div>
          </div>
        )}
    </div>
  );
}

export function Analyze() {
  const [ticker, setTicker] = useState('2222');
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [buyTicket, setBuyTicket] = useState<{ ticker: string; price?: number; qty?: number } | null>(null);

  // Live Preview State
  const [liveTicker, setLiveTicker] = useState('2222');
  const [liveData, setLiveData] = useState<any>(null);
  const [liveLoading, setLiveLoading] = useState(false);
  const [liveError, setLiveError] = useState('');
  const [showActionPlan, setShowActionPlan] = useState(false);

  const runAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!ticker) return;
    
    setLoading(true);
    setError('');
    try {
      const res = await api.post(`/analyze/${ticker}`);
      setData(res.data);
    } catch (err: any) {
      setError(err.message || 'Analyze failed');
    } finally {
      setLoading(false);
    }
  };

  const runLivePreview = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!liveTicker) return;
    
    setLiveLoading(true);
    setLiveError('');
    setLiveData(null);
    try {
      const res = await api.post(`/live-preview/analyze/${liveTicker}`);
      setLiveData(res.data);
    } catch (err: any) {
      setLiveError(err.response?.data?.detail || err.message || 'Live Preview failed');
    } finally {
      setLiveLoading(false);
    }
  };

  const handleActionPlan = async (actionType: string) => {
    if (!data) return;
    try {
      await api.post('/action-plan', {
        ticker: data.ticker,
        action_type: actionType,
        planned_price: data.price || null,
        planned_quantity: data.proposal?.shares || null,
        notes: `From Analyze: ${data.setup_type} / ${data.market_regime}`
      });
      alert(`Simulation: Added ${data.ticker} to Action Plan as ${actionType}`);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to add to action plan');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold text-white tracking-tight">Analyze</h1>
          <div className="bg-yellow-900/20 text-yellow-500 px-3 py-1.5 rounded-md text-xs font-bold border border-yellow-700/30 flex items-center gap-1.5">
            <span>⚡</span> SANDBOX MODE
          </div>
        </div>
      </div>

      <form onSubmit={runAnalyze} className="flex gap-4">
        <input 
          value={ticker}
          onChange={e => setTicker(e.target.value)}
          placeholder="Ticker"
          className="bg-gray-800 border border-gray-700 rounded px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all uppercase" 
        />
        <button 
          type="submit"
          disabled={loading}
          className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md disabled:bg-blue-800 font-semibold"
        >
          {loading ? 'Analyzing...' : 'Analyze (Sandbox)'}
        </button>
      </form>

      {error && <div className="text-red-500 bg-red-900/20 p-4 rounded text-sm">{error}</div>}

      {data && (
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-6 space-y-4">
           {data.mocked_data && (
             <div className="bg-yellow-900/20 text-yellow-500 px-3 py-1.5 rounded-md inline-block text-xs font-bold border border-yellow-700/30">
               ⚡ MOCKED DATA : TRUE (SANDBOX)
             </div>
           )}

           <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
             <div className="space-y-4">
               <h3 className="text-lg font-medium text-white border-b border-gray-800 pb-2">Analysis Result for {data.ticker}</h3>
               <div className="bg-gray-800/50 p-4 rounded-xl border border-gray-700 space-y-3 text-sm">
                 <div className="flex justify-between"><span className="text-gray-400">Setup Type</span> <span className="text-white font-medium">{data.setup_type}</span></div>
                 <div className="flex justify-between"><span className="text-gray-400">Regime</span> <span className="text-white font-medium">{data.market_regime}</span></div>
                 <div className="flex justify-between">
                    <span className="text-gray-400">Claude Signal (Mock)</span> 
                    <span className={data.claude_signal_mocked === 'BUY' ? 'text-green-500 font-bold' : 'text-gray-400'}>{data.claude_signal_mocked}</span>
                 </div>
               </div>
               {data.mechanical_reason && (
                 <div className="bg-gray-800/80 p-4 border-l-4 border-yellow-500 rounded-lg text-sm text-gray-300 leading-relaxed italic">
                   "{data.mechanical_reason}"
                 </div>
               )}
             </div>

             {data.proposal && (
               <div className="space-y-4">
                 <h3 className="text-lg font-medium text-white border-b border-gray-800 pb-2">Sizing Proposal</h3>
                 <div className="bg-gray-800/50 p-4 rounded-xl border border-gray-700 space-y-3 text-sm font-mono">
                   <div className="flex justify-between"><span className="text-gray-400">Shares</span> <span className="text-green-400 font-bold">{data.proposal.shares}</span></div>
                   <div className="flex justify-between"><span className="text-gray-400">Notional</span> <span className="text-white">${data.proposal.notional.toLocaleString()}</span></div>
                   <div className="flex justify-between"><span className="text-gray-400">Risk Amount</span> <span className="text-red-400">${data.proposal.risk_amount.toFixed(2)}</span></div>
                   <div className="flex justify-between"><span className="text-gray-400">Stop Price</span> <span className="text-red-500 font-bold">${data.proposal.stop_price.toFixed(2)}</span></div>
                   <div className="flex justify-between"><span className="text-gray-400">TP1</span> <span className="text-green-500 font-bold">${data.proposal.tp1_price.toFixed(2)}</span></div>
                 </div>

                   <div className="pt-2 space-y-2">
                   <button 
                     onClick={() => setBuyTicket({ ticker: data.ticker, price: data.price, qty: data.proposal.shares })} 
                     className="w-full bg-green-600 hover:bg-green-500 text-white py-3 rounded-xl font-bold shadow-lg transition-all"
                   >
                     Create Sandbox Buy Ticket
                   </button>
                   
                   <div className="grid grid-cols-4 gap-2">
                     <button onClick={() => handleActionPlan('Plan Buy')} className="bg-gray-800 hover:bg-gray-700 text-white py-2 rounded-lg text-xs font-bold transition-all">Plan</button>
                     <button onClick={() => handleActionPlan('Watch Closely')} className="bg-gray-800 hover:bg-gray-700 text-white py-2 rounded-lg text-xs font-bold transition-all">Watch</button>
                     <button onClick={() => handleActionPlan('Ignore')} className="bg-gray-800 hover:bg-gray-700 text-white py-2 rounded-lg text-xs font-bold transition-all">Ignore</button>
                     <Link to="/journal" className="bg-gray-800 hover:bg-gray-700 text-white py-2 rounded-lg text-xs font-bold transition-all text-center leading-loose">Note</Link>
                   </div>
                   
                   <p className="text-[10px] text-gray-500 text-center mt-3 uppercase tracking-tighter">Sandbox only • No live execution</p>
                 </div>
               </div>
             )}
           </div>

        </div>
      )}

      {buyTicket && (
        <TradeTicket 
          type="BUY"
          initialTicker={buyTicket.ticker}
          initialPrice={buyTicket.price}
          initialQty={buyTicket.qty}
          onClose={() => setBuyTicket(null)}
          onSuccess={() => {
            alert('Sandbox buy recorded successfully.');
          }}
        />
      )}

      {/* --- Live Preview Section --- */}
      <div className="mt-12 bg-gray-900 border border-indigo-700/50 rounded-lg p-6 space-y-4 relative overflow-hidden">
        <div className="absolute top-0 right-0 bg-indigo-600/20 text-indigo-400 px-4 py-1 text-xs font-bold tracking-widest rounded-bl-lg">
          READ-ONLY PREVIEW
        </div>
        
        <h2 className="text-xl font-bold text-indigo-400">Live Data Preview</h2>
        <p className="text-sm text-gray-400 mb-4">
          Read-only live-data preview only. No trade execution, no alerts, no scheduler, and no production DB.
        </p>

        <form onSubmit={runLivePreview} className="flex gap-4">
          <input 
            value={liveTicker}
            onChange={e => setLiveTicker(e.target.value)}
            placeholder="Ticker"
            className="bg-gray-800 border border-gray-700 rounded px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all uppercase" 
          />
          <button 
            type="submit"
            disabled={liveLoading}
            className="px-6 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-md disabled:bg-indigo-800 font-semibold"
          >
            {liveLoading ? 'Fetching...' : 'Run Live Preview'}
          </button>
        </form>

        {liveError && (
          <div className="space-y-2">
            <div className="text-red-500 bg-red-900/20 p-4 rounded text-sm">{liveError}</div>
            {!liveData && <div className="text-gray-500 text-sm italic">No live preview result available.</div>}
          </div>
        )}

        {liveData && (
          <div className="space-y-4 mt-6">
            <div className="bg-orange-900/40 border border-orange-700/50 p-3 rounded text-sm text-orange-400 font-medium flex justify-between items-center">
              <div>
                <span className="mr-2">⚠️</span>
                LIVE DATA PREVIEW • SANDBOX ONLY • NO EXECUTION • NO ALERTS • NOT USED FOR TRADE RECORDING
              </div>
              <button 
                onClick={() => setShowActionPlan(true)}
                className="text-xs bg-green-600/20 hover:bg-green-600/40 text-green-400 font-bold px-3 py-1.5 rounded transition-colors"
              >
                Action Plan
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <h3 className="text-lg font-medium text-white border-b border-gray-800 pb-2">Data Quality & Setup</h3>
                <div className="bg-gray-800/50 p-4 rounded-xl border border-gray-700 space-y-3 text-sm">
                  <div className="flex justify-between"><span className="text-gray-400">Provider</span> <span className="text-white uppercase">{liveData.provider}</span></div>
                  <div className="flex justify-between"><span className="text-gray-400">Provider Ticker</span> <span className="text-white font-mono">{liveData.provider_ticker}</span></div>
                  <div className="flex justify-between"><span className="text-gray-400">Bars Returned</span> <span className="text-white">{liveData.bars_returned}</span></div>
                  <div className="flex justify-between"><span className="text-gray-400">Latest Close</span> <span className="text-green-400 font-mono">{liveData.latest_close !== null ? `$${liveData.latest_close.toFixed(2)}` : 'N/A'}</span></div>
                  <div className="flex justify-between"><span className="text-gray-400">Latest Volume</span> <span className="text-white">{liveData.latest_volume !== null ? liveData.latest_volume.toLocaleString() : 'N/A'}</span></div>
                  <div className="border-t border-gray-700 pt-3 mt-3"></div>
                  <div className="flex justify-between"><span className="text-gray-400">Data Quality</span> <span className={liveData.data_quality === 'OK' ? 'text-green-400' : 'text-red-400'}>{liveData.data_quality ?? 'N/A'}</span></div>
                  <div className="flex justify-between"><span className="text-gray-400">Regime</span> <span className="text-blue-400">{liveData.regime ?? 'N/A'}</span></div>
                  <div className="flex justify-between"><span className="text-gray-400">Setup Type</span> <span className="text-white">{liveData.setup_type ?? 'N/A'}</span></div>
                  <div className="flex justify-between border-t border-gray-700 pt-3 mt-3">
                    <span className="text-gray-400">Signal Preview</span>
                    <span className={liveData.signal === 'BUY' ? 'text-green-500 font-bold' : 'text-gray-500'}>{liveData.signal ?? 'N/A'}</span>
                  </div>
                </div>
                
                {liveData.warnings && liveData.warnings.length > 0 && (
                  <div className="bg-red-900/20 p-4 border border-red-900/50 rounded-lg text-sm text-red-400 space-y-1">
                    <div className="font-bold mb-2">Warnings:</div>
                    {liveData.warnings.map((w: string, i: number) => <div key={i}>• {w}</div>)}
                  </div>
                )}
              </div>

              {liveData.sizing_preview !== null && liveData.sizing_preview !== undefined && (
                <div className="space-y-4">
                  <h3 className="text-lg font-medium text-white border-b border-gray-800 pb-2">Sizing Preview</h3>
                  <div className="bg-gray-800/50 p-4 rounded-xl border border-gray-700 space-y-3 text-sm font-mono">
                    <div className="flex justify-between"><span className="text-gray-400">Predicted Shares</span> <span className="text-green-400 font-bold">{liveData.sizing_preview}</span></div>
                    <div className="flex justify-between"><span className="text-gray-400">Initial Stop</span> <span className="text-red-500">{liveData.stop_preview !== null && liveData.stop_preview !== undefined ? `$${liveData.stop_preview.toFixed(2)}` : 'N/A'}</span></div>
                  </div>
                  <p className="text-xs text-gray-500 mt-2">Sizing based on 100k static preview equity with real latest close.</p>
                </div>
              )}

              {liveData.diagnostic_summary && (
                <div className="space-y-4 md:col-span-2 mt-4">
                  <h3 className="text-lg font-medium text-indigo-400 border-b border-indigo-900/50 pb-2 flex items-center gap-2">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                    Why this signal?
                  </h3>
                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <div className="space-y-3">
                      <div className="text-xs text-gray-500 uppercase font-bold">Diagnostic Summary</div>
                      <div className="text-sm bg-gray-800/80 p-3 rounded-lg text-gray-300 font-mono">
                        {liveData.diagnostic_summary}
                      </div>

                      {liveData.signal_reasons?.length > 0 && (
                        <div className="space-y-1">
                          <div className="text-xs text-green-500 uppercase font-bold mt-4">Signal Reasons</div>
                          <ul className="text-sm space-y-1 text-gray-300 ml-4 list-disc marker:text-green-500">
                             {liveData.signal_reasons.map((r: string, i: number) => <li key={i}>{r}</li>)}
                          </ul>
                        </div>
                      )}
                      
                      {liveData.blocking_reasons?.length > 0 && (
                        <div className="space-y-1">
                          <div className="text-xs text-red-400 uppercase font-bold mt-4">Blocking Reasons</div>
                          <ul className="text-sm space-y-1 text-gray-300 ml-4 list-disc marker:text-red-500/50">
                             {liveData.blocking_reasons.map((r: string, i: number) => <li key={i}>{r}</li>)}
                          </ul>
                        </div>
                      )}
                    </div>

                    <div className="space-y-3">
                       <div className="text-xs text-gray-500 uppercase font-bold">Indicator Snapshot</div>
                       <div className="bg-gray-800/50 p-3 rounded-lg border border-gray-700/50 space-y-2 text-sm font-mono">
                          <div className="flex justify-between"><span className="text-gray-500">RSI</span> <span className="text-white">{liveData.indicator_snapshot?.RSI !== null && liveData.indicator_snapshot?.RSI !== undefined ? liveData.indicator_snapshot.RSI.toFixed(2) : 'N/A'}</span></div>
                          <div className="flex justify-between"><span className="text-gray-500">ADX</span> <span className="text-white">{liveData.indicator_snapshot?.ADX !== null && liveData.indicator_snapshot?.ADX !== undefined ? liveData.indicator_snapshot.ADX.toFixed(2) : 'N/A'}</span></div>
                          <div className="flex justify-between"><span className="text-gray-500">Vol Ratio</span> <span className="text-white">{liveData.indicator_snapshot?.volume_ratio !== null && liveData.indicator_snapshot?.volume_ratio !== undefined ? liveData.indicator_snapshot.volume_ratio.toFixed(2) : 'N/A'}</span></div>
                          <div className="flex justify-between" title="Close - BB Upper"><span className="text-gray-500">vs BB Upper</span> <span className={liveData.indicator_snapshot?.close_vs_bb_upper > 0 ? 'text-green-400' : 'text-gray-400'}>{liveData.indicator_snapshot?.close_vs_bb_upper !== null && liveData.indicator_snapshot?.close_vs_bb_upper !== undefined ? liveData.indicator_snapshot.close_vs_bb_upper.toFixed(2) : 'N/A'}</span></div>
                          <div className="flex justify-between" title="Close - BB Lower"><span className="text-gray-500">vs BB Lower</span> <span className={liveData.indicator_snapshot?.close_vs_bb_lower < 0 ? 'text-red-400' : 'text-gray-400'}>{liveData.indicator_snapshot?.close_vs_bb_lower !== null && liveData.indicator_snapshot?.close_vs_bb_lower !== undefined ? liveData.indicator_snapshot.close_vs_bb_lower.toFixed(2) : 'N/A'}</span></div>
                          <div className="flex justify-between" title="Close - MA20"><span className="text-gray-500">vs MA20</span> <span className="text-white">{liveData.indicator_snapshot?.close_vs_ma20 !== null && liveData.indicator_snapshot?.close_vs_ma20 !== undefined ? liveData.indicator_snapshot.close_vs_ma20.toFixed(2) : 'N/A'}</span></div>
                       </div>
                    </div>

                    <div className="space-y-3">
                       <div className="text-xs text-gray-500 uppercase font-bold">Thresholds Checked</div>
                       <div className="bg-gray-800/50 p-3 rounded-lg border border-gray-700/50 space-y-2 text-sm font-mono text-gray-400">
                          <div className="flex justify-between"><span>ADX Reqd</span> <span>{liveData.thresholds_snapshot?.adx_threshold_used ?? 'N/A'}</span></div>
                          <div className="flex justify-between"><span>Vol Reqd</span> <span>{liveData.thresholds_snapshot?.vol_surge_threshold_used ?? 'N/A'}</span></div>
                          <div className="flex justify-between"><span>RSI Oversold</span> <span>{liveData.thresholds_snapshot?.rsi_oversold_threshold_used ?? 'N/A'}</span></div>
                          <div className="flex justify-between"><span>RSI Overbought</span> <span>{liveData.thresholds_snapshot?.rsi_overbought_threshold_used ?? 'N/A'}</span></div>
                          <div className="flex justify-between"><span>Min Bars</span> <span>{liveData.thresholds_snapshot?.min_required_bars ?? 'N/A'}</span></div>
                       </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
            <div className="mt-4 p-4 text-xs font-mono text-gray-500 bg-gray-950 rounded border border-gray-800 break-all">
              {liveData.message}
            </div>
          </div>
        )}

        {showActionPlan && liveData && (
          <ActionPlanDrawer candidate={{...liveData, ticker: liveData.provider_ticker?.split('.')[0] || liveTicker}} onClose={() => setShowActionPlan(false)} />
        )}
      </div>
      
      <LivePreviewAuditLog />
    </div>
  );
}

