import { assetUrl } from './config.js';
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

initNav('index');

const store = await loadStore();
const participants = getParticipants(store);
const rounds = store.rounds;

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
    return `<div class="d-flex align-items-center mb-3">
      <div class="flex-grow-1"><strong>${p.name}</strong></div>${badge}</div>`;
  })
  .join('');

const roundsSection = document.getElementById('roundsSection');
if (rounds.length) {
  const last = rounds[rounds.length - 1];
  document.getElementById('roundNumber').value = last.round_number + 1;
  const links = rounds
    .map(
      (r) =>
        `<a href="${assetUrl(`leaderboard.html?round=${r.round_number}`)}" class="btn btn-sm btn-afl-outline round-btn">Rd ${r.round_number}</a>`,
    )
    .join('');
  roundsSection.innerHTML = `<div class="card">
    <div class="card-header"><i class="bi bi-calendar3 me-2"></i>Rounds Recorded</div>
    <div class="card-body">
      <div class="d-flex flex-wrap gap-2">${links}</div>
      <p class="text-muted small mt-3 mb-0">Last updated: ${last.fetched_at}</p>
    </div>
  </div>`;
}

document.getElementById('ladderForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const roundNumber = parseInt(document.getElementById('roundNumber').value, 10);
  if (!roundNumber || roundNumber < 1) {
    renderAlerts('alerts', [{ type: 'danger', text: 'Please enter a valid round number.' }]);
    return;
  }

  const btn = e.submitter;
  const defaultHtml = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Fetching…';

  try {
    const ladder = await fetchAflLadder();
    saveRound(store, roundNumber, ladder);
    saveStore(store);
    renderAlerts('alerts', [
      {
        type: 'success',
        text: `Round ${roundNumber} ladder saved (${ladder.length} teams). <a href="${assetUrl(`leaderboard.html?round=${roundNumber}`)}">View leaderboard</a>`,
      },
    ]);
    setTimeout(() => location.reload(), 800);
  } catch (err) {
    renderAlerts('alerts', [
      {
        type: 'danger',
        text: `Failed to fetch ladder: ${err.message}. Try again, or run the “Update AFL ladder” GitHub Action.`,
      },
    ]);
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
