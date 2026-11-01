import React, { useEffect, useState } from 'react';
import {
  fetchOverviewKPIs,
  fetchLocationCharts,
  fetchCategoryCharts,
  KPIOverviewData
} from '../services/api';
import {
  Boxes,
  MapPin,
  TrendingUp,
  ShieldAlert,
  Percent,
  CheckCircle2,
  Clock,
  Truck,
  Layers,
  ArrowUpRight
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend
} from 'recharts';

const COLORS = ['#0284c7', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899', '#6366f1'];

export const ExecutiveOverview: React.FC = () => {
  const [kpis, setKpis] = useState<KPIOverviewData | null>(null);
  const [locationData, setLocationData] = useState<any[]>([]);
  const [categoryData, setCategoryData] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [kpiRes, locRes, catRes] = await Promise.all([
        fetchOverviewKPIs(),
        fetchLocationCharts(),
        fetchCategoryCharts()
      ]);
      setKpis(kpiRes);
      setLocationData(locRes || []);
      setCategoryData(catRes || []);
    } catch (err) {
      console.error('Failed to load overview data', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading || !kpis) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin"></div>
          <span className="text-xs font-mono text-slate-400">LOADING INVENTORY INTELLIGENCE...</span>
        </div>
      </div>
    );
  }

  const cards = [
    {
      label: 'Total SKUs',
      value: kpis.total_skus.toLocaleString(),
      subtext: `${kpis.total_locations} Active Nodes`,
      icon: Boxes,
      color: 'text-cyan-400',
      bg: 'bg-cyan-500/10 border-cyan-500/20'
    },
    {
      label: 'On-Hand Inventory',
      value: kpis.total_on_hand_inventory.toLocaleString(),
      subtext: `${kpis.available_to_promise_quantity.toLocaleString()} ATP`,
      icon: Layers,
      color: 'text-blue-400',
      bg: 'bg-blue-500/10 border-blue-500/20'
    },
    {
      label: 'In-Transit Stock',
      value: kpis.in_transit_inventory.toLocaleString(),
      subtext: 'Across Active Transfers',
      icon: Truck,
      color: 'text-indigo-400',
      bg: 'bg-indigo-500/10 border-indigo-500/20'
    },
    {
      label: 'Active Reservations',
      value: kpis.active_reservations.toLocaleString(),
      subtext: `${kpis.reservation_expiry_rate_pct}% Expired Rate`,
      icon: Clock,
      color: 'text-amber-400',
      bg: 'bg-amber-500/10 border-amber-500/20'
    },
    {
      label: 'Fulfillment Rate',
      value: `${kpis.fulfillment_rate_pct}%`,
      subtext: `${kpis.open_orders} Open Orders`,
      icon: Percent,
      color: 'text-emerald-400',
      bg: 'bg-emerald-500/10 border-emerald-500/20'
    },
    {
      label: 'Inventory Accuracy',
      value: `${kpis.inventory_accuracy_pct}%`,
      subtext: `${kpis.stockout_rate_pct}% Stockout Exposure`,
      icon: CheckCircle2,
      color: 'text-teal-400',
      bg: 'bg-teal-500/10 border-teal-500/20'
    },
    {
      label: 'Detected Anomalies',
      value: kpis.total_anomalies.toString(),
      subtext: `${kpis.critical_anomalies} Critical / ${kpis.open_anomalies} Open`,
      icon: ShieldAlert,
      color: 'text-rose-400',
      bg: 'bg-rose-500/10 border-rose-500/20'
    }
  ];

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-6 rounded-2xl bg-gradient-to-r from-slate-900 via-[#0d1627] to-slate-900 border border-slate-800 shadow-xl">
        <div>
          <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-cyan-950/80 border border-cyan-800 text-cyan-400 text-xs font-mono mb-2">
            <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-ping"></span>
            PRODUCTION LEDGER ENGINE ACTIVE
          </div>
          <h2 className="text-2xl font-bold tracking-tight text-white">
            Unified Inventory Intelligence Overview
          </h2>
          <p className="text-sm text-slate-400 mt-1 max-w-2xl">
            Real-time reconciliation, deterministic ATP calculations, and autonomous anomaly detection across multi-channel distribution networks.
          </p>
        </div>
      </div>

      {/* KPI Metric Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
        {cards.map((c, idx) => {
          const Icon = c.icon;
          return (
            <div
              key={idx}
              className={`p-4 rounded-xl border ${c.bg} backdrop-blur-sm transition-all hover:translate-y-[-2px]`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-slate-400 font-medium">{c.label}</span>
                <Icon className={`w-4 h-4 ${c.color}`} />
              </div>
              <div className="text-xl font-bold text-white font-mono tracking-tight">
                {c.value}
              </div>
              <div className="text-[10px] text-slate-400 mt-1 truncate">
                {c.subtext}
              </div>
            </div>
          );
        })}
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Location Stock Chart */}
        <div className="lg:col-span-2 p-6 rounded-2xl bg-[#090e1d] border border-slate-800/80 shadow-lg">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-base font-semibold text-white">Inventory by Node Location</h3>
              <p className="text-xs text-slate-400">Comparison of On-Hand vs Available to Promise across facilities</p>
            </div>
            <div className="flex items-center gap-3 text-xs">
              <span className="flex items-center gap-1.5 text-cyan-400 font-mono">
                <span className="w-2.5 h-2.5 rounded bg-cyan-500"></span> On-Hand
              </span>
              <span className="flex items-center gap-1.5 text-emerald-400 font-mono">
                <span className="w-2.5 h-2.5 rounded bg-emerald-500"></span> Available
              </span>
            </div>
          </div>
          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={locationData}>
                <XAxis dataKey="location_name" stroke="#64748b" fontSize={10} tickLine={false} interval={0} angle={-15} textAnchor="end" height={50} />
                <YAxis stroke="#64748b" fontSize={11} tickLine={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
                />
                <Bar dataKey="on_hand" fill="#0284c7" radius={[4, 4, 0, 0]} />
                <Bar dataKey="available" fill="#10b981" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Category Share Donut Chart */}
        <div className="p-6 rounded-2xl bg-[#090e1d] border border-slate-800/80 shadow-lg flex flex-col">
          <div className="mb-4">
            <h3 className="text-base font-semibold text-white">Product Category Distribution</h3>
            <p className="text-xs text-slate-400">Inventory units grouped by merchandise category</p>
          </div>
          <div className="h-64 w-full flex-1">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={categoryData}
                  dataKey="total_units"
                  nameKey="category"
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={80}
                  paddingAngle={4}
                >
                  {categoryData.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
                />
                <Legend layout="horizontal" verticalAlign="bottom" wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};
