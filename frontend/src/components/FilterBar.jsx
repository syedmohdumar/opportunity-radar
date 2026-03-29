import React, { useState } from 'react';
import { SlidersHorizontal, TrendingUp, Zap, Target, Gauge } from 'lucide-react';

const FILTERS = {
  category: [
    { value: '', label: 'All Categories' },
    { value: 'bullish', label: 'Bullish' },
    { value: 'bearish', label: 'Bearish' },
    { value: 'neutral', label: 'Neutral' },
  ],
  signal_type: [
    { value: '', label: 'All Types' },
    { value: 'insider_trade', label: 'Insider Trades' },
    { value: 'bulk_deal', label: 'Bulk Deals' },
    { value: 'block_deal', label: 'Block Deals' },
    { value: 'quarterly_result', label: 'Quarterly Results' },
    { value: 'filing_merger', label: 'Mergers' },
    { value: 'filing_bonus', label: 'Bonus' },
    { value: 'filing_buyback', label: 'Buybacks' },
    { value: 'regulatory_change', label: 'Regulatory' },
    { value: 'multi_event', label: 'Multi-Event' },
  ],
  impact: [
    { value: '', label: 'All Impact' },
    { value: 'high', label: 'High' },
    { value: 'medium', label: 'Medium' },
    { value: 'low', label: 'Low' },
  ],
};

export default function FilterBar({ onFilter }) {
  const [filters, setFilters] = useState({ category: '', signal_type: '', impact: '', min_confidence: 0 });

  const handleChange = (key, value) => {
    const newFilters = { ...filters, [key]: value };
    setFilters(newFilters);
    const cleaned = Object.fromEntries(Object.entries(newFilters).filter(([_, v]) => v !== '' && v !== 0));
    onFilter(cleaned);
  };

  return (
    <div className="filter-bar">
      <div className="flex items-center gap-2">
        <SlidersHorizontal className="w-4 h-4" style={{ color: 'var(--text-primary)' }} />
        <span className="text-[12px] font-semibold uppercase tracking-wider" style={{ color: 'var(--text-primary)' }}>Filters</span>
      </div>

      <div className="flex items-center gap-1.5">
        <TrendingUp className="w-3.5 h-3.5" style={{ color: 'var(--text-primary)' }} />
        <select
          value={filters.category}
          onChange={(e) => handleChange('category', e.target.value)}
          className="filter-select"
        >
          {FILTERS.category.map((opt) => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
      </div>

      <div className="flex items-center gap-1.5">
        <Zap className="w-3.5 h-3.5" style={{ color: 'var(--text-primary)' }} />
        <select
          value={filters.signal_type}
          onChange={(e) => handleChange('signal_type', e.target.value)}
          className="filter-select"
        >
          {FILTERS.signal_type.map((opt) => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
      </div>

      <div className="flex items-center gap-1.5">
        <Target className="w-3.5 h-3.5" style={{ color: 'var(--text-primary)' }} />
        <select
          value={filters.impact}
          onChange={(e) => handleChange('impact', e.target.value)}
          className="filter-select"
        >
          {FILTERS.impact.map((opt) => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
      </div>

      <div className="flex items-center gap-2 ml-auto">
        <Gauge className="w-4 h-4" style={{ color: 'var(--text-primary)' }} />
        <label className="text-[12px] font-medium" style={{ color: 'var(--text-primary)' }}>Confidence</label>
        <input
          type="range"
          min="0"
          max="100"
          value={filters.min_confidence * 100}
          onChange={(e) => handleChange('min_confidence', Number(e.target.value) / 100)}
          className="w-20 h-1 confidence-slider"
        />
        <span className="text-[12px] font-mono w-8 text-right" style={{ color: 'var(--text-primary)' }}>
          {Math.round(filters.min_confidence * 100)}%
        </span>
      </div>
    </div>
  );
}