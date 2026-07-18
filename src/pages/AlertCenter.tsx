import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { Bell, Copy, CheckCircle, XCircle } from 'lucide-react';

const alertTemplates = [
  { id: 'general_test', title: 'General Test Alert', message: 'TASI Sandbox: General System check. Pipeline is nominal.' },
  { id: 'scout_summary', title: 'Scout Summary Test', message: 'TASI Sandbox Scout: Found 3 candidate setups (R/R > 2.0). Review command center for details.' },
  { id: 'action_plan_reminder', title: 'Action Plan Reminder Test', message: 'TASI Sandbox Reminder: You have 2 pending entry orders awaiting trigger.' },
  { id: 'tp_hit', title: 'TP Hit Test', message: 'TASI Sandbox Alert: Target Profit (TP1) hit on sample trade. Partial close simulated.' },
  { id: 'stop_alert', title: 'Stop Alert Test', message: 'TASI Sandbox Alert: Hard Stop condition met on sample trade. Risk containment verified.' },
];

export function AlertCenter() {
  const [selectedTemplateId, setSelectedTemplateId] = useState(alertTemplates[0].id);
  const [customText, setCustomText] = useState(alertTemplates[0].message);
  const [testStatus, setTestStatus] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [logs, setLogs] = useState<any[]>([]);
  const [logTypeFilter, setLogTypeFilter] = useState('ALL');
  const [logStatusFilter, setLogStatusFilter] = useState('ALL');

  const filteredLogs = logs.filter(log => {
    if (logTypeFilter !== 'ALL' && log.alert_type !== logTypeFilter) return false;
    if (logStatusFilter !== 'ALL') {
      const isSent = log.delivery_status.startsWith('SENT');
      if (logStatusFilter === 'SENT' && !isSent) return false;
      if (logStatusFilter === 'FAILED' && isSent) return false;
    }
    return true;
  });

  useEffect(() => {
    const tmpl = alertTemplates.find(t => t.id === selectedTemplateId);
    if (tmpl) setCustomText(tmpl.message);
  }, [selectedTemplateId]);

  const [schedulerStatus, setSchedulerStatus] = useState<any>(null);

  const loadLogs = async () => {
    try {
      const res = await api.get('/alerts/log');
      setLogs(res.data);
    } catch (e) {
      console.error(e);
    }
  };

  const loadSchedulerStatus = async () => {
    try {
      const res = await api.get('/scheduler/status');
      setSchedulerStatus(res.data);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    loadLogs();
    loadSchedulerStatus();
  }, []);

  const handleSend = async () => {
    setLoading(true);
    setTestStatus('Sending manual alert...');
    try {
      const res = await api.post('/alerts/send-template', {
        template_id: selectedTemplateId,
        preview_message: customText
      });
      if (res.data.success) {
        setTestStatus(res.data.message || 'Manual alert sent successfully.');
      } else {
        setTestStatus(`Manual alert failed: ${res.data.message || 'Unknown error'}`);
      }
      loadLogs();
    } catch (err: any) {
      setTestStatus(`Manual alert failed: ${err.response?.data?.detail || err.message}`);
      loadLogs();
    } finally {
      setLoading(false);
    }
  };

  const handleStartScheduler = async () => {
    try {
      const res = await api.post('/scheduler/start-dry-run');
      setTestStatus(res.data.message || 'Scheduler started.');
      loadSchedulerStatus();
      loadLogs();
    } catch (e: any) {
      setTestStatus(`Scheduler error: ${e.response?.data?.detail || e.message}`);
    }
  };

  const handleStopScheduler = async () => {
    try {
      const res = await api.post('/scheduler/stop-all');
      setTestStatus(res.data.message || 'Scheduler stopped.');
      loadSchedulerStatus();
      loadLogs();
    } catch (e: any) {
      setTestStatus(`Scheduler error: ${e.response?.data?.detail || e.message}`);
    }
  };

  const handleSendDryRunNow = async () => {
    try {
      const res = await api.post('/scheduler/send-dry-run-now');
      setTestStatus(res.data.message || 'Immediate dry-run alert sent.');
      loadLogs();
    } catch (e: any) {
      setTestStatus(`Dry run error: ${e.response?.data?.detail || e.message}`);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl">
      <div className="flex justify-between items-center bg-yellow-900/20 border border-yellow-700/30 p-4 rounded-xl text-yellow-500">
        <div className="flex items-center space-x-3">
          <Bell className="w-5 h-5 text-yellow-500" />
          <div>
            <h2 className="font-semibold">Sandbox Alert Center</h2>
            <p className="text-xs text-yellow-400">Manual alert only. No scheduler, no live signal, no trade execution.</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        
        {/* Scheduler */}
        <div className="md:col-span-3 bg-gray-800 p-6 border border-gray-700 rounded-xl space-y-4">
          <div className="flex justify-between items-center border-b border-gray-700 pb-2">
            <h3 className="text-lg font-medium text-white">Scheduler Dry Run</h3>
            {schedulerStatus && (
              <span className={`px-2 py-1 text-xs rounded font-semibold ${schedulerStatus.is_running ? 'bg-green-900/30 text-green-400 border border-green-700/30' : (schedulerStatus.enabled_in_env ? 'bg-gray-700 text-gray-400' : 'bg-red-900/30 text-red-500 border border-red-700/30')}`}>
                {schedulerStatus.is_running ? 'RUNNING' : (schedulerStatus.enabled_in_env ? 'STOPPED' : 'DISABLED')}
              </span>
            )}
          </div>
          {schedulerStatus?.is_running && (
             <div className="bg-blue-900/20 border border-blue-700/30 p-3 rounded text-blue-300 text-xs font-semibold">
               Dry-run scheduler is currently sending test alerts. No live trading logic is active.
             </div>
          )}
          <div className="flex flex-col md:flex-row gap-4 items-start md:items-center justify-between">
            <div className="text-sm text-gray-400 space-y-1">
              <p>Dry-run scheduler only. No live signals, no TP/SL monitoring, no trade execution.</p>
              {schedulerStatus && (
                <div className="flex flex-wrap gap-4 mt-2">
                  <span className="text-xs space-x-1">
                    <span className="text-gray-500">Enabled in .env:</span>
                    <span className={schedulerStatus.enabled_in_env ? "text-green-400" : "text-red-400"}>{schedulerStatus.enabled_in_env ? "Yes" : "No"}</span>
                  </span>
                  <span className="text-xs space-x-1">
                    <span className="text-gray-500">Dry Run Only:</span>
                    <span className={schedulerStatus.dry_run_only_env ? "text-green-400" : "text-red-400"}>{schedulerStatus.dry_run_only_env ? "Yes" : "No"}</span>
                  </span>
                  <span className="text-xs space-x-1">
                    <span className="text-gray-500">Interval:</span>
                    <span className="text-yellow-400">{schedulerStatus.interval_seconds}s</span>
                  </span>
                  <span className="text-xs space-x-1">
                    <span className="text-gray-500">Total Sent:</span>
                    <span className="text-blue-400">{schedulerStatus.total_dry_run_sent}</span>
                  </span>
                  {schedulerStatus.last_run_at && (
                    <span className="text-xs space-x-1">
                      <span className="text-gray-500">Last Run:</span>
                      <span className="text-gray-400">{new Date(schedulerStatus.last_run_at).toLocaleTimeString()}</span>
                    </span>
                  )}
                  {schedulerStatus.next_run_estimate && (
                    <span className="text-xs space-x-1">
                      <span className="text-gray-500">Next Run:</span>
                      <span className="text-gray-400">{new Date(schedulerStatus.next_run_estimate).toLocaleTimeString()}</span>
                    </span>
                  )}
                </div>
              )}
            </div>
            <div className="flex gap-2 w-full md:w-auto">
              {schedulerStatus?.is_running ? (
                <button onClick={handleStopScheduler} className="px-4 py-2 bg-red-600 hover:bg-red-500 rounded text-xs font-semibold text-white transition-colors whitespace-nowrap">
                  Stop All Scheduler Tasks
                </button>
              ) : (
                <button onClick={handleStartScheduler} className="px-4 py-2 bg-green-600 hover:bg-green-500 rounded text-xs font-semibold text-white transition-colors whitespace-nowrap">
                  Start Dry Run Scheduler
                </button>
              )}
              <button onClick={handleSendDryRunNow} className="px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded text-xs font-semibold text-white transition-colors whitespace-nowrap">
                Send Dry Run Alert Now
              </button>
            </div>
          </div>
        </div>

        {/* Composer */}
        <div className="md:col-span-1 bg-gray-800 p-6 border border-gray-700 rounded-xl space-y-4">
          <h3 className="text-lg font-medium text-white border-b border-gray-700 pb-2">Send Telegram Alert</h3>
          <div className="space-y-4 text-sm">
            
            <div className="space-y-2">
              <label className="text-gray-400 text-xs font-semibold">Select Template</label>
              <select
                value={selectedTemplateId}
                onChange={(e) => setSelectedTemplateId(e.target.value)}
                className="w-full bg-gray-900 border border-gray-700 rounded p-2 text-white outline-none focus:border-blue-500 transition-colors"
              >
                {alertTemplates.map(tmpl => (
                  <option key={tmpl.id} value={tmpl.id}>{tmpl.title}</option>
                ))}
              </select>
            </div>

            <div className="space-y-2">
              <label className="text-gray-400 text-xs font-semibold">Preview Message</label>
              <textarea
                value={customText}
                onChange={(e) => setCustomText(e.target.value)}
                className="w-full bg-gray-900 border border-gray-700 rounded p-2 text-white h-32 outline-none focus:border-blue-500 transition-colors"
              />
            </div>

            {testStatus && (
              <div className={`p-3 rounded text-xs break-words ${testStatus.includes('failed') ? 'bg-red-900/20 text-red-400 border border-red-700/30' : 'bg-blue-900/20 text-blue-400 border border-blue-700/30'}`}>
                {testStatus}
              </div>
            )}

            <button 
              onClick={handleSend}
              disabled={loading}
              className="w-full py-2.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed rounded text-sm font-semibold text-white transition-colors"
            >
              {loading ? 'Sending...' : 'Send Manual Alert'}
            </button>
            
          </div>
        </div>

        {/* Log Viewer */}
        <div className="md:col-span-2 bg-gray-800 p-6 border border-gray-700 rounded-xl flex flex-col space-y-4">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center border-b border-gray-700 pb-2 gap-4">
            <h3 className="text-lg font-medium text-white">Alert Delivery Log</h3>
            <div className="flex gap-2 text-xs">
              <select 
                value={logTypeFilter}
                onChange={(e) => setLogTypeFilter(e.target.value)}
                className="bg-gray-900 border border-gray-700 rounded p-1.5 text-gray-300 outline-none"
              >
                <option value="ALL">All Types</option>
                {[...new Set(logs.map(l => l.alert_type))].map(t => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
              <select 
                value={logStatusFilter}
                onChange={(e) => setLogStatusFilter(e.target.value)}
                className="bg-gray-900 border border-gray-700 rounded p-1.5 text-gray-300 outline-none"
              >
                <option value="ALL">All Status</option>
                <option value="SENT">SENT</option>
                <option value="FAILED">FAILED</option>
              </select>
              <button onClick={loadLogs} className="px-3 py-1.5 bg-blue-600/20 text-blue-400 hover:bg-blue-600/30 rounded transition-colors whitespace-nowrap">Refresh</button>
            </div>
          </div>
          
          <div className="flex-1 overflow-auto rounded bg-gray-900 border border-gray-700 max-h-[500px]">
             <table className="w-full text-left text-sm text-gray-400 border-collapse relative">
                <thead className="bg-gray-800/80 sticky top-0 border-b border-gray-700 backdrop-blur-sm z-10">
                  <tr>
                    <th className="px-4 py-2 font-medium text-gray-300">Time</th>
                    <th className="px-4 py-2 font-medium text-gray-300">Type</th>
                    <th className="px-4 py-2 font-medium text-gray-300">Message</th>
                    <th className="px-4 py-2 font-medium text-gray-300">Target</th>
                    <th className="px-4 py-2 font-medium text-gray-300 text-right">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-800">
                  {filteredLogs.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="px-4 py-8 text-center text-gray-500">No alert events found matching criteria.</td>
                    </tr>
                  ) : (
                    filteredLogs.map(log => (
                      <tr key={log.id} className="hover:bg-gray-800/50 transition-colors">
                        <td className="px-4 py-3 whitespace-nowrap text-xs">{new Date(log.created_at).toLocaleString()}</td>
                        <td className="px-4 py-3 whitespace-nowrap text-gray-300 text-xs">{log.alert_type}</td>
                        <td className="px-4 py-3 text-xs max-w-xs truncate" title={log.message}>{log.message}</td>
                        <td className="px-4 py-3 whitespace-nowrap font-mono text-xs text-gray-500">{log.destination_masked}</td>
                        <td className="px-4 py-3 whitespace-nowrap text-right">
                           <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-xs font-semibold ${log.delivery_status.startsWith('SENT') ? 'text-green-400 bg-green-400/10 border border-green-700/30' : 'text-red-400 bg-red-400/10 border border-red-700/30'}`}>
                             {log.delivery_status.startsWith('SENT') ? <CheckCircle className="w-3 h-3 mr-1" /> : <XCircle className="w-3 h-3 mr-1" />}
                             {log.delivery_status.startsWith('FAILED') ? 'FAILED' : 'SENT'}
                           </span>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
             </table>
          </div>
        </div>

      </div>
    </div>
  );
}
