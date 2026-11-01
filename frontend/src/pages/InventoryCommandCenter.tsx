import React, { useEffect, useState } from 'react';
import {
  fetchInventoryBalances,
  fetchATPBreakdown,
  reconcileBalance,
  applyCompensatingAdjustment,
  InventoryBalanceItem,
  ATPData
} from '../services/api';
import {
  Search,
  Filter,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  ShieldAlert,
  ArrowRight,
  Layers,
  Calculator,
  Sliders,
  X
} from 'lucide-react';

export const InventoryCommandCenter: React.FC = () => {
  const [balances, setBalances] = useState<InventoryBalanceItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [search, setSearch] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [selectedItem, setSelectedItem] = useState<InventoryBalanceItem | null>(null);
  const [atpDetail, setAtpDetail] = useState<ATPData | null>(null);
  const [reconResult, setReconResult] = useState<any | null>(null);
  const [actionLoading, setActionLoading] = useState<boolean>(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  useEffect(() => {
    loadBalances();
  }, [statusFilter]);

  const loadBalances = async () => {
    setLoading(true);
    try {
      const data = await fetchInventoryBalances({
        status: statusFilter || undefined,
        limit: 100
      });
      setBalances(data);
    } catch (err) {
      console.error('Failed to load inventory', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectItem = async (item: InventoryBalanceItem) => {
    setSelectedItem(item);
    setAtpDetail(null);
    setReconResult(null);
    setActionMessage(null);
    try {
      const atp = await fetchATPBreakdown(item.sku_id, item.location_id);
      setAtpDetail(atp);
    } catch (err) {
      console.error('Failed to fetch ATP detail', err);
    }
  };

  const handleReconcile = async () => {
    if (!selectedItem) return;
    setActionLoading(true);
    try {
      const res = await reconcileBalance(selectedItem.sku_id, selectedItem.location_id);
      setReconResult(res);
      setActionMessage(
        res.is_matched
          ? 'Ledger and stored balance matched perfectly!'
          : `Discrepancy detected: Stored ${res.stored_on_hand} vs Ledger ${res.ledger_on_hand} (drift: ${res.discrepancy})`
      );
    } catch (err) {
      console.error(err);
    } finally {
      setActionLoading(false);
    }
  };

  const handleCompensate = async () => {
    if (!selectedItem) return;
    setActionLoading(true);
    try {
      const res = await applyCompensatingAdjustment(selectedItem.sku_id, selectedItem.location_id);
      setActionMessage(res.message || `Compensating movement ${res.movement_id} recorded successfully.`);
      await loadBalances();
      const updatedAtp = await fetchATPBreakdown(selectedItem.sku_id, selectedItem.location_id);
      setAtpDetail(updatedAtp);
      const recon = await reconcileBalance(selectedItem.sku_id, selectedItem.location_id);
      setReconResult(recon);
    } catch (err) {
      console.error(err);
    } finally {
      setActionLoading(false);
    }
  };

  const filteredBalances = balances.filter(b =>
    b.sku_id.toLowerCase().includes(search.toLowerCase()) ||
    b.location_id.toLowerCase().includes(search.toLowerCase())
  );

  const getStatusBadge = (b: InventoryBalanceItem) => {
    if (b.available_quantity === 0) {
      return <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-rose-950/70 text-rose-400 border border-rose-800">STOCKOUT</span>;
    }
    if (b.blocked_quantity > 0) {
      return <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-amber-950/70 text-amber-400 border border-amber-800">BLOCKED</span>;
    }
    if (b.available_quantity <= b.safety_stock_quantity) {
      return <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-yellow-950/70 text-yellow-400 border border-yellow-800">LOW_STOCK</span>;
    }
    return <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-emerald-950/70 text-emerald-400 border border-emerald-800">HEALTHY</span>;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">Inventory Command Center</h2>
          <p className="text-xs text-slate-400">Searchable multi-node balance ledger, safety buffers, and real-time ATP state</p>
        </div>

        <div className="flex items-center gap-2">
          {/* Filter Dropdown */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2 rounded-lg bg-[#0e1628] border border-slate-700 text-xs text-slate-200 focus:outline-none focus:border-cyan-500 font-mono"
          >
            <option value="">ALL STATUSES</option>
            <option value="HEALTHY">HEALTHY</option>
            <option value="LOW_STOCK">LOW STOCK</option>
            <option value="STOCKOUT">STOCKOUT</option>
            <option value="BLOCKED">BLOCKED LOTS</option>
          </select>

          {/* Search Box */}
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              placeholder="Filter SKU or Node..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9 pr-3 py-2 rounded-lg bg-[#0e1628] border border-slate-700 text-xs text-slate-200 focus:outline-none focus:border-cyan-500 font-mono w-48 sm:w-60"
            />
          </div>
        </div>
      </div>

      {/* Main Table */}
      <div className="rounded-xl border border-slate-800/80 bg-[#090e1d] overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#0f172a] text-slate-400 border-b border-slate-800 font-mono uppercase text-[11px]">
              <tr>
                <th className="py-3 px-4">SKU Code</th>
                <th className="py-3 px-4">Node Location</th>
                <th className="py-3 px-4 text-right">On-Hand</th>
                <th className="py-3 px-4 text-right">Reserved</th>
                <th className="py-3 px-4 text-right">Blocked</th>
                <th className="py-3 px-4 text-right">Safety Stock</th>
                <th className="py-3 px-4 text-right">In-Transit</th>
                <th className="py-3 px-4 text-right font-bold text-cyan-400">ATP</th>
                <th className="py-3 px-4 text-center">Health Status</th>
                <th className="py-3 px-4 text-center">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/50">
              {loading ? (
                <tr>
                  <td colSpan={10} className="py-12 text-center text-slate-400">
                    <div className="flex items-center justify-center gap-2">
                      <div className="w-4 h-4 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin"></div>
                      <span>Loading inventory ledger...</span>
                    </div>
                  </td>
                </tr>
              ) : filteredBalances.length === 0 ? (
                <tr>
                  <td colSpan={10} className="py-8 text-center text-slate-400">
                    No matching inventory records found.
                  </td>
                </tr>
              ) : (
                filteredBalances.map((b) => (
                  <tr
                    key={b.balance_id}
                    onClick={() => handleSelectItem(b)}
                    className="hover:bg-slate-800/40 cursor-pointer transition-colors group"
                  >
                    <td className="py-3 px-4 font-mono font-medium text-white group-hover:text-cyan-400">
                      {b.sku_id}
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-300">
                      {b.location_id}
                    </td>
                    <td className="py-3 px-4 text-right font-mono text-slate-200">
                      {b.on_hand_quantity.toLocaleString()}
                    </td>
                    <td className="py-3 px-4 text-right font-mono text-amber-400/90">
                      {b.reserved_quantity.toLocaleString()}
                    </td>
                    <td className="py-3 px-4 text-right font-mono text-rose-400/90">
                      {b.blocked_quantity.toLocaleString()}
                    </td>
                    <td className="py-3 px-4 text-right font-mono text-slate-400">
                      {b.safety_stock_quantity.toLocaleString()}
                    </td>
                    <td className="py-3 px-4 text-right font-mono text-indigo-400">
                      {b.in_transit_quantity.toLocaleString()}
                    </td>
                    <td className="py-3 px-4 text-right font-mono font-bold text-cyan-400">
                      {b.available_quantity.toLocaleString()}
                    </td>
                    <td className="py-3 px-4 text-center">
                      {getStatusBadge(b)}
                    </td>
                    <td className="py-3 px-4 text-center">
                      <button className="px-2.5 py-1 rounded bg-slate-800 text-[10px] text-slate-300 hover:bg-cyan-900/40 hover:text-cyan-300 border border-slate-700">
                        Inspect
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Detail Slideout / Modal */}
      {selectedItem && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex justify-end">
          <div className="w-full max-w-xl h-full bg-[#0a101f] border-l border-slate-800 p-6 overflow-y-auto space-y-6">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <div>
                <span className="text-xs font-mono text-cyan-400 font-bold">INVENTORY LEDGER DETAIL</span>
                <h3 className="text-lg font-bold text-white font-mono mt-0.5">
                  {selectedItem.sku_id} @ {selectedItem.location_id}
                </h3>
              </div>
              <button
                onClick={() => setSelectedItem(null)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Metric Grid */}
            <div className="grid grid-cols-3 gap-3">
              <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800">
                <div className="text-[10px] text-slate-400 font-mono">ON-HAND</div>
                <div className="text-lg font-bold text-white font-mono">{selectedItem.on_hand_quantity}</div>
              </div>
              <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800">
                <div className="text-[10px] text-amber-400 font-mono">RESERVED</div>
                <div className="text-lg font-bold text-amber-400 font-mono">{selectedItem.reserved_quantity}</div>
              </div>
              <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800">
                <div className="text-[10px] text-cyan-400 font-mono">CALCULATED ATP</div>
                <div className="text-lg font-bold text-cyan-400 font-mono">
                  {atpDetail ? atpDetail.final_atp : selectedItem.available_quantity}
                </div>
              </div>
            </div>

            {/* ATP Math Breakdown Box */}
            <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
              <div className="flex items-center gap-2 text-xs font-semibold text-slate-200">
                <Calculator className="w-4 h-4 text-cyan-400" />
                <span>Deterministic ATP Breakdown Formula</span>
              </div>
              <div className="p-3 rounded bg-black/40 font-mono text-[11px] text-cyan-300 border border-cyan-950">
                ATP = On-Hand ({selectedItem.on_hand_quantity}) - Reserved ({selectedItem.reserved_quantity}) - Blocked ({selectedItem.blocked_quantity}) + Eligible Inbound ({atpDetail?.eligible_inbound || 0})
              </div>
              {atpDetail && (
                <div className="text-xs text-slate-300 space-y-1">
                  <div className="text-slate-400 text-[11px] font-mono">DECISION REASON:</div>
                  <p className="p-2.5 rounded bg-slate-950/60 border border-slate-800/80 text-[11px] text-slate-300 font-mono">
                    {atpDetail.explanatory_decision_reason}
                  </p>
                </div>
              )}
            </div>

            {/* Actions: Reconcile & Compensate */}
            <div className="space-y-3 pt-2">
              <span className="text-xs font-mono text-slate-400 font-bold uppercase">Ledger Source-of-Truth Actions</span>
              <div className="grid grid-cols-2 gap-3">
                <button
                  onClick={handleReconcile}
                  disabled={actionLoading}
                  className="flex items-center justify-center gap-2 py-2 px-3 rounded-lg text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${actionLoading ? 'animate-spin' : ''}`} />
                  Reconcile vs Ledger
                </button>
                <button
                  onClick={handleCompensate}
                  disabled={actionLoading}
                  className="flex items-center justify-center gap-2 py-2 px-3 rounded-lg text-xs font-medium bg-cyan-900/50 hover:bg-cyan-800/60 text-cyan-300 border border-cyan-700 transition-colors"
                >
                  <CheckCircle className="w-3.5 h-3.5" />
                  Auto-Compensate
                </button>
              </div>

              {actionMessage && (
                <div className="p-3 rounded-lg text-xs font-mono bg-cyan-950/50 text-cyan-300 border border-cyan-800/60">
                  {actionMessage}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
