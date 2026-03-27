import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Play, Pause, RotateCcw, Film, BarChart3, PieChart, ArrowLeftRight,
  TrendingUp, Loader2, Volume2, VolumeX, ChevronRight, Clock, Zap
} from 'lucide-react';

const API = `${import.meta.env.VITE_API_URL || '/api'}/video`;

const VIDEO_TYPES = [
  { id: 'market-wrap', label: 'Daily Market Wrap', icon: Film, color: '#0088EA', desc: 'AI-narrated summary of today\'s market activity', gradient: ['#0088EA', '#00C4FF', '#0055A4'] },
  { id: 'race-chart', label: 'Stock Race Chart', icon: BarChart3, color: '#00C853', desc: 'Animated ranking of stocks by signal strength', gradient: ['#00C853', '#69F0AE', '#00897B'] },
  { id: 'sector-rotation', label: 'Sector Rotation', icon: PieChart, color: '#7C3AED', desc: 'Heatmap of signal distribution across sectors', gradient: ['#7C3AED', '#B388FF', '#4A148C'] },
  { id: 'fii-dii', label: 'FII / DII Flows', icon: ArrowLeftRight, color: '#F59E0B', desc: 'Institutional money flow visualization', gradient: ['#F59E0B', '#FFD54F', '#E65100'] },
  { id: 'ipo-tracker', label: 'IPO Tracker', icon: TrendingUp, color: '#EB5B3C', desc: 'Visual pipeline of upcoming & active IPOs', gradient: ['#EB5B3C', '#FF8A65', '#BF360C'] },
];

// ═══════════════════════════════════════════════════
// WEB AUDIO — Synthesized ambient background music
// ═══════════════════════════════════════════════════
class BGMusic {
  constructor() {
    this.ctx = null;
    this.nodes = [];
    this.masterGain = null;
    this.playing = false;
  }

  start(color = '#0088EA') {
    if (this.playing) this.stop();
    try {
      this.ctx = new (window.AudioContext || window.webkitAudioContext)();
      this.masterGain = this.ctx.createGain();
      this.masterGain.gain.setValueAtTime(0, this.ctx.currentTime);
      this.masterGain.gain.linearRampToValueAtTime(0.12, this.ctx.currentTime + 1.5);
      this.masterGain.connect(this.ctx.destination);

      const chords = {
        '#0088EA': [220, 277.18, 329.63, 440],
        '#00C853': [261.63, 329.63, 392, 523.25],
        '#7C3AED': [233.08, 293.66, 349.23, 466.16],
        '#F59E0B': [246.94, 311.13, 369.99, 493.88],
        '#EB5B3C': [261.63, 311.13, 392, 523.25],
      };
      const notes = chords[color] || chords['#0088EA'];

      notes.forEach((freq, i) => {
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        osc.type = i % 2 === 0 ? 'sine' : 'triangle';
        osc.frequency.setValueAtTime(freq, this.ctx.currentTime);
        const lfo = this.ctx.createOscillator();
        const lfoGain = this.ctx.createGain();
        lfo.frequency.setValueAtTime(0.5 + i * 0.3, this.ctx.currentTime);
        lfoGain.gain.setValueAtTime(1.5, this.ctx.currentTime);
        lfo.connect(lfoGain);
        lfoGain.connect(osc.frequency);
        lfo.start();
        gain.gain.setValueAtTime(0.03 + (i === 0 ? 0.02 : 0), this.ctx.currentTime);
        osc.connect(gain);
        gain.connect(this.masterGain);
        osc.start();
        this.nodes.push(osc, lfo, gain, lfoGain);
      });

      this._schedulePulse(notes[0] / 2);
      this.playing = true;
    } catch (e) {
      console.warn('Audio not available:', e);
    }
  }

  _schedulePulse(freq) {
    if (!this.ctx || !this.playing) return;
    for (let i = 0; i < 60; i++) {
      const time = this.ctx.currentTime + i * 2;
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(freq, time);
      osc.frequency.exponentialRampToValueAtTime(freq * 0.5, time + 0.3);
      gain.gain.setValueAtTime(0.06, time);
      gain.gain.exponentialRampToValueAtTime(0.001, time + 0.6);
      osc.connect(gain);
      gain.connect(this.masterGain);
      osc.start(time);
      osc.stop(time + 0.6);
    }
  }

  stop() {
    this.playing = false;
    if (this.masterGain) {
      try { this.masterGain.gain.linearRampToValueAtTime(0, this.ctx.currentTime + 0.5); } catch {}
    }
    setTimeout(() => {
      this.nodes.forEach(n => { try { n.stop?.(); n.disconnect?.(); } catch {} });
      this.nodes = [];
      if (this.ctx) { try { this.ctx.close(); } catch {} }
      this.ctx = null;
      this.masterGain = null;
    }, 600);
  }
}

// ═══════════════════════════════════════════════════
// ANIMATED BACKGROUND — Gradient + floating particles
// ═══════════════════════════════════════════════════
function AnimatedBackground({ gradient }) {
  const canvasRef = useRef(null);
  const particlesRef = useRef([]);
  const animRef = useRef(null);

  useEffect(() => {
    const particles = [];
    for (let i = 0; i < 25; i++) {
      particles.push({
        x: Math.random() * 100, y: Math.random() * 100,
        size: 2 + Math.random() * 6, speed: 0.15 + Math.random() * 0.3,
        opacity: 0.08 + Math.random() * 0.15, wobble: Math.random() * 2,
      });
    }
    particlesRef.current = particles;
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    const resize = () => {
      const rect = canvas.parentElement?.getBoundingClientRect();
      canvas.width = rect?.width || 800;
      canvas.height = rect?.height || 450;
    };
    resize();

    let tick = 0;
    const draw = () => {
      const w = canvas.width, h = canvas.height;
      tick++;
      ctx.clearRect(0, 0, w, h);

      // Rotating gradient
      const angle = (tick * 0.3) % 360;
      const rad = (angle * Math.PI) / 180;
      const gx0 = w * 0.5 + Math.cos(rad) * w * 0.5;
      const gy0 = h * 0.5 + Math.sin(rad) * h * 0.5;
      const grad = ctx.createLinearGradient(gx0, gy0, w - gx0, h - gy0);
      grad.addColorStop(0, gradient[0] + '18');
      grad.addColorStop(0.5, gradient[1] + '10');
      grad.addColorStop(1, gradient[2] + '18');
      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, w, h);

      // Floating particles
      particlesRef.current.forEach((p) => {
        p.y -= p.speed;
        p.x += Math.sin(tick * 0.02 + p.wobble) * 0.15;
        if (p.y < -5) { p.y = 105; p.x = Math.random() * 100; }
        const px = (p.x / 100) * w, py = (p.y / 100) * h;
        ctx.beginPath();
        ctx.arc(px, py, p.size, 0, Math.PI * 2);
        ctx.fillStyle = gradient[0] + Math.round(p.opacity * 255).toString(16).padStart(2, '0');
        ctx.fill();
      });

      // Subtle grid
      ctx.strokeStyle = gradient[0] + '08';
      ctx.lineWidth = 0.5;
      for (let x = 0; x < w; x += 40) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, h); ctx.stroke(); }
      for (let y = 0; y < h; y += 40) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke(); }

      animRef.current = requestAnimationFrame(draw);
    };
    draw();
    return () => cancelAnimationFrame(animRef.current);
  }, [gradient]);

  return <canvas ref={canvasRef} className="absolute inset-0 w-full h-full pointer-events-none" style={{ zIndex: 0 }} />;
}

// ═══════════════════════════════════════════════════
// SCENE TRANSITION WRAPPER
// ═══════════════════════════════════════════════════
function SceneTransition({ children, sceneKey }) {
  const [visible, setVisible] = useState(false);
  const [cls, setCls] = useState('');

  useEffect(() => {
    setVisible(false);
    setCls('scene-exit');
    const t = setTimeout(() => { setCls('scene-enter'); setVisible(true); }, 180);
    return () => clearTimeout(t);
  }, [sceneKey]);

  return <div className={`scene-transition ${cls} ${visible ? 'scene-visible' : ''}`}>{children}</div>;
}

// ═══════════════════════════════════════════════════
// PLAYER COMPONENTS
// ═══════════════════════════════════════════════════

function MarketWrapPlayer({ data, frame, playing, gradient }) {
  const scenes = data?.scenes || [];
  let elapsed = 0, currentScene = scenes[0], sceneIndex = 0;
  for (let i = 0; i < scenes.length; i++) {
    if (frame >= elapsed && frame < elapsed + scenes[i].duration) { currentScene = scenes[i]; sceneIndex = i; break; }
    elapsed += scenes[i].duration;
  }
  if (!currentScene) currentScene = scenes[scenes.length - 1] || {};
  const signalData = data?.signal_data || {};
  const totalDuration = scenes.reduce((a, s) => a + (s.duration || 0), 0);
  const progress = totalDuration > 0 ? Math.min((frame / totalDuration) * 100, 100) : 0;

  return (
    <div className="video-canvas">
      <AnimatedBackground gradient={gradient} />
      <div className="absolute top-0 left-0 right-0 h-1 bg-black/5 z-10">
        <div className="h-full transition-all duration-500 video-progress-glow" style={{ width: `${progress}%`, background: gradient[0] }} />
      </div>
      <div className="absolute top-4 left-1/2 -translate-x-1/2 flex gap-1.5 z-10">
        {scenes.map((_, i) => (
          <div key={i} className={`scene-dot ${i === sceneIndex ? 'active' : ''} ${i < sceneIndex ? 'done' : ''}`} style={i === sceneIndex ? { background: gradient[0] } : {}} />
        ))}
      </div>
      <div className="absolute top-4 left-4 z-10">
        <span className="video-scene-badge" style={{ background: gradient[0] }}>{currentScene.type?.replace('_', ' ')}</span>
      </div>

      <SceneTransition sceneKey={sceneIndex}>
        <div className="flex flex-col items-center justify-center h-full px-8 text-center relative z-10">
          <h3 className="text-xl sm:text-2xl font-extrabold text-[#44475B] mb-3 drop-shadow-sm">{currentScene.headline}</h3>
          <p className="text-sm text-[#7F8FA4] max-w-md leading-relaxed">{currentScene.narration}</p>

          {currentScene.type === 'intro' && (
            <div className="mt-4 flex items-center gap-2">
              <div className="w-2 h-2 rounded-full pulse-dot" style={{ background: gradient[0] }} />
              <span className="text-xs font-semibold" style={{ color: gradient[0] }}>LIVE MARKET UPDATE</span>
            </div>
          )}

          {currentScene.type === 'top_movers' && currentScene.stocks && (
            <div className="flex gap-3 mt-5">
              {currentScene.stocks.map((stock, i) => (
                <div key={i} className="stock-card-animated" style={{ animationDelay: `${i * 0.2}s`, borderTop: `3px solid ${gradient[0]}` }}>
                  <div className="text-sm font-bold" style={{ color: gradient[0] }}>{stock.symbol}</div>
                  <div className="text-xs font-semibold text-[#00C853] mt-1">{stock.move}</div>
                  <div className="text-[10px] text-[#A0A7B4] mt-0.5 max-w-[120px] truncate">{stock.reason}</div>
                </div>
              ))}
            </div>
          )}

          {currentScene.type === 'signals_summary' && (
            <div className="flex items-center gap-10 mt-6">
              <div className="signal-counter-animated">
                <div className="text-4xl font-black text-[#00C853] tabular-nums">{currentScene.bullish_count || signalData.bullish || 0}</div>
                <div className="text-[10px] text-[#A0A7B4] uppercase font-bold mt-1 tracking-wider">Bullish</div>
              </div>
              <div className="w-0.5 h-12 rounded-full" style={{ background: `${gradient[0]}30` }} />
              <div className="signal-counter-animated" style={{ animationDelay: '0.3s' }}>
                <div className="text-4xl font-black text-[#EB5B3C] tabular-nums">{currentScene.bearish_count || signalData.bearish || 0}</div>
                <div className="text-[10px] text-[#A0A7B4] uppercase font-bold mt-1 tracking-wider">Bearish</div>
              </div>
            </div>
          )}
        </div>
      </SceneTransition>

      <div className="video-watermark"><Zap className="w-3 h-3" style={{ color: gradient[0] }} /><span>Opportunity Radar</span></div>
    </div>
  );
}

function RaceChartPlayer({ data, frame, gradient }) {
  const frames = data?.frames || [];
  const frameIdx = Math.min(frame, frames.length - 1);
  const currentFrame = frames[frameIdx] || [];
  const maxVal = Math.max(...currentFrame.map(d => d.value || 0), 1);

  return (
    <div className="video-canvas">
      <AnimatedBackground gradient={gradient} />
      <div className="absolute top-4 left-4 z-10">
        <span className="video-scene-badge" style={{ background: gradient[0] }}>Race Chart</span>
        <span className="text-[10px] text-[#A0A7B4] ml-2">Frame {frameIdx + 1}/{frames.length}</span>
      </div>
      <div className="flex flex-col justify-center h-full px-6 py-12 gap-2 relative z-10">
        {currentFrame.map((item, i) => {
          const width = maxVal > 0 ? (item.value / maxVal) * 100 : 0;
          const color = item.category === 'bullish' ? '#00C853' : item.category === 'bearish' ? '#EB5B3C' : '#F59E0B';
          return (
            <div key={item.symbol} className="race-bar-row">
              <span className="text-xs font-bold text-[#44475B] w-24 text-right shrink-0 tabular-nums">
                <span className="race-rank">{i + 1}</span>{item.symbol}
              </span>
              <div className="flex-1 h-8 bg-white/60 rounded-lg overflow-hidden backdrop-blur-sm border border-white/40">
                <div className="h-full rounded-lg transition-all duration-700 ease-out flex items-center justify-end pr-3 race-bar-fill"
                  style={{ width: `${Math.max(width, 8)}%`, background: `linear-gradient(90deg, ${color}CC, ${color})` }}>
                  <span className="text-[11px] font-bold text-white drop-shadow-sm">{item.value}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
      <div className="video-watermark"><Zap className="w-3 h-3" style={{ color: gradient[0] }} /><span>Opportunity Radar</span></div>
    </div>
  );
}

function SectorRotationPlayer({ data, frame, gradient }) {
  const sectors = data?.sectors || [];
  const maxTotal = Math.max(...sectors.map(s => s.total), 1);

  return (
    <div className="video-canvas">
      <AnimatedBackground gradient={gradient} />
      <div className="absolute top-4 left-4 z-10">
        <span className="video-scene-badge" style={{ background: gradient[0] }}>Sector Map</span>
      </div>
      <div className="flex flex-col justify-center h-full px-6 py-10 relative z-10">
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          {sectors.map((sec, i) => {
            const sentColor = sec.sentiment === 'bullish' ? '#00C853' : sec.sentiment === 'bearish' ? '#EB5B3C' : '#F59E0B';
            const show = frame >= i * 0.5;
            return (
              <div key={sec.name} className={`sector-tile-enhanced ${show ? 'animate-scale-in' : 'opacity-0'}`} style={{ animationDelay: `${i * 0.12}s` }}>
                <div className="sector-tile-glow" style={{ background: sentColor }} />
                <div className="relative z-10">
                  <div className="text-xs font-bold text-[#44475B]">{sec.name}</div>
                  <div className="flex items-center gap-2 mt-1.5">
                    <span className="text-xl font-black" style={{ color: sentColor }}>{sec.total}</span>
                    <span className="text-[10px] text-[#A0A7B4]">signals</span>
                  </div>
                  <div className="flex gap-3 mt-1.5">
                    <span className="text-[10px] text-[#00C853] font-bold">▲ {sec.bullish}</span>
                    <span className="text-[10px] text-[#EB5B3C] font-bold">▼ {sec.bearish}</span>
                  </div>
                  <div className="mt-1.5 h-1.5 bg-black/5 rounded-full overflow-hidden">
                    <div className="h-full rounded-full transition-all duration-700" style={{ width: `${sec.avg_confidence}%`, background: sentColor }} />
                  </div>
                  <div className="text-[9px] text-[#A0A7B4] mt-1">{sec.avg_confidence}% confidence</div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
      <div className="video-watermark"><Zap className="w-3 h-3" style={{ color: gradient[0] }} /><span>Opportunity Radar</span></div>
    </div>
  );
}

function FIIDIIPlayer({ data, frame, gradient }) {
  const ai = data?.ai || {};
  const summary = data?.summary || {};
  const flowFrames = data?.flow_frames || [];
  const frameIdx = Math.min(frame, flowFrames.length - 1);
  const currentFlow = flowFrames[frameIdx] || { fii_buy: 0, fii_sell: 0, dii_buy: 0, dii_sell: 0 };
  const maxFlow = Math.max(currentFlow.fii_buy, currentFlow.fii_sell, currentFlow.dii_buy, currentFlow.dii_sell, 1);

  const bars = [
    { label: 'FII Buy', value: currentFlow.fii_buy, color: '#00C853', icon: '🟢' },
    { label: 'FII Sell', value: currentFlow.fii_sell, color: '#EB5B3C', icon: '🔴' },
    { label: 'DII Buy', value: currentFlow.dii_buy, color: '#0088EA', icon: '🔵' },
    { label: 'DII Sell', value: currentFlow.dii_sell, color: '#F59E0B', icon: '🟡' },
  ];

  return (
    <div className="video-canvas">
      <AnimatedBackground gradient={gradient} />
      <div className="absolute top-4 left-4 z-10">
        <span className="video-scene-badge" style={{ background: gradient[0] }}>FII/DII Flows</span>
      </div>
      <div className="flex flex-col justify-center h-full px-6 py-8 gap-4 relative z-10">
        <p className="text-sm text-[#44475B] text-center leading-relaxed max-w-lg mx-auto font-medium">
          {ai.commentary || 'Analyzing institutional flow patterns...'}
        </p>
        <div className="space-y-3">
          {bars.map((bar, i) => (
            <div key={bar.label} className="flow-bar-row animate-slide-up" style={{ animationDelay: `${i * 0.15}s` }}>
              <span className="text-[11px] font-bold text-[#7F8FA4] w-20 text-right flex items-center justify-end gap-1">
                <span className="text-xs">{bar.icon}</span> {bar.label}
              </span>
              <div className="flex-1 h-7 bg-white/60 rounded-lg overflow-hidden backdrop-blur-sm border border-white/30">
                <div className="h-full rounded-lg transition-all duration-700 flex items-center justify-end pr-3"
                  style={{ width: `${Math.max((bar.value / maxFlow) * 100, 5)}%`, background: `linear-gradient(90deg, ${bar.color}AA, ${bar.color})` }}>
                  <span className="text-[10px] font-bold text-white drop-shadow-sm">₹{bar.value}Cr</span>
                </div>
              </div>
            </div>
          ))}
        </div>
        {ai.key_insight && (
          <div className="mx-auto px-5 py-2.5 bg-white/70 backdrop-blur border border-white/50 rounded-xl shadow-sm">
            <p className="text-[11px] font-semibold text-center" style={{ color: gradient[0] }}>💡 {ai.key_insight}</p>
          </div>
        )}
        {summary.stocks?.length > 0 && (
          <div className="flex flex-wrap items-center justify-center gap-1.5">
            {summary.stocks.map((sym, i) => (
              <span key={i} className="px-2.5 py-1 bg-white/70 backdrop-blur text-[10px] font-bold text-[#44475B] rounded-lg border border-white/50 shadow-sm">{sym}</span>
            ))}
          </div>
        )}
      </div>
      <div className="video-watermark"><Zap className="w-3 h-3" style={{ color: gradient[0] }} /><span>Opportunity Radar</span></div>
    </div>
  );
}

function IPOTrackerPlayer({ data, frame, gradient }) {
  const ai = data?.ai || {};
  const ipos = data?.ipos || [];

  return (
    <div className="video-canvas">
      <AnimatedBackground gradient={gradient} />
      <div className="absolute top-4 left-4 z-10">
        <span className="video-scene-badge" style={{ background: gradient[0] }}>IPO Pipeline</span>
      </div>
      <div className="flex flex-col justify-center h-full px-6 py-8 gap-4 relative z-10">
        <p className="text-sm text-[#44475B] text-center leading-relaxed max-w-lg mx-auto font-medium">
          {ai.narration || 'Loading IPO pipeline data...'}
        </p>
        {ai.market_mood && (
          <div className="flex justify-center">
            <span className={`ipo-mood-badge ${ai.market_mood}`}>
              {ai.market_mood === 'hot' ? '🔥' : ai.market_mood === 'warm' ? '☀️' : '❄️'} IPO Market: {ai.market_mood?.toUpperCase()}
            </span>
          </div>
        )}
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5 max-h-[200px] overflow-y-auto">
          {ipos.slice(0, 6).map((ipo, i) => {
            const show = frame >= i * 0.8;
            return (
              <div key={i} className={`ipo-card-animated ${show ? 'animate-slide-up' : 'opacity-0'}`} style={{ animationDelay: `${i * 0.12}s` }}>
                <div className="text-[11px] font-bold text-[#44475B] truncate">{ipo.company}</div>
                <div className="text-[10px] text-[#A0A7B4] mt-0.5">{ipo.price_band}</div>
                <div className="flex items-center gap-1.5 mt-2">
                  <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded-md ${
                    ipo.category === 'sme' ? 'bg-[#F59E0B]/15 text-[#F59E0B]' : 'bg-[#0088EA]/15 text-[#0088EA]'
                  }`}>{ipo.category?.toUpperCase()}</span>
                  {ipo.red_flags > 0 && (
                    <span className="text-[9px] font-bold px-1.5 py-0.5 rounded-md bg-[#EB5B3C]/15 text-[#EB5B3C]">⚠ {ipo.red_flags}</span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
      <div className="video-watermark"><Zap className="w-3 h-3" style={{ color: gradient[0] }} /><span>Opportunity Radar</span></div>
    </div>
  );
}

const PLAYER_MAP = {
  'market-wrap': MarketWrapPlayer,
  'race-chart': RaceChartPlayer,
  'sector-rotation': SectorRotationPlayer,
  'fii-dii': FIIDIIPlayer,
  'ipo-tracker': IPOTrackerPlayer,
};

// ═══════════════════════════════════════════════════
// MAIN COMPONENT
// ═══════════════════════════════════════════════════
export default function VideoEngine() {
  const [activeType, setActiveType] = useState(null);
  const [videoData, setVideoData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [playing, setPlaying] = useState(false);
  const [frame, setFrame] = useState(0);
  const [muted, setMuted] = useState(false);
  const intervalRef = useRef(null);
  const musicRef = useRef(new BGMusic());

  const totalFrames = useCallback(() => {
    if (!videoData) return 30;
    if (videoData.frames) return videoData.frames.length;
    if (videoData.flow_frames) return videoData.flow_frames.length;
    if (videoData.scenes) return videoData.scenes.reduce((a, s) => a + (s.duration || 0), 0);
    return 30;
  }, [videoData]);

  const activeConfig = VIDEO_TYPES.find(v => v.id === activeType);

  useEffect(() => {
    if (playing) {
      intervalRef.current = setInterval(() => {
        setFrame((prev) => {
          if (prev >= totalFrames() - 1) { setPlaying(false); return prev; }
          return prev + 1;
        });
      }, 1000);
    } else {
      clearInterval(intervalRef.current);
    }
    return () => clearInterval(intervalRef.current);
  }, [playing, totalFrames]);

  useEffect(() => {
    if (playing && !muted && activeConfig) {
      musicRef.current.start(activeConfig.color);
    } else {
      musicRef.current.stop();
    }
    return () => musicRef.current.stop();
  }, [playing, muted, activeConfig]);

  const handleGenerate = async (typeId) => {
    setActiveType(typeId);
    setLoading(true);
    setError(null);
    setVideoData(null);
    setFrame(0);
    setPlaying(false);
    musicRef.current.stop();
    try {
      const res = await fetch(`${API}/${typeId}`);
      if (!res.ok) throw new Error(`Server error (${res.status})`);
      setVideoData(await res.json());
    } catch (e) {
      setError(e.message || 'Failed to generate video');
    } finally {
      setLoading(false);
    }
  };

  const handlePlay = () => { if (frame >= totalFrames() - 1) setFrame(0); setPlaying(true); };
  const handleReset = () => { setPlaying(false); setFrame(0); musicRef.current.stop(); };

  const PlayerComponent = activeType ? PLAYER_MAP[activeType] : null;

  return (
    <div>
      <div className="section-header">
        <div>
          <h2 className="section-title">AI Video Engine</h2>
          <p className="section-subtitle">Auto-generate animated market update videos — zero editing required</p>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 mb-5">
        {VIDEO_TYPES.map((vt) => {
          const Icon = vt.icon;
          const isActive = activeType === vt.id;
          return (
            <button key={vt.id} onClick={() => handleGenerate(vt.id)} disabled={loading}
              className={`video-type-card ${isActive ? 'active' : ''}`}
              style={isActive ? { borderColor: vt.color, background: `${vt.color}08` } : {}}>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0" style={{ background: `${vt.color}15` }}>
                  <Icon className="w-5 h-5" style={{ color: vt.color }} />
                </div>
                <div className="text-left">
                  <div className="text-sm font-semibold text-[#44475B]">{vt.label}</div>
                  <div className="text-[11px] text-[#A0A7B4] mt-0.5">{vt.desc}</div>
                </div>
              </div>
              <ChevronRight className="w-4 h-4 text-[#A0A7B4] shrink-0" />
            </button>
          );
        })}
      </div>

      {(loading || videoData || error) && (
        <div className="analysis-card overflow-hidden">
          {activeConfig && (
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <activeConfig.icon className="w-4 h-4" style={{ color: activeConfig.color }} />
                <h3 className="text-sm font-bold text-[#44475B]">{videoData?.title || activeConfig.label}</h3>
              </div>
              {videoData && (
                <div className="flex items-center gap-1.5 text-[10px] text-[#A0A7B4]">
                  <Clock className="w-3 h-3" />{videoData.duration || 30}s
                </div>
              )}
            </div>
          )}

          {loading && (
            <div className="flex flex-col items-center justify-center py-16 gap-3">
              <div className="video-loading-ring" style={{ borderTopColor: activeConfig?.color || '#0088EA' }} />
              <p className="text-sm text-[#7F8FA4] font-medium">Generating video with AI...</p>
              <p className="text-[11px] text-[#A0A7B4]">Analyzing market data & creating scenes</p>
            </div>
          )}

          {error && <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-sm text-[#EB5B3C]">{error}</div>}

          {videoData && !loading && PlayerComponent && (
            <>
              <div className="video-player-wrapper">
                <PlayerComponent data={videoData} frame={frame} playing={playing} gradient={activeConfig.gradient} />
              </div>

              <div className="flex items-center justify-between mt-4 pt-3 border-t border-[#ECEDF1]">
                <div className="flex items-center gap-2">
                  <button onClick={() => playing ? setPlaying(false) : handlePlay()}
                    className="video-control-btn" style={{ background: activeConfig?.color || '#0088EA' }}>
                    {playing ? <Pause className="w-4 h-4 text-white" /> : <Play className="w-4 h-4 text-white" />}
                  </button>
                  <button onClick={handleReset} className="video-control-btn-ghost"><RotateCcw className="w-3.5 h-3.5" /></button>
                  <button onClick={() => setMuted(!muted)} className="video-control-btn-ghost" title={muted ? 'Unmute' : 'Mute'}>
                    {muted ? <VolumeX className="w-3.5 h-3.5" /> : <Volume2 className="w-3.5 h-3.5" />}
                  </button>
                </div>
                <div className="flex-1 mx-4">
                  <div className="h-2 bg-[#F0F2F5] rounded-full overflow-hidden">
                    <div className="h-full rounded-full transition-all duration-300 video-progress-glow"
                      style={{ width: `${(frame / Math.max(totalFrames() - 1, 1)) * 100}%`,
                        background: `linear-gradient(90deg, ${activeConfig?.gradient?.[0]}, ${activeConfig?.gradient?.[1]})` }} />
                  </div>
                </div>
                <span className="text-[11px] font-mono text-[#A0A7B4] tabular-nums">{frame + 1} / {totalFrames()}</span>
              </div>
            </>
          )}
        </div>
      )}

      {!activeType && !loading && (
        <div className="empty-state">
          <div className="empty-icon"><Film className="w-8 h-8 text-[#A0A7B4]" /></div>
          <p className="text-sm text-[#7F8FA4] mt-3 font-medium">Select a video type above</p>
          <p className="text-xs text-[#A0A7B4]">AI will generate animated market visualizations from your data</p>
        </div>
      )}
    </div>
  );
}
