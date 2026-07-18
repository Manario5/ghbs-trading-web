import React, { useState } from 'react';
import { clsx } from 'clsx';

interface ActionPlanDrawerProps {
  candidate: any;
  onClose: () => void;
}

export function ActionPlanDrawer({ candidate, onClose }: ActionPlanDrawerProps) {
  const [copiedMap, setCopiedMap] = useState<Record<string, boolean>>({});

  if (!candidate) return null;

  const signal = candidate.signal || 'HOLD';
  const isBuy = signal === 'BUY';
  const isSell = signal === 'SELL';
  
  const copyToClipboard = async (text: string, id: string) => {
    let success = false;
    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(text);
        success = true;
      } else {
        const textArea = document.createElement("textarea");
        textArea.value = text;
        textArea.style.position = "fixed";
        textArea.style.left = "-999999px";
        textArea.style.top = "-999999px";
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();

        try {
          document.execCommand('copy');
          success = true;
        } catch (err) {
          console.error("execCommand error", err);
        }
        textArea.remove();
      }
    } catch (err) {
      console.error("clipboard writeText error", err);
    }

    if (success) {
      setCopiedMap(prev => ({ ...prev, [id]: true }));
      setTimeout(() => {
        setCopiedMap(prev => ({ ...prev, [id]: false }));
      }, 1500);
    } else {
      alert("Copy failed — select text manually");
    }
  };

  const CommandRow = ({ id, command }: { id: string, command: string }) => {
    const isCopied = copiedMap[id];
    return (
       <div className="flex justify-between items-center bg-gray-900 border border-gray-800 p-2 rounded">
         <div className="font-mono text-xs text-gray-300 truncate mr-2" title={command}>
           {command}
         </div>
         <button 
           onClick={() => copyToClipboard(command, id)} 
           className={clsx(
             "text-xs px-2 py-1 rounded font-bold uppercase transition-colors shrink-0",
             isCopied ? "bg-green-500/20 text-green-400" : "bg-indigo-500/10 text-indigo-400 hover:text-indigo-300"
           )}
         >
           {isCopied ? "Copied" : "Copy"}
         </button>
       </div>
    );
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80">
      <div className="bg-gray-900 border border-gray-700 rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col overflow-hidden">
        {/* Header */}
        <div className="flex justify-between items-center p-4 border-b border-gray-800 bg-gray-800/40">
          <div className="flex items-center gap-3">
            <h2 className="text-xl font-bold text-white">Action Plan</h2>
            <span className="font-mono text-gray-400">{candidate.ticker}</span>
            <span className={clsx(
              "px-2 py-0.5 rounded text-[10px] uppercase font-bold",
              isBuy ? "bg-green-500/20 text-green-400" :
              isSell ? "bg-red-500/20 text-red-400" :
              "bg-gray-700 text-gray-300"
            )}>
              {signal}
            </span>
          </div>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-300 p-1">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-6 text-sm">
          {/* Risk Reminder */}
          <div className="bg-orange-500/10 border border-orange-500/20 p-3 rounded-lg text-orange-400 flex gap-2 items-start shrink-0">
            <svg className="w-5 h-5 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
            <p className="text-xs font-semibold leading-relaxed break-words whitespace-normal text-wrap">
              This is a manual action plan. It does not place orders. Always execute in Derayah first, then record the fill in Telegram.
            </p>
          </div>

          {/* Candidate Summary */}
          <section className="space-y-3">
            <h3 className="text-sm font-bold text-gray-300 flex items-center gap-2">
              <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
              Candidate Summary
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 bg-gray-800/30 p-4 rounded-lg border border-gray-700/50">
              <div><div className="text-[10px] uppercase text-gray-500 font-bold mb-1">Tier / Segment</div> <div className="text-white font-mono">{candidate.tier || '—'} <span className="opacity-50">/</span> {candidate.sector || candidate.segment || '—'}</div></div>
              <div><div className="text-[10px] uppercase text-gray-500 font-bold mb-1">Setup Type</div> <div className="text-indigo-400 font-bold">{candidate.setup_type || '—'}</div></div>
              <div><div className="text-[10px] uppercase text-gray-500 font-bold mb-1">Market Regime</div> <div className="text-blue-400 font-bold">{candidate.regime || '—'}</div></div>
              <div>
                <div className="text-[10px] uppercase text-gray-500 font-bold mb-1">Status</div> 
                <div className={candidate.signal === 'BUY' ? 'text-green-400 font-bold' : 'text-gray-400 font-bold'}>
                  {candidate.signal === 'BUY' ? 'ACTIONABLE' : 'BLOCKED'}
                </div>
              </div>
            </div>
            {candidate.diagnostic_summary && (
              <div className="mt-2 bg-gray-800/80 p-3 rounded font-mono text-xs text-gray-300 leading-relaxed border border-gray-700/50">
                <span className="text-[10px] uppercase font-bold text-gray-500 block mb-1">Mechanical Reason</span>
                {candidate.diagnostic_summary}
              </div>
            )}
          </section>

          {/* Technical Snapshot */}
          <section className="space-y-3">
            <h3 className="text-sm font-bold text-gray-300 flex items-center gap-2">
              <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>
              Technical Snapshot
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 bg-gray-800/30 p-4 rounded-lg border border-gray-700/50">
              <div><div className="text-[10px] uppercase text-gray-500 font-bold mb-1">Close Price</div> <div className="text-white font-mono">{candidate.latest_close ? `$${candidate.latest_close.toFixed(2)}` : '—'}</div></div>
              <div><div className="text-[10px] uppercase text-gray-500 font-bold mb-1">Vol Ratio</div> <div className="text-white font-mono">{candidate.indicator_snapshot?.volume_ratio ? candidate.indicator_snapshot.volume_ratio.toFixed(2) : '—'}</div></div>
              <div><div className="text-[10px] uppercase text-gray-500 font-bold mb-1">RSI</div> <div className="text-white font-mono">{candidate.indicator_snapshot?.RSI ? candidate.indicator_snapshot.RSI.toFixed(2) : '—'}</div></div>
              <div><div className="text-[10px] uppercase text-gray-500 font-bold mb-1">ADX</div> <div className="text-white font-mono">{candidate.indicator_snapshot?.ADX ? candidate.indicator_snapshot.ADX.toFixed(2) : '—'}</div></div>
            </div>
          </section>

          {/* Trade Plan */}
          <section className="space-y-3">
             <h3 className="text-sm font-bold text-gray-300 flex items-center gap-2">
              <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2v1m-6 4h.01M13 10h.01M10 14h.01M14 14h.01m-2 4h.01M14 18h.01" /></svg>
              Trade Plan
             </h3>
             <div className="bg-gray-800/30 p-4 rounded-lg border border-gray-700/50">
               {isBuy ? (
                 candidate.sizing_preview ? (
                   <div className="space-y-4">
                     <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                        <div><div className="text-[10px] uppercase text-gray-500 font-bold mb-1">Suggested Entry</div><div className="text-white font-mono">{candidate.latest_close ? `$${candidate.latest_close.toFixed(2)}` : 'Market'}</div></div>
                        <div><div className="text-[10px] uppercase text-gray-500 font-bold mb-1">Shares</div><div className="text-green-400 font-bold font-mono">{candidate.sizing_preview}</div></div>
                        <div><div className="text-[10px] uppercase text-gray-500 font-bold mb-1">Notional</div><div className="text-white font-mono">{candidate.latest_close && candidate.sizing_preview ? `$${(candidate.latest_close * candidate.sizing_preview).toFixed(2)}` : '—'}</div></div>
                        <div><div className="text-[10px] uppercase text-gray-500 font-bold mb-1">Stop Loss</div><div className="text-red-400 font-bold font-mono">{candidate.stop_preview ? `$${candidate.stop_preview.toFixed(2)}` : '—'}</div></div>
                     </div>
                     <p className="text-[10px] text-gray-500">Note: This sizing preview is based on a simulated 100k account. Actual amounts will vary by your account size.</p>
                   </div>
                 ) : (
                   <div className="text-xs text-gray-400">Buy signal present, but sizing preview data is unavailable. Evaluate manual size based on stop loss constraints.</div>
                 )
               ) : isSell ? (
                 <div className="text-sm font-bold text-red-400">Review existing position before action.</div>
               ) : (
                 <div className="text-sm font-bold text-gray-400">No trade action recommended. Waiting for setup criteria to improve.</div>
               )}
             </div>
          </section>

          {/* Manual Execution Checklist */}
          {isBuy && (
            <section className="space-y-3">
              <h3 className="text-sm font-bold text-gray-300 flex items-center gap-2">
                <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                Manual Execution Checklist
              </h3>
              <ul className="list-none space-y-2 text-xs text-gray-300">
                <li className="flex items-center gap-2"><input type="checkbox" className="rounded bg-gray-800 border-gray-600 text-indigo-500" /> Confirm live price in Derayah</li>
                <li className="flex items-center gap-2"><input type="checkbox" className="rounded bg-gray-800 border-gray-600 text-indigo-500" /> Confirm spread/liquidity is acceptable</li>
                <li className="flex items-center gap-2"><input type="checkbox" className="rounded bg-gray-800 border-gray-600 text-indigo-500" /> Confirm market regime is not worsening</li>
                <li className="flex items-center gap-2"><input type="checkbox" className="rounded bg-gray-800 border-gray-600 text-indigo-500" /> Confirm position heat is below limit</li>
                <li className="flex items-center gap-2"><input type="checkbox" className="rounded bg-gray-800 border-gray-600 text-indigo-500" /> Execute manually in Derayah only</li>
                <li className="flex items-center gap-2"><input type="checkbox" className="rounded bg-gray-800 border-gray-600 text-indigo-500" /> Confirm fill in Telegram bot</li>
              </ul>
            </section>
          )}

          {/* Telegram Command Helper */}
          {isBuy && (
            <section className="space-y-3 pb-4">
              <h3 className="text-sm font-bold text-gray-300 flex items-center gap-2">
                <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" /></svg>
                Telegram Command Helper
              </h3>
              <div className="bg-gray-950 border border-gray-800 rounded-lg p-3 space-y-3 overflow-hidden">
                 <CommandRow id="buy" command={`/buy ${candidate.ticker} <fill_price> ${candidate.sizing_preview || '<qty>'}`} />
                 <CommandRow id="tp1" command={`/sell ${candidate.ticker} <tp1_fill_price> <tp1_qty>`} />
                 <CommandRow id="tp2" command={`/sell ${candidate.ticker} <tp2_fill_price> <tp2_qty>`} />
                 <CommandRow id="tp3" command={`/sell ${candidate.ticker} <tp3_fill_price>`} />
                 <CommandRow id="stop" command={`/sell ${candidate.ticker} <stop_fill_price>`} />
                 <div className="text-[10px] text-gray-500 mt-1 break-words whitespace-normal">Replace &lt;fill_price&gt; and other placeholders with your actual executed price.</div>
              </div>
            </section>
          )}
        </div>
      </div>
    </div>
  );
}
