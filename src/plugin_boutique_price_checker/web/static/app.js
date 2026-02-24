const state = {
  token: localStorage.getItem("pb_token"),
  me: null,
  items: [],
  authEmail: null,
};

const authStatus = document.getElementById("auth-status");
const authDevCode = document.getElementById("auth-dev-code");
const itemsContainer = document.getElementById("items-container");
const runsContainer = document.getElementById("runs-container");
const runsHint = document.getElementById("runs-hint");
const statusBox = document.getElementById("status");

function notify(message, isError = false) {
  statusBox.textContent = message;
  statusBox.classList.add("show");
  statusBox.classList.toggle("error", isError);
  window.setTimeout(() => statusBox.classList.remove("show"), 2400);
}

function showDevCode(code) {
  authDevCode.textContent = code ? `Dev code: ${code}` : "";
}

function setToken(token) {
  state.token = token;
  if (token) {
    localStorage.setItem("pb_token", token);
  } else {
    localStorage.removeItem("pb_token");
  }
}

function renderAuthStatus() {
  if (state.me) {
    authStatus.textContent = `Authenticated: ${state.me.email}`;
  } else {
    authStatus.textContent = "Not authenticated.";
  }
}

async function request(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  if (state.token) {
    headers.Authorization = `Bearer ${state.token}`;
  }
  const response = await fetch(path, { ...options, headers });
  const body = await response.text();
  let json = null;
  if (body) {
    try {
      json = JSON.parse(body);
    } catch (_error) {
      json = null;
    }
  }
  if (!response.ok) {
    const detail = json && json.detail ? json.detail : `${response.status} ${response.statusText}`;
    const error = new Error(detail);
    error.status = response.status;
    throw error;
  }
  return json;
}

function formatDate(value) {
  if (!value) return "-";
  return new Date(value).toLocaleString();
}

function renderItems() {
  itemsContainer.innerHTML = "";
  if (!state.me) {
    itemsContainer.innerHTML = '<p class="muted">Authenticate first to manage watchlist items.</p>';
    return;
  }
  if (state.items.length === 0) {
    itemsContainer.innerHTML = '<p class="muted">No watchlist items yet.</p>';
    return;
  }

  state.items.forEach((item) => {
    const element = document.createElement("div");
    element.className = "item";
    element.innerHTML = `
      <div class="item-top">
        <p class="item-url">${item.product_url}</p>
        <span>${item.is_active ? "Active" : "Paused"}</span>
      </div>
      <small class="muted">Last check: ${formatDate(item.last_checked_at)} | Last price: ${item.last_currency || ""}${item.last_price ?? "-"}</small>
      <div class="item-controls">
        <input class="mini threshold-input" type="number" step="0.01" min="0.01" value="${item.threshold}">
        <select class="mini active-select">
          <option value="true" ${item.is_active ? "selected" : ""}>Active</option>
          <option value="false" ${!item.is_active ? "selected" : ""}>Paused</option>
        </select>
        <button class="mini save-btn" type="button">Save</button>
        <button class="mini run-btn" type="button">Run Check</button>
      </div>
      <div class="item-controls">
        <button class="mini show-runs-btn" type="button">Show Runs</button>
        <button class="mini remove-btn button-danger" type="button">Remove</button>
      </div>
    `;

    const thresholdInput = element.querySelector(".threshold-input");
    const activeSelect = element.querySelector(".active-select");

    element.querySelector(".save-btn").addEventListener("click", async () => {
      try {
        await request(`/me/watchlist-items/${item.id}`, {
          method: "PATCH",
          body: JSON.stringify({
            threshold: Number(thresholdInput.value),
            is_active: activeSelect.value === "true",
          }),
        });
        notify(`Item ${item.id} updated`);
        await loadItems();
      } catch (error) {
        notify(error.message, true);
      }
    });

    element.querySelector(".run-btn").addEventListener("click", async () => {
      try {
        await request(`/me/watchlist-items/${item.id}/check`, { method: "POST" });
        notify(`Check completed for item ${item.id}`);
        await loadItems();
      } catch (error) {
        notify(error.message, true);
      }
    });

    element.querySelector(".show-runs-btn").addEventListener("click", async () => {
      try {
        const runs = await request(`/me/watchlist-items/${item.id}/runs`);
        renderRuns(runs);
      } catch (error) {
        notify(error.message, true);
      }
    });

    element.querySelector(".remove-btn").addEventListener("click", async () => {
      const confirmed = window.confirm("Delete this watchlist item and its run history?");
      if (!confirmed) return;
      try {
        await request(`/me/watchlist-items/${item.id}`, { method: "DELETE" });
        runsContainer.innerHTML = "";
        runsHint.textContent = "Choose \"Show Runs\" on an item to load history.";
        notify(`Item ${item.id} removed`);
        await loadItems();
      } catch (error) {
        notify(error.message, true);
      }
    });

    itemsContainer.appendChild(element);
  });
}

function renderRuns(runs) {
  runsHint.textContent = `${runs.length} runs loaded`;
  runsContainer.innerHTML = "";
  if (runs.length === 0) {
    runsContainer.innerHTML = '<p class="muted">No runs yet.</p>';
    return;
  }
  runs.forEach((run) => {
    const element = document.createElement("div");
    element.className = "run";
    element.innerHTML = `
      <strong>#${run.id} ${run.status.toUpperCase()}</strong>
      <p>${run.message}</p>
      <small class="muted">Price: ${run.price_currency || ""}${run.price_amount ?? "-"} | Alert sent: ${run.alert_sent ? "yes" : "no"} | ${formatDate(run.created_at)}</small>
    `;
    runsContainer.appendChild(element);
  });
}

async function loadMe() {
  if (!state.token) {
    state.me = null;
    renderAuthStatus();
    return;
  }
  try {
    state.me = await request("/me");
    renderAuthStatus();
  } catch (error) {
    setToken(null);
    state.me = null;
    renderAuthStatus();
    notify(error.message, true);
  }
}

async function loadItems() {
  if (!state.me) {
    state.items = [];
    renderItems();
    return;
  }
  state.items = await request("/me/watchlist-items");
  renderItems();
}

document.getElementById("register-start-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const formData = new FormData(form);
  const email = String(formData.get("email")).trim();
  const phone = String(formData.get("phone_number")).trim();
  state.authEmail = email;
  document.getElementById("login-email").value = email;
  try {
    const response = await request("/auth/register/start", {
      method: "POST",
      body: JSON.stringify({ email, phone_number: phone }),
    });
    showDevCode(response.dev_code || null);
    notify(response.message);
  } catch (error) {
    notify(error.message, true);
  }
});

document.getElementById("verify-email-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(event.currentTarget);
  const email = state.authEmail || document.getElementById("register-email").value.trim();
  const code = String(formData.get("code")).trim();
  try {
    const response = await request("/auth/register/verify-email", {
      method: "POST",
      body: JSON.stringify({ email, code }),
    });
    showDevCode(response.dev_code || null);
    notify(response.message);
  } catch (error) {
    notify(error.message, true);
  }
});

document.getElementById("verify-phone-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(event.currentTarget);
  const email = state.authEmail || document.getElementById("register-email").value.trim();
  const code = String(formData.get("code")).trim();
  try {
    const response = await request("/auth/register/verify-phone", {
      method: "POST",
      body: JSON.stringify({ email, code }),
    });
    setToken(response.access_token);
    state.me = response.user;
    renderAuthStatus();
    showDevCode(null);
    notify("Registration complete and authenticated");
    await loadItems();
  } catch (error) {
    notify(error.message, true);
  }
});

document.getElementById("login-start-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(event.currentTarget);
  const email = String(formData.get("email")).trim();
  state.authEmail = email;
  try {
    const response = await request("/auth/login/start", {
      method: "POST",
      body: JSON.stringify({ email }),
    });
    showDevCode(response.dev_code || null);
    notify(response.message);
  } catch (error) {
    notify(error.message, true);
  }
});

document.getElementById("login-verify-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(event.currentTarget);
  const email = state.authEmail || document.getElementById("login-email").value.trim();
  const code = String(formData.get("code")).trim();
  try {
    const response = await request("/auth/login/verify", {
      method: "POST",
      body: JSON.stringify({ email, code }),
    });
    setToken(response.access_token);
    state.me = response.user;
    renderAuthStatus();
    showDevCode(null);
    notify("Authenticated");
    await loadItems();
  } catch (error) {
    notify(error.message, true);
  }
});

document.getElementById("logout-button").addEventListener("click", async () => {
  try {
    await request("/auth/logout", { method: "POST" });
  } catch (_error) {
    // Ignore logout endpoint errors and still clear local state.
  }
  setToken(null);
  state.me = null;
  state.items = [];
  renderAuthStatus();
  renderItems();
  showDevCode(null);
  notify("Logged out");
});

document.getElementById("create-item-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  if (!state.me) {
    notify("Authenticate first", true);
    return;
  }

  const formData = new FormData(form);
  try {
    await request("/me/watchlist-items", {
      method: "POST",
      body: JSON.stringify({
        product_url: String(formData.get("product_url")),
        threshold: Number(formData.get("threshold")),
      }),
    });
    form.reset();
    await loadItems();
    notify("Watchlist item added");
  } catch (error) {
    notify(error.message, true);
  }
});

document.getElementById("refresh-items-button").addEventListener("click", async () => {
  try {
    await loadMe();
    await loadItems();
    notify("Data refreshed");
  } catch (error) {
    notify(error.message, true);
  }
});

async function init() {
  renderAuthStatus();
  renderItems();
  await loadMe();
  await loadItems();
}

init();
