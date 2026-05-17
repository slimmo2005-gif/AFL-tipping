import { AFL_COMP_SEASON_ID, AFL_TEAMS_FALLBACK } from './config.js';

function parseLadder(data) {
  const entries = data.ladders[0].entries;
  return entries
    .map((e) => ({ position: e.position, team: e.team.name }))
    .sort((a, b) => a.position - b.position);
}

async function fetchJson(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

/** Try AFL API directly, then via CORS proxy (needed on GitHub Pages). */
export async function fetchAflLadder() {
  const apiUrl = `https://aflapi.afl.com.au/afl/v2/compseasons/${AFL_COMP_SEASON_ID}/ladders`;

  try {
    return parseLadder(await fetchJson(apiUrl));
  } catch {
    const proxyUrl = `https://api.allorigins.win/raw?url=${encodeURIComponent(apiUrl)}`;
    return parseLadder(await fetchJson(proxyUrl));
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
