import React from 'react';
import { TrendingUp, TrendingDown, Activity, Target, AlertTriangle, Zap } from 'lucide-react';
import Sparkline from './Sparkline';

export default function StatsPanel({ stats }) {
  if (!stats) return null;

  const d = stats.last_24h || {};
  const cats = d.categories || {};
  const total = d.total || 0;
  const bullish = cats.bullish || 0;
  const bearish = cats.bearish || 0;
  const avgConf = d.avg_confidence ? Math.round(d.avg_confidence * 100) : 0;

  // Mini chart data for visual flair
  const bullData = [2, 4, 3, 5, bullish || 3, 4, bullish || 5];
  const bearData = [3, 2, 4, 2, bearish || 2, 3, bearish || 1];

  const cards = [
    {
      label: 'Total Signals',
      value: total,
      icon: Activity,
      color: '#ff4444',
      sparkData: [1, 3, 2, 5, 4, total || 3, total || 6],
    },
    {
      label: 'Bullish',
      value: bullish,
      icon: TrendingUp,
      color: '#00ff00',
      sparkData: bullData,
    },
    {
      label: 'Bearish',
      value: bearish,
      icon: TrendingDown,
      color: '#ff4444',
      sparkData: bearData,
    },
    {
      label: 'Avg Confidence',
      value: avgConf ? `${avgConf}%` : 'N/A',
      icon: Target,
      color: '#ffff00',
      sparkData: [60, 70, 65, 75, 80, avgConf || 72, avgConf || 78],
    },
  ];

  return (
    <div className="stats-grid">
      {cards.map((card) => {
        const Icon = card.icon;
        return (
          <div key={card.label} className="stat-card group">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div
                  className="w-7 h-7 rounded-lg flex items-center justify-center"
                  style={{ background: `${card.color}15` }}
                >
                  <Icon className="w-3.5 h-3.5" style={{ color: card.color }} />
                </div>
                <span className="stat-label">{card.label}</span>
              </div>
              <Sparkline data={card.sparkData} width={48} height={20} color={card.color} strokeWidth={1.5} />
            </div>
            <div className="stat-value" style={{ color: card.color }}>{card.value}</div>
          </div>
        );
      })}
    </div>
  );
}