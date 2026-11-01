import React, { useEffect, useState } from 'react';
import { fetchReplenishmentRecommendations } from '../services/api';
import { RefreshCw, AlertTriangle, ArrowRight, ShieldCheck, DollarSign } from 'lucide-react';

export const ReplenishmentView: React.FC = () => {
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    loadRecommendations();
  }, []);

  const loadRecommendations = async () => {
    setLoading(true);
    try {
      const data = await fetchReplenishmentRecommendations();
      setRecommendations(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const getUrgencyBadge = (urgency: string) => {
    switch (urgency) {
      case 'CRITICAL':
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-rose-950 text-rose-400 border border-rose-800 font-bold">CRITICAL DEFICIT</span>;
      case 'HIGH':
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-amber-950 text-amber-400 border border-amber-800 font-bold">SAFETY BREACH</span>;
      default:
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-yellow-950 text-yellow-400 border border-yellow-800 font-medium">REORDER POINT</span>;
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
          <RefreshCw className="w-5 h-5 text-cyan-400" />
          Autonomous Replenishment Intelligence
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Automated purchase and transfer recommendations derived from lead times, reorder points, and safety buffers.
        </p>
      </div>

      <div className="rounded-xl border border-slate-800/80 bg-[#090e1d] overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#0f172a] text-slate-400 border-b border-slate-800 font-mono uppercase text-[11px]">
              <tr>
                <th className="py-3 px-4">SKU / Variant</th>
                <th className="py-3 px-4">Location</th>
                <th className="py-3 px-4 text-right">Available</th>
                <th className="py-3 px-4 text-right">Reorder Pt</th>
                <th className="py-3 px-4 text-right">Safety Buffer</th>
                <th className="py-3 px-4 text-right font-bold text-cyan-400">Recommended Qty</th>
                <th className="py-3 px-4 text-right">Est. Cost</th>
                <th className="py-3 px-4 text-center">Urgency</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/50">
              {loading ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-slate-400">Loading replenishment signals...</td>
                </tr>
              ) : recommendations.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-8 text-center text-emerald-400 font-mono">
                    All inventory levels healthy and above reorder thresholds!
                  </td>
                </tr>
              ) : recommendations.map((rec, idx) => (
                <tr key={idx} className="hover:bg-slate-800/40 transition-colors">
                  <td className="py-3 px-4">
                    <div className="font-mono font-medium text-white">{rec.sku_code}</div>
                    <div className="text-[10px] text-slate-400">{rec.variant}</div>
                  </td>
                  <td className="py-3 px-4 font-mono text-slate-300">{rec.location_name}</td>
                  <td className="py-3 px-4 text-right font-mono text-slate-200">{rec.available_stock}</td>
                  <td className="py-3 px-4 text-right font-mono text-slate-400">{rec.reorder_point}</td>
                  <td className="py-3 px-4 text-right font-mono text-slate-400">{rec.safety_stock}</td>
                  <td className="py-3 px-4 text-right font-mono font-bold text-cyan-400">+{rec.recommended_order_quantity}</td>
                  <td className="py-3 px-4 text-right font-mono text-slate-300">${rec.estimated_cost.toLocaleString()}</td>
                  <td className="py-3 px-4 text-center">{getUrgencyBadge(rec.urgency)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
