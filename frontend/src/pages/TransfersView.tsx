import React, { useEffect, useState } from 'react';
import { fetchTransfers, dispatchTransfer, receiveTransfer, TransferItem } from '../services/api';
import { ArrowRightLeft, Send, CheckCircle2, Truck, AlertCircle } from 'lucide-react';

export const TransfersView: React.FC = () => {
  const [transfers, setTransfers] = useState<TransferItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [actionMsg, setActionMsg] = useState<string | null>(null);

  useEffect(() => {
    loadTransfers();
  }, []);

  const loadTransfers = async () => {
    setLoading(true);
    try {
      const data = await fetchTransfers();
      setTransfers(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleDispatch = async (id: string) => {
    try {
      await dispatchTransfer(id);
      setActionMsg(`Transfer ${id} dispatched: Source stock deducted, in-transit created.`);
      await loadTransfers();
    } catch (err: any) {
      setActionMsg(err?.response?.data?.detail || 'Dispatch failed');
    }
  };

  const handleReceive = async (id: string) => {
    try {
      await receiveTransfer(id);
      setActionMsg(`Transfer ${id} received: In-transit cleared, destination on-hand credited.`);
      await loadTransfers();
    } catch (err: any) {
      setActionMsg(err?.response?.data?.detail || 'Receipt failed');
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'COMPLETED':
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-950 text-emerald-400 border border-emerald-800">COMPLETED</span>;
      case 'IN_TRANSIT':
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-cyan-950 text-cyan-400 border border-cyan-800 animate-pulse">IN_TRANSIT</span>;
      case 'APPROVED':
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-blue-950 text-blue-400 border border-blue-800">APPROVED</span>;
      default:
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-800 text-slate-300 border border-slate-700">{status}</span>;
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
          <ArrowRightLeft className="w-5 h-5 text-cyan-400" />
          Two-Phase Inter-Location Transfers
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Guaranteed zero double-counting: Source deduction on dispatch &rarr; Destination receipt on arrival.
        </p>
      </div>

      {actionMsg && (
        <div className="p-3 rounded-lg bg-cyan-950/60 border border-cyan-800 text-cyan-300 text-xs font-mono flex items-center justify-between">
          <span>{actionMsg}</span>
          <button onClick={() => setActionMsg(null)} className="text-cyan-400 hover:text-white">&times;</button>
        </div>
      )}

      {/* Transfers Table */}
      <div className="rounded-xl border border-slate-800/80 bg-[#090e1d] overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#0f172a] text-slate-400 border-b border-slate-800 font-mono uppercase text-[11px]">
              <tr>
                <th className="py-3 px-4">Transfer ID</th>
                <th className="py-3 px-4">Source Node</th>
                <th className="py-3 px-4">Destination Node</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Carrier / Tracking</th>
                <th className="py-3 px-4 text-center">Lifecycle Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/50">
              {loading ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-400">Loading transfers...</td>
                </tr>
              ) : transfers.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-slate-400">No active transfers found.</td>
                </tr>
              ) : transfers.map((trn) => (
                <tr key={trn.transfer_id} className="hover:bg-slate-800/40 transition-colors">
                  <td className="py-3 px-4 font-mono font-medium text-white">{trn.transfer_id}</td>
                  <td className="py-3 px-4 font-mono text-slate-300">{trn.source_location_id}</td>
                  <td className="py-3 px-4 font-mono text-cyan-400">{trn.destination_location_id}</td>
                  <td className="py-3 px-4">{getStatusBadge(trn.status)}</td>
                  <td className="py-3 px-4 font-mono text-slate-400">{trn.carrier || 'Internal Fleet'} {trn.tracking_reference ? `(${trn.tracking_reference})` : ''}</td>
                  <td className="py-3 px-4 text-center space-x-2">
                    {trn.status === 'CREATED' && (
                      <button
                        onClick={() => handleDispatch(trn.transfer_id)}
                        className="px-2.5 py-1 rounded bg-cyan-900/60 hover:bg-cyan-800 text-[10px] text-cyan-300 font-medium border border-cyan-700"
                      >
                        Dispatch Stock
                      </button>
                    )}
                    {trn.status === 'IN_TRANSIT' && (
                      <button
                        onClick={() => handleReceive(trn.transfer_id)}
                        className="px-2.5 py-1 rounded bg-emerald-900/60 hover:bg-emerald-800 text-[10px] text-emerald-300 font-medium border border-emerald-700"
                      >
                        Receive Stock
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
