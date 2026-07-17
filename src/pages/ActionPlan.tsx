import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { AlertTriangle, Plus, X, Edit2, Trash2 } from 'lucide-react';
import { twMerge } from 'tailwind-merge';
import { clsx } from 'clsx';

function cn(...inputs: any[]) {
  return twMerge(clsx(inputs));
}

export function ActionPlan() {
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showAddForm, setShowAddForm] = useState(false);

  // Form states
  const [ticker, setTicker] = useState('');
  const [actionType, setActionType] = useState('Plan Buy');
  const [price, setPrice] = useState('');
  const [qty, setQty] = useState('');
  const [notes, setNotes] = useState('');

  const fetchItems = async () => {
    setLoading(true);
    try {
      const res = await api.get('/action-plan/tomorrow');
      setItems(res.data);
      setError('');
    } catch (err: any) {
      setError(err.message || 'Failed to load action plan');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchItems();
  }, []);

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post('/action-plan', {
        ticker: ticker.toUpperCase(),
        action_type: actionType,
        planned_price: price ? parseFloat(price) : null,
        planned_quantity: qty ? parseInt(qty) : null,
        notes: notes || null
      });
      setShowAddForm(false);
      resetForm();
      fetchItems();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to add item');
    }
  };

  const handleUpdateStatus = async (id: number, newStatus: string) => {
    try {
      await api.patch(`/action-plan/${id}?status=${newStatus}`);
      fetchItems();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to update status');
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to cancel and remove this sandbox action plan item?')) return;
    try {
      await api.delete(`/action-plan/${id}`);
      fetchItems();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete item');
    }
  };

  const resetForm = () => {
    setTicker('');
    setActionType('Plan Buy');
    setPrice('');
    setQty('');
    setNotes('');
  };

  return (
    <div className="space-y-6 max-w-6xl">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold text-white tracking-tight">Tomorrow Action Plan</h1>
          <div className="bg-yellow-900/20 text-yellow-500 px-3 py-1.5 rounded-md text-xs font-bold border border-yellow-700/30 flex items-center gap-1.5">
            <span>⚡</span> SANDBOX MODE
          </div>
        </div>
        <button 
          onClick={() => setShowAddForm(true)}
          className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-bold shadow-lg transition-all"
        >
          <Plus className="w-4 h-4" />
          <span>Add Plan Item</span>
        </button>
      </div>

      <div className="bg-yellow-900/20 border border-yellow-700/30 rounded-xl p-3 flex gap-3 items-start">
         <AlertTriangle className="w-5 h-5 text-yellow-500 shrink-0 mt-0.5" />
         <div className="text-sm text-yellow-500/90 leading-relaxed">
           <strong>SANDBOX MODE:</strong> This action plan is for simulation and note-taking only. 
           No real orders or automated reminders are executed.
         </div>
      </div>

      {loading && <div className="text-gray-400">Loading plan items...</div>}
      {error && <div className="text-red-500 bg-red-900/10 border border-red-500/20 p-4 rounded-xl text-sm">{error}</div>}

      {!loading && items.length === 0 && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-8 text-center space-y-3">
          <div className="text-gray-500 text-lg">No pending action items for tomorrow.</div>
          <button onClick={() => setShowAddForm(true)} className="text-blue-400 hover:text-blue-300 font-medium text-sm">Create your first plan item</button>
        </div>
      )}

      {items.length > 0 && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {items.map(item => (
            <div key={item.id} className="bg-gray-950 border border-gray-800 rounded-xl p-5 space-y-4 hover:border-gray-700 transition-colors">
              <div className="flex items-center justify-between">
                <span className="font-bold text-lg text-white">{item.ticker}</span>
                <span className={cn(
                  "text-xs font-bold px-2 py-1 rounded uppercase tracking-wider",
                  item.action_type === 'Plan Buy' ? "bg-green-500/10 text-green-500" :
                  item.action_type === 'Plan Sell' ? "bg-red-500/10 text-red-500" :
                  item.action_type === 'Watch Closely' ? "bg-blue-500/10 text-blue-500" :
                  "bg-gray-800 text-gray-400"
                )}>
                  {item.action_type}
                </span>
              </div>
              
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div className="text-gray-500">Plan Price</div>
                <div className="text-white text-right font-mono">{item.planned_price ? `$${item.planned_price.toFixed(2)}` : '-'}</div>
                <div className="text-gray-500">Quantity</div>
                <div className="text-white text-right font-mono">{item.planned_quantity || '-'}</div>
              </div>

              {item.notes && (
                <div className="bg-gray-900/50 p-3 rounded-lg border border-gray-800/50 text-sm text-gray-300 italic">
                  "{item.notes}"
                </div>
              )}

              <div className="flex gap-2 pt-2 border-t border-gray-800">
                <button 
                  onClick={() => handleUpdateStatus(item.id, 'completed')}
                  className="flex-1 py-1.5 bg-green-500/10 hover:bg-green-500/20 text-green-500 rounded text-xs font-bold transition-colors"
                >
                  Mark Complete
                </button>
                <button 
                  onClick={() => handleDelete(item.id)}
                  className="px-3 py-1.5 bg-red-500/10 hover:bg-red-500/20 text-red-500 rounded transition-colors"
                  title="Cancel/Remove"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Add Modal */}
      {showAddForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="bg-gray-900 border border-gray-800 w-full max-w-md rounded-2xl shadow-2xl p-6 space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-xl font-bold text-white">Add Sandbox Plan Item</h2>
              <button onClick={() => setShowAddForm(false)} className="text-gray-500 hover:text-white"><X className="w-5 h-5"/></button>
            </div>
            <form onSubmit={handleAdd} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-gray-500 uppercase mb-1">Ticker</label>
                <input required value={ticker} onChange={e => setTicker(e.target.value)} className="w-full bg-gray-950 border border-gray-800 rounded-lg px-4 py-2 text-white focus:ring-blue-500 uppercase" placeholder="e.g. 2222" />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-500 uppercase mb-1">Action</label>
                <select value={actionType} onChange={e => setActionType(e.target.value)} className="w-full bg-gray-950 border border-gray-800 rounded-lg px-4 py-2 text-white focus:ring-blue-500">
                  <option>Plan Buy</option>
                  <option>Plan Sell</option>
                  <option>Watch Closely</option>
                  <option>Ignore</option>
                  <option>Manual Review</option>
                </select>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-gray-500 uppercase mb-1">Price (Optional)</label>
                  <input type="number" step="0.01" value={price} onChange={e => setPrice(e.target.value)} className="w-full bg-gray-950 border border-gray-800 rounded-lg px-4 py-2 text-white" placeholder="0.00" />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-500 uppercase mb-1">Shares (Optional)</label>
                  <input type="number" value={qty} onChange={e => setQty(e.target.value)} className="w-full bg-gray-950 border border-gray-800 rounded-lg px-4 py-2 text-white" placeholder="0" />
                </div>
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-500 uppercase mb-1">Notes / Reason (Optional)</label>
                <textarea rows={3} value={notes} onChange={e => setNotes(e.target.value)} className="w-full bg-gray-950 border border-gray-800 rounded-lg px-4 py-2 text-white" placeholder="Setup thesis..."/>
              </div>
              <button type="submit" className="w-full py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-bold transition-all shadow-lg">Save Sandbox Plan</button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
