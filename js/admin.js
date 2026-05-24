import { publicUrl, assetUrl } from './config.js';
import { fetchAflLadder } from './api.js';
import { initNav, renderAlerts } from './nav.js';
import {
  loadStore,
  saveStore,
  saveRound,
  getParticipants,
  predictionCount,
  downloadStoreJson,
} from './storage.js';
import { hasGitHubToken, pushStoreToGitHub, initGitHubSettings } from './github.js';
import { checkQuattroRound } from './quattro-check.js';

initNav('admin');
initGitHubSettings();

const store = await loadStore();
const participants = getParticipants(store);
const rounds = store.rounds;
const D = 'x';

const statusEl = document.getElementById('predStatus');
statusEl.innerHTML = participants
  .map((p) => {
    const count = predictionCount(store, p.id);
    let badge;
    if (count === 10) {
      badge = '<span class="badge bg-success"><i class="bi bi-check-circle me-1"></i>10 teams set</span>';
    } else if (count > 0) {
      badge = `<span class="badge bg-warning text-dark"><i class="bi bi-exclamation-circle me-1"></i>${count}/10</span>`;
    } else {
      badge = '<span class="badge bg-danger"><i class="bi bi-x-circle me-1"></i>Not set</span>';
    }
    return `<${D} class="d-flex align-items-center mb-3">
      <${D} class="flex-grow-1"><strong>${p.name}</strong></${D}>${badge}</${D}>`;
  })
  .join('')
  .replaceAll(`<${D}`, '<div')
  .replaceAll(`</${D}>`, '</div>');

const roundsSection = document.getElementById('roundsSection');
if (rounds.length) {
  const last = rounds[rounds.length - 1];
  document.getElementById('roundNumber').value = last.round_number + 1;
  const links = rounds
    .map(
      (r) =>
        `<a href="${publicUrl(`?round=${r.round_number}`)}" class="btn btn-sm btn-afl-outline round-btn">Rd ${r.round_number}</a>`,
    )
    .join('');
  roundsSection.innerHTML = `<${D} class="card">
    <${D} class="card-header"><i class="bi bi-calendar3 me-2"></i>Rounds Recorded</${D}>
    <${D} class="card-body">
      <${D} class="d-flex flex-wrap gap-2">${links}</${D}>
      <p class="text-muted small mt-3 mb-0">Last updated: ${last.fetched_at}</p>
    </${D}>
  </${D}>`
    .replaceAll(`<${D}`, '<div')
    .replaceAll(`</${D}>`, '</div>');
}

document.getElementById('ladderForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const roundNumber = parseInt(document.getElementById('roundNumber').value, 10);
  if (!roundNumber || roundNumber < 1) {
    renderAlerts('alerts', [{ type: 'danger', text: 'Please enter a valid round number.' }]);
    return;
  }

  if (!hasGitHubToken()) {
    renderAlerts('alerts', [
      {
        type: 'warning',
        text: 'Add a GitHub token below first — that lets the app save round data straight to the repo for everyone.',
      },
    ]);
    document.getElementById('githubSyncCard')?.scrollIntoView({ behavior: 'smooth' });
    return;
  }

  const btn = e.submitter;
  const defaultHtml = btn.innerHTML;
  btn.disabled = true;

  try {
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Fetching ladder…';
    const ladder = await fetchAflLadder();
    saveRound(store, roundNumber, ladder);
    saveStore(store);

    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Saving to GitHub…';
    await pushStoreToGitHub(store, `Update ladder for round ${roundNumber}`);

    let qfMsg = '';
    try {
      const season = new Date().getFullYear();
      const qf = await checkQuattroRound(season, roundNumber);
      qfMsg = qf.isQuattro
        ? ` <strong>Quattro Formaggi!</strong> All four won — run the GitHub Action or <code>scripts/check_quattro_round.py</code> to add to history. <a href="${assetUrl('quattro-formaggi.html')}">View page</a>`
        : ` Quattro Formaggi: not this round (${qf.reason}).`;
    } catch {
      qfMsg = ' Quattro check skipped (Squiggle unavailable in browser). Use GitHub Action to update history.';
    }

    renderAlerts('alerts', [
      {
        type: 'success',
        text: `Round ${roundNumber} saved to GitHub (${ladder.length} teams).${qfMsg} <a href="${publicUrl(`?round=${roundNumber}`)}">View leaderboard</a>`,
      },
    ]);
    setTimeout(() => location.reload(), 1500);
  } catch (err) {
    renderAlerts('alerts', [{ type: 'danger', text: err.message }]);
    btn.disabled = false;
    btn.innerHTML = defaultHtml;
  }
});

document.getElementById('exportBtn')?.addEventListener('click', () => downloadStoreJson(store));
document.getElementById('resetBtn')?.addEventListener('click', () => {
  if (confirm('Clear local changes and reload shared data from the site?')) {
    localStorage.removeItem('afl_tipping_store_v1');
    location.reload();
  }
});
