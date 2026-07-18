import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { useAuth } from '../services/auth';
import { useNavigate } from 'react-router-dom';

export function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [safety, setSafety] = useState<any>(null);
  const { login } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    // Fetch safety matrix on mount
    api.get('/system/safety-matrix')
      .then(res => setSafety(res.data))
      .catch(err => console.warn("Could not fetch safety matrix. Ensure backend is running.", err.message));
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const formData = new FormData();
      formData.append('username', username);
      formData.append('password', password);

      const res = await api.post('/auth/login', formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      });
      login(res.data.access_token);
      navigate('/dashboard');
    } catch (err: any) {
      if (err.response?.status === 503) {
        setError('Database access blocked by safety guard.');
      } else {
        setError(err.response?.data?.detail || 'Login failed');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen py-10 flex flex-col items-center justify-center bg-gray-900 border-gray-800">
      <div className="w-full max-w-md p-8 space-y-6 bg-gray-800 rounded-xl shadow-lg border border-gray-700">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-white tracking-tight">GHBS Trading</h1>
          <p className="mt-2 text-sm text-gray-400">TASI Quant Command Center</p>
        </div>

        <div className="bg-yellow-900/50 border border-yellow-700/50 rounded p-3 mb-6">
          <p className="text-yellow-400 text-xs text-center font-bold">SANDBOX MODE</p>
        </div>

        <form className="space-y-4" onSubmit={handleSubmit}>
          <div>
            <label className="block text-sm font-medium text-gray-300">Username</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="mt-1 block w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-1 block w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>

          {error && <div className="text-red-500 text-sm">{error}</div>}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2 px-4 border border-transparent rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>
      </div>

      {safety && (
        <div className="w-full max-w-md mt-6 bg-gray-800 p-6 border border-gray-700 rounded-xl space-y-4">
          <h3 className="text-lg font-medium text-white border-b border-gray-700 pb-2">Safety Matrix</h3>
          
          {safety.safety_state === 'UNSAFE' && (
            <div className="bg-red-900/40 border border-red-700/50 rounded p-3 text-red-500 text-sm font-bold text-center">
              System is in UNSAFE / degraded safety mode. Database access is blocked by safety guard.
            </div>
          )}

          <div className="grid grid-cols-1 gap-2 text-xs">
             <div className="flex justify-between items-center py-1">
               <span className="text-gray-400">Production DB Access</span>
               <span className={safety.allow_production_db ? "text-red-400 font-bold" : "text-green-400 font-bold"}>{safety.allow_production_db ? "Enabled" : "Disabled"}</span>
             </div>
             <div className="flex justify-between items-center py-1 border-t border-gray-800">
               <span className="text-gray-400">Database Path</span>
               <span className="text-gray-300 font-mono text-right truncate max-w-[150px]">{safety.db_path || '-'}</span>
             </div>
             <div className="flex justify-between items-center py-1 border-t border-gray-800">
               <span className="text-gray-400">Live Analyze Preview</span>
               <span className={safety.live_analyze_preview_enabled ? "text-blue-400 font-bold" : "text-gray-500 font-bold"}>{safety.live_analyze_preview_enabled ? "Enabled" : "Disabled"}</span>
             </div>
             <div className="flex justify-between items-center py-1 border-t border-gray-800">
               <span className="text-gray-400">Live Scout Preview</span>
               <span className={safety.live_scout_preview_enabled ? "text-blue-400 font-bold" : "text-gray-500 font-bold"}>{safety.live_scout_preview_enabled ? "Enabled" : "Disabled"}</span>
             </div>
             <div className="flex justify-between items-center py-1 border-t border-gray-800">
               <span className="text-gray-400">Alert Scheduler</span>
               <span className={safety.alert_scheduler_enabled ? "text-blue-400 font-bold" : "text-gray-500 font-bold"}>{safety.alert_scheduler_enabled ? "Enabled" : "Disabled"}</span>
             </div>
             <div className="flex justify-between items-center py-1 border-t border-gray-800">
               <span className="text-gray-400">Provider Coverage Scan</span>
               <span className={safety.provider_coverage_scan_enabled ? "text-blue-400 font-bold" : "text-gray-500 font-bold"}>{safety.provider_coverage_scan_enabled ? "Enabled" : "Disabled"}</span>
             </div>
             <div className="flex justify-between items-center py-1 border-t border-gray-800">
               <span className="text-gray-400">Telegram Bot</span>
               <span className="text-gray-300 font-mono text-right truncate max-w-[150px]">{safety.telegram_configured_masked || '-'}</span>
             </div>
             <div className="flex justify-between items-center py-1 border-t border-gray-800">
               <span className="text-gray-400">Anthropic AI</span>
               <span className="text-gray-300 font-mono text-right truncate max-w-[150px]">{safety.anthropic_configured_masked || '-'}</span>
             </div>
          </div>
          
          <div className={`mt-2 p-2 rounded text-sm font-bold text-center border ${
              safety.safety_state === 'SAFE' ? 'bg-green-900/30 text-green-400 border-green-700/50' :
              safety.safety_state === 'WARNING' ? 'bg-yellow-900/40 text-yellow-500 border-yellow-700/50' :
              'bg-red-900/40 text-red-500 border-red-700/50'
          }`}>
             Safety State: {safety.safety_state || 'UNKNOWN'}
          </div>
        </div>
      )}
    </div>
  );
}
