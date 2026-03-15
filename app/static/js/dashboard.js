/* Trading Platform – dashboard.js */
"use strict";

// ─── Tab navigation ────────────────────────────────────────────────────────
function initTabs() {
  const tabs   = document.querySelectorAll(".nav-tab");
  const panels = document.querySelectorAll(".tab-panel");

  tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      const target = tab.dataset.tab;
      tabs.forEach(t => t.classList.toggle("active", t === tab));
      panels.forEach(p => p.classList.toggle("active", p.id === target));
      // Trigger load if first visit
      if (tab.dataset.loaded !== "1") {
        tab.dataset.loaded = "1";
        loadTabData(target);
      }
    });
  });
}

// ─── Generic fetch helpers ─────────────────────────────────────────────────
async function apiFetch(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`HTTP ${r.status}: ${r.statusText}`);
  return r.json();
}

function setHtml(selector, html) {
  const el = document.querySelector(selector);
  if (el) el.innerHTML = html;
}

function loading(selector) {
  setHtml(selector, `<div class="loading-overlay"><span class="spinner"></span> Loading…</div>`);
}

function errorHtml(msg) {
  return `<div class="alert alert-error" style="margin:.5rem 0">⚠ ${msg}</div>`;
}

// ─── Number formatters ─────────────────────────────────────────────────────
const fmt = new Intl.NumberFormat("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const fmtBig = new Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 2 });

function pctClass(v) {
  if (v > 0) return "up";
  if (v < 0) return "down";
  return "flat";
}

function arrow(v) {
  if (v > 0) return "▲";
  if (v < 0) return "▼";
  return "–";
}

// ─── Quotes ────────────────────────────────────────────────────────────────
async function loadQuotes() {
  loading("#quotes-grid");
  try {
    const data = await apiFetch("/markets/quotes");
    const { quotes } = data;
    if (!quotes || !quotes.length) {
      setHtml("#quotes-grid", errorHtml("No quote data available."));
      return;
    }
    const html = quotes.map(q => {
      if (q.error) return `<div class="quote-card">${errorHtml(q.symbol + ": " + q.error)}</div>`;
      const dp  = q.dp ?? 0;
      const cls = pctClass(dp);
      return `
        <div class="quote-card">
          <div class="quote-symbol">${q.symbol}</div>
          <div class="quote-price">${q.c ? "$" + fmt.format(q.c) : "–"}</div>
          <div class="quote-change ${cls}">${arrow(dp)} ${fmt.format(Math.abs(dp))}%
            (${dp >= 0 ? "+" : ""}${fmt.format(q.d ?? 0)})</div>
          <div class="quote-meta">
            O: $${fmt.format(q.o ?? 0)} &nbsp;
            H: $${fmt.format(q.h ?? 0)} &nbsp;
            L: $${fmt.format(q.l ?? 0)} &nbsp;
            PC: $${fmt.format(q.pc ?? 0)}
          </div>
        </div>`;
    }).join("");
    setHtml("#quotes-grid", html);
  } catch (e) {
    setHtml("#quotes-grid", errorHtml(e.message));
  }
}

// ─── Options ───────────────────────────────────────────────────────────────
async function loadOptions(symbol) {
  if (!symbol) return;
  symbol = symbol.toUpperCase();
  loading("#options-content");
  try {
    const data = await apiFetch(`/options/${symbol}`);
    if (data.unavailable) {
      setHtml("#options-content", `
        <div class="alert alert-warn">
          ℹ ${data.message || "Options data not available on your current Finnhub plan."}
        </div>`);
      return;
    }
    if (data.error) { setHtml("#options-content", errorHtml(data.error)); return; }
    renderOptions(data);
  } catch (e) {
    setHtml("#options-content", errorHtml(e.message));
  }
}

function renderOptions(data) {
  const expirations = data.data || [];
  if (!expirations.length) {
    setHtml("#options-content", `<p class="text-muted">No options data returned.</p>`);
    return;
  }
  // Show first expiration date as example
  const first = expirations[0];
  const calls = first.options?.CALL || [];
  const puts  = first.options?.PUT  || [];

  const tableHtml = (rows, type) => {
    if (!rows.length) return `<p class="text-muted mt-1">No ${type}s</p>`;
    return `
      <div style="overflow-x:auto">
        <table class="data-table">
          <thead><tr>
            <th>Strike</th><th>Last</th><th>Bid</th><th>Ask</th>
            <th>Volume</th><th>OI</th><th>IV</th>
          </tr></thead>
          <tbody>
            ${rows.map(r => `<tr>
              <td>${r.strike}</td>
              <td>${r.lastPrice ?? "–"}</td>
              <td>${r.bid ?? "–"}</td>
              <td>${r.ask ?? "–"}</td>
              <td>${r.volume ?? "–"}</td>
              <td>${r.openInterest ?? "–"}</td>
              <td>${r.impliedVolatility ? (r.impliedVolatility * 100).toFixed(1) + "%" : "–"}</td>
            </tr>`).join("")}
          </tbody>
        </table>
      </div>`;
  };

  setHtml("#options-content", `
    <p class="text-muted text-sm">Expiry: <strong>${first.expirationDate}</strong></p>
    <h3 style="margin:.75rem 0 .3rem;font-size:.9rem">Calls</h3>
    ${tableHtml(calls, "call")}
    <h3 style="margin:.75rem 0 .3rem;font-size:.9rem">Puts</h3>
    ${tableHtml(puts, "put")}
  `);
}

// ─── Weather ───────────────────────────────────────────────────────────────
async function loadWeather(city) {
  loading("#weather-content");
  const url = city ? `/weather?city=${encodeURIComponent(city)}` : "/weather";
  try {
    const d = await apiFetch(url);
    if (d.error) { setHtml("#weather-content", errorHtml(d.error)); return; }
    renderWeather(d);
  } catch (e) {
    setHtml("#weather-content", errorHtml(e.message));
  }
}

function weatherIcon(code) {
  const c = parseInt(code);
  if (c === 0)              return "☀️";
  if (c <= 2)               return "🌤️";
  if (c === 3)              return "☁️";
  if (c <= 48)              return "🌫️";
  if (c <= 57)              return "🌦️";
  if (c <= 67)              return "🌧️";
  if (c <= 77)              return "❄️";
  if (c <= 82)              return "🌦️";
  if (c <= 86)              return "🌨️";
  return "⛈️";
}

function renderWeather(d) {
  const cur = d.current;
  const forecast = (d.forecast || []).slice(0, 7);
  const forecastHtml = forecast.map(f => `
    <div class="forecast-day">
      <div class="date">${f.date}</div>
      <div class="icon">${weatherIcon(f.code)}</div>
      <div class="temps">${f.temp_max ?? "–"}° / ${f.temp_min ?? "–"}°</div>
      <div class="text-muted text-sm">${f.description}</div>
    </div>`).join("");

  setHtml("#weather-content", `
    <div class="weather-current">
      <div class="weather-icon">${weatherIcon(cur.code)}</div>
      <div>
        <div class="weather-temp">${cur.temperature ?? "–"}°C</div>
        <div>${cur.description}</div>
        <div class="text-muted text-sm">
          Feels like ${cur.feels_like ?? "–"}°C &nbsp;|&nbsp;
          Humidity ${cur.humidity ?? "–"}% &nbsp;|&nbsp;
          Wind ${cur.wind_speed ?? "–"} km/h
        </div>
      </div>
    </div>
    <div class="weather-forecast">${forecastHtml}</div>
  `);
  const locEl = document.querySelector("#weather-location");
  if (locEl) locEl.textContent = d.location;
}

// ─── Shipping ──────────────────────────────────────────────────────────────
async function lookupShipping() {
  const origin    = document.querySelector("#ship-origin").value.trim();
  const dest      = document.querySelector("#ship-dest").value.trim();
  const container = document.querySelector("#ship-container").value;
  const weight    = document.querySelector("#ship-weight").value;

  if (!origin || !dest) {
    setHtml("#shipping-results", `<div class="alert alert-warn">Please enter origin and destination ports.</div>`);
    return;
  }

  loading("#shipping-results");
  let url = `/shipping/rates?origin=${encodeURIComponent(origin)}&destination=${encodeURIComponent(dest)}&container_type=${encodeURIComponent(container)}`;
  if (weight) url += `&weight=${encodeURIComponent(weight)}`;

  try {
    const data = await apiFetch(url);
    if (data.error) { setHtml("#shipping-results", errorHtml(data.error)); return; }
    renderShipping(data);
  } catch (e) {
    setHtml("#shipping-results", errorHtml(e.message));
  }
}

function renderShipping(data) {
  const rates = data.rates || [];
  if (!rates.length) {
    setHtml("#shipping-results", `<div class="alert alert-info">No rates found for this route.</div>`);
    return;
  }
  const rows = rates.map(r => `
    <tr>
      <td>${r.carrier || "–"}</td>
      <td>${r.service || "–"}</td>
      <td>${r.transit_days ? r.transit_days + " days" : "–"}</td>
      <td>${r.total_price ? r.currency + " " + fmt.format(r.total_price) : "–"}</td>
      <td>${r.valid_until || "–"}</td>
    </tr>`).join("");

  setHtml("#shipping-results", `
    <p class="text-muted text-sm mt-1">
      ${data.origin} → ${data.destination} &nbsp;|&nbsp; ${data.container_type}
    </p>
    <div style="overflow-x:auto;margin-top:.75rem">
      <table class="data-table">
        <thead><tr>
          <th>Carrier</th><th>Service</th><th>Transit</th><th>Total</th><th>Valid Until</th>
        </tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </div>`);
}

// ─── News ──────────────────────────────────────────────────────────────────
async function loadNews(query) {
  loading("#news-list");
  const url = query
    ? `/news/search?q=${encodeURIComponent(query)}`
    : "/news/headlines";
  try {
    const data = await apiFetch(url);
    if (data.error) { setHtml("#news-list", errorHtml(data.error)); return; }
    renderNews(data.articles || []);
  } catch (e) {
    setHtml("#news-list", errorHtml(e.message));
  }
}

function renderNews(articles) {
  if (!articles.length) {
    setHtml("#news-list", `<p class="text-muted">No articles found.</p>`);
    return;
  }
  const html = articles.slice(0, 30).map(a => {
    const img = a.urlToImage
      ? `<img src="${a.urlToImage}" alt="" loading="lazy" onerror="this.style.display='none'">`
      : `<div class="placeholder-img">📰</div>`;
    return `
      <div class="news-item">
        ${img}
        <div>
          <div class="news-title">
            <a href="${a.url}" target="_blank" rel="noopener">${a.title || "(No title)"}</a>
          </div>
          <div class="news-meta">
            ${a.source?.name || "Unknown source"} &nbsp;·&nbsp;
            ${a.publishedAt ? new Date(a.publishedAt).toLocaleDateString() : ""}
          </div>
          ${a.description ? `<div class="text-sm text-muted" style="margin-top:.25rem">${a.description}</div>` : ""}
        </div>
      </div>`;
  }).join("");
  setHtml("#news-list", `<div class="news-list">${html}</div>`);
}

// ─── Tab data loader ───────────────────────────────────────────────────────
function loadTabData(tabId) {
  switch (tabId) {
    case "tab-markets":
      loadQuotes();
      break;
    case "tab-options": {
      const sym = document.querySelector("#options-symbol");
      if (sym?.value) loadOptions(sym.value);
      break;
    }
    case "tab-weather":
      loadWeather(null);
      break;
    case "tab-news":
      loadNews(null);
      break;
    // shipping is form-driven, no auto-load
  }
}

// ─── Auto-refresh quotes ───────────────────────────────────────────────────
function startAutoRefresh() {
  setInterval(() => {
    const activeTab = document.querySelector(".nav-tab.active");
    if (activeTab?.dataset.tab === "tab-markets") {
      loadQuotes();
    }
  }, 30000); // refresh every 30 s
}

// ─── Init ──────────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  initTabs();

  // Wire up refresh button for quotes
  document.querySelector("#btn-refresh-quotes")?.addEventListener("click", loadQuotes);

  // Options form
  document.querySelector("#btn-load-options")?.addEventListener("click", () => {
    const sym = document.querySelector("#options-symbol")?.value;
    loadOptions(sym);
  });

  // Weather form
  document.querySelector("#btn-weather-search")?.addEventListener("click", () => {
    const city = document.querySelector("#weather-city-input")?.value;
    loadWeather(city || null);
  });
  document.querySelector("#weather-city-input")?.addEventListener("keydown", e => {
    if (e.key === "Enter") {
      const city = e.target.value;
      loadWeather(city || null);
    }
  });

  // Shipping form
  document.querySelector("#btn-ship-search")?.addEventListener("click", lookupShipping);

  // News form
  document.querySelector("#btn-news-search")?.addEventListener("click", () => {
    const q = document.querySelector("#news-query")?.value.trim();
    loadNews(q || null);
  });
  document.querySelector("#news-query")?.addEventListener("keydown", e => {
    if (e.key === "Enter") loadNews(e.target.value.trim() || null);
  });

  // Load the first tab (Markets) on page load
  const firstTab = document.querySelector(".nav-tab");
  if (firstTab) {
    firstTab.dataset.loaded = "1";
    loadTabData(firstTab.dataset.tab);
  }

  startAutoRefresh();
});
