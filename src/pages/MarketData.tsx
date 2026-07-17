import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { LineChart, CheckCircle, XCircle } from 'lucide-react';

export function MarketData() {
  const [status, setStatus] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [testResult, setTestResult] = useState<any>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const loadStatus = async () => {
    try {
      const res = await api.get('/market-data/status');
      setStatus(res.data);
    } catch (e: any) {
      console.error(e);
    }
  };

  const [testingUniverse, setTestingUniverse] = useState(false);
  const [universeResults, setUniverseResults] = useState<any[]>([]);
  const [symbolMap, setSymbolMap] = useState<any[]>([]);

  const loadSymbolMap = async () => {
    try {
      const res = await api.get('/market-data/symbol-map');
      setSymbolMap(res.data);
    } catch (e: any) {
      console.error(e);
    }
  };

  const handleTestQuote = async () => {
    setLoading(true);
    setErrorMsg(null);
    setTestResult(null);
    try {
      const res = await api.post('/market-data/test-quote', {
        ticker: status?.sample_ticker || ''
      });
      if (res.data.success) {
        setTestResult(res.data.data);
      } else {
        setErrorMsg(res.data.message || 'Test quote failed');
      }
    } catch (e: any) {
      setErrorMsg(e.response?.data?.detail || e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleTestUniverse = async () => {
    setTestingUniverse(true);
    setUniverseResults([]);
    try {
      const res = await api.post('/market-data/test-universe-sample', { limit: 5 });
      if (res.data.success) {
        setUniverseResults(res.data.results);
      } else {
        alert("Failed to test universe: " + res.data.error);
      }
    } catch (e: any) {
      alert(e.response?.data?.detail || e.message);
    } finally {
      setTestingUniverse(false);
    }
  };

  const [testingOhlcv, setTestingOhlcv] = useState(false);
  const [ohlcvResult, setOhlcvResult] = useState<any>(null);
  const [ohlcvErrorMsg, setOhlcvErrorMsg] = useState<string | null>(null);

  const [testingUniverseOhlcv, setTestingUniverseOhlcv] = useState(false);
  const [universeOhlcvResults, setUniverseOhlcvResults] = useState<any[]>([]);

  const [runningCoverage, setRunningCoverage] = useState(false);
  const [coverageData, setCoverageData] = useState<any>(null);

  const loadCoverageLast = async () => {
    try {
      const res = await api.get('/market-data/provider-coverage-last');
      if (res.data.success) {
        setCoverageData(res.data.data);
      }
    } catch (e: any) {
      console.log('No previous coverage scan found or error', e);
    }
  };

  useEffect(() => {
    loadStatus();
    loadSymbolMap();
    loadCoverageLast();
  }, []);

  const handleRunCoverage = async () => {
    setRunningCoverage(true);
    setCoverageData(null);
    try {
      const res = await api.post('/market-data/provider-coverage-scan', { limit: 80 });
      if (res.data.success) {
        setCoverageData(res.data.data);
      } else {
        alert("Failed to run coverage scan: " + res.data.error);
      }
    } catch (e: any) {
      alert(e.response?.data?.detail || e.message);
    } finally {
      setRunningCoverage(false);
    }
  };

  const handleExportCoverageCSV = () => {
    if (!coverageData?.results) return;
    const headers = [
      "Internal Ticker", "Provider Ticker", "Provider", "Tier", "Sector",
      "Quote Status", "Quote Price", "OHLCV Status", "Bars Returned",
      "Min Required", "Missing Cols", "Latest Close", "Latest Vol", "Message"
    ];
    const rows = coverageData.results.map((r: any) => [
      r.internal_ticker, r.provider_ticker, r.provider, r.tier, r.sector,
      r.quote_status, r.quote_price || '', r.ohlcv_status, r.bars_returned || '',
      r.min_required_bars || '', r.missing_columns?.join(';') || '',
      r.latest_close || '', r.latest_volume || '',
      `"${(r.safe_message || '').replace(/"/g, '""')}"`
    ]);

    const csvContent = "data:text/csv;charset=utf-8," 
      + headers.join(",") + "\n" 
      + rows.map((e: any[]) => e.join(",")).join("\n");

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `provider_coverage_${coverageData.summary.provider}_${new Date().toISOString().split('T')[0]}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleTestOhlcv = async () => {
    setTestingOhlcv(true);
    setOhlcvErrorMsg(null);
    setOhlcvResult(null);
    try {
      const res = await api.post('/market-data/test-ohlcv', {
        ticker: status?.sample_ticker || '',
        lookback_days: 180
      });
      setOhlcvResult(res.data);
    } catch (e: any) {
      setOhlcvErrorMsg(e.response?.data?.detail || e.message);
    } finally {
      setTestingOhlcv(false);
    }
  };

  const handleTestUniverseOhlcv = async () => {
    setTestingUniverseOhlcv(true);
    setUniverseOhlcvResults([]);
    try {
      const res = await api.post('/market-data/test-universe-ohlcv-sample', { limit: 5 });
      if (res.data.success) {
        setUniverseOhlcvResults(res.data.results);
      } else {
        alert("Failed to test universe ohlcv: " + res.data.error);
      }
    } catch (e: any) {
      alert(e.response?.data?.detail || e.message);
    } finally {
      setTestingUniverseOhlcv(false);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl">
      <div className="flex justify-between items-center bg-blue-900/20 border border-blue-700/30 p-4 rounded-xl text-blue-500">
        <div className="flex items-center space-x-3">
          <LineChart className="w-5 h-5 text-blue-500" />
          <div>
            <h2 className="font-semibold">Market Data Foundation</h2>
            <p className="text-xs text-blue-400">Read-only market data test only. Data is not used for strategy, scout, analyze, alerts, or trade execution.</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Status Panel */}
        <div className="bg-gray-800 p-6 border border-gray-700 rounded-xl space-y-4">
          <h3 className="text-lg font-medium text-white border-b border-gray-700 pb-2">Provider Status</h3>
          {status ? (
            <div className="space-y-3 text-sm text-gray-300">
              <div className="flex justify-between">
                <span className="text-gray-500">Provider:</span>
                <span className="font-semibold text-white capitalize">{status.provider_name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Configured:</span>
                <span className={status.configured ? 'text-green-400 font-semibold' : 'text-red-400 font-semibold'}>
                  {status.configured ? 'YES' : 'NO'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Smoke Tests Enabled:</span>
                <span className={status.enabled ? 'text-green-400 font-semibold' : 'text-red-400 font-semibold'}>
                  {status.enabled ? 'YES' : 'NO'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Sample Ticker:</span>
                <span className="font-mono text-blue-400">{status.sample_ticker}</span>
              </div>
              
              <div className="pt-2">
                <div className="text-xs text-gray-500">System Message:</div>
                <div className="text-sm text-gray-400">{status.safe_message}</div>
              </div>
            </div>
          ) : (
            <div className="text-sm text-gray-500">Loading status...</div>
          )}
        </div>

        {/* Test Panel */}
        <div className="bg-gray-800 p-6 border border-gray-700 rounded-xl space-y-4">
          <h3 className="text-lg font-medium text-white border-b border-gray-700 pb-2">Smoke Test</h3>
          
          <button 
            onClick={handleTestQuote}
            disabled={loading || !status?.enabled || !status?.configured}
            className="w-full py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed rounded text-sm font-semibold text-white transition-colors"
          >
            {loading ? 'Testing...' : 'Test Sample Quote'}
          </button>

          {errorMsg && (
            <div className="p-3 bg-red-900/20 border border-red-700/30 rounded text-red-400 text-sm">
              <div className="flex items-center"><XCircle className="w-4 h-4 mr-2" /> Error</div>
              <div className="mt-1 text-xs">{errorMsg}</div>
            </div>
          )}

          {testResult && (
            <div className="p-4 bg-gray-900 border border-gray-700 rounded space-y-2 text-sm text-gray-300">
              <div className="flex items-center text-green-400 font-semibold pb-2 border-b border-gray-800">
                <CheckCircle className="w-4 h-4 mr-2" /> Success
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Input Ticker:</span>
                <span className="font-mono">{testResult.input_ticker || testResult.ticker}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Provider Ticker:</span>
                <span className="font-mono">{testResult.provider_ticker}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Price:</span>
                <span className="font-mono font-semibold text-white">{testResult.price} {testResult.currency}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Provider:</span>
                <span>{testResult.provider}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Time:</span>
                <span className="text-xs">{new Date(testResult.timestamp).toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Mocked Data:</span>
                <span className={testResult.is_mocked ? 'text-yellow-500' : 'text-blue-400'}>
                  {testResult.is_mocked ? 'YES' : 'NO'}
                </span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Diagnostics Testing Panel */}
      <div className="bg-gray-800 p-6 border border-gray-700 rounded-xl space-y-4">
        <div className="flex justify-between items-center border-b border-gray-700 pb-2">
          <div>
            <h3 className="text-lg font-medium text-white">Market Data Diagnostics</h3>
            <p className="text-xs text-gray-400">Read-only diagnostics only. Results are not used for strategy, scout, analyze, alerts, scheduler, or trade execution.</p>
          </div>
          <button 
            onClick={handleTestUniverse}
            disabled={testingUniverse || !status?.enabled || !status?.configured}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed rounded text-sm font-semibold text-white transition-colors whitespace-nowrap"
          >
            {testingUniverse ? 'Testing Sample...' : 'Test Universe Sample'}
          </button>
        </div>

        {universeResults.length > 0 && (
          <div className="overflow-x-auto pt-2">
            <table className="w-full text-left text-sm text-gray-400">
              <thead className="bg-gray-900 border-b border-gray-700 text-gray-300">
                <tr>
                  <th className="px-4 py-3 font-medium">Internal</th>
                  <th className="px-4 py-3 font-medium">Provider Ticker</th>
                  <th className="px-4 py-3 font-medium">Provider</th>
                  <th className="px-4 py-3 font-medium">Price</th>
                  <th className="px-4 py-3 font-medium">Status / Message</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800">
                {universeResults.map((r, i) => (
                  <tr key={i} className="hover:bg-gray-800/50">
                    <td className="px-4 py-3 font-mono text-white">{r.ticker}</td>
                    <td className="px-4 py-3 font-mono">{r.provider_ticker}</td>
                    <td className="px-4 py-3 capitalize">{r.provider}</td>
                    <td className="px-4 py-3 font-mono font-semibold text-gray-300">
                      {r.price ? `${r.price} ${r.currency}` : '-'}
                    </td>
                    <td className="px-4 py-3">
                      {r.status === 'success' ? (
                        <div className="text-green-400 text-xs flex items-center">
                          <CheckCircle className="w-3 h-3 mr-1" />
                          {r.safe_message} {r.is_mocked && '(Mock)'}
                        </div>
                      ) : (
                        <div className="text-red-400 text-xs flex items-center">
                          <XCircle className="w-3 h-3 mr-1" />
                          {r.safe_message}
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* OHLCV Diagnostics Panel */}
      <div className="bg-gray-800 p-6 border border-gray-700 rounded-xl space-y-4">
        <div className="flex justify-between items-center border-b border-gray-700 pb-2">
          <div>
            <h3 className="text-lg font-medium text-white">Historical OHLCV Diagnostics</h3>
            <p className="text-xs text-gray-400">Read-only OHLCV diagnostics only. Data is not used for strategy, Scout, Analyze, Alerts, Scheduler, or trade execution.</p>
          </div>
          <div className="flex space-x-2">
            <button 
              onClick={handleTestOhlcv}
              disabled={testingOhlcv || !status?.enabled || !status?.configured}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed rounded text-sm font-semibold text-white transition-colors whitespace-nowrap"
            >
              {testingOhlcv ? 'Testing...' : 'Test OHLCV'}
            </button>
            <button 
              onClick={handleTestUniverseOhlcv}
              disabled={testingUniverseOhlcv || !status?.enabled || !status?.configured}
              className="px-4 py-2 bg-purple-600 hover:bg-purple-500 disabled:opacity-50 disabled:cursor-not-allowed rounded text-sm font-semibold text-white transition-colors whitespace-nowrap"
            >
              {testingUniverseOhlcv ? 'Testing Sample...' : 'Test Universe OHLCV Sample'}
            </button>
          </div>
        </div>
        
        {status && (
          <div className="flex space-x-6 text-sm text-gray-400 bg-gray-900/50 p-3 rounded">
            <div>Provider: <span className="text-white capitalize">{status.provider_name}</span></div>
            <div>Sample Ticker: <span className="text-white">{status.sample_ticker}</span></div>
            <div>Lookback Days: <span className="text-white">180</span></div>
            <div>Min Required Bars: <span className="text-white">120</span></div>
          </div>
        )}

        {ohlcvErrorMsg && (
          <div className="p-3 bg-red-900/20 border border-red-700/30 rounded text-red-400 text-sm">
            <div className="flex items-center"><XCircle className="w-4 h-4 mr-2" /> Error</div>
            <div className="mt-1 text-xs">{ohlcvErrorMsg}</div>
          </div>
        )}

        {ohlcvResult && (
          <div className="p-4 bg-gray-900 border border-gray-700 rounded space-y-2 text-sm text-gray-300">
            <div className="flex items-center text-green-400 font-semibold pb-2 border-b border-gray-800">
              <CheckCircle className="w-4 h-4 mr-2" /> Success
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <span className="text-gray-500">Input Ticker: </span>
                <span className="font-mono">{ohlcvResult.input_ticker}</span>
              </div>
              <div>
                <span className="text-gray-500">Provider Ticker: </span>
                <span className="font-mono">{ohlcvResult.provider_ticker}</span>
              </div>
              <div>
                <span className="text-gray-500">Bars Returned: </span>
                <span className="font-mono font-semibold text-white">{ohlcvResult.bars_returned} / {ohlcvResult.min_required_bars} min</span>
              </div>
              <div>
                <span className="text-gray-500">Date Range: </span>
                <span className="font-mono text-xs">{ohlcvResult.start_date} to {ohlcvResult.end_date}</span>
              </div>
              <div>
                <span className="text-gray-500">Columns: </span>
                <span className="text-xs">
                  O:{ohlcvResult.has_open?'Y':'N'} H:{ohlcvResult.has_high?'Y':'N'} L:{ohlcvResult.has_low?'Y':'N'} C:{ohlcvResult.has_close?'Y':'N'} V:{ohlcvResult.has_volume?'Y':'N'}
                </span>
              </div>
              <div>
                <span className="text-gray-500">Mocked Data: </span>
                <span className={ohlcvResult.is_mocked ? 'text-yellow-500' : 'text-blue-400'}>
                  {ohlcvResult.is_mocked ? 'YES' : 'NO'}
                </span>
              </div>
            </div>
          </div>
        )}

        {universeOhlcvResults.length > 0 && (
          <div className="overflow-x-auto pt-2">
            <table className="w-full text-left text-sm text-gray-400">
              <thead className="bg-gray-900 border-b border-gray-700 text-gray-300">
                <tr>
                  <th className="px-4 py-3 font-medium">Internal</th>
                  <th className="px-4 py-3 font-medium">Provider Ticker</th>
                  <th className="px-4 py-3 font-medium">Provider</th>
                  <th className="px-4 py-3 font-medium">Bars</th>
                  <th className="px-4 py-3 font-medium">Columns missing</th>
                  <th className="px-4 py-3 font-medium">Status / Message</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800">
                {universeOhlcvResults.map((r, i) => {
                  let missing = [];
                  if (r.has_open === false) missing.push("Open");
                  if (r.has_high === false) missing.push("High");
                  if (r.has_low === false) missing.push("Low");
                  if (r.has_close === false) missing.push("Close");
                  if (r.has_volume === false) missing.push("Volume");
                  const missingStr = missing.length > 0 ? missing.join(", ") : "None";
                  
                  return (
                    <tr key={i} className="hover:bg-gray-800/50">
                      <td className="px-4 py-3 font-mono text-white">{r.ticker}</td>
                      <td className="px-4 py-3 font-mono">{r.provider_ticker}</td>
                      <td className="px-4 py-3 capitalize">{r.provider}</td>
                      <td className="px-4 py-3 font-mono text-gray-300">
                        {r.bars_returned !== null ? `${r.bars_returned}/${r.min_required_bars}` : '-'}
                      </td>
                      <td className="px-4 py-3 text-xs text-gray-500">{missingStr}</td>
                      <td className="px-4 py-3">
                        {r.status === 'success' ? (
                          <div className="text-green-400 text-xs flex items-center">
                            <CheckCircle className="w-3 h-3 mr-1" />
                            {r.safe_message} {r.is_mocked && '(Mock)'}
                          </div>
                        ) : (
                          <div className="text-red-400 text-xs flex items-center">
                            <XCircle className="w-3 h-3 mr-1" />
                            {r.safe_message}
                          </div>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Provider Coverage Report Panel */}
      <div className="bg-gray-800 p-6 border border-gray-700 rounded-xl space-y-4">
        <div className="flex justify-between items-center border-b border-gray-700 pb-2">
          <div>
            <h3 className="text-lg font-medium text-white">Provider Coverage Report</h3>
            <p className="text-xs text-gray-400">Read-only provider coverage only. Results are not used for strategy, Scout, Analyze, Alerts, Scheduler, or trade execution.</p>
          </div>
          <div className="flex space-x-2">
            <button 
              onClick={handleRunCoverage}
              disabled={runningCoverage || !status?.enabled || !status?.configured}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed rounded text-sm font-semibold text-white transition-colors whitespace-nowrap"
            >
              {runningCoverage ? 'Scanning...' : 'Run Coverage Scan'}
            </button>
            <button 
              onClick={handleExportCoverageCSV}
              disabled={!coverageData}
              className="px-4 py-2 bg-gray-700 hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed rounded text-sm font-semibold text-white transition-colors whitespace-nowrap border border-gray-600"
            >
              Export CSV
            </button>
          </div>
        </div>

        {status && (
          <div className="flex space-x-6 text-sm text-gray-400 bg-gray-900/50 p-3 rounded">
            <div>Provider: <span className="text-white capitalize">{status.provider_name}</span></div>
            <div>Universe Size: <span className="text-white">{symbolMap.length}</span></div>
            <div>Scan Limit: <span className="text-white">80</span></div>
            <div>Lookback Days: <span className="text-white">180</span></div>
            <div>Min Required Bars: <span className="text-white">120</span></div>
          </div>
        )}

        {coverageData && (
          <div className="space-y-4 pt-2">
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <div className="bg-gray-900 p-4 rounded border border-gray-700 flex flex-col">
                <span className="text-xs text-gray-400 uppercase tracking-wider">Total Tested</span>
                <span className="text-2xl font-bold text-white">{coverageData.summary.total_tested}</span>
              </div>
              <div className="bg-gray-900 p-4 rounded border border-gray-700 flex flex-col">
                <span className="text-xs text-gray-400 uppercase tracking-wider">Quote OK</span>
                <span className="text-2xl font-bold text-green-400">{coverageData.summary.quote_success}</span>
              </div>
              <div className="bg-gray-900 p-4 rounded border border-gray-700 flex flex-col">
                <span className="text-xs text-gray-400 uppercase tracking-wider">OHLCV OK</span>
                <span className="text-2xl font-bold text-green-400">{coverageData.summary.ohlcv_success}</span>
              </div>
              <div className="bg-gray-900 p-4 rounded border border-gray-700 flex flex-col">
                <span className="text-xs text-gray-400 uppercase tracking-wider">Insufficient</span>
                <span className="text-2xl font-bold text-yellow-400">{coverageData.summary.insufficient_bars}</span>
              </div>
              <div className="bg-gray-900 p-4 rounded border border-gray-700 flex flex-col">
                <span className="text-xs text-gray-400 uppercase tracking-wider">Failures</span>
                <span className="text-2xl font-bold text-red-400">{coverageData.summary.failures}</span>
              </div>
            </div>

            <div className="overflow-x-auto max-h-[500px] border border-gray-700 rounded">
              <table className="w-full text-left text-sm text-gray-400 relative border-collapse">
                <thead className="bg-gray-800/90 sticky top-0 border-b border-gray-700 backdrop-blur-sm z-10 text-gray-300">
                  <tr>
                    <th className="px-4 py-3 font-medium whitespace-nowrap">Ticker</th>
                    <th className="px-4 py-3 font-medium whitespace-nowrap">Tier / Sector</th>
                    <th className="px-4 py-3 font-medium whitespace-nowrap">Quote</th>
                    <th className="px-4 py-3 font-medium whitespace-nowrap">Price</th>
                    <th className="px-4 py-3 font-medium whitespace-nowrap">OHLCV</th>
                    <th className="px-4 py-3 font-medium whitespace-nowrap">Bars</th>
                    <th className="px-4 py-3 font-medium whitespace-nowrap max-w-xs">Message</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-800 bg-gray-900/50">
                  {coverageData.results.map((r: any, i: number) => (
                    <tr key={i} className="hover:bg-gray-800/80">
                      <td className="px-4 py-3">
                        <div className="font-mono text-white">{r.internal_ticker}</div>
                        <div className="text-xs text-gray-500 font-mono">{r.provider_ticker}</div>
                      </td>
                      <td className="px-4 py-3 text-xs leading-tight">
                        <div className="text-gray-300">{r.tier}</div>
                        <div className="text-gray-500 truncate max-w-[120px]" title={r.sector}>{r.sector}</div>
                      </td>
                      <td className="px-4 py-3">
                        {r.quote_status === 'success' ? (
                          <span className="text-green-400 text-xs font-semibold px-2 py-1 bg-green-400/10 rounded">OK</span>
                        ) : (
                          <span className="text-red-400 text-xs font-semibold px-2 py-1 bg-red-400/10 rounded">FAIL</span>
                        )}
                      </td>
                      <td className="px-4 py-3 font-mono text-gray-300">
                        {r.quote_price || '-'}
                      </td>
                      <td className="px-4 py-3">
                        {r.ohlcv_status === 'success' ? (
                          <span className="text-green-400 text-xs font-semibold px-2 py-1 bg-green-400/10 rounded">OK</span>
                        ) : r.ohlcv_status === 'insufficient' ? (
                          <span className="text-yellow-400 text-xs font-semibold px-2 py-1 bg-yellow-400/10 rounded">WARN</span>
                        ) : (
                          <span className="text-red-400 text-xs font-semibold px-2 py-1 bg-red-400/10 rounded">FAIL</span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        {r.bars_returned ? (
                          <div className={r.ohlcv_status === 'insufficient' ? 'text-yellow-400' : 'text-gray-300'}>
                            <span className="font-mono">{r.bars_returned}</span><span className="text-xs text-gray-500">/{r.min_required_bars}</span>
                          </div>
                        ) : '-'}
                      </td>
                      <td className="px-4 py-3 text-xs text-gray-400 max-w-xs truncate" title={r.safe_message}>
                        {r.safe_message}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* TASI Universe Symbol Map Panel */}
      <div className="bg-gray-800 p-6 border border-gray-700 rounded-xl space-y-4">
        <div className="flex justify-between items-center mb-3">
          <h4 className="text-sm font-medium text-gray-300">TASI Universe Symbol Map ({symbolMap.length} total)</h4>
        </div>
        <div className="max-h-[400px] overflow-y-auto rounded border border-gray-700 bg-gray-900">
          <table className="w-full text-left text-sm text-gray-400 relative border-collapse">
            <thead className="bg-gray-800/80 sticky top-0 border-b border-gray-700 backdrop-blur-sm z-10 text-gray-300">
              <tr>
                <th className="px-4 py-3 font-medium">Internal Ticker</th>
                <th className="px-4 py-3 font-medium">yfinance Map</th>
                <th className="px-4 py-3 font-medium">TwelveData Map</th>
                <th className="px-4 py-3 font-medium">Sector</th>
                <th className="px-4 py-3 font-medium">Tier</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {symbolMap.map((m, i) => (
                <tr key={i} className="hover:bg-gray-800/50">
                  <td className="px-4 py-3 font-mono font-semibold text-white">{m.internal_ticker}</td>
                  <td className="px-4 py-3 font-mono text-blue-400">{m.yfinance_symbol}</td>
                  <td className="px-4 py-3 font-mono text-green-400">{m.twelvedata_symbol}</td>
                  <td className="px-4 py-3 text-xs">{m.sector}</td>
                  <td className="px-4 py-3 text-xs">{m.tier}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
