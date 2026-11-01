import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Layers,
  Calculator,
  ShieldAlert,
  ShoppingCart,
  ArrowRightLeft,
  SlidersHorizontal,
  RefreshCw,
  Database,
  FileCheck2,
  PackageCheck
} from 'lucide-react';

interface SidebarProps {
  collapsed: boolean;
  setCollapsed: (val: boolean) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ collapsed }) => {
  const navItems = [
    { label: 'Executive Overview', path: '/', icon: LayoutDashboard },
    { label: 'Inventory Center', path: '/inventory', icon: Layers },
    { label: 'ATP Explorer', path: '/atp', icon: Calculator },
    { label: 'Anomaly Center', path: '/anomalies', icon: ShieldAlert, highlight: true },
    { label: 'Orders & Allocation', path: '/orders', icon: ShoppingCart },
    { label: 'Transfers', path: '/transfers', icon: ArrowRightLeft },
    { label: 'What-If Simulator', path: '/simulator', icon: SlidersHorizontal },
    { label: 'Replenishment', path: '/replenishment', icon: RefreshCw },
    { label: 'Data Generator', path: '/generator', icon: Database },
    { label: 'Validation & Audit', path: '/audit', icon: FileCheck2 },
  ];

  return (
    <aside
      className={`fixed top-0 left-0 h-screen z-40 transition-all duration-300 ease-in-out border-r border-slate-800/80 bg-[#090e1d] flex flex-col ${
        collapsed ? 'w-20' : 'w-64'
      }`}
    >
      {/* Brand Header */}
      <div className="h-16 flex items-center px-4 border-b border-slate-800/80 gap-3">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-600 to-blue-500 flex items-center justify-center shadow-lg shadow-cyan-500/20 flex-shrink-0">
          <PackageCheck className="w-6 h-6 text-white" />
        </div>
        {!collapsed && (
          <div className="overflow-hidden">
            <h1 className="text-base font-bold tracking-tight text-white flex items-center gap-1.5">
              STOCKMIND <span className="text-cyan-400 font-extrabold text-xs px-1.5 py-0.5 rounded bg-cyan-950/60 border border-cyan-800/50">AI</span>
            </h1>
            <p className="text-[10px] text-slate-400 font-mono tracking-wider truncate">
              UNIFIED INVENTORY INTELLIGENCE
            </p>
          </div>
        )}
      </div>

      {/* Nav List */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all group ${
                  isActive
                    ? 'bg-cyan-500/15 text-cyan-400 border border-cyan-500/30 shadow-sm shadow-cyan-500/10'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                }`
              }
            >
              <Icon className="w-5 h-5 flex-shrink-0 group-hover:text-cyan-400 transition-colors" />
              {!collapsed && (
                <span className="truncate flex-1 flex items-center justify-between">
                  {item.label}
                  {item.highlight && (
                    <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse"></span>
                  )}
                </span>
              )}
            </NavLink>
          );
        })}
      </nav>

      {/* Footer Info */}
      <div className="p-4 border-t border-slate-800/80 text-[11px] text-slate-400">
        {!collapsed ? (
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
              <span className="text-slate-300 font-mono">CORE ENGINE OPERATIONAL</span>
            </div>
            <div className="text-slate-400 text-[10px]">
              YottaFlex Round 2 &bull; Python 3.11 &bull; SQLite/PG
            </div>
          </div>
        ) : (
          <div className="flex justify-center">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400"></span>
          </div>
        )}
      </div>
    </aside>
  );
};
