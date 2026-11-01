import React, { useEffect, useState } from 'react';
import { fetchOrders, allocateOrder, fulfillOrder, OrderItem } from '../services/api';
import { ShoppingCart, Send, CheckCircle2, AlertCircle, Clock, Truck } from 'lucide-react';

export const OrdersAllocation: React.FC = () => {
  const [orders, setOrders] = useState<OrderItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [actionMsg, setActionMsg] = useState<string | null>(null);

  useEffect(() => {
    loadOrders();
  }, []);

  const loadOrders = async () => {
    setLoading(true);
    try {
      const data = await fetchOrders(50);
      setOrders(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleAllocate = async (orderId: string) => {
    try {
      const res = await allocateOrder(orderId);
      setActionMsg(`Order ${orderId} allocated successfully across eligible fulfillment locations.`);
      await loadOrders();
    } catch (err: any) {
      setActionMsg(err?.response?.data?.detail || 'Allocation failed');
    }
  };

  const handleFulfill = async (orderId: string) => {
    try {
      const res = await fulfillOrder(orderId);
      setActionMsg(`Shipment ${res.shipment_id} created with tracking ${res.tracking_reference}. Reserved stock consumed.`);
      await loadOrders();
    } catch (err: any) {
      setActionMsg(err?.response?.data?.detail || 'Fulfillment failed');
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'SHIPPED':
      case 'DELIVERED':
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-950 text-emerald-400 border border-emerald-800">{status}</span>;
      case 'ALLOCATED':
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-cyan-950 text-cyan-400 border border-cyan-800">ALLOCATED</span>;
      case 'PARTIALLY_ALLOCATED':
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-yellow-950 text-yellow-400 border border-yellow-800">PARTIAL</span>;
      case 'BACKORDERED':
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-rose-950 text-rose-400 border border-rose-800">BACKORDERED</span>;
      default:
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-800 text-slate-300 border border-slate-700">PENDING</span>;
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
          <ShoppingCart className="w-5 h-5 text-cyan-400" />
          Multi-Channel Order Allocation & Fulfillment
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Traceable order lines, ATP-based location allocation, and shipment dispatch lifecycle.
        </p>
      </div>

      {actionMsg && (
        <div className="p-3 rounded-lg bg-cyan-950/60 border border-cyan-800 text-cyan-300 text-xs font-mono flex items-center justify-between">
          <span>{actionMsg}</span>
          <button onClick={() => setActionMsg(null)} className="text-cyan-400 hover:text-white">&times;</button>
        </div>
      )}

      {/* Orders List */}
      <div className="rounded-xl border border-slate-800/80 bg-[#090e1d] overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#0f172a] text-slate-400 border-b border-slate-800 font-mono uppercase text-[11px]">
              <tr>
                <th className="py-3 px-4">Order ID</th>
                <th className="py-3 px-4">Channel</th>
                <th className="py-3 px-4">Customer Ref</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Lines</th>
                <th className="py-3 px-4 text-right">Total Amount</th>
                <th className="py-3 px-4">Fulfillment Node</th>
                <th className="py-3 px-4 text-center">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/50">
              {loading ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-slate-400">Loading orders...</td>
                </tr>
              ) : orders.map((ord) => (
                <tr key={ord.order_id} className="hover:bg-slate-800/40 transition-colors">
                  <td className="py-3 px-4 font-mono font-medium text-white">{ord.order_id}</td>
                  <td className="py-3 px-4 font-mono text-cyan-400">{ord.channel}</td>
                  <td className="py-3 px-4 font-mono text-slate-400">{ord.customer_reference}</td>
                  <td className="py-3 px-4">{getStatusBadge(ord.order_status)}</td>
                  <td className="py-3 px-4 text-right font-mono text-slate-300">{ord.order_lines.length}</td>
                  <td className="py-3 px-4 text-right font-mono font-bold text-white">${ord.total_amount.toLocaleString()}</td>
                  <td className="py-3 px-4 font-mono text-slate-300">{ord.fulfillment_location_id || 'UNASSIGNED'}</td>
                  <td className="py-3 px-4 text-center space-x-2">
                    {ord.order_status === 'PENDING' && (
                      <button
                        onClick={() => handleAllocate(ord.order_id)}
                        className="px-2.5 py-1 rounded bg-cyan-900/60 hover:bg-cyan-800 text-[10px] text-cyan-300 font-medium border border-cyan-700"
                      >
                        Allocate
                      </button>
                    )}
                    {ord.order_status === 'ALLOCATED' && (
                      <button
                        onClick={() => handleFulfill(ord.order_id)}
                        className="px-2.5 py-1 rounded bg-emerald-900/60 hover:bg-emerald-800 text-[10px] text-emerald-300 font-medium border border-emerald-700"
                      >
                        Fulfill & Ship
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
