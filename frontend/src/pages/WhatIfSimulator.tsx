import React, { useState } from 'react';
import { runWhatIfSimulation } from '../services/api';
import { SlidersHorizontal, TrendingDown, AlertTriangle, ShieldCheck, Play } from 'lucide-react';

export const WhatIfSimulator: React.FC = () => {
  const [demandSurge, setDemandSurge] = useState<number>(25);
  const [leadTimeDelay, setLeadTimeDelay] = useState<number>(5);
  const [results, setResults] = useState<any | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  const handleSimulate = async () => {
    setLoading(true);
    try {
      const data = await runWhatIfSimulation(demandSurge, leadTimeDelay);
      setResults(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
          <SlidersHorizontal className="w-5 h-5 text-cyan-400" />
          Inventory Digital Twin & Scenario Simulator
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Non-destructive scenario modeling: simulate unexpected demand shocks and transit disruptions without modifying real records.
        </p>
      </div>

      {/* Sliders Card */}
      <div className="p-6 rounded-2xl bg-[#090e1d] border border-slate-800 shadow-xl space-y-6">
        <div className="space-y-4">
          <div>
            <div className="flex justify-between text-xs font-mono mb-2">
              <span className="text-slate-300">PROJECTED DEMAND SURGE:</span>
              <span className="text-cyan-400 font-bold">+{demandSurge}%</span>
            </div>
            <input
              type="range"
              min="0"
              max="100"
              step="5"
              value={demandSurge}
              onChange={(e) => setDemandSurge(Number(e.target.value))}
              className="w-full accent-cyan-500 bg-slate-800 h-2 rounded-lg cursor-pointer"
            />
          </div>

          <div>
            <div className="flex justify-between text-xs font-mono mb-2">
              <span className="text-slate-300">SUPPLIER LEAD-TIME DELAY:</span>
              <span className="text-amber-400 font-bold">+{leadTimeDelay} DAYS</span>
            </div>
            <input
              type="range"
              min="0"
              max="30"
              step="1"
              value={leadTimeDelay}
              onChange={(e) => setLeadTimeDelay(Number(e.target.value))}
              className="w-full accent-amber-500 bg-slate-800 h-2 rounded-lg cursor-pointer"
            />
          </div>
        </div>

        <button
          onClick={handleSimulate}
          disabled={loading}
          className="w-full py-2.5 rounded-lg text-xs font-semibold bg-gradient-to-r from-cyan-600 to-blue-600 text-white hover:from-cyan-500 hover:to-blue-500 transition-all flex items-center justify-center gap-2 shadow-lg shadow-cyan-500/20"
        >
          <Play className="w-4 h-4 fill-current" />
          {loading ? 'Simulating Dynamic Impact...' : 'Run Non-Destructive Simulation'}
        </button>
      </div>

      {/* Simulation Results */}
      {results && (
        <div className="p-6 rounded-2xl bg-[#090e1d] border border-slate-800/80 shadow-2xl space-y-6">
          <h3 className="text-sm font-bold text-white font-mono uppercase tracking-wide">
            Projected Network Stress Impact
          </h3>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800">
              <span className="text-[10px] text-slate-400 font-mono">BASELINE ATP</span>
              <div className="text-lg font-bold text-slate-200 font-mono mt-1">
                {results.baseline.available_to_promise.toLocaleString()}
              </div>
            </div>
            <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800">
              <span className="text-[10px] text-cyan-400 font-mono">SIMULATED ATP</span>
              <div className="text-lg font-bold text-cyan-400 font-mono mt-1">
                {results.projected_simulation.projected_available_to_promise.toLocaleString()}
              </div>
              <div className="text-[10px] text-rose-400 font-mono mt-1">
                -{results.projected_simulation.atp_reduction_pct}% reduction
              </div>
            </div>
            <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800">
              <span className="text-[10px] text-slate-400 font-mono">BASELINE STOCKOUTS</span>
              <div className="text-lg font-bold text-slate-200 font-mono mt-1">
                {results.baseline.stockout_locations_count} ({results.baseline.stockout_rate_pct}%)
              </div>
            </div>
            <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800">
              <span className="text-[10px] text-rose-400 font-mono">SIMULATED STOCKOUTS</span>
              <div className="text-lg font-bold text-rose-400 font-mono mt-1">
                {results.projected_simulation.projected_stockout_locations} ({results.projected_simulation.projected_stockout_rate_pct}%)
              </div>
            </div>
          </div>

          <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 space-y-1 font-mono text-xs text-slate-300">
            <span className="text-[10px] text-cyan-400 font-bold uppercase">Automated Operational Mitigation Recommendation:</span>
            <p className="text-slate-300">{results.projected_simulation.recommendation}</p>
          </div>
        </div>
      )}
    </div>
  );
};
