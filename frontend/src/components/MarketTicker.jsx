import React, { useState, useEffect } from 'react';
import Sparkline from './Sparkline';

// Generate fake intraday sparkline data based on prev_close and current price
function generateSparkData(prevClose, current, points = 20) {
  const data = [prevClose];
  const diff = current - prevClose;
  for (let i = 1; i < points - 1; i++) {
    const progress = i / (points - 1);
    const noise = (Math.random() - 0.5) * Math.abs(diff) * 0.4;
    data.push(prevClose + diff * progress + noise);
  }
  data.push(current);
  return data;
}

export default function MarketTicker() {
  const [indices, setIndices] = useState([]);
  const [isLive, setIsLive] = useState(false);

  useEffect(() => {
    fetchIndices();
    const interval = setInterval(fetchIndices, 120000); // refresh every 2 min
    return () => clearInterval(interval);
  }, []);

  const fetchIndices = async () => {
    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL || '/api'}/market/indices`);
      const data = await res.json();
      setIndices(data.indices || []);
      setIsLive(data.live || false);
    } catch (e) {
      console.error('Failed to fetch indices:', e);
    }
  };

  if (indices.length === 0) return null;

  return (
    <div className="market-ticker">
      <div className="market-ticker-inner">
        {indices.map((idx, i) => {
          const isUp = idx.change >= 0;
          const color = isUp ? '#00C853' : '#EB5B3C';
          const sparkData = generateSparkData(
            idx.prev_close || idx.last - idx.change_pts,
            idx.last
          );

          return (
            <div key={i} className="ticker-item">
              <div className="ticker-label">{idx.symbol}</div>
              <div className="ticker-row">
                <span className="ticker-price">
                  {idx.last >= 1000
                    ? idx.last.toLocaleString('en-IN', { maximumFractionDigits: 2 })
                    : idx.last.toFixed(2)}
                </span>
                <Sparkline data={sparkData} width={48} height={18} color={color} strokeWidth={1.2} />
                <span className={`ticker-change ${isUp ? 'up' : 'down'}`}>
                  {isUp ? '+' : ''}{typeof idx.change === 'number' ? idx.change.toFixed(2) : idx.change}%
                </span>
              </div>
            </div>
          );
        })}
        {isLive && (
          <div className="ticker-item" style={{ minWidth: 'auto' }}>
            <div className="flex items-center gap-1.5">
              <div className="w-1.5 h-1.5 bg-emerald-500 rounded-full pulse-dot" />
              <span className="text-[10px] text-emerald-500 font-medium">LIVE</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
