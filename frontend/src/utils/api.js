const API_BASE = '/api';

export async function fetchSignals(params = {}) {
  const query = new URLSearchParams(params).toString();
  const res = await fetch(`${API_BASE}/signals/?${query}`);
  return res.json();
}

export async function fetchTopSignals(limit = 10) {
  const res = await fetch(`${API_BASE}/signals/top?limit=${limit}`);
  return res.json();
}

export async function fetchSignalStats() {
  const res = await fetch(`${API_BASE}/signals/stats`);
  return res.json();
}

export async function fetchAlerts(params = {}) {
  const query = new URLSearchParams(params).toString();
  const res = await fetch(`${API_BASE}/alerts/?${query}`);
  return res.json();
}

export async function markAlertRead(alertId) {
  const res = await fetch(`${API_BASE}/alerts/${alertId}/read`, { method: 'POST' });
  return res.json();
}

export async function triggerFullScan() {
  const res = await fetch(`${API_BASE}/scan/full`, { method: 'POST' });
  return res.json();
}

export async function triggerAgentScan(agentName) {
  const res = await fetch(`${API_BASE}/scan/agent/${agentName}`, { method: 'POST' });
  return res.json();
}

export async function getDeepAnalysis(symbol) {
  const res = await fetch(`${API_BASE}/scan/deep-analysis/${symbol}`);
  if (!res.ok) throw new Error(`Server error (${res.status})`);
  return res.json();
}

export async function getWatchlist() {
  const res = await fetch(`${API_BASE}/watchlist/`);
  return res.json();
}

export async function addToWatchlist(item) {
  const res = await fetch(`${API_BASE}/watchlist/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(item),
  });
  return res.json();
}

export async function removeFromWatchlist(symbol) {
  const res = await fetch(`${API_BASE}/watchlist/${symbol}`, { method: 'DELETE' });
  return res.json();
}
