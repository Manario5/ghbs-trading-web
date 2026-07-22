import React, { useState, useEffect } from 'react';
import { ModeBadge } from '../components/ModeBadge';
import { api } from '../services/api';
import { AlertTriangle, Plus, X } from 'lucide-react';
import { twMerge } from 'tailwind-merge';
import { clsx } from 'clsx';

function cn(...inputs: any[]) {
  return twMerge(clsx(inputs));
}

export function Journal() {
  const [entries, setEntries] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showAddForm, setShowAddForm] = useState(false);

  // Form states
  const [ticker, setTicker] = useState('');
  const [noteType, setNoteType] = useState('pre-trade thesis');
  const [noteText, setNoteText] = useState('');

  const [filterTicker, setFilterTicker] = useState('');
  const [filterType, setFilterType] = useState('All');

  const fetchEntries = async () => {
    setLoading(true);
    try {
      const res = await api.get('/journal');
      setEntries(res.data);
      setError('');
    } catch (err: any) {
      setError(err.message || 'Failed to load journal entries');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEntries();
  }, []);

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post('/journal', {
        ticker: ticker.toUpperCase(),
        note_type: noteType,
        note_text: noteText,
        position_id: null,
        transaction_id: null
      });
      setShowAddForm(false);
      resetForm();
      fetchEntries();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to add journal entry');
    }
  };

  const resetForm = () => {
    setTicker('');
    setNoteType('pre-trade thesis');
    setNoteText('');
  };

  const filteredEntries = entries.filter(e => {
    if (filterTicker && !e.ticker.includes(filterTicker.toUpperCase())) return false;
    if (filterType !== 'All' && e.note_type !== filterType) return false;
    return true;
  });

  const uniqueTypes = ['All', ...new Set(entries.map(e => e.note_type))];

  return (
    <div className="space-y-6 max-w-6xl">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold text-white tracking-tight">Trading Journal</h1>
          <ModeBadge />
        </div>
        <button 
          onClick={() => setShowAddForm(true)}
          className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-bold shadow-lg transition-all"
        >
          <Plus className="w-4 h-4" />
          <span>Add Note</span>
        </button>
      </div>

      <div className="bg-yellow-900/20 border border-yellow-700/30 rounded-xl p-3 flex gap-3 items-start">
         <AlertTriangle className="w-5 h-5 text-yellow-500 shrink-0 mt-0.5" />
         <div className="text-sm text-yellow-500/90 leading-relaxed">
           <strong>SIMULATION:</strong> Journal entries are stored in the simulation database.
         </div>
      </div>

      <div className="flex gap-4 items-end bg-gray-950 p-4 rounded-xl border border-gray-800">
        <div>
          <label className="block text-xs font-semibold text-gray-500 uppercase mb-1">Filter by Ticker</label>
          <input 
            value={filterTicker}
            onChange={e => setFilterTicker(e.target.value)}
            placeholder="e.g. 2222"
            className="w-48 bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:ring-blue-500 uppercase"
          />
        </div>
        <div>
          <label className="block text-xs font-semibold text-gray-500 uppercase mb-1">Filter by Type</label>
          <select 
            value={filterType}
            onChange={e => setFilterType(e.target.value)}
            className="w-48 bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:ring-blue-500"
          >
            {uniqueTypes.map(t => <option key={t} value={t}>{t}</option>)}
          </select>
        </div>
      </div>

      {loading && <div className="text-gray-400">Loading journal entries...</div>}
      {error && <div className="text-red-500 bg-red-900/10 border border-red-500/20 p-4 rounded-xl text-sm">{error}</div>}

      {!loading && filteredEntries.length === 0 && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-8 text-center space-y-3">
          <div className="text-gray-500 text-lg">No matching journal entries.</div>
          {entries.length === 0 && <button onClick={() => setShowAddForm(true)} className="text-blue-400 hover:text-blue-300 font-medium text-sm">Write your first note</button>}
        </div>
      )}

      {filteredEntries.length > 0 && (
        <div className="space-y-4">
          {filteredEntries.map(entry => (
            <div key={entry.id} className="bg-gray-950 border border-gray-800 rounded-xl p-5 space-y-3 hover:border-gray-700 transition-colors">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <span className="font-bold text-lg text-white">{entry.ticker}</span>
                  <span className={cn(
                    "text-xs font-bold px-2 py-0.5 rounded-full",
                    entry.note_type === 'pre-trade thesis' ? "bg-blue-500/10 text-blue-500" :
                    entry.note_type === 'emotion note' ? "bg-yellow-500/10 text-yellow-500" :
                    entry.note_type === 'post-trade lesson' ? "bg-purple-500/10 text-purple-500" :
                    "bg-gray-800 text-gray-400"
                  )}>
                    {entry.note_type}
                  </span>
                </div>
                <span className="text-xs text-gray-500 font-mono">
                  {new Date(entry.created_at).toLocaleString()}
                </span>
              </div>
              
              <div className="text-gray-300 text-sm leading-relaxed whitespace-pre-wrap">
                {entry.note_text}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Add Modal */}
      {showAddForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="bg-gray-900 border border-gray-800 w-full max-w-lg rounded-2xl shadow-2xl p-6 space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-xl font-bold text-white">Add Journal Note</h2>
              <button onClick={() => setShowAddForm(false)} className="text-gray-500 hover:text-white"><X className="w-5 h-5"/></button>
            </div>
            <form onSubmit={handleAdd} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-gray-500 uppercase mb-1">Ticker</label>
                  <input required value={ticker} onChange={e => setTicker(e.target.value)} className="w-full bg-gray-950 border border-gray-800 rounded-lg px-4 py-2 text-white focus:ring-blue-500 uppercase" placeholder="e.g. 2222" />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-500 uppercase mb-1">Type</label>
                  <select value={noteType} onChange={e => setNoteType(e.target.value)} className="w-full bg-gray-950 border border-gray-800 rounded-lg px-4 py-2 text-white focus:ring-blue-500">
                    <option value="pre-trade thesis">Pre-trade thesis</option>
                    <option value="execution note">Execution note</option>
                    <option value="emotion note">Emotion note</option>
                    <option value="risk note">Risk note</option>
                    <option value="post-trade lesson">Post-trade lesson</option>
                    <option value="manual review">Manual review</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-500 uppercase mb-1">Note Text</label>
                <textarea required rows={5} value={noteText} onChange={e => setNoteText(e.target.value)} className="w-full bg-gray-950 border border-gray-800 rounded-lg px-4 py-2 text-white font-serif" placeholder="Write your thoughts..."/>
              </div>
              <button type="submit" className="w-full py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-bold transition-all shadow-lg">Save Note</button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
