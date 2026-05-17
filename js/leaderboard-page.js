import { assetUrl } from './config.js';
import { calculateScore } from './scoring.js';
import { initNav } from './nav.js';
import { loadStore, getParticipants, getPredictionsList, parseLadder } from './storage.js';

initNav('leaderboard');

const store = await loadStore();
const participants = getParticipants(store);
const rounds = store.rounds;
const root = document.getElementById('lbRoot');
const medals = ['🥇', '🥈', '🥉'];
const D = 'div';

if (!rounds.length) {
  root.innerHTML = `<${D} class="alert alert-info">
    <i class="bi bi-info-circle me-2"></i>
    No rounds recorded yet. Go to <a href="${assetUrl('index.html')}">Home</a> and fetch the AFL ladder.
  </${D}>`;
} else {
  const params = new URLSearchParams(location.search);
  let selectedRound = parseInt(params.get('round'), 10);
  if (!selectedRound) selectedRound = rounds[rounds.length - 1].round_number;

  const roundRec = rounds.find((r) => r.round_number === selectedRound) || rounds[rounds.length - 1];
  const ladder = parseLadder(roundRec);

  const roundParticipants = participants
    .map((p) => {
      const { total, details } = calculateScore(getPredictionsList(store, p.id), ladder);
      return { name: p.name, total, details };
    })
    .sort((a, b) => b.total - a.total);

  const seasonRows = participants
    .map((p) => {
      const predList = getPredictionsList(store, p.id);
      const scores = rounds.map((rnd) => calculateScore(predList, parseLadder(rnd)).total);
      return { name: p.name, scores, total: scores.at(-1) ?? 0 };
    })
    .sort((a, b) => b.total - a.total);

  const roundLinks = rounds
    .map((r) => {
      const active = r.round_number === roundRec.round_number;
      return `<a href="${assetUrl(`leaderboard.html?round=${r.round_number}`)}"
        class="btn btn-sm round-btn ${active ? 'active' : 'btn-afl-outline'}">Rd ${r.round_number}</a>`;
    })
    .join('');

  const summaryCards = roundParticipants
    .map((pp, i) => {
      const rankCls = i === 0 ? 'rank-1' : i === 1 ? 'rank-2' : i === 2 ? 'rank-3' : '';
      const bg = i === 0 ? 'bg-warning bg-opacity-25' : '';
      return `<${D} class="col-6 col-md-3">
        <${D} class="card text-center border-0 ${bg}">
          <${D} class="card-body py-3">
            <${D} class="fs-4 fw-bold ${rankCls}">${medals[i] || i + 1}</${D}>
            <${D} class="fw-semibold mt-1">${pp.name}</${D}>
            <${D} class="display-6 fw-bold text-primary">${pp.total}</${D}>
            <${D} class="text-muted small">points</${D}>
          </${D}>
        </${D}>
      </${D}>`;
    })
    .join('');

  function detailTable(pp) {
    const rows = pp.details
      .map((d) => {
        const rowCls =
          d.points === 5 ? 'pts-top1' : d.points === 2 ? 'pts-exact' : d.points === 1 ? 'pts-partial' : 'pts-zero';
        const predLabel = d.position === 1 ? '🥇' : d.position;
        const pts =
          d.points > 0 ? `<span class="badge-pts">${d.points}</span>` : '<span class="text-muted">0</span>';
        return `<tr class="${rowCls}">
          <td class="text-center fw-bold">${predLabel}</td>
          <td>${d.team}</td>
          <td class="text-center">${d.actual ? `#${d.actual}` : '—'}</td>
          <td class="text-center">${pts}</td>
        </tr>`;
      })
      .join('');
    return `<${D} class="col-12 col-lg-6">
      <${D} class="card">
        <${D} class="card-header d-flex justify-content-between">
          <span><i class="bi bi-person me-1"></i>${pp.name}</span>
          <span class="badge-pts">${pp.total} pts</span>
        </${D}>
        <${D} class="card-body p-0">
          <table class="table table-sm mb-0">
            <thead><tr>
              <th style="width:50px">Pred.</th><th>Team</th>
              <th style="width:60px">Actual</th><th style="width:70px" class="text-center">Points</th>
            </tr></thead>
            <tbody>${rows}</tbody>
            <tfoot><tr class="table-light">
              <td colspan="3" class="text-end fw-bold">Total</td>
              <td class="text-center"><span class="badge-pts">${pp.total}</span></td>
            </tr></tfoot>
          </table>
        </${D}>
      </${D}>
    </${D}>`;
  }

  const detailCards = roundParticipants.map(detailTable).join('');
  const seasonHeader = rounds.map((r) => `<th class="text-center">Rd ${r.round_number}</th>`).join('');
  const seasonBody = seasonRows
    .map((row, i) => {
      const medal = medals[i] ? `${medals[i]} ` : '';
      const cells = row.scores.map((s) => `<td class="text-center">${s}</td>`).join('');
      return `<tr>
        <td class="fw-semibold">${medal}${row.name}</td>${cells}
        <td class="text-center fw-bold"><span class="badge-pts">${row.total}</span></td>
      </tr>`;
    })
    .join('');

  root.innerHTML = `
    <${D} class="card mb-4"><${D} class="card-body">
      <h6 class="fw-bold mb-3"><i class="bi bi-calendar3 me-2"></i>Select Round</h6>
      <${D} class="d-flex flex-wrap gap-2">${roundLinks}</${D}>
    </${D}></${D}>
    <ul class="nav nav-tabs" role="tablist">
      <li class="nav-item"><button class="nav-link active fw-semibold" data-bs-toggle="tab"
        data-bs-target="#roundDetail" type="button">
        <i class="bi bi-list-ol me-1"></i>Round ${roundRec.round_number} Detail</button></li>
      <li class="nav-item"><button class="nav-link fw-semibold" data-bs-toggle="tab"
        data-bs-target="#seasonHistory" type="button">
        <i class="bi bi-table me-1"></i>Season History</button></li>
    </ul>
    <${D} class="tab-content card card-body border-top-0 rounded-top-0 mb-5">
      <${D} class="tab-pane fade show active" id="roundDetail">
        <${D} class="d-flex align-items-center justify-content-between mt-3 mb-4">
          <h5 class="fw-bold mb-0">Round ${roundRec.round_number} Scores</h5>
          <small class="text-muted">Updated: ${roundRec.fetched_at}</small>
        </${D}>
        <${D} class="row g-3 mb-4">${summaryCards}</${D}>
        <${D} class="row g-4">${detailCards}</${D}>
      </${D}>
      <${D} class="tab-pane fade" id="seasonHistory">
        <h5 class="fw-bold mt-3 mb-4">Points by Round</h5>
        <${D} class="table-responsive">
          <table class="table table-bordered table-hover align-middle">
            <thead><tr><th>Person</th>${seasonHeader}
              <th class="text-center bg-warning bg-opacity-50">Latest Total</th></tr></thead>
            <tbody>${seasonBody}</tbody>
          </table>
        </${D}>
        <p class="text-muted small"><i class="bi bi-info-circle me-1"></i>
          Each round score is total points against the ladder at the end of that round.</p>
      </${D}>
    </${D}>`;
}
