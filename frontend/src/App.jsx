import React, { useState, useEffect, useCallback } from 'react';
import {
  Radar, RefreshCw, Bell, Crosshair, Loader2, TrendingUp,
  Activity, Menu, X, ChevronRight, Film
} from 'lucide-react';
import MarketTicker from './components/MarketTicker';
import SignalCard from './components/SignalCard';
import StatsPanel from './components/StatsPanel';
import AlertsPanel from './components/AlertsPanel';
import FilterBar from './components/FilterBar';
import DeepAnalysis from './components/DeepAnalysis';
import IPOAnalyzer from './components/IPOAnalyzer';
import VideoEngine from './components/VideoEngine';
import { fetchSignals, fetchSignalStats, fetchAlerts, triggerFullScan, markAlertRead } from './utils/api';

const NAV_ITEMS = [
  { id: 'signals', label: 'Signals', icon: Activity },
  { id: 'alerts', label: 'Alerts', icon: Bell },
  { id: 'analysis', label: 'Deep Analysis', icon: Crosshair },
  { id: 'ipo', label: 'IPO Analyzer', icon: TrendingUp },
  { id: 'video', label: 'Video Engine', icon: Film },
];

export default function App() {
  const [tab, setTab] = useState('signals');
  const [signals, setSignals] = useState([]);
  const [stats, setStats] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [filters, setFilters] = useState({});
  const [mobileMenu, setMobileMenu] = useState(false);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [sigRes, statRes, alertRes] = await Promise.all([
        fetchSignals(filters),
        fetchSignalStats(),
        fetchAlerts({ unread_only: false, limit: 30 }),
      ]);
      setSignals(sigRes.signals || []);
      setStats(statRes);
      setAlerts(alertRes.alerts || []);
    } catch (e) {
      console.error('Failed to load data:', e);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 60000);
    return () => clearInterval(interval);
  }, [loadData]);

  const handleScan = async () => {
    setScanning(true);
    try {
      await triggerFullScan();
      await loadData();
    } catch (e) {
      console.error('Scan failed:', e);
    } finally {
      setScanning(false);
    }
  };

  const handleMarkRead = async (alertId) => {
    await markAlertRead(alertId);
    setAlerts((prev) => prev.map((a) => (a.id === alertId ? { ...a, is_read: true } : a)));
  };

  const unreadCount = alerts.filter((a) => !a.is_read).length;

  return (
    <div className="min-h-screen bg-[#F7F8FA]">
      {/* Market Ticker Bar */}
      <MarketTicker />

      {/* Header */}
      <header className="header-bar">
        <div className="header-inner">
          <div className="flex items-center gap-3">
            <div className="logo-icon">
              <Radar className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-[15px] font-bold text-[#44475B] tracking-tight leading-none">
                Opportunity Radar
              </h1>
              <p className="text-[10px] text-[#A0A7B4] mt-0.5">AI Market Intelligence</p>
            </div>
          </div>

          <nav className="hidden md:flex items-center gap-0.5">
            {NAV_ITEMS.map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setTab(id)}
                className={`nav-item ${tab === id ? 'active' : ''}`}
              >
                <Icon className="w-4 h-4" />
                {label}
                {id === 'alerts' && unreadCount > 0 && (
                  <span className="nav-badge">{unreadCount}</span>
                )}
              </button>
            ))}
          </nav>

          <div className="flex items-center gap-2">
            <button onClick={handleScan} disabled={scanning} className="scan-btn">
              {scanning ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <RefreshCw className="w-3.5 h-3.5" />
              )}
              <span className="hidden sm:inline">{scanning ? 'Scanning...' : 'Run Scan'}</span>
            </button>
            <button
              onClick={() => setMobileMenu(!mobileMenu)}
              className="md:hidden p-2 text-[#7F8FA4] hover:text-[#44475B]"
            >
              {mobileMenu ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>

        {mobileMenu && (
          <div className="md:hidden border-t border-[#ECEDF1] px-4 py-2">
            {NAV_ITEMS.map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => { setTab(id); setMobileMenu(false); }}
                className={`flex items-center gap-3 w-full px-3 py-2.5 rounded-lg text-sm ${
                  tab === id ? 'text-[#0088EA] bg-[#0088EA]/10' : 'text-[#7F8FA4]'
                }`}
              >
                <Icon className="w-4 h-4" />
                {label}
                {id === 'alerts' && unreadCount > 0 && (
                  <span className="nav-badge ml-auto">{unreadCount}</span>
                )}
                <ChevronRight className="w-3 h-3 ml-auto text-[#A0A7B4]" />
              </button>
            ))}
          </div>
        )}
      </header>

      {/* Main Content */}
      <main className="max-w-[1280px] mx-auto px-4 sm:px-6 py-5">
        {tab === 'signals' && <StatsPanel stats={stats} />}

        {tab === 'signals' && (
          <section>
            <FilterBar onFilter={setFilters} />
            {loading && signals.length === 0 ? (
              <div className="flex items-center justify-center py-24">
                <Loader2 className="w-7 h-7 text-blue-500 animate-spin" />
              </div>
            ) : signals.length === 0 ? (
              <div className="empty-state">
                <div className="empty-icon">
                  <Radar className="w-8 h-8 text-[#A0A7B4]" />
                </div>
                <p className="text-sm text-[#7F8FA4] mt-3 mb-1 font-medium">No signals detected yet</p>
                <p className="text-xs text-[#A0A7B4] mb-4">Run a scan to start monitoring the market</p>
                <button onClick={handleScan} className="scan-btn">
                  <RefreshCw className="w-3.5 h-3.5" />
                  Run First Scan
                </button>
              </div>
            ) : (
              <div className="signal-grid">
                {signals.map((signal) => (
                  <SignalCard key={signal.id} signal={signal} />
                ))}
              </div>
            )}
          </section>
        )}

        {tab === 'alerts' && <AlertsPanel alerts={alerts} onMarkRead={handleMarkRead} />}
        {tab === 'analysis' && <DeepAnalysis />}
        {tab === 'ipo' && <IPOAnalyzer />}
        {tab === 'video' && <VideoEngine />}
      </main>

      <footer className="border-t border-[#ECEDF1] mt-12">
        <div className="max-w-[1280px] mx-auto px-6 py-5 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-5 h-5 bg-gradient-to-br from-[#0088EA] to-[#005BB5] rounded flex items-center justify-center">
              <Radar className="w-3 h-3 text-white" />
            </div>
            <span className="text-xs text-[#A0A7B4]">Opportunity Radar</span>
          </div>
          <p className="text-[11px] text-[#A0A7B4]">
            Built for ET Markets Hackathon · Data from NSE, BSE, SEBI
          </p>
        </div>
      </footer>
    </div>
  );
}