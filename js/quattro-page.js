import { assetUrl } from './config.js';
import { initNav } from './nav.js';

initNav('quattro');

const TEAM_IMG = {
  Essendon: 'essendon',
  Hawthorn: 'hawthorn',
  Carlton: 'carlton',
  Geelong: 'geelong',
};

function formatDate(iso) {
  if (!iso) return '—';
  const d = new Date(iso.replace(' ', 'T'));
  if (Number.isNaN(d.getTime())) return iso.split(' ')[0];
  return d.toLocaleDateString('en-AU', { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' });
}

function formatAttendance(n) {
  if (n == null || n === '') return '—';
  return Number(n).toLocaleString('en-AU');
}

function formatGapDays(days) {
  if (days == null || days === '') return '';
  const n = Number(days);
  if (Number.isNaN(n)) return '';
  if (n === 0) return 'same day as previous';
  if (n === 1) return '1 day since previous';
  const years = Math.floor(n / 365);
  const rem = n % 365;
  if (years >= 1 && rem < 30) return `${years} yr${years > 1 ? 's' : ''} since previous`;
  return `${n.toLocaleString('en-AU')} days since previous`;
}

function formatSinceToday(days) {
  if (days == null || days === '') return '';
  const n = Number(days);
  if (Number.isNaN(n)) return '';
  return `${n.toLocaleString('en-AU')} days since last Quattro (today)`;
}

function scoreLine(m) {
  const ha = m.home ? 'vs' : '@';
  return `${m.team} ${m.team_score}–${m.opponent_score} ${ha} ${m.opponent}`;
}

async function loadData() {
  const url = assetUrl('data/quattro-formaggi.json') + `?t=${Date.now()}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error('Could not load Quattro Formaggi data');
  return res.json();
}

function renderHero(data) {
  const count = data.events.length;
  const seasons = data.meta?.seasons_scanned || [];
  document.getElementById('qfStats').innerHTML = `
    <div class="col-md-4"><div class="card text-center h-100"><div class="card-body">
      <div class="display-6 fw-bold text-primary">${count}</div>
      <div class="text-muted small">Quattro rounds found</div>
    </div></div></div>
    <div class="col-md-4"><div class="card text-center h-100"><div class="card-body">
      <div class="display-6 fw-bold">${seasons.length || '—'}</div>
      <div class="text-muted small">Seasons scanned (${seasons[0] || ''}–${seasons[seasons.length - 1] || ''})</div>
    </div></div></div>
    <div class="col-md-4"><div class="card text-center h-100"><div class="card-body">
      <div class="fs-5 fw-semibold">Matt · Brett · Tim · Johno</div>
      <div class="text-muted small">Essendon · Carlton · Hawthorn · Geelong</div>
    </div></div></div>`;
}

function renderPeople(data) {
  const el = document.getElementById('qfPeople');
  el.innerHTML = data.people
    .map((p) => {
      const slug = TEAM_IMG[p.team] || p.team.toLowerCase();
      return `<div class="qf-team-card">
        <img src="${assetUrl(`images/teams/${slug}.svg`)}" alt="${p.team}" class="qf-team-logo">
        <div class="fw-bold">${p.name}</div>
        <div class="text-muted small">${p.team}</div>
      </div>`;
    })
    .join('');
}

function renderEvents(data) {
  const root = document.getElementById('qfEvents');
  if (!data.events.length) {
    root.innerHTML = `<div class="alert alert-info">No Quattro Formaggi rounds in the scanned seasons yet.</div>`;
    return;
  }

  const reversed = [...data.events].reverse();
  root.innerHTML = reversed
    .map((ev, idx) => {
      const badge = ev.is_final
        ? '<span class="badge bg-warning text-dark ms-2">Finals</span>'
        : '';
      const gapParts = [];
      if (ev.days_since_previous != null) gapParts.push(formatGapDays(ev.days_since_previous));
      if (idx === 0 && ev.days_since_today != null) gapParts.push(formatSinceToday(ev.days_since_today));
      const gapHtml = gapParts.length
        ? `<div class="qf-gap-note small text-white-50 mt-1">${gapParts.join(' · ')}</div>`
        : '';
      const rows = ev.matches
        .map((m) => {
          const slug = TEAM_IMG[m.team] || 'essendon';
          return `<tr>
            <td class="qf-team-cell">
              <img src="${assetUrl(`images/teams/${slug}.svg`)}" alt="" class="qf-table-logo">
              <span class="fw-semibold">${m.team}</span>
            </td>
            <td>${m.opponent}</td>
            <td class="text-center">${m.team_score}–${m.opponent_score}</td>
            <td>${m.venue || '—'}</td>
            <td class="text-end">${formatAttendance(m.attendance)}</td>
            <td class="text-center">${m.ladder_position_before != null ? `#${m.ladder_position_before}` : '—'}</td>
            <td class="text-muted small">${formatDate(m.date)}</td>
          </tr>`;
        })
        .join('');
      return `<div class="card mb-4 qf-event-card">
        <div class="card-header">
          <div class="d-flex justify-content-between align-items-center flex-wrap gap-2">
            <span><strong>${ev.season}</strong> — ${ev.round_label}${badge}</span>
            <span class="badge-pts">All four won</span>
          </div>
          ${gapHtml}
        </div>
        <div class="card-body p-0">
          <div class="table-responsive">
            <table class="table table-sm table-hover mb-0 align-middle qf-match-table">
              <colgroup>
                <col class="qf-col-team">
                <col class="qf-col-opponent">
                <col class="qf-col-score">
                <col class="qf-col-venue">
                <col class="qf-col-att">
                <col class="qf-col-ladder">
                <col class="qf-col-date">
              </colgroup>
              <thead><tr>
                <th>Team</th><th>Opponent</th><th class="text-center">Score</th>
                <th>Venue</th><th class="text-end">Attendance</th>
                <th class="text-center">Ladder (prior)</th><th>Date</th>
              </tr></thead>
              <tbody>${rows}</tbody>
            </table>
          </div>
        </div>
      </div>`;
    })
    .join('');
}

try {
  const data = await loadData();
  renderHero(data);
  renderPeople(data);
  renderEvents(data);
  const note = document.getElementById('qfMetaNote');
  if (note && data.meta?.last_backfill) {
    note.textContent = `Data via ${data.meta.source || 'Squiggle'}. Last updated ${data.meta.last_backfill}. ${data.meta.attendance_note || ''}`;
  }
} catch (err) {
  document.getElementById('qfEvents').innerHTML = `<div class="alert alert-danger">${err.message}</div>`;
}
