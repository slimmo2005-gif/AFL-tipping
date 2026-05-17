import { assetUrl } from './config.js';
import { initNav } from './nav.js';
import { loadStore, getParticipants, getPredictionMap } from './storage.js';

initNav('compare');

const store = await loadStore();
const participants = getParticipants(store);
const root = document.getElementById('compareRoot');

const allPreds = {};
for (const p of participants) {
  allPreds[p.id] = getPredictionMap(store, p.id);
}
const pickedTeams = Object.fromEntries(
  participants.map((p) => [p.id, new Set(Object.values(allPreds[p.id]))]),
);
const hasPredictions = participants.some((p) => Object.keys(allPreds[p.id]).length === 10);

if (!hasPredictions) {
  root.innerHTML = `<div class="alert alert-warning">
    <i class="bi bi-exclamation-triangle me-2"></i>
    No predictions entered yet.
    <a href="${assetUrl('setup.html')}" class="alert-link">Enter predictions</a> first.
  </div>`;
} else {
  const matrix = [];
  for (let pos = 1; pos <= 10; pos++) {
    const teamsAtPos = {};
    for (const p of participants) {
      teamsAtPos[p.id] = allPreds[p.id][pos] || '';
    }
    const posTeamCounts = {};
    for (const team of Object.values(teamsAtPos)) {
      if (team) posTeamCounts[team] = (posTeamCounts[team] || 0) + 1;
    }

    const cells = participants.map((p) => {
      const team = teamsAtPos[p.id];
      if (!team) return { name: p.name, team: '', highlight: 'empty', shared_count: 0 };

      const sameSpotCount = posTeamCounts[team] || 1;
      if (sameSpotCount >= 2) {
        return { name: p.name, team, highlight: 'same-spot', shared_count: sameSpotCount };
      }
      const pickedByOthers = participants.filter(
        (o) => o.id !== p.id && pickedTeams[o.id].has(team),
      ).length;
      if (pickedByOthers > 0) {
        return { name: p.name, team, highlight: 'diff-spot', shared_count: pickedByOthers + 1 };
      }
      return { name: p.name, team, highlight: '', shared_count: 1 };
    });
    matrix.push({ position: pos, cells });
  }

  const headerCols = participants.map((p) => `<th>${p.name}</th>`).join('');
  const bodyRows = matrix
    .map((row) => {
      const posLabel = row.position === 1 ? '<span title="Position 1">🥇</span>' : row.position;
      const cells = row.cells
        .map((cell) => {
          const cls =
            cell.highlight === 'same-spot'
              ? 'cell-same'
              : cell.highlight === 'diff-spot'
                ? 'cell-diff'
                : cell.highlight === 'empty'
                  ? 'cell-empty'
                  : '';
          if (!cell.team) {
            return `<td class="pick-cell ${cls}"><span class="text-muted fst-italic small">not set</span></td>`;
          }
          const badge =
            cell.shared_count > 1
              ? `<span class="shared-badge ${cell.highlight === 'same-spot' ? 'badge-same' : 'badge-diff'}">×${cell.shared_count}</span>`
              : '';
          return `<td class="pick-cell ${cls}">
            <span class="team-name">${cell.team}</span>${badge}
          </td>`;
        })
        .join('');
      return `<tr>
        <td class="pos-cell fw-bold ${row.position === 1 ? 'pos-one' : ''}">${posLabel}</td>
        ${cells}
      </tr>`;
    })
    .join('');

  const agreements = [];
  const shared = [];
  for (const row of matrix) {
    const seen = new Set();
    for (const cell of row.cells) {
      if (cell.team && cell.highlight === 'same-spot' && !seen.has(cell.team)) {
        seen.add(cell.team);
        agreements.push({ pos: row.position, team: cell.team, count: cell.shared_count });
      }
      if (cell.team && cell.highlight === 'diff-spot' && !shared.some((s) => s.team === cell.team)) {
        shared.push({ team: cell.team, count: cell.shared_count });
      }
    }
  }

  const agreeList = agreements.length
    ? agreements
        .map(
          (a) => `<li class="mb-2">
        <span class="legend-swatch swatch-same me-2"></span>
        <strong>${a.team}</strong> at position ${a.pos}
        <span class="badge bg-warning text-dark ms-1">${a.count} people</span>
      </li>`,
        )
        .join('')
    : '<p class="text-muted mb-0">No exact agreements yet.</p>';

  const sharedList = shared.length
    ? shared
        .map(
          (s) => `<li class="mb-2">
        <span class="legend-swatch swatch-diff me-2"></span>
        <strong>${s.team}</strong>
        <span class="badge bg-primary ms-1">${s.count} people, different spots</span>
      </li>`,
        )
        .join('')
    : '<p class="text-muted mb-0">No shared teams at different positions.</p>';

  root.innerHTML = `
    <div class="table-responsive">
      <table class="table table-bordered compare-table text-center align-middle mb-4">
        <thead><tr><th class="pos-col">Position</th>${headerCols}</tr></thead>
        <tbody>${bodyRows}</tbody>
      </table>
    </div>
    <div class="row g-4 mb-5">
      <div class="col-md-6">
        <div class="card">
          <div class="card-header"><i class="bi bi-check2-all me-2"></i>Exact Agreements (same position)</div>
          <div class="card-body"><ul class="list-unstyled mb-0">${agreeList}</ul></div>
        </div>
      </div>
      <div class="col-md-6">
        <div class="card">
          <div class="card-header"><i class="bi bi-arrow-left-right me-2"></i>Shared Teams (different positions)</div>
          <div class="card-body"><ul class="list-unstyled mb-0">${sharedList}</ul></div>
        </div>
      </div>
    </div>`;

  root.innerHTML = root.innerHTML.replaceAll('<div', '<div').replaceAll('</div>', '</div>');
}
