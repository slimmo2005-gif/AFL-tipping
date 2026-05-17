import { adminUrl, isAdminMode, isPredictionsPage, publicUrl } from './config.js';
import { getTeams } from './api.js';
import { initNav, renderAlerts } from './nav.js';

if (!isAdminMode() || !isPredictionsPage()) {
  location.replace(publicUrl());
}
import {
  loadStore,
  saveStore,
  getParticipants,
  getPredictionMap,
  savePredictions,
  downloadStoreJson,
} from './storage.js';
import { hasGitHubToken, pushStoreToGitHub } from './github.js';

initNav('predictions');

const store = await loadStore();
const participants = getParticipants(store);
const teams = await getTeams();

if (new URLSearchParams(location.search).get('saved') === '1') {
  renderAlerts('alerts', [{ type: 'success', text: 'Predictions saved successfully!' }]);
}

function buildForm() {
  const tabs = document.getElementById('participantTabs');
  const panes = document.getElementById('tabPanes');
  let tabsHtml = '';
  let panesHtml = '';

  participants.forEach((p, i) => {
    const existing = getPredictionMap(store, p.id);
    const complete = Object.keys(existing).length === 10;
    tabsHtml += `<li class="nav-item" role="presentation">
      <button class="nav-link ${i === 0 ? 'active' : ''} fw-semibold" id="tab-${p.id}"
        data-bs-toggle="tab" data-bs-target="#pane-${p.id}" type="button" role="tab">
        <i class="bi bi-person me-1"></i>${p.name}
        ${complete ? '<i class="bi bi-check-circle-fill text-success ms-1"></i>' : ''}
      </button>
    </li>`;

    let rows = '';
    for (let pos = 1; pos <= 10; pos++) {
      const opts = ['<option value="">— Select team —</option>']
        .concat(
          teams.map(
            (t) =>
              `<option value="${t}" ${existing[pos] === t ? 'selected' : ''}>${t}</option>`,
          ),
        )
        .join('');
      rows += `<tr>
        <td class="text-center fw-bold ${pos === 1 ? 'table-warning' : ''}">${pos === 1 ? '🥇' : pos}</td>
        <td><select class="form-select form-select-sm team-select" name="p${p.id}_pos${pos}"
          data-participant="${p.id}" required>${opts}</select></td>
      </tr>`;
    }

    const next = participants[i + 1];
    const nextBtn = next
      ? `<div class="d-flex justify-content-end">
        <button type="button" class="btn btn-afl-outline btn-sm next-tab" data-next="tab-${next.id}">
          Next: ${next.name} <i class="bi bi-arrow-right ms-1"></i>
        </button>
      </div>`
      : '';

    panesHtml += `<div class="tab-pane fade ${i === 0 ? 'show active' : ''}" id="pane-${p.id}" role="tabpanel">
      <h5 class="mt-3 mb-3 fw-bold">${p.name}'s Top 10 Predictions</h5>
      <div class="table-responsive">
        <table class="table table-bordered align-middle" style="max-width:480px">
          <thead><tr><th style="width:60px">Position</th><th>Team</th></tr></thead>
          <tbody>${rows}</tbody>
        </table>
      </div>
      ${nextBtn.replaceAll('<div', '<div').replaceAll('</div>', '</div>')}
    </div>`;
  });

  tabs.innerHTML = tabsHtml;
  panes.innerHTML = panesHtml;

  document.querySelectorAll('.next-tab').forEach((btn) => {
    btn.addEventListener('click', () => {
      bootstrap.Tab.getOrCreateInstance(document.getElementById(btn.dataset.next)).show();
    });
  });

  document.querySelectorAll('.team-select').forEach((sel) => {
    sel.addEventListener('change', () => {
      const pid = sel.dataset.participant;
      const selects = document.querySelectorAll(`.team-select[data-participant="${pid}"]`);
      const counts = {};
      selects.forEach((s) => {
        if (s.value) counts[s.value] = (counts[s.value] || 0) + 1;
      });
      selects.forEach((s) => {
        s.classList.remove('is-invalid');
        if (s.value && counts[s.value] > 1) s.classList.add('is-invalid');
      });
    });
  });
}

buildForm();

document.getElementById('predForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const errors = [];

  for (const p of participants) {
    const picks = [];
    for (let pos = 1; pos <= 10; pos++) {
      const team = document.querySelector(`[name="p${p.id}_pos${pos}"]`).value.trim();
      if (!team) errors.push(`${p.name}: position ${pos} is empty.`);
      else picks.push([pos, team]);
    }
    const teamsPicked = picks.map((x) => x[1]);
    if (new Set(teamsPicked).size !== teamsPicked.length) {
      errors.push(`${p.name}: duplicate team selected.`);
    }
    if (!errors.length) savePredictions(store, p.id, picks);
  }

  if (errors.length) {
    renderAlerts('alerts', errors.map((text) => ({ type: 'danger', text })));
    return;
  }

  saveStore(store);

  const btn = e.submitter;
  const defaultHtml = btn?.innerHTML;
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Saving…';
  }

  try {
    if (hasGitHubToken()) {
      await pushStoreToGitHub(store, 'Update predictions');
    }
    location.href = adminUrl('page=predictions&saved=1');
  } catch (err) {
    renderAlerts('alerts', [
      {
        type: 'danger',
        text: `${err.message} Predictions are saved in this browser — add a token on Admin to sync.`,
      },
    ]);
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = defaultHtml;
    }
  }
});

document.getElementById('exportBtn')?.addEventListener('click', () => downloadStoreJson(store));
