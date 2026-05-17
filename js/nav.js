import { assetUrl } from './config.js';

const PAGES = [
  { id: 'index', href: 'index.html', icon: 'bi-house', label: 'Home' },
  { id: 'setup', href: 'setup.html', icon: 'bi-pencil-square', label: 'Predictions' },
  { id: 'leaderboard', href: 'leaderboard.html', icon: 'bi-bar-chart-fill', label: 'Leaderboard' },
  { id: 'compare', href: 'compare.html', icon: 'bi-grid-3x3-gap-fill', label: 'Compare' },
];

export function initNav(activePage) {
  const ul = document.getElementById('mainNav');
  if (!ul) return;
  ul.innerHTML = PAGES.map(
    (p) => `<li class="nav-item">
      <a class="nav-link ${p.id === activePage ? 'active' : ''}" href="${assetUrl(p.href)}">
        <i class="bi ${p.icon} me-1"></i>${p.label}
      </a>
    </li>`,
  ).join('');
}

export function renderAlerts(containerId, messages) {
  const el = document.getElementById(containerId);
  if (!el) return;
  if (!messages.length) {
    el.innerHTML = '';
    return;
  }
  el.innerHTML = messages
    .map((m) => {
      const cls = m.type === 'danger' ? 'danger' : m.type === 'success' ? 'success' : 'info';
      return [
        `<div class="alert alert-${cls} alert-dismissible fade show" role="alert">`,
        m.text,
        '<button type="button" class="btn-close" data-bs-dismiss="alert"></button>',
        '</div>',
      ].join('');
    })
    .join('');
}
