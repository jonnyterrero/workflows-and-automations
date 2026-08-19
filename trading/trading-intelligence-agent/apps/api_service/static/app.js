const state = {
  token: localStorage.getItem("trading-intel-admin-token") || "",
  log: [],
};

const elements = {
  adminToken: document.getElementById("adminToken"),
  saveTokenBtn: document.getElementById("saveTokenBtn"),
  refreshAllBtn: document.getElementById("refreshAllBtn"),
  endpointText: document.getElementById("endpointText"),
  lastRefreshText: document.getElementById("lastRefreshText"),
  healthBadge: document.getElementById("healthBadge"),
  modeValue: document.getElementById("modeValue"),
  versionValue: document.getElementById("versionValue"),
  uptimeValue: document.getElementById("uptimeValue"),
  healthSummary: document.getElementById("healthSummary"),
  providerBadge: document.getElementById("providerBadge"),
  providerCards: document.getElementById("providerCards"),
  opsBadge: document.getElementById("opsBadge"),
  operationOutput: document.getElementById("operationOutput"),
  watchlistBadge: document.getElementById("watchlistBadge"),
  watchlistList: document.getElementById("watchlistList"),
  signalBadge: document.getElementById("signalBadge"),
  signalForm: document.getElementById("signalForm"),
  signalSymbol: document.getElementById("signalSymbol"),
  signalHorizon: document.getElementById("signalHorizon"),
  signalResult: document.getElementById("signalResult"),
  recentSignalsList: document.getElementById("recentSignalsList"),
  briefingBadge: document.getElementById("briefingBadge"),
  briefingDate: document.getElementById("briefingDate"),
  briefingCreatedAt: document.getElementById("briefingCreatedAt"),
  marketRegimeText: document.getElementById("marketRegimeText"),
  macroSummaryText: document.getElementById("macroSummaryText"),
  equitySummaryText: document.getElementById("equitySummaryText"),
  etfSummaryText: document.getElementById("etfSummaryText"),
  bondSummaryText: document.getElementById("bondSummaryText"),
  cryptoSummaryText: document.getElementById("cryptoSummaryText"),
  opportunitiesList: document.getElementById("opportunitiesList"),
  risksList: document.getElementById("risksList"),
  newsEventsList: document.getElementById("newsEventsList"),
  activityLog: document.getElementById("activityLog"),
  bootstrapBtn: document.getElementById("bootstrapBtn"),
  runDailyBtn: document.getElementById("runDailyBtn"),
  runResearchBtn: document.getElementById("runResearchBtn"),
  verifyXBtn: document.getElementById("verifyXBtn"),
};

function setStatusPill(element, tone, text) {
  element.className = `status-pill ${tone}`;
  element.textContent = text;
}

function setOperationOutput(data) {
  elements.operationOutput.textContent =
    typeof data === "string" ? data : JSON.stringify(data, null, 2);
}

function logEvent(kind, message) {
  state.log.unshift({
    kind,
    message,
    timestamp: new Date().toLocaleTimeString(),
  });
  state.log = state.log.slice(0, 10);
  renderActivityLog();
}

function renderActivityLog() {
  elements.activityLog.innerHTML = "";
  if (!state.log.length) {
    const row = document.createElement("li");
    row.innerHTML = '<div class="activity-text">No activity yet.</div>';
    elements.activityLog.appendChild(row);
    return;
  }

  state.log.forEach((entry) => {
    const row = document.createElement("li");
    row.innerHTML = `
      <div class="activity-text">
        <span class="log-kind">${entry.kind}</span>${entry.message}
      </div>
      <span class="log-time">${entry.timestamp}</span>
    `;
    elements.activityLog.appendChild(row);
  });
}

function adminHeaders() {
  return state.token ? { "X-Admin-Token": state.token } : {};
}

async function requestJson(path, options = {}) {
  const { admin = false, method = "GET", body } = options;
  const headers = { ...(admin ? adminHeaders() : {}) };
  if (body !== undefined) {
    headers["Content-Type"] = "application/json";
  }

  const response = await fetch(path, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json")
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    const detail =
      typeof payload === "object" && payload
        ? payload.detail || payload.error || JSON.stringify(payload)
        : payload;
    throw new Error(`${response.status} ${detail}`);
  }

  return payload;
}

function formatUptime(seconds) {
  if (typeof seconds !== "number") {
    return "-";
  }
  if (seconds < 60) {
    return `${Math.round(seconds)}s`;
  }
  const minutes = Math.floor(seconds / 60);
  const remSeconds = Math.round(seconds % 60);
  return `${minutes}m ${remSeconds}s`;
}

function formatDateTime(value) {
  if (!value) {
    return "-";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return String(value);
  }
  return date.toLocaleString();
}

function renderHealth(data) {
  setStatusPill(elements.healthBadge, "good", data.status || "ok");
  elements.modeValue.textContent = data.demo_mode ? "demo" : "live";
  elements.versionValue.textContent = data.version || "-";
  elements.uptimeValue.textContent = formatUptime(data.uptime_seconds);
  elements.healthSummary.textContent = `Market: ${data.providers.market} | Macro: ${data.providers.macro} | Crypto: ${data.providers.crypto}`;
}

function providerCard(title, body, note = "") {
  return `
    <article class="provider-card">
      <h3>${title}</h3>
      <p>${body}</p>
      ${note ? `<p class="provider-note">${note}</p>` : ""}
    </article>
  `;
}

function renderProviders(data) {
  const xStatus = data.x_api?.configured
    ? "Configured"
    : "Not configured";
  const xNote = data.x_api?.configured
    ? "Recent-search checks are available from the admin console."
    : "X key is still missing. The rest of the system can run without it.";
  const cryptoCatalog = data.crypto_source_catalog || {};
  const cards = [
    providerCard("Market data", data.market),
    providerCard("Macro", data.macro),
    providerCard("Crypto", data.crypto),
    providerCard("News", Array.isArray(data.news) ? data.news.join(", ") : String(data.news)),
    providerCard("Social", Array.isArray(data.social) ? data.social.join(", ") : String(data.social)),
    providerCard("Filings", data.filings),
    providerCard("Fundamentals", data.fundamentals || "not configured"),
    providerCard(
      "Crypto feed catalog",
      `${cryptoCatalog.rss_feed_count || 0} RSS feeds`,
      `${cryptoCatalog.api_integrations_pending || 0} API integrations pending`
    ),
    providerCard("X API", xStatus, xNote),
  ];
  elements.providerCards.innerHTML = cards.join("");
  setStatusPill(elements.providerBadge, "good", data.demo_mode ? "demo" : "live stack");
}

function renderWatchlist(items) {
  elements.watchlistList.innerHTML = "";
  if (!items.length) {
    elements.watchlistList.innerHTML =
      '<li><div class="activity-text">No watchlist assets yet.</div></li>';
    setStatusPill(elements.watchlistBadge, "warn", "empty");
    return;
  }

  items.forEach((item) => {
    const row = document.createElement("li");
    row.innerHTML = `
      <div>
        <div class="ticker">${item.symbol}</div>
        <div class="asset-meta">${item.name}</div>
      </div>
      <div class="asset-meta">${item.asset_class}</div>
    `;
    elements.watchlistList.appendChild(row);
  });
  setStatusPill(elements.watchlistBadge, "good", `${items.length} assets`);
}

function renderSignals(data) {
  elements.recentSignalsList.innerHTML = "";
  if (!data.signals?.length) {
    elements.recentSignalsList.innerHTML =
      '<li><div class="activity-text">No stored signals yet. Run research or generate one manually.</div></li>';
    return;
  }

  data.signals.forEach((signal) => {
    const row = document.createElement("li");
    row.innerHTML = `
      <div>
        <div class="ticker">${signal.direction}</div>
        <div class="asset-meta">${signal.horizon} | confidence ${signal.confidence}</div>
      </div>
      <div class="asset-meta">score ${signal.score}</div>
    `;
    elements.recentSignalsList.appendChild(row);
  });
}

function normalizeListItem(item) {
  if (typeof item === "string") {
    return item;
  }
  if (item?.title) {
    return item.title;
  }
  if (item?.headline) {
    return item.headline;
  }
  if (item?.summary) {
    return item.summary;
  }
  return JSON.stringify(item);
}

function renderBulletList(element, items, emptyMessage) {
  element.innerHTML = "";
  if (!items?.length) {
    const row = document.createElement("li");
    row.textContent = emptyMessage;
    element.appendChild(row);
    return;
  }
  items.forEach((item) => {
    const row = document.createElement("li");
    row.textContent = normalizeListItem(item);
    element.appendChild(row);
  });
}

function renderBriefing(data) {
  elements.briefingDate.textContent = data.date || "-";
  elements.briefingCreatedAt.textContent = formatDateTime(data.created_at);
  elements.marketRegimeText.textContent = data.market_regime_summary || "No market regime summary.";
  elements.macroSummaryText.textContent = data.macro_summary || "No macro summary.";
  elements.equitySummaryText.textContent = data.equity_summary || "No equity summary.";
  elements.etfSummaryText.textContent = data.etf_summary || "No ETF summary.";
  elements.bondSummaryText.textContent = data.bond_summary || "No bond summary.";
  elements.cryptoSummaryText.textContent = data.crypto_summary || "No crypto summary.";
  renderBulletList(elements.opportunitiesList, data.top_opportunities, "No opportunities surfaced yet.");
  renderBulletList(elements.risksList, data.top_risks, "No risks surfaced yet.");
  renderBulletList(elements.newsEventsList, data.major_news_events, "No major news events recorded yet.");
  setStatusPill(elements.briefingBadge, "good", "loaded");
}

function renderBriefingEmpty(message) {
  elements.briefingDate.textContent = "-";
  elements.briefingCreatedAt.textContent = "-";
  elements.marketRegimeText.textContent = message;
  elements.macroSummaryText.textContent = "-";
  elements.equitySummaryText.textContent = "-";
  elements.etfSummaryText.textContent = "-";
  elements.bondSummaryText.textContent = "-";
  elements.cryptoSummaryText.textContent = "-";
  renderBulletList(elements.opportunitiesList, [], "Run research to generate opportunities.");
  renderBulletList(elements.risksList, [], "Run research to generate risk highlights.");
  renderBulletList(elements.newsEventsList, [], "Run research to populate event coverage.");
  setStatusPill(elements.briefingBadge, "warn", "not generated");
}

function renderSignalResult(signal, price) {
  elements.signalResult.classList.remove("empty-state");
  elements.signalResult.innerHTML = `
    <div class="headline">
      <strong>${signal.symbol} | ${signal.direction}</strong>
      <span class="status-pill good">score ${signal.score}</span>
    </div>
    <div class="signal-detail-grid">
      <div>
        <span class="meta-label">Confidence</span>
        <strong>${signal.confidence}</strong>
      </div>
      <div>
        <span class="meta-label">Latest price</span>
        <strong>${price?.close ?? "n/a"}</strong>
      </div>
      <div>
        <span class="meta-label">Reasoning</span>
        <div class="micro-copy">${signal.reasoning || "No reasoning returned."}</div>
      </div>
      <div>
        <span class="meta-label">Risk flags</span>
        <div class="micro-copy">${(signal.risk_flags || []).join(", ") || "none"}</div>
      </div>
    </div>
  `;
}

async function refreshPublicPanels() {
  const [health, watchlist, signals] = await Promise.all([
    requestJson("/health"),
    requestJson("/assets/watchlist"),
    requestJson("/signals?limit=5"),
  ]);
  renderHealth(health);
  renderWatchlist(watchlist);
  renderSignals(signals);
}

async function refreshAdminPanels() {
  try {
    const providers = await requestJson("/admin/providers", { admin: true });
    renderProviders(providers);
  } catch (error) {
    elements.providerCards.innerHTML = providerCard(
      "Admin access",
      "Provider details require a valid ADMIN_API_TOKEN.",
      error.message
    );
    setStatusPill(elements.providerBadge, "warn", "token required");
  }

  try {
    const briefing = await requestJson("/research/daily-briefing/latest");
    renderBriefing(briefing);
  } catch (error) {
    renderBriefingEmpty(error.message);
  }
}

async function refreshAll() {
  elements.endpointText.textContent = window.location.origin;
  try {
    await refreshPublicPanels();
    await refreshAdminPanels();
    elements.lastRefreshText.textContent = new Date().toLocaleTimeString();
    logEvent("refresh", "Console synced with live API.");
  } catch (error) {
    logEvent("error", error.message);
  }
}

async function runAdminAction(path, label) {
  setStatusPill(elements.opsBadge, "warn", `${label} running`);
  try {
    const result = await requestJson(path, { method: "POST", admin: true });
    setOperationOutput(result);
    setStatusPill(elements.opsBadge, "good", `${label} complete`);
    logEvent("job", `${label} finished successfully.`);
    await refreshAll();
  } catch (error) {
    setOperationOutput(error.message);
    setStatusPill(elements.opsBadge, "bad", `${label} failed`);
    logEvent("error", `${label} failed: ${error.message}`);
  }
}

async function runSignal(event) {
  event.preventDefault();
  const symbol = elements.signalSymbol.value.trim().toUpperCase();
  const horizon = elements.signalHorizon.value;
  if (!symbol) {
    return;
  }

  setStatusPill(elements.signalBadge, "warn", "running");
  try {
    const signal = await requestJson("/signals/run", {
      method: "POST",
      body: { symbol, horizon },
    });
    let price = null;
    try {
      price = await requestJson(`/market/${symbol}/latest`);
    } catch (_error) {
      price = null;
    }
    renderSignalResult(signal, price);
    setStatusPill(elements.signalBadge, "good", "fresh signal");
    logEvent("signal", `Generated ${signal.direction} signal for ${symbol}.`);
    await refreshAll();
  } catch (error) {
    elements.signalResult.classList.add("empty-state");
    elements.signalResult.textContent = error.message;
    setStatusPill(elements.signalBadge, "bad", "failed");
    logEvent("error", `Signal generation failed for ${symbol}: ${error.message}`);
  }
}

function bindEvents() {
  elements.adminToken.value = state.token;
  elements.saveTokenBtn.addEventListener("click", async () => {
    state.token = elements.adminToken.value.trim();
    localStorage.setItem("trading-intel-admin-token", state.token);
    logEvent("auth", state.token ? "Admin token saved locally in this browser." : "Admin token cleared.");
    await refreshAll();
  });
  elements.refreshAllBtn.addEventListener("click", refreshAll);
  elements.signalForm.addEventListener("submit", runSignal);
  elements.bootstrapBtn.addEventListener("click", () => runAdminAction("/admin/jobs/bootstrap-live", "Bootstrap"));
  elements.runDailyBtn.addEventListener("click", () => runAdminAction("/admin/jobs/run-daily", "Daily ingestion"));
  elements.runResearchBtn.addEventListener("click", () => runAdminAction("/admin/jobs/run-research", "Research briefing"));
  elements.verifyXBtn.addEventListener("click", () => runAdminAction("/admin/setup/x/verify", "X verification"));
}

function boot() {
  bindEvents();
  renderActivityLog();
  renderBriefingEmpty("Waiting for the first briefing fetch.");
  refreshAll();
}

boot();
