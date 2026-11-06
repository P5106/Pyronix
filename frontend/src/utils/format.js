export const number = value => new Intl.NumberFormat('en-US', { maximumFractionDigits: 1 }).format(Number(value || 0));
export const shortNumber = value => new Intl.NumberFormat('en-US', { notation: 'compact', maximumFractionDigits: 1 }).format(Number(value || 0));
export const dateLabel = value => value ? new Date(`${value}T00:00:00`).toLocaleDateString('en-US', { day: '2-digit', month: 'short', year: 'numeric' }) : '—';
