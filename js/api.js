import { AFL_COMP_SEASON_ID, AFL_TEAMS_FALLBACK } from './config.js';

const AFL_LADDER_URL = `https://aflapi.afl.com.au/afl/v2/compseasons/${AFL_COMP_SEASON_ID}/ladders`;
const FETCH_TIMEOUT_MS = 25000;

function parseLadder(data) {
  const entries = data?.ladders?.[0]?.entries;
  if (!Array.isArray(entries) || entries.length === 0) {
    throw new Error('no ladder entries in response');
  }
  return entries
    .map((e) => ({ position: e.position, team: e.team.name }))
    .sort((a, b) => a.position - b.position);
}

// The AFL API reports the authoritative current round number.
function currentRoundFromData(data) {
  return data?.round?.roundNumber ?? data?.compSeason?.currentRoundNumber ?? null;
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
  return fetchJson(AFL_LADDER_URL);
}

// Returns the AFL JSON verbatim with permissive CORS headers.
async function fetchViaCorsSh() {
  const proxyUrl = `https://proxy.cors.sh/${AFL_LADDER_URL}`;
  let lastErr;
  for (let attempt = 0; attempt < 2; attempt += 1) {
    try {
      return await fetchJson(proxyUrl);
    } catch (err) {
      lastErr = err;
      if (attempt === 0) await new Promise((r) => setTimeout(r, 800));
    }
  }
  throw lastErr;
}

// AllOrigins "raw" passes the body through unchanged (more reliable than /get).
async function fetchViaAllOriginsRaw() {
  return fetchJson(`https://api.allorigins.win/raw?url=${encodeURIComponent(AFL_LADDER_URL)}`);
}

// AllOrigins "get" wraps the body in JSON; used as a secondary fallback.
async function fetchViaAllOrigins() {
  const proxyUrl = `https://api.allorigins.win/get?url=${encodeURIComponent(AFL_LADDER_URL)}`;
  const wrapper = await fetchJson(proxyUrl);
  if (wrapper.status?.http_code && wrapper.status.http_code !== 200) {
    throw new Error(`origin returned ${wrapper.status.http_code}`);
  }
  if (!wrapper.contents) throw new Error('empty proxy response');
  return JSON.parse(wrapper.contents);
}

async function fetchViaCodetabs() {
  return fetchJson(`https://api.codetabs.com/v1/proxy/?quest=${encodeURIComponent(AFL_LADDER_URL)}`);
}

/** Fetch raw AFL data: CORS proxies for GitHub Pages, then direct (local dev). */
async function fetchAflData() {
  const onGitHubPages = /github\.io$/i.test(location.hostname);
  const attempts = onGitHubPages
    ? [
        ['cors.sh proxy', fetchViaCorsSh],
        ['AllOrigins (raw)', fetchViaAllOriginsRaw],
        ['AllOrigins (get)', fetchViaAllOrigins],
        ['Codetabs proxy', fetchViaCodetabs],
      ]
    : [
        ['AFL API', fetchDirect],
        ['cors.sh proxy', fetchViaCorsSh],
        ['AllOrigins (raw)', fetchViaAllOriginsRaw],
        ['AllOrigins (get)', fetchViaAllOrigins],
        ['Codetabs proxy', fetchViaCodetabs],
      ];

  const errors = [];
  for (const [name, fn] of attempts) {
    try {
      const data = await fn();
      parseLadder(data); // validate before accepting this source
      return data;
    } catch (err) {
      const msg = err.name === 'AbortError' ? 'timed out' : err.message;
      errors.push(`${name}: ${msg}`);
    }
  }
  throw new Error(
    `${errors.join(' · ')}. Try again or use Fetch — it now runs via GitHub Actions when your token has Actions permission.`,
  );
}

export async function fetchAflLadder() {
  return parseLadder(await fetchAflData());
}

/** Ladder plus the AFL's authoritative current round number. */
export async function fetchAflLadderAndRound() {
  const data = await fetchAflData();
  return { ladder: parseLadder(data), currentRound: currentRoundFromData(data) };
}

/** Best-effort current round number (null if it can't be fetched). */
export async function fetchCurrentRound() {
  try {
    return currentRoundFromData(await fetchAflData());
  } catch {
    return null;
  }
}

export async function getTeams() {
  try {
    const ladder = await fetchAflLadder();
    return ladder.map((t) => t.team).sort();
  } catch {
    return [...AFL_TEAMS_FALLBACK];
  }
}
