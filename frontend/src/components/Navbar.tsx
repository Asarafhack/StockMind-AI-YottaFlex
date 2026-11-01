import React from 'react';
import { Menu, Bell, ShieldCheck, Database, RefreshCw } from 'lucide-react';

interface NavbarProps {
  collapsed: boolean;
  setCollapsed: (val: boolean) => void;
  onRefresh?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ collapsed, setCollapsed, onRefresh }) => {
  return (
    <header
      className={`fixed top-0 right-0 h-16 z-30 transition-all duration-300 ease-in-out border-b border-slate-800/80 bg-[#090e1d]/90 backdrop-blur-md flex items-center justify-between px-6 ${
        collapsed ? 'left-20' : 'left-64'
      }`}
    >
      <div className="flex items-center gap-4">
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="p-2 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-slate-800/60 transition-colors"
          title="Toggle Navigation"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-2 text-xs font-mono">
          <span className="px-2 py-1 rounded bg-slate-800 text-slate-300 border border-slate-700">
            SEED: 20261022
          </span>
          <span className="hidden sm:inline-block px-2 py-1 rounded bg-emerald-950/50 text-emerald-400 border border-emerald-800/50">
            RECONCILIATION: ACTIVE
          </span>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {onRefresh && (
          <button
            onClick={onRefresh}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-800/80 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Refresh Data</span>
          </button>
        )}

        <div className="flex items-center gap-2 pl-3 border-l border-slate-800">
          <div className="w-8 h-8 rounded-full bg-cyan-950 border border-cyan-800 text-cyan-400 font-mono text-xs flex items-center justify-center font-bold">
            FDE
          </div>
          <div className="hidden md:block text-left text-xs">
            <div className="font-semibold text-slate-200">Forward Deployed Eng</div>
            <div className="text-[10px] text-slate-400">YottaFlex AI Review</div>
          </div>
        </div>
      </div>
    </header>
  );
};
