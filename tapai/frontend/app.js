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
          <small>${item.material_az} · ${item.room_az}${item.has_tag ? " · tag" : ""}</small>
        </button>
      </li>`
    )
    .join("");
  ul.querySelectorAll("button").forEach((btn) => {
    btn.addEventListener("click", () => {
      state.activeItem = btn.dataset.id;
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
  });
}

boot().catch((err) => {
  $("banner").hidden = false;
  $("banner").textContent = `API açılmadı: ${err.message}`;
});
