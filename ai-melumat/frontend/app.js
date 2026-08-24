const listingsEl = document.getElementById("listings");
const statsEl = document.getElementById("stats");
const statusEl = document.getElementById("list-status");
const badgeEl = document.getElementById("source-badge");
const bannerEl = document.getElementById("banner");
const chipsEl = document.getElementById("chips");
const threadEl = document.getElementById("thread");
const formEl = document.getElementById("chat-form");
const queryEl = document.getElementById("query");
const confirmEl = document.getElementById("confirm");

let state = { elanlar: [], statistika: null, source: "empty" };

function showBanner(text) {
  if (!text) {
    bannerEl.hidden = true;
    bannerEl.textContent = "";
    return;
  }
  bannerEl.hidden = false;
  bannerEl.textContent = text;
}

function sourceLabel(source) {
  if (source === "live") return "real sayt";
  if (source === "fixture" || source === "file") return "lokal HTML";
  return "mənbə yoxdur";
}

function manat(n) {
  return `${Number(n).toLocaleString("az-AZ").replace(/,/g, " ")} ₼`;
}

function renderStats(s) {
  if (!s || !s.qiymetli_say) {
    statsEl.className = "stats empty";
    statsEl.textContent = "Statistika burada çıxacaq.";
    return;
  }
  statsEl.className = "stats";
  statsEl.innerHTML = `
    <div><span>Elan</span><strong>${s.say}</strong></div>
    <div><span>Orta</span><strong>${manat(s.ortalama)}</strong></div>
    <div><span>Ucuz / baha</span><strong>${manat(s.en_ucuz)} · ${manat(s.en_baha)}</strong></div>
  `;
}

function renderListings(elanlar, activeIdx) {
  listingsEl.innerHTML = "";
  elanlar.forEach((e, i) => {
    const li = document.createElement("li");
    if (i === activeIdx) li.classList.add("active");
    li.innerHTML = `
      <span class="price">${e.qiymet}</span>
      <h3>${e.ad}</h3>
      <div class="meta">${e.atributlar || "—"} · ${e.yer_vaxt || ""}</div>
    `;
    li.addEventListener("click", () => {
      queryEl.value = `${e.ad} haqqında`;
      queryEl.focus();
      renderListings(state.elanlar, i);
    });
    listingsEl.appendChild(li);
  });
}

function renderChips(items) {
  chipsEl.innerHTML = "";
  (items || []).forEach((text) => {
    const b = document.createElement("button");
    b.type = "button";
    b.textContent = text;
    b.addEventListener("click", () => sendChat(text));
    chipsEl.appendChild(b);
  });
}

function addMsg(role, text, extra = {}) {
  const div = document.createElement("div");
  div.className = `msg ${role}`;
  if (extra.pattern) {
    const pat = document.createElement("span");
    pat.className = "pat";
    pat.textContent = extra.pattern;
    div.appendChild(pat);
  }
  const body = document.createElement("div");
  body.textContent = text;
  div.appendChild(body);
  if (extra.elanlar && extra.elanlar.length) {
    const cite = document.createElement("div");
    cite.className = "cite";
    extra.elanlar.slice(0, 8).forEach((e) => {
      const b = document.createElement("button");
      b.type = "button";
      b.textContent = `${e.ad} · ${e.qiymet}`;
      b.addEventListener("click", () => {
        const i = state.elanlar.findIndex((x) => x.ad === e.ad && x.qiymet === e.qiymet);
        renderListings(state.elanlar, i);
        const li = listingsEl.children[i];
        if (li) li.scrollIntoView({ block: "nearest" });
      });
      cite.appendChild(b);
    });
    div.appendChild(cite);
  }
  threadEl.appendChild(div);
  threadEl.scrollTop = threadEl.scrollHeight;
}

async function loadListings() {
  const res = await fetch("/api/listings");
  const data = await res.json();
  applyData(data);
}

function applyData(data) {
  state = data;
  badgeEl.textContent = sourceLabel(data.source);
  badgeEl.className = `badge ${data.source}`;
  statusEl.textContent = `${(data.elanlar || []).length} elan`;
  renderStats(data.statistika);
  renderListings(data.elanlar || []);
  renderChips(data.suggestions);
  if (data.source !== "live") {
    showBanner("Turbo.az bu mühitdə Cloudflare arxasındadır. Dərs fixture-u (lokal HTML) işlədilir — eyni selector-lar, şəbəkəsiz.");
  } else {
    showBanner("");
  }
}

async function scrape(source) {
  statusEl.textContent = "yığılır…";
  const res = await fetch("/api/scrape", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ source }),
  });
  const data = await res.json();
  if (!res.ok) {
    showBanner(data.detail || "Scraping alınmadı");
    statusEl.textContent = "xəta";
    return;
  }
  applyData(data);
  addMsg("agent", `${data.elanlar.length} elan yığıldı (${sourceLabel(data.source)}). Soldakı kartlar AI üçün xammaldır.`, {
    pattern: "status",
  });
}

async function sendChat(text) {
  const query = (text || queryEl.value || "").trim();
  if (!query) return;
  queryEl.value = "";
  addMsg("user", query);
  const res = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query }),
  });
  const data = await res.json();
  addMsg("agent", data.text, { pattern: data.pattern, elanlar: data.elanlar });
  if (data.citations && data.citations.length) {
    renderListings(state.elanlar, data.citations[0]);
  }
}

function downloadJson() {
  const blob = new Blob([JSON.stringify(state.elanlar, null, 2)], { type: "application/json" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "elanlar.json";
  a.click();
  URL.revokeObjectURL(a.href);
}

document.getElementById("btn-fixture").addEventListener("click", () => scrape("fixture"));
document.getElementById("btn-live").addEventListener("click", () => scrape("live"));
document.getElementById("btn-export").addEventListener("click", () => {
  confirmEl.hidden = false;
});
document.getElementById("confirm-no").addEventListener("click", () => {
  confirmEl.hidden = true;
});
document.getElementById("confirm-yes").addEventListener("click", () => {
  confirmEl.hidden = true;
  downloadJson();
});
formEl.addEventListener("submit", (ev) => {
  ev.preventDefault();
  sendChat();
});

loadListings().then(() => {
  addMsg("agent", "Elanlar hazırdır. Büdcə, marka və ya şəhər yaz — cavabımı soldakı kartlara bağlayacağam.", {
    pattern: "grounded-summary",
  });
});
