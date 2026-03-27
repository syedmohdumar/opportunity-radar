import React from 'react';
import { TrendingUp, TrendingDown, Minus, Clock, Zap, Shield, ChevronRight } from 'lucide-react';

const categoryConfig = {
  bullish: { color: '#00C853', icon: TrendingUp, label: 'Bullish' },
  bearish: { color: '#EB5B3C', icon: TrendingDown, label: 'Bearish' },
  neutral: { color: '#F59E0B', icon: Minus, label: 'Neutral' },
};

export default function SignalCard({ signal, onAnalyze }) {
  const cat = categoryConfig[signal.signal_category] || categoryConfig.neutral;
  const CatIcon = cat.icon;
  const confidencePct = Math.round(signal.confidence_score * 100);
  const confColor = confidencePct >= 85 ? '#00C853' : confidencePct >= 70 ? '#0088EA' : '#F59E0B';
  const actionSuggestion = signal.raw_data?.action_suggestion || '';
  const timeHorizon = signal.raw_data?.time_horizon || '';
  const timeAgo = signal.created_at ? getTimeAgo(new Date(signal.created_at)) : '';

  return (
    <div
      className={`signal-card ${signal.signal_category}`}
      onClick={() => onAnalyze?.(signal.symbol)}
    >
      {/* Top row: category + time */}
      <div className="flex items-center justify-between mb-2.5">
        <div className="flex items-center gap-2">
          <span
            className="badge"
            style={{ background: `${cat.color}15`, color: cat.color }}
          >
            <CatIcon className="w-3 h-3" />
            {cat.label}
          </span>
          <span className="text-[11px] text-[#A0A7B4] font-medium">{signal.signal_type?.replace(/_/g, ' ')}</span>
        </div>
        <span className="flex items-center gap-1 text-[11px] text-[#A0A7B4]">
          <Clock className="w-3 h-3" />
          {timeAgo}
        </span>
      </div>

      {/* Symbol + Title */}
      <div className="flex items-start gap-3 mb-2">
        <div className="shrink-0 w-9 h-9 rounded-lg bg-[#F0F2F5] border border-[#ECEDF1] flex items-center justify-center">
          <span className="text-[10px] font-bold text-[#44475B] leading-none">
            {(signal.symbol || '??').slice(0, 3)}
          </span>
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold text-[#0088EA]">{signal.symbol}</span>
            {signal.company_name && signal.company_name !== signal.symbol && (
              <span className="text-[11px] text-[#7F8FA4] truncate">{signal.company_name}</span>
            )}
          </div>
          <h3 className="text-[13px] font-semibold text-[#44475B] leading-snug mt-0.5 line-clamp-2">
            {signal.title}
          </h3>
        </div>
      </div>

      {/* Summary */}
      <p className="text-xs text-[#7F8FA4] leading-relaxed mb-3 line-clamp-2">
        {signal.summary}
      </p>

      {/* AI Analysis expandable */}
      {signal.ai_analysis && (
        <details className="mb-3 group/details">
          <summary className="text-[11px] text-[#0088EA]/80 cursor-pointer hover:text-[#0088EA] font-medium">
            View AI Analysis
          </summary>
          <p className="text-[11px] text-[#7F8FA4] mt-1.5 leading-relaxed pl-3 border-l-2 border-[#ECEDF1]">
            {signal.ai_analysis}
          </p>
        </details>
      )}

      {/* Bottom bar: confidence + impact + symbol */}
      <div className="flex items-center justify-between pt-2.5 border-t border-[#ECEDF1]">
        <div className="flex items-center gap-4">
          {/* Confidence */}
          <div className="flex items-center gap-1.5">
            <Zap className="w-3 h-3" style={{ color: confColor }} />
            <div className="w-16">
              <div className="confidence-bar">
                <div className="confidence-fill" style={{ width: `${confidencePct}%`, background: confColor }} />
              </div>
            </div>
            <span className="text-[11px] font-mono font-bold" style={{ color: confColor }}>
              {confidencePct}%
            </span>
          </div>

          {/* Impact */}
          {signal.potential_impact && (
            <span className={`badge badge-${signal.potential_impact === 'high' ? 'red' : signal.potential_impact === 'medium' ? 'blue' : 'yellow'}`}>
              <Shield className="w-2.5 h-2.5" />
              {signal.potential_impact}
            </span>
          )}
        </div>

        {signal.is_actionable && (
          <span className="badge badge-green">
            Actionable
          </span>
        )}
      </div>

      {/* Action suggestion */}
      {actionSuggestion && (
        <div className="mt-2.5 px-3 py-2 bg-[#0088EA]/5 border border-[#0088EA]/10 rounded-lg">
          <span className="text-[11px] text-[#7F8FA4]">
            <span className="font-semibold text-[#0088EA]">Action: </span>
            {actionSuggestion}
            {timeHorizon && (
              <span className="text-[#A0A7B4] ml-1">· {timeHorizon.replace('_', ' ')}</span>
            )}
          </span>
        </div>
      )}
    </div>
  );
}

function getTimeAgo(date) {
  const now = new Date();
  const diffMs = now - date;
  const diffMin = Math.floor(diffMs / 60000);
  if (diffMin < 1) return 'just now';
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHr = Math.floor(diffMin / 60);
  if (diffHr < 24) return `${diffHr}h ago`;
  const diffDays = Math.floor(diffHr / 24);
  return `${diffDays}d ago`;
}