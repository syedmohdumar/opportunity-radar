import React, { useState } from 'react';
import { Search, Loader2, TrendingUp, TrendingDown, Target, Shield, BarChart3, ArrowRight } from 'lucide-react';
import { getDeepAnalysis } from '../utils/api';

export default function DeepAnalysis() {
  const [symbol, setSymbol] = useState('');
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleAnalyze = async (sym) => {
    const target = sym || symbol;
    if (!target.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const result = await getDeepAnalysis(target.trim().toUpperCase());
      if (result.error) {
        setError(result.error);
        setAnalysis(null);
      } else {
        setAnalysis(result);
        setError(null);
      }
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="section-header">
        <div>
          <h2 className="section-title">Deep Analysis</h2>
          <p className="section-subtitle">AI-powered cross-event analysis for any stock</p>
        </div>
      </div>

      {/* Search */}
      <div className="analysis-card mb-4">
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#A0A7B4]" />
            <input
              type="text"
              value={symbol}
              onChange={(e) => setSymbol(e.target.value.toUpperCase())}
              onKeyDown={(e) => e.key === 'Enter' && handleAnalyze()}
              placeholder="Enter stock symbol (e.g., RELIANCE, RKFORGE)"
              className="input pl-10"
            />
          </div>
          <button
            onClick={() => handleAnalyze()}
            disabled={loading || !symbol.trim()}
            className="btn-primary"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <ArrowRight className="w-4 h-4" />}
            Analyze
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-500/5 border border-red-500/20 rounded-lg text-sm text-[#EB5B3C]">
          {error}
        </div>
      )}

      {analysis?.analysis && (
        <div className="space-y-3">
          {/* Thesis */}
          {analysis.analysis.thesis && (
            <div className="analysis-card">
              <div className="flex items-center gap-2 mb-3">
                <BarChart3 className="w-4 h-4 text-[#ff4444]" />
                <h4 className="text-sm font-bold text-white">Investment Thesis</h4>
                <span className="text-xs text-[#ff4444] font-semibold ml-1">{analysis.symbol}</span>
              </div>
              <p className="text-[13px] text-white leading-relaxed">{analysis.analysis.thesis}</p>
            </div>
          )}

          {/* Bull vs Bear */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {analysis.analysis.bull_case && (
              <div className="analysis-card" style={{ borderLeft: '3px solid #00C853' }}>
                <div className="flex items-center gap-2 mb-2">
                  <TrendingUp className="w-3.5 h-3.5 text-[#00C853]" />
                  <h4 className="text-xs font-bold text-[#00C853] uppercase tracking-wider">Bull Case</h4>
                </div>
                <p className="text-xs text-[#7F8FA4] leading-relaxed">{analysis.analysis.bull_case}</p>
              </div>
            )}
            {analysis.analysis.bear_case && (
              <div className="analysis-card" style={{ borderLeft: '3px solid #EB5B3C' }}>
                <div className="flex items-center gap-2 mb-2">
                  <TrendingDown className="w-3.5 h-3.5 text-[#EB5B3C]" />
                  <h4 className="text-xs font-bold text-[#EB5B3C] uppercase tracking-wider">Bear Case</h4>
                </div>
                <p className="text-xs text-[#7F8FA4] leading-relaxed">{analysis.analysis.bear_case}</p>
              </div>
            )}
          </div>

          {/* Action */}
          {analysis.analysis.action && (
            <div className="analysis-card" style={{ borderLeft: '3px solid #7C3AED' }}>
              <div className="flex items-center gap-2 mb-2">
                <Target className="w-3.5 h-3.5 text-[#7C3AED]" />
                <h4 className="text-xs font-bold text-[#7C3AED] uppercase tracking-wider">Recommended Action</h4>
              </div>
              <p className="text-sm text-[#44475B] font-medium">{analysis.analysis.action}</p>
            </div>
          )}

          {/* Risk Reward + Confidence */}
          <div className="flex items-center justify-between px-1">
            {analysis.analysis.risk_reward && (
              <div className="flex items-center gap-2">
                <Shield className="w-3.5 h-3.5 text-[#A0A7B4]" />
                <span className="text-xs text-[#A0A7B4]">
                  Risk/Reward: <span className="text-[#44475B] font-medium">{analysis.analysis.risk_reward}</span>
                </span>
              </div>
            )}
            {analysis.analysis.confidence && (
              <span className="text-xs text-[#888888]">
                AI Confidence: <span className="text-[#ff4444] font-bold">{Math.round(analysis.analysis.confidence * 100)}%</span>
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}