"""Generate static HTML pages (run once)."""
from pathlib import Path

TAG = "motion"  # replaced below


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


INDEX_BODY = f"""
<{TAG} class="page-header"><{TAG} class="container">
  <h1><i class="bi bi-trophy-fill me-2"></i>AFL Tipping Leaderboard 2026</h1>
  <p class="subtitle mb-0">Track who called the top 10 best — updated each round</p>
</{TAG}></{TAG}>
<{TAG} class="container">
  <{TAG} class="sync-banner mb-4">
    <i class="bi bi-cloud me-1"></i>
    <strong>Shared data:</strong> Everyone sees the same scores from <code>data/store.json</code>.
    After editing, use <strong>Download store.json</strong> and commit to GitHub.
  </{TAG}>
  <{TAG} class="row g-4">
    <{TAG} class="col-md-6">
      <{TAG} class="card h-100">
        <{TAG} class="card-header"><i class="bi bi-person-check me-2"></i>Prediction Status</{TAG}>
        <{TAG} class="card-body">
          <{TAG} id="predStatus"></{TAG}>
          <a href="setup.html" class="btn btn-afl mt-2 w-100">
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
</{TAG}>"""

SETUP_BODY = f"""
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
      <a href="index.html" class="btn btn-secondary btn-lg">Cancel</a>
      <button type="button" class="btn btn-afl-outline btn-lg" id="exportBtn">Download store.json</button>
    </{TAG}>
  </form>
</{TAG}>"""

LEADERBOARD_BODY = f"""
<{TAG} class="page-header"><{TAG} class="container">
  <h1><i class="bi bi-bar-chart-fill me-2"></i>Leaderboard</h1>
  <p class="subtitle mb-0">Round-by-round scores &amp; season totals</p>
</{TAG}></{TAG}>
<{TAG} class="container" id="lbRoot"></{TAG}>"""

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

pages = {
    "index.html": shell("Home – AFL Tipping 2026", "home.js", INDEX_BODY),
    "setup.html": shell("Enter Predictions – AFL Tipping 2026", "setup-page.js", SETUP_BODY),
    "leaderboard.html": shell("Leaderboard – AFL Tipping 2026", "leaderboard-page.js", LEADERBOARD_BODY),
    "compare.html": shell("Compare – AFL Tipping 2026", "compare-page.js", COMPARE_BODY),
}

root = Path(__file__).parent
for name, content in pages.items():
    (root / name).write_text(d(content), encoding="utf-8")
    print("wrote", name)
