import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { AlertTriangle, Info, X } from 'lucide-react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: any[]) {
  return twMerge(clsx(inputs));
}

interface TradeTicketProps {
  type: 'BUY' | 'SELL';
  initialTicker?: string;
  initialPrice?: number;
  initialQty?: number;
  onClose: () => void;
  onSuccess: () => void;
}

export function TradeTicket({ type, initialTicker = '', initialPrice, initialQty, onClose, onSuccess }: TradeTicketProps) {
  const [ticker, setTicker] = useState(initialTicker);
  const [price, setPrice] = useState(initialPrice?.toString() || '');
  const [qty, setQty] = useState(initialQty?.toString() || '');
  const [riskData, setRiskData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [riskLoading, setRiskLoading] = useState(false);
  const [error, setError] = useState('');
  const [showConfirm, setShowConfirm] = useState(false);

  // Debounced risk check for Buy trades
  useEffect(() => {
    if (type === 'BUY' && ticker.length >= 4 && price && qty) {
      const timer = setTimeout(fetchRisk, 500);
      return () => clearTimeout(timer);
    } else {
      setRiskData(null);
    }
  }, [ticker, price, qty, type]);

  const fetchRisk = async () => {
    setRiskLoading(true);
    try {
      const res = await api.post('/risk/can-i-take-this-trade', {
        ticker: ticker.toUpperCase(),
        entry_price: parseFloat(price),
        qty: parseInt(qty)
      });
      setRiskData(res.data);
    } catch (err) {
      console.error('Risk check failed', err);
    } finally {
      setRiskLoading(false);
    }
  };

  const handleSubmit = async () => {
    setLoading(true);
    setError('');
    try {
      const endpoint = type === 'BUY' ? '/trades/buy' : '/trades/sell';
      await api.post(endpoint, {
        ticker: ticker.toUpperCase(),
        price: parseFloat(price),
        qty: parseInt(qty)
      });
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Trade failed');
    } finally {
      setLoading(false);
      setShowConfirm(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div className="bg-gray-900 border border-gray-800 w-full max-w-md rounded-2xl shadow-2xl overflow-hidden flex flex-col">
        {/* Header */}
        <div className={cn(
          "px-6 py-4 flex items-center justify-between border-b border-gray-800",
          type === 'BUY' ? "bg-green-900/10" : "bg-red-900/10"
        )}>
          <div className="flex items-center space-x-2">
            <div className={cn("w-2 h-2 rounded-full animate-pulse", type === 'BUY' ? "bg-green-500" : "bg-red-500")}></div>
            <h2 className="text-lg font-bold text-white tracking-tight">
              SANDBOX {type} TICKET
            </h2>
          </div>
          <button onClick={onClose} className="text-gray-500 hover:text-white transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 space-y-6 overflow-y-auto max-h-[80vh]">
          {/* Sandbox Warning */}
          <div className="bg-yellow-900/20 border border-yellow-700/30 rounded-xl p-3 flex gap-3 items-start">
             <AlertTriangle className="w-5 h-5 text-yellow-500 shrink-0 mt-0.5" />
             <div className="text-xs text-yellow-500/90 leading-relaxed">
               <strong>SANDBOX MODE:</strong> This records a simulated trade only. 
               No real order will be placed in Derayah. Manual execution required for live trading.
             </div>
          </div>

          {/* Form */}
          <div className="grid grid-cols-2 gap-4">
            <div className="col-span-2">
              <label className="block text-xs font-semibold text-gray-500 uppercase mb-1.5">Ticker</label>
              <input 
                value={ticker}
                onChange={e => setTicker(e.target.value)}
                placeholder="e.g. 2222"
                className="w-full bg-gray-950 border border-gray-800 rounded-lg px-4 py-2.5 text-white focus:ring-2 focus:ring-blue-500 outline-none transition-all uppercase"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-500 uppercase mb-1.5">Price (SAR)</label>
              <input 
                type="number"
                step="0.01"
                value={price}
                onChange={e => setPrice(e.target.value)}
                placeholder="0.00"
                className="w-full bg-gray-950 border border-gray-800 rounded-lg px-4 py-2.5 text-white focus:ring-2 focus:ring-blue-500 outline-none transition-all"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-500 uppercase mb-1.5">Quantity</label>
              <input 
                type="number"
                value={qty}
                onChange={e => setQty(e.target.value)}
                placeholder="0"
                className="w-full bg-gray-950 border border-gray-800 rounded-lg px-4 py-2.5 text-white focus:ring-2 focus:ring-blue-500 outline-none transition-all"
              />
            </div>
          </div>

          {/* Risk Preview (Only for Buy) */}
          {type === 'BUY' && (
            <div className="bg-gray-950 border border-gray-800 rounded-xl p-4 space-y-3">
              <h3 className="text-xs font-bold text-gray-400 uppercase tracking-widest flex items-center">
                <Info className="w-3.5 h-3.5 mr-1.5" />
                Risk Preview
              </h3>
              
              {riskLoading ? (
                <div className="h-20 flex items-center justify-center">
                  <div className="w-4 h-4 border-2 border-blue-500/30 border-t-blue-500 rounded-full animate-spin"></div>
                </div>
              ) : riskData ? (
                <div className="grid grid-cols-2 gap-y-3 text-sm">
                   <div className="text-gray-500">Notional</div>
                   <div className="text-right text-white font-mono">${riskData.notional_sar?.toLocaleString()}</div>
                   
                   <div className="text-gray-500">Portfolio Heat</div>
                   <div className="text-right text-white font-mono">{riskData.heat_estimate_pct?.toFixed(2)}%</div>
                   
                   <div className="col-span-2 pt-2 border-t border-gray-800">
                     <div className={cn(
                       "text-xs font-bold px-2 py-1 rounded text-center",
                       riskData.pass ? "bg-green-500/10 text-green-500" : "bg-red-500/10 text-red-500"
                     )}>
                       {riskData.pass ? '✓ RISK PARAMETERS MET' : `✗ RISK REJECTED: ${riskData.warnings?.join('; ') || 'See warnings'}`}
                     </div>
                   </div>
                </div>
              ) : (
                <div className="text-xs text-gray-600 text-center py-4">Enter ticker, price, and qty to see risk simulation.</div>
              )}
            </div>
          )}

          {error && <div className="text-red-500 text-sm bg-red-900/10 p-3 rounded-lg border border-red-500/20">{error}</div>}

          {/* Submit */}
          <button 
            onClick={() => setShowConfirm(true)}
            disabled={!ticker || !price || parseFloat(price) <= 0 || !qty || parseInt(qty) <= 0 || (type === 'BUY' && (!riskData || !riskData.pass))}
            className={cn(
              "w-full py-3 rounded-xl font-bold transition-all shadow-lg",
              type === 'BUY' 
                ? "bg-green-600 hover:bg-green-500 text-white" 
                : "bg-red-600 hover:bg-red-500 text-white",
              "disabled:opacity-50 disabled:cursor-not-allowed"
            )}
          >
            {type === 'BUY' ? 'Execute Buy Simulation' : 'Execute Sell Simulation'}
          </button>
        </div>

        {/* Confirmation Overlay */}
        {showConfirm && (
          <div className="absolute inset-0 bg-gray-950/95 flex flex-col items-center justify-center p-8 text-center animate-in fade-in zoom-in duration-200">
            <div className="w-16 h-16 bg-yellow-500/10 rounded-full flex items-center justify-center mb-6 border border-yellow-500/20">
              <AlertTriangle className="w-8 h-8 text-yellow-500" />
            </div>
            <h3 className="text-xl font-bold text-white mb-2">Confirm Sandbox Trade</h3>
            <p className="text-gray-400 text-sm mb-8 leading-relaxed">
              This will record a simulated <strong>{type}</strong> of <strong>{qty} shares</strong> of <strong>{ticker.toUpperCase()}</strong> at <strong>${price}</strong> 
              in the sandbox database. No real money or orders will be involved.
            </p>
            <div className="flex gap-3 w-full">
              <button 
                onClick={() => setShowConfirm(false)}
                className="flex-1 px-4 py-3 bg-gray-800 hover:bg-gray-700 text-white rounded-xl font-semibold transition-colors"
              >
                Cancel
              </button>
              <button 
                onClick={handleSubmit}
                disabled={loading}
                className={cn(
                  "flex-1 px-4 py-3 rounded-xl font-bold transition-all",
                  type === 'BUY' ? "bg-green-600 hover:bg-green-500" : "bg-red-600 hover:bg-red-500",
                  "text-white disabled:opacity-50"
                )}
              >
                {loading ? 'Processing...' : 'Confirm Simulation'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
