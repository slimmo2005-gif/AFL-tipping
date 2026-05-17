import { assetUrl, PARTICIPANT_NAMES } from './config.js';

const STORAGE_KEY = 'afl_tipping_store_v1';

function emptyStore() {
  return {
    participants: PARTICIPANT_NAMES.map((name, i) => ({ id: i + 1, name })),
    predictions: [],
    rounds: [],
  };
}

function normalizeStore(store) {
  const out = {
    participants: [...(store.participants || [])],
    predictions: [...(store.predictions || [])],
    rounds: [...(store.rounds || [])],
  };

  const names = new Set(out.participants.map((p) => p.name));
  if (!names.has('Johno')) {
    const matt2 = out.participants.find((p) => p.name === 'Matt2');
    const john = out.participants.find((p) => p.name === 'John');
    if (matt2) matt2.name = 'Johno';
    else if (john) john.name = 'Johno';
  }
  out.participants = out.participants.filter((p) => !['Matt2', 'John'].includes(p.name));

  for (const name of PARTICIPANT_NAMES) {
    if (!out.participants.some((p) => p.name === name)) {
      const nextId = Math.max(0, ...out.participants.map((p) => p.id)) + 1;
      out.participants.push({ id: nextId, name });
    }
  }
  out.participants.sort((a, b) => a.name.localeCompare(b.name));

  return out;
}

export async function fetchSharedStore() {
  const url = assetUrl('data/store.json') + `?t=${Date.now()}`;
  const res = await fetch(url);
  if (!res.ok) return null;
  return normalizeStore(await res.json());
}

export function loadLocalStore() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    return normalizeStore(JSON.parse(raw));
  } catch {
    return null;
  }
}

/** Prefer local edits; fall back to shared store.json from the repo. */
export async function loadStore() {
  const shared = await fetchSharedStore();
  const local = loadLocalStore();

  if (!local || (!local.predictions.length && !local.rounds.length)) {
    if (shared) {
      saveStore(shared);
      return shared;
    }
    return emptyStore();
  }

  // Merge newer rounds from the committed store (after someone pushes to GitHub)
  if (shared?.rounds?.length > local.rounds.length) {
    local.rounds = shared.rounds;
    saveStore(local);
  }
  return local;
}

export function saveStore(store) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(normalizeStore(store)));
}

export function getParticipants(store) {
  return [...store.participants].sort((a, b) => a.id - b.id);
}

export function getPredictionMap(store, participantId) {
  const map = {};
  for (const p of store.predictions) {
    if (p.participant_id === participantId) map[p.position] = p.team_name;
  }
  return map;
}

export function predictionCount(store, participantId) {
  return store.predictions.filter((p) => p.participant_id === participantId).length;
}

export function getPredictionsList(store, participantId) {
  return store.predictions
    .filter((p) => p.participant_id === participantId)
    .sort((a, b) => a.position - b.position)
    .map((p) => [p.position, p.team_name]);
}

export function savePredictions(store, participantId, picks) {
  store.predictions = store.predictions.filter((p) => p.participant_id !== participantId);
  let nextId = Math.max(0, ...store.predictions.map((p) => p.id)) + 1;
  for (const [position, team_name] of picks) {
    store.predictions.push({ id: nextId++, participant_id: participantId, position, team_name });
  }
}

export function saveRound(store, roundNumber, ladder) {
  const fetchedAt = new Date().toISOString().slice(0, 16).replace('T', ' ');
  const entry = {
    round_number: roundNumber,
    fetched_at: fetchedAt,
    ladder_json: JSON.stringify(ladder),
  };
  const idx = store.rounds.findIndex((r) => r.round_number === roundNumber);
  if (idx >= 0) store.rounds[idx] = { ...store.rounds[idx], ...entry };
  else store.rounds.push(entry);
  store.rounds.sort((a, b) => a.round_number - b.round_number);
}

export function parseLadder(round) {
  return JSON.parse(round.ladder_json);
}

export function serializeStore(store) {
  return JSON.stringify(normalizeStore(store), null, 2);
}

export function downloadStoreJson(store) {
  const blob = new Blob([serializeStore(store)], { type: 'application/json' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'store.json';
  a.click();
  URL.revokeObjectURL(a.href);
}
