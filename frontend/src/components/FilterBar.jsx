import React, { useState } from 'react';
import { SlidersHorizontal } from 'lucide-react';

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
      <div className="flex items-center gap-2 mr-2">
        <SlidersHorizontal className="w-3.5 h-3.5 text-[#7F8FA4]" />
        <span className="text-[11px] font-semibold text-[#7F8FA4] uppercase tracking-wider">Filters</span>
      </div>

      {Object.entries(FILTERS).map(([key, options]) => (
        <select
          key={key}
          value={filters[key]}
          onChange={(e) => handleChange(key, e.target.value)}
          className="filter-select"
        >
          {options.map((opt) => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
      ))}

      <div className="flex items-center gap-2 ml-auto">
        <label className="text-[11px] text-[#7F8FA4] font-medium">Confidence</label>
        <input
          type="range"
          min="0"
          max="100"
          value={filters.min_confidence * 100}
          onChange={(e) => handleChange('min_confidence', Number(e.target.value) / 100)}
          className="w-20 accent-[#0088EA] h-1"
        />
        <span className="text-[11px] text-[#7F8FA4] font-mono w-7 text-right">
          {Math.round(filters.min_confidence * 100)}%
        </span>
      </div>
    </div>
  );
}