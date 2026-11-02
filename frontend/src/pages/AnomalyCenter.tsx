import React, { useEffect, useState } from 'react';
import {
  fetchAnomalies,
  triggerAnomalyScan,
  acknowledgeAnomaly,
  resolveAnomaly,
  autoHealAnomaly,
  AnomalyItem
} from '../services/api';
import {
  ShieldAlert,
  AlertTriangle,
  CheckCircle,
  RefreshCw,
  Search,
  Filter,
  ArrowRight,
  ExternalLink,
  Target,
  Sparkles,
  Wrench
} from 'lucide-react';

export const AnomalyCenter: React.FC = () => {
  const [anomalies, setAnomalies] = useState<AnomalyItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [severityFilter, setSeverityFilter] = useState<string>('');
  const [scanning, setScanning] = useState<boolean>(false);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  useEffect(() => {
    loadAnomalies();
  }, [statusFilter, severityFilter]);

  const loadAnomalies = async () => {
    setLoading(true);
    try {
      const data = await fetchAnomalies({
        status: statusFilter || undefined,
        severity: severityFilter || undefined
      });
      setAnomalies(data);
    } catch (err) {
      console.error('Failed to load anomalies', err);
    } finally {
      setLoading(false);
    }
  };

  const handleScan = async () => {
    setScanning(true);
    try {
      await triggerAnomalyScan();
      setActionSuccess('Deep anomaly scan completed across all 4 mandatory scenarios.');
      await loadAnomalies();
    } catch (err) {
      console.error(err);
    } finally {
      setScanning(false);
    }
  };

  const handleAcknowledge = async (id: string) => {
    try {
      await acknowledgeAnomaly(id);
      setActionSuccess(`Anomaly ${id} acknowledged.`);
      await loadAnomalies();
    } catch (err) {
      console.error(err);
    }
  };

  const handleResolve = async (id: string) => {
    try {
      await resolveAnomaly(id, 'Resolved via operator dashboard audit.');
      setActionSuccess(`Anomaly ${id} resolved.`);
      await loadAnomalies();
    } catch (err) {
      console.error(err);
    }
  };

  const handleAutoHeal = async (id: string) => {
    try {
      const res = await autoHealAnomaly(id);
      setActionSuccess(`Anomaly ${id} auto-healed: ${res.action_taken}`);
      await loadAnomalies();
    } catch (err) {
      console.error('Failed to auto-heal', err);
    }
  };

  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case 'CRITICAL':
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-rose-950 text-rose-400 border border-rose-800">CRITICAL</span>;
      case 'HIGH':
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-950 text-amber-400 border border-amber-800">HIGH</span>;
      case 'MEDIUM':
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-yellow-950 text-yellow-400 border border-yellow-800">MEDIUM</span>;
      default:
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono text-slate-400 border border-slate-700">LOW</span>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <ShieldAlert className="w-6 h-6 text-rose-400" />
            <h2 className="text-xl font-bold text-white tracking-tight">Autonomous Anomaly & Exception Center</h2>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Rule-based detection for Balance Mismatch, Reservation Overflow, Blocked Lot Fulfillment, and Premature Transfers.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleScan}
            disabled={scanning}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold bg-rose-600/20 text-rose-300 border border-rose-500/30 hover:bg-rose-600/30 transition-all"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${scanning ? 'animate-spin' : ''}`} />
            Run Exception Scan
          </button>
        </div>
      </div>

      {actionSuccess && (
        <div className="p-3 rounded-lg bg-emerald-950/40 border border-emerald-800 text-emerald-300 text-xs font-mono flex items-center justify-between">
          <span>{actionSuccess}</span>
          <button onClick={() => setActionSuccess(null)} className="text-emerald-400 hover:text-white">&times;</button>
        </div>
      )}

      {/* Mandatory Scenario Highlights */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
        <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800">
          <div className="text-[11px] font-bold text-rose-400 font-mono">SCENARIO 1</div>
          <div className="text-xs font-semibold text-white mt-0.5">Balance Mismatch</div>
          <p className="text-[10px] text-slate-400 mt-1">Stored projected balance differs from immutable ledger</p>
        </div>
        <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800">
          <div className="text-[11px] font-bold text-amber-400 font-mono">SCENARIO 2</div>
          <div className="text-xs font-semibold text-white mt-0.5">Reservation Overflow</div>
          <p className="text-[10px] text-slate-400 mt-1">Active reservation exceeds physical reservable capacity</p>
        </div>
        <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800">
          <div className="text-[11px] font-bold text-cyan-400 font-mono">SCENARIO 3</div>
          <div className="text-xs font-semibold text-white mt-0.5">Blocked Stock Fulfillment</div>
          <p className="text-[10px] text-slate-400 mt-1">Fulfillment allocated from damaged or quarantined stock</p>
        </div>
        <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800">
          <div className="text-[11px] font-bold text-indigo-400 font-mono">SCENARIO 4</div>
          <div className="text-xs font-semibold text-white mt-0.5">Premature Transfer</div>
          <p className="text-[10px] text-slate-400 mt-1">Destination credited before physical transfer dispatch</p>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="flex items-center gap-3">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-3 py-1.5 rounded-lg bg-[#0e1628] border border-slate-700 text-xs text-slate-200 font-mono"
        >
          <option value="">ALL STATUSES</option>
          <option value="OPEN">OPEN</option>
          <option value="ACKNOWLEDGED">ACKNOWLEDGED</option>
          <option value="RESOLVED">RESOLVED</option>
        </select>
        <select
          value={severityFilter}
          onChange={(e) => setSeverityFilter(e.target.value)}
          className="px-3 py-1.5 rounded-lg bg-[#0e1628] border border-slate-700 text-xs text-slate-200 font-mono"
        >
          <option value="">ALL SEVERITIES</option>
          <option value="CRITICAL">CRITICAL</option>
          <option value="HIGH">HIGH</option>
          <option value="MEDIUM">MEDIUM</option>
          <option value="LOW">LOW</option>
        </select>
      </div>

      {/* Anomalies List */}
      <div className="space-y-3">
        {loading ? (
          <div className="p-12 text-center text-slate-400 font-mono text-xs">
            Loading detected operational exceptions...
          </div>
        ) : anomalies.length === 0 ? (
          <div className="p-12 text-center text-slate-400 border border-slate-800 rounded-xl bg-[#090e1d]">
            No anomalies found matching current filters.
          </div>
        ) : (
          anomalies.map((anom) => (
            <div
              key={anom.anomaly_id}
              className="p-5 rounded-xl bg-[#090e1d] border border-slate-800/80 hover:border-slate-700 transition-all space-y-3"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800/60 pb-3">
                <div className="flex items-center gap-3">
                  {getSeverityBadge(anom.severity)}
                  <span className="font-mono font-bold text-sm text-white">{anom.issue_type}</span>
                  <span className="text-xs text-slate-400 font-mono">({anom.entity_type}: {anom.entity_id})</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`text-[10px] font-mono px-2 py-0.5 rounded ${
                    anom.status === 'RESOLVED'
                      ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                      : anom.status === 'ACKNOWLEDGED'
                      ? 'bg-blue-950 text-blue-400 border border-blue-800'
                      : 'bg-rose-950 text-rose-400 border border-rose-800'
                  }`}>
                    {anom.status}
                  </span>
                  <span className="text-[10px] text-slate-400 font-mono">{new Date(anom.detection_timestamp).toLocaleTimeString()}</span>
                </div>
              </div>

              {/* Detail comparison */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs font-mono">
                <div className="p-2.5 rounded bg-slate-900/60 border border-slate-800">
                  <span className="text-slate-400 text-[10px] block">EXPECTED CONDITION:</span>
                  <span className="text-emerald-400">{anom.expected_value}</span>
                </div>
                <div className="p-2.5 rounded bg-slate-900/60 border border-slate-800">
                  <span className="text-slate-400 text-[10px] block">OBSERVED ANOMALY VALUE:</span>
                  <span className="text-rose-400">{anom.observed_value}</span>
                </div>
              </div>

              {/* Explanation & Action */}
              <div className="text-xs text-slate-300 space-y-1">
                <p><span className="text-slate-400 font-medium">Root Cause:</span> {anom.explanation}</p>
                <p><span className="text-cyan-400 font-medium">Recommended Action:</span> {anom.recommended_action}</p>
              </div>

              {/* Ground Truth Badge */}
              {anom.ground_truth_label && (
                <div className="flex items-center justify-between pt-2 border-t border-slate-800/60">
                  <span className="inline-flex items-center gap-1.5 text-[10px] font-mono text-purple-400 bg-purple-950/40 px-2 py-0.5 rounded border border-purple-800/40">
                    <Target className="w-3 h-3" /> GROUND TRUTH LABEL: {anom.ground_truth_label}
                  </span>

                  <div className="flex items-center gap-2">
                    {anom.status !== 'RESOLVED' && (
                      <button
                        onClick={() => handleAutoHeal(anom.anomaly_id)}
                        className="px-2.5 py-1 rounded bg-cyan-950/70 text-[11px] font-semibold text-cyan-300 hover:bg-cyan-900/80 border border-cyan-700/60 flex items-center gap-1.5 shadow-sm shadow-cyan-950 transition-colors"
                        title="Execute automated AI remediation and immutable ledger reconciliation"
                      >
                        <Sparkles className="w-3 h-3 text-cyan-400" />
                        AI Auto-Heal
                      </button>
                    )}
                    {anom.status === 'OPEN' && (
                      <button
                        onClick={() => handleAcknowledge(anom.anomaly_id)}
                        className="px-2.5 py-1 rounded bg-slate-800 text-[11px] text-slate-200 hover:bg-slate-700 border border-slate-700 transition-colors"
                      >
                        Acknowledge
                      </button>
                    )}
                    {anom.status !== 'RESOLVED' && (
                      <button
                        onClick={() => handleResolve(anom.anomaly_id)}
                        className="px-2.5 py-1 rounded bg-emerald-900/40 text-[11px] text-emerald-300 hover:bg-emerald-800/50 border border-emerald-700 transition-colors"
                      >
                        Resolve
                      </button>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};
