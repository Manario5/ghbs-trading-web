import React, { useState } from 'react';
import { api } from '../services/api';
import { TradeTicket } from '../components/TradeTicket';
import { ActionPlanDrawer } from '../components/ActionPlanDrawer';

export function Scout() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [buyTicket, setBuyTicket] = useState<{ ticker: string } | null>(null);

  // Live Scout Preview State
  const [liveScoutData, setLiveScoutData] = useState<any>(null);
  const [liveScoutLoading, setLiveScoutLoading] = useState(false);
  const [liveScoutError, setLiveScoutError] = useState('');
  
  // Sorting/Filters for Live Scout
  const [filterSignal, setFilterSignal] = useState('ALL');
  const [filterSetup, setFilterSetup] = useState('ALL');
  const [filterTier, setFilterTier] = useState('ALL');
  const [filterSector, setFilterSector] = useState('ALL');
  const [filterQuality, setFilterQuality] = useState('ALL');
  const [buyOnly, setBuyOnly] = useState(false);
  const [topN, setTopN] = useState<number | ''>('');

  const runScout = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await api.post('/scout/run');
      setData(res.data);
    } catch (err: any) {
      setError(err.message || 'Scout failed');
    } finally {
      setLoading(false);
    }
  };

  const runLiveScoutPreview = async () => {
    setLiveScoutLoading(true);
    setLiveScoutError('');
    setLiveScoutData(null);
    try {
      const res = await api.post('/live-preview/scout', {
        filters: {
           signal: filterSignal,
           setup_type: filterSetup,
           tier: filterTier,
           sector: filterSector,
           data_quality: filterQuality,
           buy_only: buyOnly,
           top_n: topN
        }
      });
      setLiveScoutData(res.data);
    } catch (err: any) {
      setLiveScoutError(err.response?.data?.detail || err.message || 'Live Scout Preview failed');
    } finally {
      setLiveScoutLoading(false);
    }
  };

  const handleActionPlan = async (ticker: string, setupType: string, actionType: string) => {
    try {
      await api.post('/action-plan', {
        ticker: ticker,
        action_type: actionType,
        notes: `From Scout: ${setupType}`
      });
      alert(`Simulation: Added ${ticker} to Action Plan as ${actionType}`);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to add to action plan');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold text-white tracking-tight">Market Scout</h1>
          <div className="bg-yellow-900/20 text-yellow-500 px-3 py-1.5 rounded-md text-xs font-bold border border-yellow-700/30 flex items-center gap-1.5 mt-1">
            <span>⚡</span> SANDBOX MODE
          </div>
        </div>
        <button 
          onClick={runScout} 
          disabled={loading}
          className="px-6 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg disabled:bg-blue-800 font-bold shadow-lg transition-all"
        >
          {loading ? 'Scanning...' : 'Run Analysis (Sandbox)'}
        </button>
      </div>

      {error && <div className="text-red-500 bg-red-900/10 border border-red-500/20 p-4 rounded-xl text-sm">{error}</div>}

      {data && (
        <div className="bg-gray-950 border border-gray-800 rounded-2xl p-6 shadow-xl space-y-6">
           <div className="flex flex-wrap items-center gap-3">
              {data.mocked_data && (
                <div className="bg-yellow-900/20 text-yellow-500 px-3 py-1 rounded-md text-xs font-bold border border-yellow-700/30">
                  ⚡ MOCKED DATA : TRUE
                </div>
              )}
              <div className="bg-gray-800/50 text-gray-400 px-3 py-1 rounded-md text-xs font-medium border border-gray-700">
                Found {data.fetched} stocks
              </div>
           </div>

           <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
             <div className="bg-gray-900/50 p-4 rounded-xl border border-gray-800">
               <div className="text-xs text-gray-500 uppercase font-bold mb-1">Market Regime</div>
               <div className={clsx("text-xl font-bold", data.regime === 'GREEN' ? "text-green-500" : "text-red-500")}>{data.regime}</div>
             </div>
             <div className="bg-gray-900/50 p-4 rounded-xl border border-gray-800">
               <div className="text-xs text-gray-500 uppercase font-bold mb-1">Success Criteria</div>
               <div className="text-xl font-bold text-white">{data.actionable}/{data.fetched}</div>
             </div>
             <div className="bg-gray-900/50 p-4 rounded-xl border border-gray-800">
               <div className="text-xs text-gray-500 uppercase font-bold mb-1">Actionable</div>
               <div className="text-xl font-bold text-green-500">{(data.actionable / data.fetched * 100).toFixed(1)}%</div>
             </div>
             <div className="bg-gray-900/50 p-4 rounded-xl border border-gray-800">
               <div className="text-xs text-gray-500 uppercase font-bold mb-1">Blocked</div>
               <div className="text-xl font-bold text-red-500">{data.blocked}</div>
             </div>
           </div>

           <div className="space-y-3">
             <h3 className="text-sm font-bold text-gray-400 uppercase tracking-widest px-1">Candidate Signals</h3>
             <div className="space-y-2">
               {data.results?.map((r: any, i: number) => (
                  <div key={i} className="flex items-center justify-between bg-gray-900/50 hover:bg-gray-900 border border-gray-800 hover:border-gray-700 p-4 rounded-xl transition-all group">
                     <div className="flex items-center space-x-4">
                        <div className="w-10 h-10 bg-gray-800 rounded-lg flex items-center justify-center font-bold text-white">{r.ticker}</div>
                        <div>
                          <div className="text-sm font-bold text-white">{r.setup_type || 'Setup'}</div>
                          <div className={clsx("text-[10px] font-bold uppercase", r.actionable ? "text-green-500" : "text-gray-500")}>
                            {r.actionable ? 'Actionable Signal' : 'Blocked (Rule Guard)'}
                          </div>
                        </div>
                     </div>
                     <div className="flex items-center space-x-2 opacity-0 group-hover:opacity-100 transition-all">
                       {r.actionable && (
                         <button 
                           onClick={() => setBuyTicket({ ticker: r.ticker })}
                           className="bg-green-600 hover:bg-green-500 text-white text-xs font-bold px-3 py-2 rounded-lg shadow-lg transition-all"
                         >
                           Ticket
                         </button>
                       )}
                       <button onClick={() => handleActionPlan(r.ticker, r.setup_type, 'Plan Buy')} className="bg-gray-800 hover:bg-gray-700 text-white px-3 py-2 rounded-lg text-xs font-bold transition-all">Plan</button>
                       <button onClick={() => handleActionPlan(r.ticker, r.setup_type, 'Watch Closely')} className="bg-gray-800 hover:bg-gray-700 text-white px-3 py-2 rounded-lg text-xs font-bold transition-all">Watch</button>
                       <button onClick={() => handleActionPlan(r.ticker, r.setup_type, 'Ignore')} className="bg-gray-800 hover:bg-gray-700 text-white px-3 py-2 rounded-lg text-xs font-bold transition-all">Ignore</button>
                     </div>
                  </div>
               ))}
             </div>
           </div>
        </div>
      )}

      {/* --- Live Scout Preview Section --- */}
      <div className="mt-12 bg-gray-900 border border-indigo-700/50 rounded-lg p-6 space-y-4 relative overflow-hidden">
        <div className="absolute top-0 right-0 bg-indigo-600/20 text-indigo-400 px-4 py-1 text-xs font-bold tracking-widest rounded-bl-lg">
          READ-ONLY PREVIEW
        </div>
        
        <h2 className="text-xl font-bold text-indigo-400">Live Data Scout Preview</h2>
        <p className="text-sm text-gray-400 mb-4">
          Read-only live-data scout preview only. No trade execution, no alerts, no scheduler, no action plans, and no production DB.
        </p>

        <div className="flex gap-4">
          <button 
            onClick={runLiveScoutPreview}
            disabled={liveScoutLoading}
            className="px-6 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-md disabled:bg-indigo-800 font-semibold transition-all"
          >
            {liveScoutLoading ? 'Scanning...' : 'Run Live Scout Preview'}
          </button>
        </div>

        {liveScoutError && (
          <div className="space-y-2">
            <div className="text-red-500 bg-red-900/20 p-4 rounded text-sm">{liveScoutError}</div>
            {!liveScoutData && <div className="text-gray-500 text-sm italic">No live preview result available.</div>}
          </div>
        )}

        {liveScoutData && (
          <div className="space-y-4 mt-6">
            <div className="bg-orange-900/40 border border-orange-700/50 p-3 rounded text-sm text-orange-400 font-medium">
              <span className="mr-2">⚠️</span>
              LIVE DATA PREVIEW • SANDBOX ONLY • NO EXECUTION • NO ALERTS • NOT USED FOR TRADE RECORDING
            </div>

            <div className="bg-gray-800/30 border border-gray-700/50 p-4 rounded-lg space-y-4">
              <div className="flex flex-wrap items-center gap-4 text-sm">
                <div className="flex flex-col">
                  <label className="text-gray-500 text-xs font-bold uppercase mb-1">Signal</label>
                  <select className="bg-gray-900 border border-gray-700 rounded p-1 text-white" value={filterSignal} onChange={e => setFilterSignal(e.target.value)}>
                    <option value="ALL">All</option>
                    <option value="BUY">BUY</option>
                    <option value="HOLD">HOLD</option>
                  </select>
                </div>
                <div className="flex flex-col">
                  <label className="text-gray-500 text-xs font-bold uppercase mb-1">Setup Type</label>
                  <select className="bg-gray-900 border border-gray-700 rounded p-1 text-white" value={filterSetup} onChange={e => setFilterSetup(e.target.value)}>
                    <option value="ALL">All</option>
                    {Array.from(new Set(liveScoutData.results?.map((r: any) => r.setup_type).filter(Boolean) || [])).map((s: any) => (
                      <option key={s} value={s}>{s}</option>
                    ))}
                  </select>
                </div>
                <div className="flex flex-col">
                  <label className="text-gray-500 text-xs font-bold uppercase mb-1">Tier</label>
                  <select className="bg-gray-900 border border-gray-700 rounded p-1 text-white" value={filterTier} onChange={e => setFilterTier(e.target.value)}>
                    <option value="ALL">All</option>
                    <option value="TIER_1">Tier 1</option>
                    <option value="TIER_2">Tier 2</option>
                  </select>
                </div>
                <div className="flex flex-col">
                  <label className="text-gray-500 text-xs font-bold uppercase mb-1">Data Quality</label>
                  <select className="bg-gray-900 border border-gray-700 rounded p-1 text-white" value={filterQuality} onChange={e => setFilterQuality(e.target.value)}>
                    <option value="ALL">All</option>
                    <option value="OK">OK</option>
                    <option value="WARNINGS">WARNINGS</option>
                    <option value="FAIL">FAIL</option>
                  </select>
                </div>
                <div className="flex flex-col justify-end h-full pt-5">
                  <label className="flex items-center space-x-2 text-white cursor-pointer">
                    <input type="checkbox" className="form-checkbox text-indigo-500 rounded bg-gray-900 border-gray-700" checked={buyOnly} onChange={e => setBuyOnly(e.target.checked)} />
                    <span>Buy Only</span>
                  </label>
                </div>
                <div className="flex flex-col">
                  <label className="text-gray-500 text-xs font-bold uppercase mb-1">Top N</label>
                  <input type="number" className="bg-gray-900 w-20 border border-gray-700 rounded p-1 text-white" value={topN} onChange={e => setTopN(e.target.value === '' ? '' : Number(e.target.value))} placeholder="All" />
                </div>
              </div>
              <div className="text-xs text-indigo-400 font-medium">Candidate score is read-only and for review only. It does not change strategy logic and does not create trades, alerts, or action plans.</div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
               <div className="bg-gray-800/50 p-4 rounded-xl border border-gray-700">
                 <div className="text-xs text-gray-500 uppercase font-bold mb-1">Scanned</div>
                 <div className="text-xl font-bold text-white uppercase">{liveScoutData.scanned_count} <span className="text-sm font-normal text-gray-500">/ {liveScoutData.universe_size}</span></div>
               </div>
               <div className="bg-gray-800/50 p-4 rounded-xl border border-gray-700">
                 <div className="text-xs text-gray-500 uppercase font-bold mb-1">Eligible</div>
                 <div className="text-xl font-bold text-green-400 uppercase">{liveScoutData.eligible_count}</div>
               </div>
               <div className="bg-gray-800/50 p-4 rounded-xl border border-gray-700">
                 <div className="text-xs text-gray-500 uppercase font-bold mb-1">Blocked</div>
                 <div className="text-xl font-bold text-red-500">{liveScoutData.blocked_count}</div>
               </div>
               <div className="bg-gray-800/50 p-4 rounded-xl border border-gray-700">
                 <div className="text-xs text-gray-500 uppercase font-bold mb-1">Data Failures</div>
                 <div className="text-xl font-bold text-orange-400">{liveScoutData.data_quality_failures}</div>
               </div>
            </div>

            <div className="overflow-x-auto border border-gray-800 rounded-xl">
              <table className="w-full text-left text-sm text-gray-400 whitespace-nowrap">
                <thead className="bg-gray-900/50 text-xs uppercase font-bold text-gray-500 border-b border-gray-800">
                  <tr>
                    <th className="px-4 py-3">Rank</th>
                    <th className="px-4 py-3">Score</th>
                    <th className="px-4 py-3">Review Bucket</th>
                    <th className="px-4 py-3">Ticker</th>
                    <th className="px-4 py-3">Provider Ticker</th>
                    <th className="px-4 py-3">Sector / Tier</th>
                    <th className="px-4 py-3 text-right">Close</th>
                    <th className="px-4 py-3 text-right">Vol</th>
                    <th className="px-4 py-3 text-center">Regime</th>
                    <th className="px-4 py-3">Setup</th>
                    <th className="px-4 py-3 text-center">Signal</th>
                    <th className="px-4 py-3">Health</th>
                    <th className="px-4 py-3 text-center">Diagnose</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-800/50">
                  {(() => {
                    let filtered = liveScoutData.results || [];
                    if (filterSignal !== 'ALL') filtered = filtered.filter((r: any) => r.signal === filterSignal);
                    if (filterSetup !== 'ALL') filtered = filtered.filter((r: any) => r.setup_type === filterSetup);
                    if (filterTier !== 'ALL') filtered = filtered.filter((r: any) => r.tier === filterTier);
                    if (filterQuality !== 'ALL') filtered = filtered.filter((r: any) => r.data_quality === filterQuality);
                    if (buyOnly) filtered = filtered.filter((r: any) => r.signal === 'BUY');
                    if (topN !== '') filtered = filtered.slice(0, Number(topN));
                    
                    return filtered.map((item: any, idx: number) => (
                      <ScoutRow key={idx} item={item} />
                    ));
                  })()}
                </tbody>
              </table>
            </div>

          </div>
        )}
      </div>

      {buyTicket && (
        <TradeTicket 
          type="BUY"
          initialTicker={buyTicket.ticker}
          onClose={() => setBuyTicket(null)}
          onSuccess={() => alert('Sandbox buy recorded.')}
        />
      )}
    </div>
  );
}

const ScoutRow: React.FC<{ item: any }> = ({ item }) => {
  const [expanded, setExpanded] = useState(false);
  const [showActionPlan, setShowActionPlan] = useState(false);
  
  return (
    <>
      <tr className="hover:bg-gray-800/20 bg-gray-900/20 transition-all border-b border-gray-800/50">
        <td className="px-4 py-3 font-mono text-gray-500">#{item.rank ?? '-'}</td>
        <td className="px-4 py-3 font-mono text-blue-400">{item.candidate_score ?? '-'}</td>
        <td className="px-4 py-3"><span className="text-[10px] uppercase font-bold text-gray-300">{item.review_bucket ?? '-'}</span></td>
        <td className="px-4 py-3 text-white font-bold">{item.ticker}</td>
        <td className="px-4 py-3 font-mono text-xs text-gray-400">{item.provider_ticker}</td>
        <td className="px-4 py-3 text-xs"><span className="text-gray-300">{item.sector}</span> <span className="opacity-50">/ {item.tier}</span></td>
        <td className="px-4 py-3 text-right font-mono text-green-400">{item.latest_close !== null ? `$${item.latest_close.toFixed(2)}` : 'N/A'}</td>
        <td className="px-4 py-3 text-right font-mono text-gray-400">{item.latest_volume !== null ? item.latest_volume.toLocaleString() : 'N/A'}</td>
        <td className="px-4 py-3 text-center text-blue-400 font-bold">{item.regime ?? 'N/A'}</td>
        <td className="px-4 py-3 text-gray-300 font-medium">{item.setup_type ?? 'N/A'}</td>
        <td className={clsx("px-4 py-3 text-center font-bold", item.signal === 'BUY' ? 'text-green-500' : 'text-gray-500')}>{item.signal ?? 'N/A'}</td>
        <td className="px-4 py-3">
            {item.data_quality === 'OK' ? (
              <span className="text-green-400 bg-green-400/10 px-2 py-0.5 rounded text-[10px] font-bold">OK</span>
            ) : (
              <span className="text-red-400 bg-red-400/10 px-2 py-0.5 rounded text-[10px] font-bold" title={item.warnings?.join(' | ')}>{item.data_quality ?? 'FAIL'}</span>
            )}
        </td>
        <td className="px-4 py-3 text-center flex items-center justify-end gap-2">
          <button 
            onClick={() => setExpanded(!expanded)}
            className="text-xs bg-indigo-600/20 hover:bg-indigo-600/40 text-indigo-400 font-semibold px-2 py-1 rounded transition-colors"
          >
            {expanded ? 'Hide' : 'Details'}
          </button>
          <button 
            onClick={() => setShowActionPlan(true)}
            className="text-xs bg-green-600/20 hover:bg-green-600/40 text-green-400 font-semibold px-2 py-1 rounded transition-colors"
          >
            Action Plan
          </button>
        </td>
      </tr>
      {showActionPlan && (
        <ActionPlanDrawer candidate={item} onClose={() => setShowActionPlan(false)} />
      )}
      {expanded && (
        <tr className="bg-gray-950">
          <td colSpan={13} className="px-6 py-4">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 text-sm">
              <div className="space-y-2">
                <div className="text-xs text-indigo-400 uppercase font-bold">Diagnostic Summary</div>
                <div className="font-mono text-xs bg-gray-900 border border-gray-800 p-2 rounded text-gray-300 leading-relaxed break-all">
                  {item.diagnostic_summary || 'N/A'}
                </div>
                {item.signal_reasons?.length > 0 && (
                  <div className="mt-2">
                    <div className="text-[10px] text-green-500 uppercase font-bold">Signal Reasons</div>
                    <ul className="text-xs text-gray-400 ml-3 list-disc marker:text-green-500/50 mt-1">
                      {item.signal_reasons.map((r: string, i: number) => <li key={i}>{r}</li>)}
                    </ul>
                  </div>
                )}
                {item.blocking_reasons?.length > 0 && (
                  <div className="mt-2">
                    <div className="text-[10px] text-red-500/80 uppercase font-bold">Blocking Reasons</div>
                    <ul className="text-xs text-gray-400 ml-3 list-disc marker:text-red-500/50 mt-1">
                      {item.blocking_reasons.map((r: string, i: number) => <li key={i}>{r}</li>)}
                    </ul>
                  </div>
                )}
              </div>
              <div className="space-y-2">
                <div className="text-xs text-indigo-400 uppercase font-bold">Indicators</div>
                <div className="bg-gray-900 border border-gray-800 p-3 rounded font-mono text-xs space-y-1.5 text-gray-400">
                  <div className="flex justify-between"><span>RSI</span> <span className="text-white">{item.indicator_snapshot?.RSI !== null && item.indicator_snapshot?.RSI !== undefined ? item.indicator_snapshot.RSI.toFixed(2) : 'N/A'}</span></div>
                  <div className="flex justify-between"><span>ADX</span> <span className="text-white">{item.indicator_snapshot?.ADX !== null && item.indicator_snapshot?.ADX !== undefined ? item.indicator_snapshot.ADX.toFixed(2) : 'N/A'}</span></div>
                  <div className="flex justify-between"><span>Vol Ratio</span> <span className="text-white">{item.indicator_snapshot?.volume_ratio !== null && item.indicator_snapshot?.volume_ratio !== undefined ? item.indicator_snapshot.volume_ratio.toFixed(2) : 'N/A'}</span></div>
                  <div className="flex justify-between"><span>vs BB Upper</span> <span className={item.indicator_snapshot?.close_vs_bb_upper > 0 ? 'text-green-400' : 'text-gray-400'}>{item.indicator_snapshot?.close_vs_bb_upper !== null && item.indicator_snapshot?.close_vs_bb_upper !== undefined ? item.indicator_snapshot.close_vs_bb_upper.toFixed(2) : 'N/A'}</span></div>
                  <div className="flex justify-between"><span>vs BB Lower</span> <span className={item.indicator_snapshot?.close_vs_bb_lower < 0 ? 'text-red-400' : 'text-gray-400'}>{item.indicator_snapshot?.close_vs_bb_lower !== null && item.indicator_snapshot?.close_vs_bb_lower !== undefined ? item.indicator_snapshot.close_vs_bb_lower.toFixed(2) : 'N/A'}</span></div>
                  <div className="flex justify-between"><span>vs MA20</span> <span>{item.indicator_snapshot?.close_vs_ma20 !== null && item.indicator_snapshot?.close_vs_ma20 !== undefined ? item.indicator_snapshot.close_vs_ma20.toFixed(2) : 'N/A'}</span></div>
                </div>
              </div>
              <div className="space-y-2">
                <div className="text-xs text-indigo-400 uppercase font-bold">Thresholds Checked</div>
                <div className="bg-gray-900 border border-gray-800 p-3 rounded font-mono text-xs space-y-1.5 text-gray-500">
                  <div className="flex justify-between"><span>ADX Reqd</span> <span>{item.thresholds_snapshot?.adx_threshold_used ?? 'N/A'}</span></div>
                  <div className="flex justify-between"><span>Vol Reqd</span> <span>{item.thresholds_snapshot?.vol_surge_threshold_used ?? 'N/A'}</span></div>
                  <div className="flex justify-between"><span>RSI Oversold</span> <span>{item.thresholds_snapshot?.rsi_oversold_threshold_used ?? 'N/A'}</span></div>
                  <div className="flex justify-between"><span>RSI Overbought</span> <span>{item.thresholds_snapshot?.rsi_overbought_threshold_used ?? 'N/A'}</span></div>
                  <div className="flex justify-between"><span>Min Bars</span> <span>{item.thresholds_snapshot?.min_required_bars ?? 'N/A'}</span></div>
                </div>
              </div>
              <div className="space-y-2">
                <div className="text-xs text-indigo-400 uppercase font-bold">Score Components</div>
                <div className="text-[10px] text-gray-500 mb-1">Display-only score components.</div>
                {item.score_components ? (
                  <div className="bg-gray-900 border border-gray-800 p-3 rounded font-mono text-xs space-y-1.5 text-gray-400">
                    {Object.entries(item.score_components).map(([k, v]) => (
                      <div key={k} className="flex justify-between"><span>{k}</span> <span className="text-white">{v as string}</span></div>
                    ))}
                    <div className="flex justify-between border-t border-gray-800 pt-1 mt-1 text-blue-400 font-bold"><span>Total</span> <span>{item.candidate_score}</span></div>
                  </div>
                ) : (
                  <div className="text-xs text-gray-600">N/A</div>
                )}
              </div>
            </div>
          </td>
        </tr>
      )}
    </>
  );
}

function clsx(...classes: string[]) {
  return classes.filter(Boolean).join(' ');
}

