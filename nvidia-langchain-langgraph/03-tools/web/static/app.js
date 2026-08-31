const consoleEl = document.getElementById("console");
const resultEl = document.getElementById("result");
const toolkitEl = document.getElementById("toolkit");

function showResult(text, xeta) {
  resultEl.textContent = text;
  resultEl.className = "result " + (xeta ? "err" : "ok");
}

function appendLog(line) {
  const current = consoleEl.textContent.trim();
  consoleEl.textContent = current + "\n" + line;
  consoleEl.scrollTop = consoleEl.scrollHeight;
}

async function loadToolkit() {
  const res = await fetch("/api/toolkit");
  const data = await res.json();
  toolkitEl.innerHTML = data.tools
    .map(
      (t) =>
        `<li><strong>${t.ad}</strong><span>${t.tesvir}</span></li>`
    )
    .join("");
}

async function callVergi() {
  const mebleg = Number(document.getElementById("vergi-mebleg").value);
  const faiz = Number(document.getElementById("vergi-faiz").value);
  const res = await fetch("/api/vergi", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mebleg, faiz }),
  });
  const data = await res.json();
  appendLog(`${data.invoke} → ${data.netice}`);
  showResult(`${data.netice} ₼ vergi`, false);
}

async function callEndirim() {
  const qiymet = Number(document.getElementById("endirim-qiymet").value);
  const faiz = Number(document.getElementById("endirim-faiz").value);
  const res = await fetch("/api/endirim", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ qiymet, faiz }),
  });
  const data = await res.json();
  appendLog(`${data.invoke} → ${JSON.stringify(data.netice)}`);
  showResult(String(data.netice), data.xeta);
}

async function runDemo() {
  const res = await fetch("/api/demo");
  const data = await res.json();
  consoleEl.textContent = [
    `vergi_hesabla.invoke({"məbləğ": 200, "faiz": 18}) → ${data.vergi}`,
    `endirim_tətbiq_et.invoke({"qiymət": 100, "faiz": 20}) → ${data.endirim}`,
    `endirim_tətbiq_et.invoke({"qiymət": 100, "faiz": 150}) → ${JSON.stringify(data.endirim_xeta)}`,
    "",
    "for t in hesab_toolkit:",
    ...data.adlar.map((ad) => `  ${ad}`),
  ].join("\n");
  showResult("Tapşırıq sınaqları tamamlandı", false);
}

document.getElementById("vergi-btn").addEventListener("click", callVergi);
document.getElementById("endirim-btn").addEventListener("click", callEndirim);
document.getElementById("demo-btn").addEventListener("click", runDemo);

document.querySelectorAll("[data-fill]").forEach((btn) => {
  btn.addEventListener("click", () => {
    if (btn.dataset.fill === "vergi") {
      document.getElementById("vergi-mebleg").value = btn.dataset.m;
      document.getElementById("vergi-faiz").value = btn.dataset.f;
      callVergi();
    } else {
      document.getElementById("endirim-qiymet").value = btn.dataset.m;
      document.getElementById("endirim-faiz").value = btn.dataset.f;
      callEndirim();
    }
  });
});

loadToolkit();
