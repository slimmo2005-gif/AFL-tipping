/**
 * Browser Quattro check for current round (after admin ladder save).
 * Uses Squiggle API; merges result via GitHub push from workflow when possible.
 */
const QUATTRO_IDS = [5, 10, 3, 7];
const SQUIGGLE = 'https://api.squiggle.com.au/';

export async function checkQuattroRound(season, roundNum) {
  const url = `${SQUIGGLE}?q=games;year=${season};format=json`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Squiggle HTTP ${res.status}`);
  const games = (await res.json()).games || [];
  const roundGames = games.filter((g) => g.round === roundNum && g.complete === 100);

  const rows = [];
  for (const tid of QUATTRO_IDS) {
    const tg = roundGames.filter((g) => g.hteamid === tid || g.ateamid === tid);
    if (tg.length !== 1) return { isQuattro: false, reason: 'Not all four teams played exactly once' };
    const g = tg[0];
    const won =
      (g.hteamid === tid && g.winnerteamid === tid) || (g.ateamid === tid && g.winnerteamid === tid);
    if (!won) return { isQuattro: false, reason: 'At least one team did not win' };
    rows.push(g);
  }
  return { isQuattro: true, matches: rows };
}
