"""Generate static HTML pages."""
from pathlib import Path

TAG = "x"


def d(html: str) -> str:
    return html.replace(f"<{TAG}", "<div").replace(f"</{TAG}>", "</div>")


def shell(title: str, script: str, body: str) -> str:
    nav = d(
        f"""<nav class="navbar navbar-expand-lg">
  <{TAG} class="container">
    <a class="navbar-brand" href="index.html"><i class="bi bi-trophy-fill me-2"></i>AFL Tipping 2026</a>
    <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navMenu">
      <span class="navbar-toggler-icon"></span>
    </button>
    <{TAG} class="collapse navbar-collapse" id="navMenu">
      <ul class="navbar-nav ms-auto" id="mainNav"></ul>
    </{TAG}>
  </{TAG}>
</nav>
<{TAG} class="container mt-3" id="alerts"></{TAG}>"""
    )
    foot = d(
        f"""<footer>
  <{TAG} class="container text-center">
    AFL Tipping Leaderboard 2026 &mdash; Data from
    <a href="https://www.afl.com.au/ladder" target="_blank" rel="noopener">AFL.com.au</a>
  </{TAG}>
</footer>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
<script type="module" src="js/{script}"></script>"""
    )
    return d(
        f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" rel="stylesheet">
  <link href="css/styles.css" rel="stylesheet">
</head>
<body>
{nav}
{body}
{foot}
</body>
</html>"""
    )


LEADERBOARD_VIEW = f"""
<{TAG} id="viewLeaderboard">
  <{TAG} class="page-header page-header--branded">
    <{TAG} class="container page-header-inner">
      <{TAG} class="page-header-text">
        <h1><i class="bi bi-bar-chart-fill me-2"></i>Leaderboard</h1>
        <p class="subtitle mb-0">Round-by-round scores &amp; season totals</p>
      </{TAG}>
      <{TAG} class="page-header-brand">
        <img src="images/slim-analytics-logo.png" alt="Slim Analytics" class="slim-analytics-logo">
      </{TAG}>
    </{TAG}>
  </{TAG}>
  <{TAG} class="container" id="lbRoot"></{TAG}>
</{TAG}>"""

ADMIN_VIEW = f"""
<{TAG} id="viewAdmin" hidden>
  <{TAG} class="page-header"><{TAG} class="container">
    <h1><i class="bi bi-gear-fill me-2"></i>Admin</h1>
    <p class="subtitle mb-0">Fetch ladders, sync to GitHub, manage predictions</p>
  </{TAG}></{TAG}>
  <{TAG} class="container">
    <{TAG} class="card mb-4" id="githubSyncCard">
      <{TAG} class="card-header"><i class="bi bi-github me-2"></i>Sync to GitHub (one-time setup)</{TAG}>
      <{TAG} class="card-body">
        <p class="small text-muted mb-2">
          Create a <a href="https://github.com/settings/tokens?type=beta" target="_blank" rel="noopener">fine-grained token</a>
          for repo <strong>AFL-tipping</strong> with <em>Contents: Read and write</em>.
        </p>
        <{TAG} class="row g-2 align-items-end">
          <{TAG} class="col-md-8">
            <label for="githubToken" class="form-label fw-semibold">GitHub token</label>
            <input type="password" class="form-control" id="githubToken" autocomplete="off" placeholder="github_pat_… or ghp_…">
          </{TAG}>
          <{TAG} class="col-md-4 d-flex gap-2">
            <button type="button" class="btn btn-afl flex-grow-1" id="saveGitHubToken">Save token</button>
            <button type="button" class="btn btn-outline-secondary" id="clearGitHubToken" title="Remove token">Clear</button>
          </{TAG}>
        </{TAG}>
        <{TAG} id="githubTokenStatus" class="small mt-2"></{TAG}>
      </{TAG}>
    </{TAG}>
    <{TAG} class="row g-4">
      <{TAG} class="col-md-6">
        <{TAG} class="card h-100">
          <{TAG} class="card-header"><i class="bi bi-person-check me-2"></i>Prediction Status</{TAG}>
          <{TAG} class="card-body">
            <{TAG} id="predStatus"></{TAG}>
            <a href="index.html?admin&amp;page=predictions" class="btn btn-afl mt-2 w-100">
              <i class="bi bi-pencil-square me-2"></i>Enter / Edit Predictions
            </a>
          </{TAG}>
        </{TAG}>
      </{TAG}>
      <{TAG} class="col-md-6">
        <{TAG} class="card h-100">
          <{TAG} class="card-header"><i class="bi bi-arrow-repeat me-2"></i>Update Ladder</{TAG}>
          <{TAG} class="card-body">
            <p class="text-muted small">At the end of each round, fetch the latest AFL ladder.</p>
            <form id="ladderForm">
              <{TAG} class="mb-3">
                <label for="roundNumber" class="form-label fw-semibold">Round Number</label>
                <input type="number" class="form-control" id="roundNumber" min="1" max="27" value="1">
              </{TAG}>
              <button type="submit" class="btn btn-afl w-100">
                <i class="bi bi-cloud-download me-2"></i>Fetch AFL Ladder &amp; Save Round
              </button>
            </form>
            <p class="text-muted small mt-2 mb-3">
              <i class="bi bi-info-circle me-1"></i>From
              <a href="https://www.afl.com.au/ladder" target="_blank" rel="noopener">AFL.com.au</a>
            </p>
            <{TAG} class="d-flex gap-2 flex-wrap">
              <button type="button" class="btn btn-sm btn-afl-outline" id="exportBtn">Download store.json</button>
              <button type="button" class="btn btn-sm btn-outline-secondary" id="resetBtn">Reload from site</button>
            </{TAG}>
          </{TAG}>
        </{TAG}>
      </{TAG}>
      <{TAG} class="col-12" id="roundsSection"></{TAG}>
    </{TAG}>
  </{TAG}>
</{TAG}>"""

PREDICTIONS_VIEW = f"""
<{TAG} id="viewPredictions" hidden>
  <{TAG} class="page-header"><{TAG} class="container">
    <h1><i class="bi bi-pencil-square me-2"></i>Enter Predictions</h1>
    <p class="subtitle mb-0">Each person selects their predicted top 10 teams in order</p>
  </{TAG}></{TAG}>
  <{TAG} class="container">
    <{TAG} class="card mb-4"><{TAG} class="card-body bg-light rounded">
      <h6 class="fw-bold mb-2"><i class="bi bi-info-circle me-2 text-primary"></i>Scoring Rules</h6>
      <{TAG} class="row g-2">
        <{TAG} class="col-auto"><span class="badge-pts me-1">5 pts</span> Correct team at #1</{TAG}>
        <{TAG} class="col-auto"><span class="badge-pts me-1">2 pts</span> Right team, right spot (2–10)</{TAG}>
        <{TAG} class="col-auto"><span class="badge-pts me-1">1 pt</span> Right team, wrong spot</{TAG}>
        <{TAG} class="col-auto"><span class="badge-pts-0 me-1">0 pts</span> Not in actual top 10</{TAG}>
      </{TAG}>
    </{TAG}></{TAG}>
    <form id="predForm">
      <ul class="nav nav-tabs mb-0" id="participantTabs" role="tablist"></ul>
      <{TAG} class="tab-content card card-body border-top-0 rounded-top-0 mb-4" id="tabPanes"></{TAG}>
      <{TAG} class="d-flex gap-3 mb-5 flex-wrap">
        <button type="submit" class="btn btn-afl btn-lg px-5">
          <i class="bi bi-save me-2"></i>Save All Predictions
        </button>
        <a href="index.html?admin" class="btn btn-secondary btn-lg">Cancel</a>
        <button type="button" class="btn btn-afl-outline btn-lg" id="exportBtn">Download store.json</button>
      </{TAG}>
    </form>
  </{TAG}>
</{TAG}>"""

QUATTRO_BODY = f"""
<{TAG} class="page-header page-header--branded">
  <{TAG} class="container page-header-inner">
    <{TAG} class="page-header-text">
      <h1><i class="bi bi-emoji-smile-fill me-2"></i>Quattro Formaggi</h1>
      <p class="subtitle mb-0">When Essendon, Hawthorn, Carlton &amp; Geelong all win the same round</p>
    </{TAG}>
    <{TAG} class="page-header-brand">
      <img src="images/slim-analytics-logo.png" alt="Slim Analytics" class="slim-analytics-logo">
    </{TAG}>
  </{TAG}>
</{TAG}>
<{TAG} class="container mb-5">
  <{TAG} class="row g-4 align-items-center mb-4">
    <{TAG} class="col-md-5 text-center">
      <img src="images/quattro-formaggi.jpg" alt="Quattro formaggi" class="qf-hero-img rounded shadow">
    </{TAG}>
    <{TAG} class="col-md-7">
      <p class="lead mb-2">Matt (Essendon), Brett (Carlton), Tim (Hawthorn) and Johno (Geelong) — when all four clubs <strong>play</strong> and <strong>win</strong> in the same round, it&apos;s a Quattro Formaggi.</p>
      <p class="text-muted small mb-0">Rounds where any of the four don&apos;t play are excluded. History from Squiggle (last twenty seasons); crowd figures from AFL Tables. Ladder position is from the week before each game (rounds 1–3 use the prior season&apos;s final ladder).</p>
    </{TAG}>
  </{TAG}>
  <{TAG} class="row g-3 mb-4" id="qfStats"></{TAG}>
  <{TAG} class="d-flex flex-wrap justify-content-center gap-4 mb-4" id="qfPeople"></{TAG}>
  <h2 class="h4 fw-bold mb-3"><i class="bi bi-clock-history me-2"></i>History</h2>
  <{TAG} id="qfEvents"></{TAG}>
  <p class="text-muted small mt-3" id="qfMetaNote"></p>
</{TAG}>"""

COMPARE_BODY = f"""
<{TAG} class="page-header"><{TAG} class="container">
  <h1><i class="bi bi-grid-3x3-gap-fill me-2"></i>Predictions Comparison</h1>
  <p class="subtitle mb-0">All 4 people's top 10 picks side by side</p>
</{TAG}></{TAG}>
<{TAG} class="container">
  <{TAG} class="card mb-4"><{TAG} class="card-body py-3">
    <h6 class="fw-bold mb-3"><i class="bi bi-palette me-2 text-primary"></i>Colour Key</h6>
    <{TAG} class="d-flex flex-wrap gap-3 align-items-center">
      <{TAG} class="d-flex align-items-center gap-2">
        <span class="legend-swatch swatch-same"></span>
        <span><strong>Gold</strong> — Same team at the same position</span>
      </{TAG}>
      <{TAG} class="d-flex align-items-center gap-2">
        <span class="legend-swatch swatch-diff"></span>
        <span><strong>Blue</strong> — Team picked elsewhere at a different position</span>
      </{TAG}>
      <{TAG} class="d-flex align-items-center gap-2">
        <span class="legend-swatch swatch-unique"></span>
        <span><strong>White</strong> — Unique pick</span>
      </{TAG}>
    </{TAG}>
  </{TAG}></{TAG}>
  <{TAG} id="compareRoot"></{TAG}>
</{TAG}>"""

REDIRECT = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <script>
    const q = location.search || '';
    const path = location.pathname.replace(/[^/]*$/, '');
    const base = path.endsWith('/') ? path : path + '/';
    {redirect}
  </script>
</head>
<body><p>Redirecting…</p></body>
</html>"""

root = Path(__file__).parent

(root / "index.html").write_text(
    shell("AFL Tipping 2026", "index.js", d(LEADERBOARD_VIEW + ADMIN_VIEW + PREDICTIONS_VIEW)),
    encoding="utf-8",
)

(root / "quattro-formaggi.html").write_text(
    shell("Quattro Formaggi – AFL Tipping 2026", "quattro-page.js", d(QUATTRO_BODY)),
    encoding="utf-8",
)

(root / "compare.html").write_text(
    shell("Compare – AFL Tipping 2026", "compare-page.js", d(COMPARE_BODY)),
    encoding="utf-8",
)

(root / "leaderboard.html").write_text(
    REDIRECT.format(redirect="location.replace(base + 'index.html' + q);"),
    encoding="utf-8",
)

(root / "setup.html").write_text(
    REDIRECT.format(redirect="location.replace(base + 'index.html?admin&page=predictions');"),
    encoding="utf-8",
)

print("wrote index.html, quattro-formaggi.html, compare.html, leaderboard.html, setup.html")
