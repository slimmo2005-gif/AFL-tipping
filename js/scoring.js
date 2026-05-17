/** @param {Array<[number, string]>} predictions */
export function calculateScore(predictions, ladder) {
  const ladderMap = Object.fromEntries(ladder.map((e) => [e.team, e.position]));
  let total = 0;
  const details = [];

  for (const [predPos, team] of [...predictions].sort((a, b) => a[0] - b[0])) {
    const actualPos = ladderMap[team];
    let points = 0;
    let reason = '';

    if (actualPos == null || actualPos > 10) {
      points = 0;
      reason = actualPos ? `Outside top 10 (actual #${actualPos})` : 'Unknown team';
    } else if (predPos === actualPos) {
      points = predPos === 1 ? 5 : 2;
      reason = predPos === 1 ? '🏆 #1 spot!' : `✓ Exact – #${predPos}`;
    } else {
      points = 1;
      reason = `In top 10 (actual #${actualPos})`;
    }

    total += points;
    details.push({ position: predPos, team, actual: actualPos ?? null, points, reason });
  }

  return { total, details };
}
