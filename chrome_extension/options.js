const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";
const DEFAULT_AUTO_CHECK_MINUTES = 0;

const form = document.getElementById("options-form");
const apiBaseUrlInput = document.getElementById("api-base-url");
const autoCheckInput = document.getElementById("auto-check-minutes");
const statusEl = document.getElementById("status");

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

function requestOriginPermission(baseUrl) {
  const pattern = originPatternFromBaseUrl(baseUrl);
  return new Promise((resolve) => {
    chrome.permissions.request({ origins: [pattern] }, (granted) => resolve(Boolean(granted)));
  });
}

function showStatus(message, isError = false) {
  if (!statusEl) return;
  statusEl.textContent = message;
  statusEl.style.color = isError ? "#b91c1c" : "#065f46";
}

async function loadOptions() {
  const settings = await storageGet(["apiBaseUrl", "autoCheckMinutes"]);
  try {
    apiBaseUrlInput.value = parseApiBaseUrl(settings.apiBaseUrl || DEFAULT_API_BASE_URL);
  } catch (_error) {
    apiBaseUrlInput.value = DEFAULT_API_BASE_URL;
  }
  autoCheckInput.value = Number.isFinite(settings.autoCheckMinutes)
    ? String(settings.autoCheckMinutes)
    : String(DEFAULT_AUTO_CHECK_MINUTES);
}

async function saveOptions(event) {
  event.preventDefault();

  const current = await storageGet(["apiBaseUrl"]);

  let apiBaseUrl;
  try {
    apiBaseUrl = parseApiBaseUrl(apiBaseUrlInput.value);
  } catch (error) {
    showStatus(error.message, true);
    return;
  }

  const autoCheckMinutes = Number(autoCheckInput.value);
  if (!Number.isFinite(autoCheckMinutes) || autoCheckMinutes < 0) {
    showStatus("Auto-check interval must be 0 or greater", true);
    return;
  }

  const granted = await requestOriginPermission(apiBaseUrl);
  if (!granted) {
    showStatus("Permission denied for API origin", true);
    return;
  }

  const currentBaseUrl = parseApiBaseUrl(current.apiBaseUrl || DEFAULT_API_BASE_URL);
  const baseUrlChanged = currentBaseUrl !== apiBaseUrl;

  const updates = {
    apiBaseUrl,
    autoCheckMinutes,
  };
  if (baseUrlChanged) {
    updates.authToken = null;
    updates.authEmail = null;
  }

  await storageSet(updates);

  chrome.runtime.sendMessage(
    {
      type: "pb-settings-updated",
      apiBaseUrl,
      autoCheckMinutes,
    },
    () => {
      if (chrome.runtime.lastError) {
        showStatus(`Saved, but background update failed: ${chrome.runtime.lastError.message}`, true);
        return;
      }
      const suffix = baseUrlChanged ? " (auth cleared due API host change)" : "";
      showStatus(`Settings saved${suffix}`);
    },
  );
}

form?.addEventListener("submit", saveOptions);
loadOptions();
