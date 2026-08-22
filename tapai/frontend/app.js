const $ = (id) => document.getElementById(id);

const state = {
  catalog: null,
  home: null,
  lastSearch: null,
  activeItem: null,
};

async function api(path, options) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.detail || res.statusText);
  }
  return data;
}

function fillSelect(el, rows, valueKey, labelKey) {
  el.innerHTML = rows
    .map((row) => `<option value="${row[valueKey]}">${row[labelKey]}</option>`)
    .join("");
}

function renderItems(items) {
  const ul = $("items");
  ul.innerHTML = items
    .map(
      (item) => `
      <li>
        <button type="button" data-id="${item.id}" class="${state.activeItem === item.id ? "active" : ""}">
          ${item.name}
          <small>${item.material_az} · ${item.room_az}${item.has_tag ? " · tag" : ""}${item.has_photo ? " · foto" : ""}</small>
        </button>
      </li>`
    )
    .join("");
  ul.querySelectorAll("button").forEach((btn) => {
    btn.addEventListener("click", () => {
      state.activeItem = btn.dataset.id;
      if ($("cam-item")) $("cam-item").value = btn.dataset.id;
      $("query").value = "";
      runSearch({ item_id: btn.dataset.id, mode: $("mode").value });
      renderItems(items);
    });
  });
}

function renderFloor(home, search) {
  const floor = $("floor");
  const hitsById = {};
  (search?.hits || []).forEach((hit, idx) => {
    hitsById[hit.id] = { ...hit, rank: idx };
  });

  const rooms = home.rooms
    .map(
      (room) =>
        `<div class="room" style="left:${room.x}%;top:${room.y}%;width:${room.w}%;height:${room.h}%">${room.az}</div>`
    )
    .join("");

  const heatmapSource = search?.heatmap || home.heatmap || [];
  const heat = heatmapSource
    .map((cell) => {
      const alpha = Math.min(0.55, cell.energy * 0.55);
      return `<div class="heat-cell" style="left:${cell.x}%;top:${cell.y}%;background:rgba(196,90,42,${alpha})"></div>`;
    })
    .join("");

  const pins = home.objects
    .map((obj) => {
      const hit = hitsById[obj.id];
      const cls = [
        "pin",
        obj.category === "clutter" ? "clutter" : "",
        hit ? "hit" : "",
        hit?.is_best ? "best" : "",
      ]
        .filter(Boolean)
        .join(" ");
      const title = `${obj.name} — ${obj.room_az}`;
      return `<div class="${cls}" title="${title}" style="left:${obj.x}%;top:${obj.y}%"></div>`;
    })
    .join("");

  floor.innerHTML = rooms + heat + pins;
}

function bar(value) {
  const pct = Math.round(Math.max(0, Math.min(1, value)) * 100);
  return `<div class="bar"><span style="width:${pct}%"></span></div><span>${pct}</span>`;
}

function renderResults(payload) {
  const card = $("target-card");
  if (!payload) {
    card.className = "target empty";
    card.textContent = "Sorğu göndər, və ya soldan əşya seç.";
    $("hits").innerHTML = "";
    return;
  }
  const t = payload.target;
  card.className = "target";
  card.innerHTML = `<strong>${t.name}</strong> axtarılır · ${t.material_az} (${t.family_az}) · rejim: ${payload.mode}`;

  $("hits").innerHTML = payload.hits
    .map(
      (hit) => `
      <li class="${hit.is_best ? "best" : ""}">
        <span class="conf">${Math.round(hit.confidence * 100)}%</span>
        <h4>${hit.name}</h4>
        <div class="meta">${hit.room_az} · ${hit.hidden_note} · ${hit.material_az}</div>
        <div class="bars">
          <span>material</span>${bar(hit.scores.material)}
          <span>vizual</span>${bar(hit.scores.visual)}
          <span>forma</span>${bar(hit.scores.category)}
          <span>tag</span>${bar(hit.scores.tag)}
        </div>
        <p class="explain">${hit.explanation}</p>
      </li>`
    )
    .join("");

  const banner = $("banner");
  if (payload.warning) {
    banner.hidden = false;
    banner.textContent = payload.warning;
  } else {
    banner.hidden = true;
  }
  $("map-status").textContent = payload.hits[0]
    ? `Ən yaxın: ${payload.hits[0].room_az}`
    : "Namizəd yoxdur";
}

async function runSearch(body) {
  try {
    const payload = await api("/api/search", { method: "POST", body: JSON.stringify(body) });
    state.lastSearch = payload;
    renderResults(payload);
    renderFloor(state.home, payload);
  } catch (err) {
    $("banner").hidden = false;
    $("banner").textContent = err.message;
  }
}

async function boot() {
  state.catalog = await api("/api/catalog");
  state.home = await api("/api/home");
  fillSelect($("mode"), state.catalog.modes, "id", "az");
  fillSelect($("enroll-category"), state.catalog.categories, "id", "az");
  fillSelect(
    $("enroll-material"),
    state.catalog.materials.map((m) => ({ id: m.id, az: `${m.az} (${m.family_az})` })),
    "id",
    "az"
  );
  fillSelect($("enroll-room"), state.catalog.rooms, "id", "az");
  renderItems((await api("/api/items")).items);
  renderFloor(state.home, null);
  await bootCamera();

  $("search-form").addEventListener("submit", (event) => {
    event.preventDefault();
    state.activeItem = null;
    runSearch({ query: $("query").value, mode: $("mode").value });
  });

  $("mode").addEventListener("change", () => {
    if (state.activeItem) {
      runSearch({ item_id: state.activeItem, mode: $("mode").value });
    } else if ($("query").value.trim()) {
      runSearch({ query: $("query").value, mode: $("mode").value });
    }
  });

  $("enroll-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    await api("/api/items", {
      method: "POST",
      body: JSON.stringify({
        name: $("enroll-name").value,
        category: $("enroll-category").value,
        material: $("enroll-material").value,
        room: $("enroll-room").value,
        with_tag: $("enroll-tag").checked,
      }),
    });
    $("enroll-name").value = "";
    state.home = await api("/api/home");
    renderItems((await api("/api/items")).items);
    renderFloor(state.home, state.lastSearch);
    fillCamItems((await api("/api/items")).items);
  });
}

function fillCamItems(items) {
  const sel = $("cam-item");
  if (!sel) return;
  sel.innerHTML = items
    .map((item) => `<option value="${item.id}">${item.name}${item.has_photo ? " (foto var)" : ""}</option>`)
    .join("");
  if (state.activeItem) sel.value = state.activeItem;
}

function renderLastSeen(rows) {
  const ol = $("last-seen");
  if (!ol) return;
  if (!rows || !rows.length) {
    ol.innerHTML = "<li class='meta'>Hələ kamera ilə tapılmayıb.</li>";
    return;
  }
  ol.innerHTML = rows
    .map((row) => {
      const when = new Date(row.at).toLocaleString();
      const geo = row.lat != null ? ` · ${row.lat.toFixed(5)}, ${row.lon.toFixed(5)}` : "";
      const mark = row.verdict === "found" ? "tapıldı" : "ehtimal";
      return `<li><h4>${row.name}</h4><div class="meta">${mark} · ${Math.round(row.score * 100)}% · ${when}${geo}</div></li>`;
    })
    .join("");
}

function captureBlob() {
  const video = $("cam-video");
  const canvas = $("cam-canvas");
  if (!video.videoWidth) {
    throw new Error("Kamera görüntüsü yoxdur. Əvvəl “Kameranı aç” və ya fayl seç.");
  }
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  canvas.getContext("2d").drawImage(video, 0, 0);
  return new Promise((resolve) => canvas.toBlob((blob) => resolve(blob), "image/jpeg", 0.85));
}

async function postPhoto(url, blob, extra = {}) {
  const form = new FormData();
  form.append("photo", blob, "frame.jpg");
  Object.entries(extra).forEach(([key, value]) => {
    if (value != null && value !== "") form.append(key, value);
  });
  const res = await fetch(url, { method: "POST", body: form });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || res.statusText);
  return data;
}

async function geo() {
  if (!navigator.geolocation) return {};
  try {
    const pos = await new Promise((resolve, reject) =>
      navigator.geolocation.getCurrentPosition(resolve, reject, { timeout: 2500, maximumAge: 60000 })
    );
    return { lat: pos.coords.latitude, lon: pos.coords.longitude };
  } catch {
    return {};
  }
}

function showCamResult(payload) {
  const box = $("cam-result");
  const hit = payload.hits && payload.hits[0];
  if (!hit) {
    box.className = "cam-result miss";
    box.textContent = "Tanıdılmış foto yoxdur. Əvvəl referans kadr çək.";
    return;
  }
  box.className = `cam-result ${hit.verdict === "no_photo" ? "miss" : hit.verdict}`;
  const cue = payload.material_cues ? payload.material_cues.note : "";
  box.textContent = `${hit.name}: ${Math.round(hit.score * 100)}% · ${hit.explanation} ${cue}`;
  renderLastSeen(payload.last_seen);
}

async function bootCamera() {
  fillCamItems((await api("/api/items")).items);
  renderLastSeen((await api("/api/camera/last-seen")).last_seen);

  let stream = null;
  $("cam-start").addEventListener("click", async () => {
    try {
      stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: { ideal: "environment" } },
        audio: false,
      });
      $("cam-video").srcObject = stream;
      $("cam-status").textContent = "Kamera açıqdır";
    } catch (err) {
      $("cam-status").textContent = "Canlı kamera açılmadı";
      $("cam-result").className = "cam-result miss";
      $("cam-result").textContent =
        "Canlı kamera bloklandı (telefon + HTTP). “Kameradan foto” ilə çək — o işləyir. " + err.message;
    }
  });

  $("cam-enroll").addEventListener("click", async () => {
    try {
      const blob = await captureBlob();
      const itemId = $("cam-item").value;
      const item = await postPhoto(`/api/items/${itemId}/photo`, blob);
      $("cam-result").className = "cam-result found";
      $("cam-result").textContent = `${item.name} üçün referans foto yadda saxlandı.`;
      const items = (await api("/api/items")).items;
      renderItems(items);
      fillCamItems(items);
    } catch (err) {
      $("cam-result").className = "cam-result miss";
      $("cam-result").textContent = err.message;
    }
  });

  async function searchWithBlob(blob) {
    const extra = { item_id: $("cam-item").value, ...(await geo()) };
    const payload = await postPhoto("/api/camera/search", blob, extra);
    showCamResult(payload);
  }

  $("cam-search").addEventListener("click", async () => {
    try {
      await searchWithBlob(await captureBlob());
    } catch (err) {
      $("cam-result").className = "cam-result miss";
      $("cam-result").textContent = err.message;
    }
  });

  $("cam-file-enroll").addEventListener("change", async (event) => {
    const file = event.target.files && event.target.files[0];
    event.target.value = "";
    if (!file) return;
    try {
      const item = await postPhoto(`/api/items/${$("cam-item").value}/photo`, file);
      $("cam-result").className = "cam-result found";
      $("cam-result").textContent = `${item.name} üçün referans foto yadda saxlandı.`;
      const items = (await api("/api/items")).items;
      renderItems(items);
      fillCamItems(items);
    } catch (err) {
      $("cam-result").className = "cam-result miss";
      $("cam-result").textContent = err.message;
    }
  });

  $("cam-file-search").addEventListener("change", async (event) => {
    const file = event.target.files && event.target.files[0];
    event.target.value = "";
    if (!file) return;
    try {
      await searchWithBlob(file);
    } catch (err) {
      $("cam-result").className = "cam-result miss";
      $("cam-result").textContent = err.message;
    }
  });
}

boot().catch((err) => {
  $("banner").hidden = false;
  $("banner").textContent = `API açılmadı: ${err.message}`;
});
