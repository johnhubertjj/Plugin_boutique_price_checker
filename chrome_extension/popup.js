const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";
const REQUEST_TIMEOUT_MS = 15000;

const state = {
  apiBaseUrl: DEFAULT_API_BASE_URL,
  token: null,
  authEmail: null,
  me: null,
  items: [],
  hasOriginPermission: false,
};

const els = {
  configForm: document.getElementById("config-form"),
  apiBaseUrl: document.getElementById("api-base-url"),
  authStatus: document.getElementById("auth-status"),
  devCode: document.getElementById("dev-code"),
  status: document.getElementById("status"),
  registerStartForm: document.getElementById("register-start-form"),
  verifyEmailForm: document.getElementById("verify-email-form"),
  verifyPhoneForm: document.getElementById("verify-phone-form"),
  loginStartForm: document.getElementById("login-start-form"),
  loginVerifyForm: document.getElementById("login-verify-form"),
  loginEmail: document.getElementById("login-email"),
  registerEmail: document.getElementById("register-email"),
  refreshButton: document.getElementById("refresh-button"),
  logoutButton: document.getElementById("logout-button"),
  createItemForm: document.getElementById("create-item-form"),
  items: document.getElementById("items"),
};

function storageGet(keys) {
  return new Promise((resolve) => chrome.storage.local.get(keys, resolve));
}

function storageSet(values) {
  return new Promise((resolve) => chrome.storage.local.set(values, resolve));
}

function parseApiBaseUrl(rawValue) {
  const value = String(rawValue || "").trim();
  if (!value) {
    throw new Error("API base URL is required");
  }
  let parsed;
  try {
    parsed = new URL(value);
  } catch (_error) {
    throw new Error("API base URL is invalid");
  }
  if (parsed.protocol !== "http:" && parsed.protocol !== "https:") {
    throw new Error("API base URL must start with http:// or https://");
  }
  return parsed.origin;
}

function originPatternFromBaseUrl(baseUrl) {
  const parsed = new URL(baseUrl);
  return `${parsed.protocol}//${parsed.hostname}/*`;
}

function hasOriginPermission(baseUrl) {
  const pattern = originPatternFromBaseUrl(baseUrl);
  return new Promise((resolve) => {
    chrome.permissions.contains({ origins: [pattern] }, (granted) => resolve(Boolean(granted)));
  });
}

function requestOriginPermission(baseUrl) {
  const pattern = originPatternFromBaseUrl(baseUrl);
  return new Promise((resolve) => {
    chrome.permissions.request({ origins: [pattern] }, (granted) => resolve(Boolean(granted)));
  });
}

function showStatus(message, isError = false) {
  if (!els.status) return;
  els.status.textContent = message;
  els.status.classList.toggle("error", isError);
}

function showDevCode(code) {
  if (!els.devCode) return;
  els.devCode.textContent = code ? `Dev OTP: ${code}` : "";
}

function setAuthStatus() {
  if (!els.authStatus) return;
  if (!state.hasOriginPermission) {
    els.authStatus.textContent = "API permission not granted yet.";
    return;
  }
  if (state.me) {
    els.authStatus.textContent = `Authenticated: ${state.me.email}`;
  } else {
    els.authStatus.textContent = "Not authenticated.";
  }
}

function formatDate(value) {
  if (!value) return "-";
  return new Date(value).toLocaleString();
}

function jsonOrNull(rawText) {
  if (!rawText) return null;
  try {
    return JSON.parse(rawText);
  } catch (_error) {
    return null;
  }
}

async function ensureOriginPermission() {
  if (state.hasOriginPermission) {
    return;
  }
  state.hasOriginPermission = await hasOriginPermission(state.apiBaseUrl);
  if (!state.hasOriginPermission) {
    throw new Error("Grant API origin access in Save API URL before calling backend");
  }
}

async function apiRequest(path, { method = "GET", body = null, auth = true } = {}) {
  if (!path.startsWith("/")) {
    throw new Error("API path must start with '/'");
  }

  await ensureOriginPermission();

  const headers = { "Content-Type": "application/json" };
  if (auth && state.token) {
    headers.Authorization = `Bearer ${state.token}`;
  }

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  let response;
  try {
    response = await fetch(`${state.apiBaseUrl}${path}`, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
      credentials: "omit",
      signal: controller.signal,
    });
  } catch (error) {
    if (error?.name === "AbortError") {
      throw new Error("Request timed out");
    }
    throw error;
  } finally {
    clearTimeout(timeout);
  }

  const text = await response.text();
  const json = jsonOrNull(text);

  if (!response.ok) {
    const detail = json && json.detail ? json.detail : `${response.status} ${response.statusText}`;
    const error = new Error(detail);
    error.status = response.status;
    throw error;
  }

  return json;
}

async function persistAuthState() {
  await storageSet({
    authToken: state.token,
    authEmail: state.authEmail,
  });
}

async function saveBaseUrl() {
  await storageSet({ apiBaseUrl: state.apiBaseUrl });
}

function createItemCard(item) {
  const container = document.createElement("div");
  container.className = "item";

  const urlEl = document.createElement("p");
  urlEl.className = "item-url";
  urlEl.textContent = item.product_url;

  const metaEl = document.createElement("p");
  metaEl.className = "item-meta";
  metaEl.textContent =
    `Threshold: ${item.threshold} | Active: ${item.is_active ? "Yes" : "No"} | Last check: ${formatDate(item.last_checked_at)}`;

  const actions = document.createElement("div");
  actions.className = "item-actions";

  const runButton = document.createElement("button");
  runButton.type = "button";
  runButton.textContent = "Run Check";

  const deleteButton = document.createElement("button");
  deleteButton.type = "button";
  deleteButton.className = "danger";
  deleteButton.textContent = "Delete";

  runButton.addEventListener("click", async () => {
    try {
      await apiRequest(`/me/watchlist-items/${item.id}/check`, { method: "POST" });
      showStatus(`Ran check for item #${item.id}`);
      await refreshItems();
    } catch (error) {
      showStatus(error.message, true);
    }
  });

  deleteButton.addEventListener("click", async () => {
    try {
      await apiRequest(`/me/watchlist-items/${item.id}`, { method: "DELETE" });
      showStatus(`Deleted item #${item.id}`);
      await refreshItems();
    } catch (error) {
      showStatus(error.message, true);
    }
  });

  actions.appendChild(runButton);
  actions.appendChild(deleteButton);

  container.appendChild(urlEl);
  container.appendChild(metaEl);
  container.appendChild(actions);
  return container;
}

function renderItems() {
  if (!els.items) return;

  if (!state.hasOriginPermission) {
    els.items.textContent = "Grant API permission to load watchlist items.";
    return;
  }

  if (!state.me) {
    els.items.textContent = "Log in to manage watchlist items.";
    return;
  }

  if (state.items.length === 0) {
    els.items.textContent = "No watchlist items yet.";
    return;
  }

  els.items.innerHTML = "";
  state.items.forEach((item) => {
    els.items.appendChild(createItemCard(item));
  });
}

async function refreshMe() {
  if (!state.token) {
    state.me = null;
    setAuthStatus();
    return;
  }

  try {
    state.me = await apiRequest("/me");
  } catch (error) {
    state.me = null;
    state.token = null;
    await persistAuthState();
    showStatus(error.message, true);
  }
  setAuthStatus();
}

async function refreshItems() {
  if (!state.me) {
    state.items = [];
    renderItems();
    return;
  }

  try {
    state.items = await apiRequest("/me/watchlist-items");
    renderItems();
  } catch (error) {
    showStatus(error.message, true);
  }
}

async function handleConfigSubmit(event) {
  event.preventDefault();

  let nextBaseUrl;
  try {
    nextBaseUrl = parseApiBaseUrl(els.apiBaseUrl?.value);
  } catch (error) {
    showStatus(error.message, true);
    return;
  }

  const granted = await requestOriginPermission(nextBaseUrl);
  if (!granted) {
    showStatus("Permission denied for API origin", true);
    return;
  }

  const baseUrlChanged = nextBaseUrl !== state.apiBaseUrl;
  state.apiBaseUrl = nextBaseUrl;
  state.hasOriginPermission = true;
  await saveBaseUrl();

  if (baseUrlChanged) {
    state.token = null;
    state.me = null;
    state.items = [];
    showDevCode(null);
    await persistAuthState();
  }

  chrome.runtime.sendMessage(
    { type: "pb-settings-updated", apiBaseUrl: state.apiBaseUrl },
    () => {
      const suffix = baseUrlChanged ? " (auth cleared due API host change)" : "";
      showStatus(`Saved API URL: ${state.apiBaseUrl}${suffix}`);
    },
  );

  setAuthStatus();
  await refreshMe();
  await refreshItems();
}

async function handleRegisterStart(event) {
  event.preventDefault();
  const formData = new FormData(event.currentTarget);
  const email = String(formData.get("email") || "").trim();
  const phoneNumber = String(formData.get("phone_number") || "").trim();
  state.authEmail = email;
  await persistAuthState();

  if (els.loginEmail) {
    els.loginEmail.value = email;
  }

  try {
    const response = await apiRequest("/auth/register/start", {
      method: "POST",
      body: {
        email,
        phone_number: phoneNumber,
      },
      auth: false,
    });
    showDevCode(response?.dev_code || null);
    showStatus(response?.message || "Registration started");
  } catch (error) {
    showStatus(error.message, true);
  }
}

async function handleVerifyEmail(event) {
  event.preventDefault();
  const formData = new FormData(event.currentTarget);
  const code = String(formData.get("code") || "").trim();
  const email = state.authEmail || String(els.registerEmail?.value || "").trim();

  try {
    const response = await apiRequest("/auth/register/verify-email", {
      method: "POST",
      body: { email, code },
      auth: false,
    });
    showDevCode(response?.dev_code || null);
    showStatus(response?.message || "Email verified");
  } catch (error) {
    showStatus(error.message, true);
  }
}

async function handleVerifyPhone(event) {
  event.preventDefault();
  const formData = new FormData(event.currentTarget);
  const code = String(formData.get("code") || "").trim();
  const email = state.authEmail || String(els.registerEmail?.value || "").trim();

  try {
    const response = await apiRequest("/auth/register/verify-phone", {
      method: "POST",
      body: { email, code },
      auth: false,
    });
    state.token = response?.access_token || null;
    state.me = response?.user || null;
    await persistAuthState();
    setAuthStatus();
    showDevCode(null);
    showStatus("Registration complete and authenticated");
    await refreshItems();
  } catch (error) {
    showStatus(error.message, true);
  }
}

async function handleLoginStart(event) {
  event.preventDefault();
  const formData = new FormData(event.currentTarget);
  const email = String(formData.get("email") || "").trim();
  state.authEmail = email;
  await persistAuthState();

  try {
    const response = await apiRequest("/auth/login/start", {
      method: "POST",
      body: { email },
      auth: false,
    });
    showDevCode(response?.dev_code || null);
    showStatus(response?.message || "Login started");
  } catch (error) {
    showStatus(error.message, true);
  }
}

async function handleLoginVerify(event) {
  event.preventDefault();
  const formData = new FormData(event.currentTarget);
  const code = String(formData.get("code") || "").trim();
  const email = state.authEmail || String(els.loginEmail?.value || "").trim();

  try {
    const response = await apiRequest("/auth/login/verify", {
      method: "POST",
      body: { email, code },
      auth: false,
    });
    state.token = response?.access_token || null;
    state.me = response?.user || null;
    await persistAuthState();
    setAuthStatus();
    showDevCode(null);
    showStatus("Authenticated");
    await refreshItems();
  } catch (error) {
    showStatus(error.message, true);
  }
}

async function handleLogout() {
  try {
    await apiRequest("/auth/logout", { method: "POST" });
  } catch (_error) {
    // Ignore endpoint failure and still clear local auth state.
  }

  state.token = null;
  state.me = null;
  state.items = [];
  showDevCode(null);
  await persistAuthState();
  setAuthStatus();
  renderItems();
  showStatus("Logged out");
}

async function handleCreateItem(event) {
  event.preventDefault();
  if (!state.me) {
    showStatus("Log in first", true);
    return;
  }

  const formData = new FormData(event.currentTarget);
  const productUrl = String(formData.get("product_url") || "").trim();
  const thresholdRaw = Number(formData.get("threshold") || "0");

  try {
    const parsedProductUrl = new URL(productUrl);
    if (parsedProductUrl.protocol !== "http:" && parsedProductUrl.protocol !== "https:") {
      throw new Error("Product URL must start with http:// or https://");
    }
  } catch (error) {
    showStatus(error.message || "Product URL is invalid", true);
    return;
  }

  if (!Number.isFinite(thresholdRaw) || thresholdRaw <= 0) {
    showStatus("Threshold must be greater than 0", true);
    return;
  }

  try {
    await apiRequest("/me/watchlist-items", {
      method: "POST",
      body: {
        product_url: productUrl,
        threshold: thresholdRaw,
      },
    });
    event.currentTarget.reset();
    showStatus("Watchlist item added");
    await refreshItems();
  } catch (error) {
    showStatus(error.message, true);
  }
}

function bindEvents() {
  els.configForm?.addEventListener("submit", handleConfigSubmit);
  els.registerStartForm?.addEventListener("submit", handleRegisterStart);
  els.verifyEmailForm?.addEventListener("submit", handleVerifyEmail);
  els.verifyPhoneForm?.addEventListener("submit", handleVerifyPhone);
  els.loginStartForm?.addEventListener("submit", handleLoginStart);
  els.loginVerifyForm?.addEventListener("submit", handleLoginVerify);
  els.logoutButton?.addEventListener("click", handleLogout);
  els.refreshButton?.addEventListener("click", async () => {
    await refreshMe();
    await refreshItems();
    showStatus("Refreshed");
  });
  els.createItemForm?.addEventListener("submit", handleCreateItem);
}

async function init() {
  const stored = await storageGet(["apiBaseUrl", "authToken", "authEmail"]);

  try {
    state.apiBaseUrl = parseApiBaseUrl(stored.apiBaseUrl || DEFAULT_API_BASE_URL);
  } catch (_error) {
    state.apiBaseUrl = DEFAULT_API_BASE_URL;
  }

  state.token = stored.authToken || null;
  state.authEmail = stored.authEmail || null;
  state.hasOriginPermission = await hasOriginPermission(state.apiBaseUrl);

  if (els.apiBaseUrl) {
    els.apiBaseUrl.value = state.apiBaseUrl;
  }
  if (state.authEmail && els.loginEmail) {
    els.loginEmail.value = state.authEmail;
  }
  if (state.authEmail && els.registerEmail) {
    els.registerEmail.value = state.authEmail;
  }

  setAuthStatus();
  renderItems();

  if (!state.hasOriginPermission) {
    showStatus("Save API URL and accept permission prompt to connect", true);
    return;
  }

  await refreshMe();
  await refreshItems();
}

bindEvents();
init();
