import React, { useState } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Sidebar } from './components/Sidebar';
import { Navbar } from './components/Navbar';
import { ExecutiveOverview } from './pages/ExecutiveOverview';
import { InventoryCommandCenter } from './pages/InventoryCommandCenter';
import { ATPExplorer } from './pages/ATPExplorer';
import { AnomalyCenter } from './pages/AnomalyCenter';
import { OrdersAllocation } from './pages/OrdersAllocation';
import { TransfersView } from './pages/TransfersView';
import { WhatIfSimulator } from './pages/WhatIfSimulator';
import { ReplenishmentView } from './pages/ReplenishmentView';
import { DataGeneratorConsole } from './pages/DataGeneratorConsole';
import { AuditAndValidation } from './pages/AuditAndValidation';

export const App: React.FC = () => {
  const [collapsed, setCollapsed] = useState<boolean>(false);
  const [refreshKey, setRefreshKey] = useState<number>(0);

  const handleRefresh = () => {
    setRefreshKey((prev) => prev + 1);
  };

  return (
    <BrowserRouter>
      <div className="min-h-screen bg-[#080d1a] text-slate-100 flex">
        {/* Collapsible Sidebar */}
        <Sidebar collapsed={collapsed} setCollapsed={setCollapsed} />

        {/* Main Content Area */}
        <div
          className={`flex-1 flex flex-col min-h-screen transition-all duration-300 ease-in-out ${
            collapsed ? 'pl-20' : 'pl-64'
          }`}
        >
          {/* Top Navbar */}
          <Navbar collapsed={collapsed} setCollapsed={setCollapsed} onRefresh={handleRefresh} />

          {/* Dynamic Page Router */}
          <main key={refreshKey} className="flex-1 pt-20 pb-12 px-6 max-w-7xl w-full mx-auto">
            <Routes>
              <Route path="/" element={<ExecutiveOverview />} />
              <Route path="/inventory" element={<InventoryCommandCenter />} />
              <Route path="/atp" element={<ATPExplorer />} />
              <Route path="/anomalies" element={<AnomalyCenter />} />
              <Route path="/orders" element={<OrdersAllocation />} />
              <Route path="/transfers" element={<TransfersView />} />
              <Route path="/simulator" element={<WhatIfSimulator />} />
              <Route path="/replenishment" element={<ReplenishmentView />} />
              <Route path="/generator" element={<DataGeneratorConsole />} />
              <Route path="/audit" element={<AuditAndValidation />} />
            </Routes>
          </main>
        </div>
      </div>
    </BrowserRouter>
  );
};
