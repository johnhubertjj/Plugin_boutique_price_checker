const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";
const DEFAULT_AUTO_CHECK_MINUTES = 0;
const AUTO_CHECK_ALARM = "pb-auto-check";
const REQUEST_TIMEOUT_MS = 15000;

function storageGet(keys) {
  return new Promise((resolve) => chrome.storage.local.get(keys, resolve));
}

function storageSet(values) {
  return new Promise((resolve) => chrome.storage.local.set(values, resolve));
}

function parseApiBaseUrl(rawValue) {
  const value = String(rawValue || "").trim();
  if (!value) {
    return DEFAULT_API_BASE_URL;
  }
  try {
    const parsed = new URL(value);
    if (parsed.protocol !== "http:" && parsed.protocol !== "https:") {
      return DEFAULT_API_BASE_URL;
    }
    return parsed.origin;
  } catch (_error) {
    return DEFAULT_API_BASE_URL;
  }
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

async function loadSettings() {
  const stored = await storageGet(["apiBaseUrl", "autoCheckMinutes", "authToken"]);
  return {
    apiBaseUrl: parseApiBaseUrl(stored.apiBaseUrl || DEFAULT_API_BASE_URL),
    autoCheckMinutes: Number.isFinite(stored.autoCheckMinutes) ? stored.autoCheckMinutes : DEFAULT_AUTO_CHECK_MINUTES,
    authToken: stored.authToken || null,
  };
}

async function syncAutoCheckAlarm() {
  const { autoCheckMinutes } = await loadSettings();

  await chrome.alarms.clear(AUTO_CHECK_ALARM);

  if (autoCheckMinutes > 0) {
    chrome.alarms.create(AUTO_CHECK_ALARM, {
      delayInMinutes: autoCheckMinutes,
      periodInMinutes: autoCheckMinutes,
    });
  }
}

function jsonOrNull(rawText) {
  if (!rawText) {
    return null;
  }
  try {
    return JSON.parse(rawText);
  } catch (_error) {
    return null;
  }
}

async function requestJson(url, authToken, options = {}) {
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };
  if (authToken) {
    headers.Authorization = `Bearer ${authToken}`;
  }

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  let response;
  try {
    response = await fetch(url, {
      ...options,
      headers,
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
  const payload = jsonOrNull(text);

  if (!response.ok) {
    const detail = payload && payload.detail ? payload.detail : `${response.status} ${response.statusText}`;
    throw new Error(detail);
  }

  return payload;
}

async function runAutoChecks() {
  const { apiBaseUrl, authToken } = await loadSettings();
  if (!authToken) {
    return;
  }

  const granted = await hasOriginPermission(apiBaseUrl);
  if (!granted) {
    console.warn("Auto-check skipped: missing origin permission for", apiBaseUrl);
    return;
  }

  try {
    const items = await requestJson(`${apiBaseUrl}/me/watchlist-items`, authToken);
    const activeItems = Array.isArray(items) ? items.filter((item) => item.is_active) : [];

    for (const item of activeItems) {
      const run = await requestJson(`${apiBaseUrl}/me/watchlist-items/${item.id}/check`, authToken, {
        method: "POST",
      });

      if (run && run.alert_sent) {
        chrome.notifications.create({
          type: "basic",
          iconUrl: "icon-128.png",
          title: "Price Alert Sent",
          message: `Alert triggered for watchlist item #${item.id}`,
          priority: 1,
        });
      }
    }
  } catch (error) {
    console.warn("Auto-check run failed:", error.message);
  }
}

chrome.runtime.onInstalled.addListener(async () => {
  const stored = await storageGet(["apiBaseUrl", "autoCheckMinutes"]);
  await storageSet({
    apiBaseUrl: parseApiBaseUrl(stored.apiBaseUrl || DEFAULT_API_BASE_URL),
    autoCheckMinutes: Number.isFinite(stored.autoCheckMinutes)
      ? stored.autoCheckMinutes
      : DEFAULT_AUTO_CHECK_MINUTES,
  });
  await syncAutoCheckAlarm();
});

chrome.runtime.onStartup.addListener(async () => {
  await syncAutoCheckAlarm();
});

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message?.type !== "pb-settings-updated") {
    return;
  }

  (async () => {
    await syncAutoCheckAlarm();
    sendResponse({ ok: true });
  })().catch((error) => sendResponse({ ok: false, error: error.message }));

  return true;
});

chrome.alarms.onAlarm.addListener(async (alarm) => {
  if (alarm.name !== AUTO_CHECK_ALARM) {
    return;
  }
  await runAutoChecks();
});
