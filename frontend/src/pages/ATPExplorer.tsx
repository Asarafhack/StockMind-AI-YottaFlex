import React, { useState } from 'react';
import { fetchATPBreakdown, ATPData } from '../services/api';
import { Calculator, Sparkles, Shield, CheckCircle, Info } from 'lucide-react';

export const ATPExplorer: React.FC = () => {
  const [skuId, setSkuId] = useState<string>('SKU-000001');
  const [locId, setLocId] = useState<string>('LOC-000001');
  const [protectSafety, setProtectSafety] = useState<boolean>(false);
  const [atpData, setAtpData] = useState<ATPData | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleCalculate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const data = await fetchATPBreakdown(skuId.trim(), locId.trim(), protectSafety);
      setAtpData(data);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to calculate ATP. Verify SKU and Location IDs.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
          <Calculator className="w-5 h-5 text-cyan-400" />
          Available-to-Promise (ATP) Calculation Engine
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Inspect deterministic stock availability using non-negotiable enterprise formulas.
        </p>
      </div>

      {/* Query Card */}
      <form onSubmit={handleCalculate} className="p-6 rounded-2xl bg-[#090e1d] border border-slate-800 shadow-xl space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-mono text-slate-400 mb-1">SKU IDENTIFIER</label>
            <input
              type="text"
              value={skuId}
              onChange={(e) => setSkuId(e.target.value)}
              className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700 text-sm font-mono text-white focus:outline-none focus:border-cyan-500"
              placeholder="e.g. SKU-000001"
              required
            />
          </div>
          <div>
            <label className="block text-xs font-mono text-slate-400 mb-1">NODE LOCATION IDENTIFIER</label>
            <input
              type="text"
              value={locId}
              onChange={(e) => setLocId(e.target.value)}
              className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700 text-sm font-mono text-white focus:outline-none focus:border-cyan-500"
              placeholder="e.g. LOC-000001"
              required
            />
          </div>
        </div>

        <div className="flex items-center justify-between pt-2">
          <label className="flex items-center gap-2 cursor-pointer text-xs text-slate-300">
            <input
              type="checkbox"
              checked={protectSafety}
              onChange={(e) => setProtectSafety(e.target.checked)}
              className="rounded bg-slate-900 border-slate-700 text-cyan-500 focus:ring-0"
            />
            <span>Protect Safety Stock in Commercial ATP (Deduct Safety Stock)</span>
          </label>

          <button
            type="submit"
            disabled={loading}
            className="px-5 py-2 rounded-lg text-xs font-semibold bg-gradient-to-r from-cyan-600 to-blue-600 text-white hover:from-cyan-500 hover:to-blue-500 transition-all flex items-center gap-2 shadow-lg shadow-cyan-500/20"
          >
            <Sparkles className="w-4 h-4" />
            {loading ? 'Evaluating...' : 'Evaluate Live ATP'}
          </button>
        </div>

        {error && (
          <div className="p-3 rounded-lg bg-rose-950/50 border border-rose-800 text-rose-300 text-xs font-mono">
            {error}
          </div>
        )}
      </form>

      {/* Results View */}
      {atpData && (
        <div className="p-6 rounded-2xl bg-[#090e1d] border border-cyan-900/60 shadow-2xl space-y-6">
          <div className="flex items-center justify-between border-b border-slate-800 pb-4">
            <div>
              <span className="text-[10px] font-mono text-cyan-400 uppercase tracking-wider">Evaluation Timestamp</span>
              <div className="text-xs text-slate-400 font-mono">{atpData.calculation_timestamp}</div>
            </div>
            <div className="text-right">
              <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">Calculated Promiseable ATP</span>
              <div className="text-3xl font-extrabold text-cyan-400 font-mono">
                {atpData.final_atp} <span className="text-sm font-normal text-slate-400">UNITS</span>
              </div>
            </div>
          </div>

          {/* Component Math Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
            <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
              <div className="text-[10px] text-slate-400 font-mono">ON-HAND (OH)</div>
              <div className="text-xl font-bold text-white font-mono mt-1">+{atpData.on_hand_stock}</div>
            </div>
            <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
              <div className="text-[10px] text-amber-400 font-mono">RESERVED (R)</div>
              <div className="text-xl font-bold text-amber-400 font-mono mt-1">-{atpData.reserved_stock}</div>
            </div>
            <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
              <div className="text-[10px] text-rose-400 font-mono">BLOCKED (B)</div>
              <div className="text-xl font-bold text-rose-400 font-mono mt-1">-{atpData.blocked_stock}</div>
            </div>
            <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
              <div className="text-[10px] text-indigo-400 font-mono">INBOUND (I_e)</div>
              <div className="text-xl font-bold text-indigo-400 font-mono mt-1">+{atpData.eligible_inbound}</div>
            </div>
            <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
              <div className="text-[10px] text-teal-400 font-mono">RESERVABLE</div>
              <div className="text-xl font-bold text-teal-400 font-mono mt-1">{atpData.reservable_stock}</div>
            </div>
          </div>

          {/* Formula Line */}
          <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 font-mono text-xs text-slate-300">
            <div className="text-slate-400 text-[10px] uppercase mb-1">Formal Evaluation Formula:</div>
            <div className="text-cyan-300 text-sm">
              ATP = {atpData.on_hand_stock} (OH) - {atpData.reserved_stock} (R) - {atpData.blocked_stock} (B) + {atpData.eligible_inbound} (Eligible Inbound) = <span className="font-bold underline">{atpData.final_atp} Units</span>
            </div>
          </div>

          {/* Decision Reason */}
          <div className="space-y-1.5">
            <span className="text-xs font-mono text-slate-400 uppercase font-bold">Traceable Decision Reason</span>
            <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800 text-xs text-slate-300 font-mono leading-relaxed">
              {atpData.explanatory_decision_reason}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
