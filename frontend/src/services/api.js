const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000';

function queryString(params = {}) {
  const clean = Object.fromEntries(Object.entries(params).filter(([, value]) => value !== '' && value !== null && value !== undefined));
  return new URLSearchParams(clean).toString();
}

export async function apiGet(path, params = {}) {
  const response = await fetch(`${API_BASE}${path}?${queryString(params)}`);
  if (!response.ok) throw new Error(`API ${response.status}: ${await response.text()}`);
  return response.json();
}

export async function uploadModis(file) {
  const body = new FormData(); body.append('file', file);
  const response = await fetch(`${API_BASE}/api/upload/modis`, { method: 'POST', body });
  const result = await response.json();
  if (!response.ok) throw new Error(result.detail || 'MODIS upload failed');
  return result;
}

export { API_BASE };
