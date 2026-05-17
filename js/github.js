import { serializeStore } from './storage.js';

export const GITHUB_OWNER = 'slimmo2005-gif';
export const GITHUB_REPO = 'AFL-tipping';
export const GITHUB_BRANCH = 'main';
export const GITHUB_STORE_PATH = 'data/store.json';
const TOKEN_KEY = 'afl_github_token';

export function getGitHubToken() {
  return localStorage.getItem(TOKEN_KEY) || '';
}

export function setGitHubToken(token) {
  const t = token.trim();
  if (t) localStorage.setItem(TOKEN_KEY, t);
  else localStorage.removeItem(TOKEN_KEY);
}

export function hasGitHubToken() {
  return !!getGitHubToken();
}

function toBase64Utf8(text) {
  const bytes = new TextEncoder().encode(text);
  let binary = '';
  for (let i = 0; i < bytes.length; i += 1) binary += String.fromCharCode(bytes[i]);
  return btoa(binary);
}

async function githubApi(path, options = {}) {
  const token = getGitHubToken();
  if (!token) {
    throw new Error('GitHub token not configured. Add one in Sync settings on the Home page.');
  }

  const res = await fetch(`https://api.github.com${path}`, {
    ...options,
    headers: {
      Accept: 'application/vnd.github+json',
      Authorization: `Bearer ${token}`,
      'X-GitHub-Api-Version': '2022-11-28',
      ...(options.headers || {}),
    },
  });

  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      if (body.message) detail = body.message;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }

  if (res.status === 204) return null;
  return res.json();
}

/** Commit store to data/store.json on GitHub (updates the live site for everyone). */
export async function pushStoreToGitHub(store, commitMessage) {
  const path = encodeURIComponent(GITHUB_STORE_PATH);
  const contentJson = serializeStore(store);
  const content = toBase64Utf8(contentJson);

  let sha;
  try {
    const existing = await githubApi(
      `/repos/${GITHUB_OWNER}/${GITHUB_REPO}/contents/${path}?ref=${GITHUB_BRANCH}`,
    );
    sha = existing.sha;
  } catch (err) {
    if (!String(err.message).toLowerCase().includes('not found')) throw err;
  }

  const body = {
    message: commitMessage,
    content,
    branch: GITHUB_BRANCH,
  };
  if (sha) body.sha = sha;

  return githubApi(`/repos/${GITHUB_OWNER}/${GITHUB_REPO}/contents/${path}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

export function initGitHubSettings() {
  const input = document.getElementById('githubToken');
  const status = document.getElementById('githubTokenStatus');
  const saveBtn = document.getElementById('saveGitHubToken');
  const clearBtn = document.getElementById('clearGitHubToken');
  if (!input || !saveBtn) return;

  function refreshStatus() {
    if (!status) return;
    if (hasGitHubToken()) {
      status.innerHTML =
        '<span class="text-success"><i class="bi bi-check-circle me-1"></i>Token saved — fetch &amp; saves will sync to GitHub automatically.</span>';
      input.value = '';
      input.placeholder = '••••••••••••••••';
    } else {
      status.innerHTML =
        '<span class="text-warning"><i class="bi bi-exclamation-triangle me-1"></i>No token — ladder saves stay in this browser only.</span>';
    }
  }

  saveBtn.addEventListener('click', () => {
    const token = input.value.trim();
    if (!token) {
      status.innerHTML = '<span class="text-danger">Paste a token first.</span>';
      return;
    }
    setGitHubToken(token);
    refreshStatus();
  });

  clearBtn?.addEventListener('click', () => {
    setGitHubToken('');
    refreshStatus();
  });

  refreshStatus();
}
