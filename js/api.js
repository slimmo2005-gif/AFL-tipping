import { AFL_COMP_SEASON_ID, AFL_TEAMS_FALLBACK } from './config.js';

const AFL_LADDER_URL = `https://aflapi.afl.com.au/afl/v2/compseasons/${AFL_COMP_SEASON_ID}/ladders`;
const FETCH_TIMEOUT_MS = 25000;

function parseLadder(data) {
  const entries = data.ladders[0].entries;
  return entries
    .map((e) => ({ position: e.position, team: e.team.name }))
    .sort((a, b) => a.position - b.position);
}

async function fetchJson(url, options = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);
  try {
    const res = await fetch(url, { ...options, signal: controller.signal });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  } finally {
    clearTimeout(timer);
  }
}

async function fetchDirect() {
  return parseLadder(await fetchJson(AFL_LADDER_URL));
}

async function fetchViaCodetabs() {
  const proxyUrl = `https://api.codetabs.com/v1/proxy/?quest=${encodeURIComponent(AFL_LADDER_URL)}`;
  return parseLadder(await fetchJson(proxyUrl));
}

async function fetchViaAllOrigins() {
  const proxyUrl = `https://api.allorigins.win/get?url=${encodeURIComponent(AFL_LADDER_URL)}`;
  const wrapper = await fetchJson(proxyUrl);
  if (wrapper.status?.http_code && wrapper.status.http_code !== 200) {
    throw new Error(`origin returned ${wrapper.status.http_code}`);
  }
  if (!wrapper.contents) throw new Error('empty proxy response');
  return parseLadder(JSON.parse(wrapper.contents));
}

/** Fetch ladder: direct (local), then CORS proxies for GitHub Pages. */
export async function fetchAflLadder() {
  const attempts = [
    ['AFL API', fetchDirect],
    ['Codetabs proxy', fetchViaCodetabs],
    ['AllOrigins proxy', fetchViaAllOrigins],
  ];

  const errors = [];
  for (const [name, fn] of attempts) {
    try {
      return await fn();
    } catch (err) {
      const msg = err.name === 'AbortError' ? 'timed out' : err.message;
      errors.push(`${name}: ${msg}`);
    }
  }
  throw new Error(errors.join(' · '));
}

export async function getTeams() {
  try {
    const ladder = await fetchAflLadder();
    return ladder.map((t) => t.team).sort();
  } catch {
    return [...AFL_TEAMS_FALLBACK];
  }
}
