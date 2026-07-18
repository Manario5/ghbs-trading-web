/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './services/auth';
import { ProtectedRoute } from './pages/Layout';
import { Login } from './pages/Login';
import { Dashboard, Account, Portfolio, Performance, History, Settings } from './pages/Pages';
import { Scout } from './pages/Scout';
import { Analyze } from './pages/Analyze';
import { ActionPlan } from './pages/ActionPlan';
import { Journal } from './pages/Journal';
import { AlertCenter } from './pages/AlertCenter';
import { MarketData } from './pages/MarketData';

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          
          <Route element={<ProtectedRoute />}>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/action-plan" element={<ActionPlan />} />
            <Route path="/scout" element={<Scout />} />
            <Route path="/analyze" element={<Analyze />} />
            <Route path="/portfolio" element={<Portfolio />} />
            <Route path="/journal" element={<Journal />} />
            <Route path="/alerts" element={<AlertCenter />} />
            <Route path="/market-data" element={<MarketData />} />
            <Route path="/performance" element={<Performance />} />
            <Route path="/account" element={<Account />} />
            <Route path="/history" element={<History />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
