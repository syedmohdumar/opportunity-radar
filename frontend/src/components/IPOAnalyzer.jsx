import React, { useState, useEffect } from 'react';
import {
  Search, Loader2, TrendingUp, TrendingDown, AlertTriangle,
  CheckCircle, XCircle, ChevronDown, ChevronUp, Sparkles, ArrowRight, X
} from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_URL || '/api';

async function fetchIPOs(search = '') {
  const params = search ? `?search=${encodeURIComponent(search)}` : '';
  const res = await fetch(`${API_BASE}/ipo/${params}`);
  if (!res.ok) throw new Error(`Server error (${res.status})`);
  return res.json();
}

async function analyzeIPO(ipoId) {
  const res = await fetch(`${API_BASE}/ipo/analyze/${ipoId}`);
  if (!res.ok) throw new Error(`Server error (${res.status})`);
  return res.json();
}

async function searchAnalyzeIPO(query) {
  const res = await fetch(`${API_BASE}/ipo/search-analyze?query=${encodeURIComponent(query)}`);
  if (!res.ok) throw new Error(`Server error (${res.status})`);
  return res.json();
}

const VERDICT_COLORS = {
  Subscribe: '#00C853',
  Neutral: '#F59E0B',
  Avoid: '#EB5B3C',
  'Review Pending': '#A0A7B4',
};

const RISK_COLORS = {
  Low: '#00C853',
  Medium: '#F59E0B',
  High: '#F97316',
  'Very High': '#EB5B3C',
};

function IPOCard({ ipo, onAnalyze }) {
  const [expanded, setExpanded] = useState(false);
  const hasFlags = ipo.red_flag_count > 0;
  const isSME = ipo.category === 'sme';

  return (
    <div className="signal-card">
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h4 className="text-sm font-bold text-[#44475B] truncate">{ipo.company_name}</h4>
            {isSME && <span className="badge badge-yellow">SME</span>}
            {hasFlags && (
              <span className="badge badge-red">
                <AlertTriangle className="w-2.5 h-2.5" />
                {ipo.red_flag_count} flag{ipo.red_flag_count > 1 ? 's' : ''}
              </span>
            )}
          </div>
          <p className="text-[11px] text-[#A0A7B4]">{ipo.symbol} · {ipo.source}</p>
        </div>
        <button
          onClick={() => onAnalyze(ipo.id)}
          className="btn-ghost flex items-center gap-1.5 shrink-0 ml-3"
        >
          <Sparkles className="w-3 h-3 text-[#7C3AED]" />
          Analyze
        </button>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[
          { label: 'Price Band', value: ipo.price_band || 'N/A' },
          { label: 'Issue Size', value: ipo.issue_size || 'N/A' },
          { label: 'Open', value: ipo.open_date || 'TBA' },
          { label: 'Status', value: ipo.status || ipo.listing_date || 'Upcoming' },
        ].map(({ label, value }) => (
          <div key={label}>
            <p className="text-[10px] text-[#A0A7B4] uppercase tracking-wider font-medium">{label}</p>
            <p className="text-xs font-semibold text-[#44475B] mt-0.5">{value}</p>
          </div>
        ))}
      </div>

      {hasFlags && (
        <div className="mt-3 pt-2 border-t border-[#ECEDF1]">
          <button
            onClick={() => setExpanded(!expanded)}
            className="flex items-center gap-1 text-[11px] text-red-400/80 hover:text-red-400 font-medium"
          >
            {expanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
            {expanded ? 'Hide' : 'View'} red flags
          </button>
          {expanded && (
            <div className="mt-2 space-y-1">
              {ipo.red_flags.map((flag, i) => (
                <div key={i} className="flex items-start gap-1.5 text-[11px] text-[#EB5B3C]/80">
                  <AlertTriangle className="w-3 h-3 mt-0.5 shrink-0 text-red-400" />
                  {flag}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function AnalysisModal({ data, onClose }) {
  if (!data) return null;
  const { ipo, analysis } = data;
  if (!ipo || !analysis) return null;
  const verdictColor = VERDICT_COLORS[analysis.verdict] || VERDICT_COLORS['Review Pending'];
  const riskColor = RISK_COLORS[analysis.risk_level] || '#64748B';

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="p-5">
          {/* Header */}
          <div className="flex items-start justify-between mb-4">
            <div>
              <h3 className="text-base font-bold text-[#44475B]">{ipo.company_name}</h3>
              <p className="text-[11px] text-[#7F8FA4] mt-0.5">{ipo.symbol} · {ipo.category?.toUpperCase()}</p>
            </div>
            <div className="flex items-center gap-2">
              <span
                className="badge text-sm font-bold"
                style={{ background: `${verdictColor}15`, color: verdictColor }}
              >
                {analysis.verdict}
              </span>
              <button onClick={onClose} className="p-1 text-[#A0A7B4] hover:text-[#44475B] rounded-lg hover:bg-[#F0F2F5]">
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Metrics */}
          <div className="grid grid-cols-3 gap-2 mb-4">
            <div className="stat-card py-3 px-3">
              <p className="text-[10px] text-[#A0A7B4] uppercase font-medium">Return Potential</p>
              <p className="text-sm font-bold text-[#ff4444] mt-1">{analysis.return_potential}</p>
            </div>
            <div className="stat-card py-3 px-3">
              <p className="text-[10px] text-[#A0A7B4] uppercase font-medium">Risk Level</p>
              <p className="text-sm font-bold mt-1" style={{ color: riskColor }}>{analysis.risk_level}</p>
            </div>
            <div className="stat-card py-3 px-3">
              <p className="text-[10px] text-[#A0A7B4] uppercase font-medium">Valuation</p>
              <p className="text-sm font-bold text-[#44475B] mt-1">
                {analysis.key_metrics?.valuation_assessment || 'N/A'}
              </p>
            </div>
          </div>

          {/* AI Summary */}
          <div className="analysis-card mb-3" style={{ borderLeft: '3px solid #ff4444' }}>
            <div className="flex items-center gap-1.5 mb-2">
              <Sparkles className="w-3.5 h-3.5 text-[#ff4444]" />
              <h4 className="text-[11px] font-bold text-[#ff4444] uppercase tracking-wider">AI Summary</h4>
            </div>
            <p className="text-[13px] text-[#44475B] leading-relaxed">{analysis.ai_summary}</p>
          </div>

          {/* Positives & Negatives */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2 mb-3">
            <div className="analysis-card" style={{ borderLeft: '3px solid #00C853' }}>
              <h4 className="text-[11px] font-bold text-[#00C853] uppercase tracking-wider mb-2 flex items-center gap-1">
                <CheckCircle className="w-3 h-3" /> Positives
              </h4>
              <ul className="space-y-1.5">
                {(analysis.positives || []).map((p, i) => (
                  <li key={i} className="flex items-start gap-1.5 text-[12px] text-[#7F8FA4]">
                    <TrendingUp className="w-3 h-3 mt-0.5 text-[#00C853] shrink-0" />
                    {p}
                  </li>
                ))}
              </ul>
            </div>
            <div className="analysis-card" style={{ borderLeft: '3px solid #EB5B3C' }}>
              <h4 className="text-[11px] font-bold text-[#EB5B3C] uppercase tracking-wider mb-2 flex items-center gap-1">
                <XCircle className="w-3 h-3" /> Negatives
              </h4>
              <ul className="space-y-1.5">
                {(analysis.negatives || []).map((n, i) => (
                  <li key={i} className="flex items-start gap-1.5 text-[12px] text-[#7F8FA4]">
                    <TrendingDown className="w-3 h-3 mt-0.5 text-[#EB5B3C] shrink-0" />
                    {n}
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Red Flags */}
          {ipo.red_flags && ipo.red_flags.length > 0 && (
            <div className="analysis-card mb-3" style={{ borderLeft: '3px solid #EB5B3C' }}>
              <h4 className="text-[11px] font-bold text-[#EB5B3C] uppercase tracking-wider mb-2 flex items-center gap-1">
                <AlertTriangle className="w-3 h-3" /> Detected Red Flags
              </h4>
              <ul className="space-y-1">
                {ipo.red_flags.map((f, i) => (
                  <li key={i} className="text-[12px] text-[#EB5B3C]/70 flex items-start gap-1.5">
                    <span className="text-[#EB5B3C] mt-0.5">•</span> {f}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Extra metrics */}
          {analysis.key_metrics && (
            <div className="grid grid-cols-2 gap-2">
              {analysis.key_metrics.sector_outlook && (
                <div className="stat-card py-3 px-3">
                  <p className="text-[10px] text-[#A0A7B4] uppercase font-medium">Sector Outlook</p>
                  <p className="text-sm font-semibold text-[#44475B] mt-1">{analysis.key_metrics.sector_outlook}</p>
                </div>
              )}
              {analysis.key_metrics.promoter_track_record && (
                <div className="stat-card py-3 px-3">
                  <p className="text-[10px] text-[#A0A7B4] uppercase font-medium">Promoter Track Record</p>
                  <p className="text-sm font-semibold text-[#44475B] mt-1">{analysis.key_metrics.promoter_track_record}</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function IPOAnalyzer() {
  const [ipos, setIPOs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [searchLoading, setSearchLoading] = useState(false);
  const [analysisData, setAnalysisData] = useState(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => { loadIPOs(); }, []);

  const loadIPOs = async (query = '') => {
    setLoading(true);
    try {
      const data = await fetchIPOs(query);
      setIPOs(data.ipos || []);
    } catch (e) {
      console.error('Failed to load IPOs:', e);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!search.trim()) { loadIPOs(); return; }
    setSearchLoading(true);
    setError(null);
    setAnalysisData(null);
    try {
      const data = await searchAnalyzeIPO(search.trim());
      if (data.error) {
        setError(data.error);
        await loadIPOs(search.trim());
      } else if (data.ipo && data.analysis) {
        setAnalysisData(data);
        await loadIPOs(search.trim());
      } else {
        setError('Unexpected response from server');
      }
    } catch (e) {
      setError(e.message || 'Failed to search');
    } finally {
      setSearchLoading(false);
    }
  };

  const handleAnalyze = async (ipoId) => {
    setAnalysisLoading(true);
    setError(null);
    try {
      const data = await analyzeIPO(ipoId);
      if (data.error) setError(data.error);
      else setAnalysisData(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setAnalysisLoading(false);
    }
  };

  return (
    <div>
      <div className="section-header">
        <div>
          <h2 className="section-title">IPO Analyzer</h2>
          <p className="section-subtitle">AI-powered analysis of upcoming and current IPOs</p>
        </div>
      </div>

      {/* Search */}
      <div className="analysis-card mb-4">
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#A0A7B4]" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="Search IPO by company name..."
              className="input pl-10"
            />
          </div>
          <button onClick={handleSearch} disabled={searchLoading} className="btn-primary">
            {searchLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
            <span className="hidden sm:inline">{searchLoading ? 'Analyzing...' : 'Search & Analyze'}</span>
          </button>
        </div>
        {error && (
          <div className="mt-3 p-3 bg-red-500/5 border border-red-500/20 rounded-lg text-sm text-[#EB5B3C]">
            {error}
          </div>
        )}
      </div>

      {/* Loading overlays */}
      {analysisLoading && (
        <div className="modal-overlay">
          <div className="analysis-card flex flex-col items-center gap-3 p-8">
            <Loader2 className="w-7 h-7 text-[#7C3AED] animate-spin" />
            <p className="text-sm text-[#7F8FA4]">Generating AI analysis...</p>
          </div>
        </div>
      )}

      {analysisData && !analysisLoading && (
        <AnalysisModal data={analysisData} onClose={() => setAnalysisData(null)} />
      )}

      {/* IPO List */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-7 h-7 text-blue-500 animate-spin" />
        </div>
      ) : ipos.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">
            <TrendingUp className="w-8 h-8 text-[#A0A7B4]" />
          </div>
          <p className="text-sm text-[#7F8FA4] mt-3 font-medium">No IPO data yet</p>
          <p className="text-xs text-[#A0A7B4]">Run a scan to fetch the latest IPO data</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
          {ipos.map((ipo) => (
            <IPOCard key={ipo.id} ipo={ipo} onAnalyze={handleAnalyze} />
          ))}
        </div>
      )}
    </div>
  );
}