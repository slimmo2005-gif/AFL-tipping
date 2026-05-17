import { isAdminMode, isPredictionsPage } from './config.js';

const VIEWS = ['viewLeaderboard', 'viewAdmin', 'viewPredictions'];

function showView(id) {
  for (const viewId of VIEWS) {
    const el = document.getElementById(viewId);
    if (el) el.hidden = viewId !== id;
  }
  document.title =
    id === 'viewAdmin'
      ? 'Admin – AFL Tipping 2026'
      : id === 'viewPredictions'
        ? 'Predictions – AFL Tipping 2026'
        : 'Leaderboard – AFL Tipping 2026';
}

if (!isAdminMode()) {
  showView('viewLeaderboard');
  await import('./leaderboard-page.js');
} else if (isPredictionsPage()) {
  showView('viewPredictions');
  await import('./setup-page.js');
} else {
  showView('viewAdmin');
  await import('./admin.js');
}
