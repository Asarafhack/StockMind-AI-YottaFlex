import React, { useEffect, useState } from 'react';
import { fetchValidationReport, fetchAuditLogs } from '../services/api';
import { FileCheck2, ShieldCheck, AlertCircle, History, CheckCircle2 } from 'lucide-react';

export const AuditAndValidation: React.FC = () => {
  const [valReport, setValReport] = useState<any | null>(null);
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [val, audit] = await Promise.all([
        fetchValidationReport(),
        fetchAuditLogs(50)
      ]);
      setValReport(val);
      setAuditLogs(audit || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
          <FileCheck2 className="w-5 h-5 text-cyan-400" />
          Enterprise Data Validation & Audit Trail
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Automated integrity verification (PK, FK, Enum, Dates, Arithmetic, Lifecycle) and append-only audit events.
        </p>
      </div>

      {/* Validation Summary Cards */}
      {valReport && (
        <div className="p-6 rounded-2xl bg-[#090e1d] border border-slate-800 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2">
              <span className={`px-2 py-0.5 rounded text-xs font-mono font-bold ${
                valReport.overall_status === 'PASS' ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' : 'bg-cyan-950 text-cyan-400 border border-cyan-800'
              }`}>
                SYSTEM INTEGRITY: {valReport.overall_status}
              </span>
            </div>
            <span className="text-xs font-mono text-slate-400">
              Evaluated {valReport.total_rules_evaluated} Relational Rules
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            <div className="p-3 rounded-xl bg-slate-900 border border-slate-800">
              <span className="text-[10px] text-slate-400 font-mono">RULES PASSED</span>
              <div className="text-xl font-bold text-emerald-400 font-mono">{valReport.rules_passed}</div>
            </div>
            <div className="p-3 rounded-xl bg-slate-900 border border-slate-800">
              <span className="text-[10px] text-slate-400 font-mono">ANOMALIES / FLAGGED</span>
              <div className="text-xl font-bold text-amber-400 font-mono">{valReport.rules_failed}</div>
            </div>
            <div className="p-3 rounded-xl bg-slate-900 border border-slate-800">
              <span className="text-[10px] text-slate-400 font-mono">EVALUATION TIMESTAMP</span>
              <div className="text-xs font-bold text-slate-200 font-mono mt-1 truncate">
                {valReport.validation_timestamp}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Audit Log Chronology */}
      <div className="p-6 rounded-2xl bg-[#090e1d] border border-slate-800 space-y-4">
        <h3 className="text-sm font-bold text-white font-mono uppercase tracking-wide flex items-center gap-2">
          <History className="w-4 h-4 text-cyan-400" />
          Chronological Audit Ledger Trail
        </h3>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#0f172a] text-slate-400 border-b border-slate-800 font-mono uppercase text-[11px]">
              <tr>
                <th className="py-2.5 px-3">Timestamp</th>
                <th className="py-2.5 px-3">Event Type</th>
                <th className="py-2.5 px-3">Entity Type</th>
                <th className="py-2.5 px-3">Action</th>
                <th className="py-2.5 px-3">Operator</th>
                <th className="py-2.5 px-3">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/50 font-mono text-[11px]">
              {loading ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-slate-400">Loading audit trail...</td>
                </tr>
              ) : auditLogs.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-6 text-center text-slate-400">No recent audit events logged.</td>
                </tr>
              ) : auditLogs.map((log) => (
                <tr key={log.audit_id} className="hover:bg-slate-800/30">
                  <td className="py-2.5 px-3 text-slate-400">{new Date(log.timestamp).toLocaleTimeString()}</td>
                  <td className="py-2.5 px-3 text-cyan-400">{log.event_type}</td>
                  <td className="py-2.5 px-3 text-slate-300">{log.entity_type}</td>
                  <td className="py-2.5 px-3 text-white font-bold">{log.action}</td>
                  <td className="py-2.5 px-3 text-slate-400">{log.user_id}</td>
                  <td className="py-2.5 px-3 text-slate-300 max-w-xs truncate">{log.details}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
