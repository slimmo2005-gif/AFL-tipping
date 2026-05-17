import { assetUrl, adminUrl, isAdminMode, publicUrl } from './config.js';

const PUBLIC_PAGES = [
  { id: 'leaderboard', href: publicUrl(), icon: 'bi-bar-chart-fill', label: 'Leaderboard' },
  { id: 'compare', href: assetUrl('compare.html'), icon: 'bi-grid-3x3-gap-fill', label: 'Compare' },
];

const ADMIN_PAGES = [
  { id: 'admin', href: adminUrl(), icon: 'bi-gear-fill', label: 'Admin' },
  { id: 'predictions', href: adminUrl('page=predictions'), icon: 'bi-pencil-square', label: 'Predictions' },
  { id: 'leaderboard', href: publicUrl(), icon: 'bi-bar-chart-fill', label: 'View leaderboard' },
  { id: 'compare', href: assetUrl('compare.html'), icon: 'bi-grid-3x3-gap-fill', label: 'Compare' },
];

export function initNav(activePage) {
  const ul = document.getElementById('mainNav');
  if (!ul) return;
  const pages = isAdminMode() ? ADMIN_PAGES : PUBLIC_PAGES;
  ul.innerHTML = pages
    .map(
      (p) => `<li class="nav-item">
      <a class="nav-link ${p.id === activePage ? 'active' : ''}" href="${p.href}">
        <i class="bi ${p.icon} me-1"></i>${p.label}
      </a>
    </li>`,
    )
    .join('');
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
