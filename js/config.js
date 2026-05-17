/** GitHub Pages project path (e.g. /AFL-tipping/) or / for local root. */
export function getBasePath() {
  const parts = location.pathname.split('/').filter(Boolean);
  const idx = parts.findIndex((p) => p.toLowerCase() === 'afl-tipping');
  if (idx >= 0) return '/' + parts.slice(0, idx + 1).join('/') + '/';
  const dir = location.pathname.replace(/\/[^/]*$/, '/');
  return dir || '/';
}

export function assetUrl(path) {
  const base = getBasePath();
  const clean = path.replace(/^\//, '');
  return base + clean;
}

export function isAdminMode() {
  return new URLSearchParams(location.search).has('admin');
}

export function isPredictionsPage() {
  const params = new URLSearchParams(location.search);
  return params.has('admin') && params.get('page') === 'predictions';
}

/** Admin area URLs (index.html?admin…). */
export function adminUrl(extra = '') {
  const q = extra ? (extra.startsWith('&') ? extra : `&${extra}`) : '';
  return `${assetUrl('index.html')}?admin${q}`;
}

/** Public leaderboard URL. */
export function publicUrl(extra = '') {
  const q = extra ? (extra.startsWith('?') ? extra : `?${extra}`) : '';
  return `${assetUrl('index.html')}${q}`;
}

export const AFL_COMP_SEASON_ID = 85;
export const PARTICIPANT_NAMES = ['Matt', 'Brett', 'Tim', 'Johno'];

export const AFL_TEAMS_FALLBACK = [
  'Adelaide Crows', 'Brisbane Lions', 'Carlton', 'Collingwood', 'Essendon',
  'Fremantle', 'Geelong Cats', 'Gold Coast SUNS', 'GWS GIANTS', 'Hawthorn',
  'Melbourne', 'North Melbourne', 'Port Adelaide', 'Richmond', 'St Kilda',
  'Sydney Swans', 'West Coast Eagles', 'Western Bulldogs',
];
