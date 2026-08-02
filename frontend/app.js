const API_BASE = "http://127.0.0.1:8000";

// ---------- Tab switching ----------
document.querySelectorAll(".tab").forEach(tab => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
    document.querySelectorAll(".panel").forEach(p => p.classList.remove("active"));
    tab.classList.add("active");
    document.getElementById(tab.dataset.tab).classList.add("active");
  });
});

// ---------- Helpers ----------
function el(html) {
  const div = document.createElement("div");
  div.innerHTML = html.trim();
  return div.firstChild;
}

function confidenceBand(label, value, min, max, rangeLow, rangeHigh) {
  const pct = v => Math.max(0, Math.min(100, ((v - min) / (max - min)) * 100));
  return `
    <div class="confidence-band">
      <div class="cb-label"><span>${label}</span><span>${value}</span></div>
      <div class="cb-track">
        <div class="cb-range" style="left:${pct(rangeLow)}%; width:${pct(rangeHigh) - pct(rangeLow)}%;"></div>
        <div class="cb-point" style="left:${pct(value)}%;"></div>
      </div>
    </div>`;
}

function simpleBand(label, value01) {
  return confidenceBand(label, (value01 * 100).toFixed(0) + "%", 0, 1, value01, value01);
}

async function callApi(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, options);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed (${res.status})`);
  }
  return res.json();
}

function setStatus(id, msg, isError = false) {
  const s = document.getElementById(id);
  s.textContent = msg;
  s.classList.toggle("error", isError);
}

// ============================================
// SKIN SCAN
// ============================================
const scanDropzone = document.getElementById("scanDropzone");
const scanFile = document.getElementById("scanFile");
scanDropzone.addEventListener("click", () => scanFile.click());
scanFile.addEventListener("change", () => {
  document.getElementById("scanFilename").textContent = scanFile.files[0]?.name || "";
});

document.getElementById("scanSubmit").addEventListener("click", async () => {
  if (!scanFile.files[0]) { setStatus("scanStatus", "Please choose a photo first.", true); return; }

  const btn = document.getElementById("scanSubmit");
  btn.disabled = true;
  setStatus("scanStatus", "Analyzing...");
  document.getElementById("scanResults").innerHTML = "";

  const tone = document.getElementById("toneCategory").value;
  const type = document.getElementById("skinTypeSelfReport").value;

  const params = new URLSearchParams();
  if (tone) params.set("tone_category", tone);
  if (type) params.set("skin_type_self_report", type);

  const formData = new FormData();
  formData.append("file", scanFile.files[0]);

  try {
    const data = await callApi(`/api/skin/analyze?${params.toString()}`, { method: "POST", body: formData });
    renderScanResults(data);
    setStatus("scanStatus", "Done.");
  } catch (e) {
    setStatus("scanStatus", e.message, true);
  } finally {
    btn.disabled = false;
  }
});

function renderScanResults(d) {
  const [lo, hi] = d.tone_confidence_interval_90 || [d.skin_tone_fitzpatrick_estimate, d.skin_tone_fitzpatrick_estimate];
  const card = el(`
    <div class="result-card">
      <h3>Skin Profile</h3>
      ${confidenceBand("Skin tone (Fitzpatrick 1-6)", d.skin_tone_fitzpatrick_estimate, 1, 6, lo, hi)}
      <div class="badge ok">Source: ${d.tone_source || "model"}</div>
      <br>
      <div style="margin-top:14px;">
        ${simpleBand(`Skin type: ${d.skin_type} (confidence)`, d.skin_type_confidence)}
      </div>
      <div class="badge ok">Type source: ${d.type_source || "model"}</div>
      <div style="margin-top:14px;">
        ${simpleBand("Acne probability", d.acne_probability)}
        ${simpleBand("Dark circle probability", d.darkcircle_probability)}
      </div>
      <div class="disclaimer-note">${d.disclaimer}</div>
    </div>
  `);
  document.getElementById("scanResults").appendChild(card);
}

// ============================================
// PRODUCT SCAN
// ============================================
const productDropzone = document.getElementById("productDropzone");
const productFile = document.getElementById("productFile");
productDropzone.addEventListener("click", () => productFile.click());
productFile.addEventListener("change", () => {
  document.getElementById("productFilename").textContent = productFile.files[0]?.name || "";
});

document.getElementById("productSubmit").addEventListener("click", async () => {
  if (!productFile.files[0]) { setStatus("productStatus", "Please choose a label photo first.", true); return; }

  const btn = document.getElementById("productSubmit");
  btn.disabled = true;
  setStatus("productStatus", "Reading label...");
  document.getElementById("productResults").innerHTML = "";

  const skinType = document.getElementById("productSkinType").value;
  const params = new URLSearchParams();
  if (skinType) params.set("skin_type", skinType);

  const formData = new FormData();
  formData.append("file", productFile.files[0]);

  try {
    const data = await callApi(`/api/product/scan-label?${params.toString()}`, { method: "POST", body: formData });
    renderProductResults(data);
    setStatus("productStatus", "Done.");
  } catch (e) {
    setStatus("productStatus", e.message, true);
  } finally {
    btn.disabled = false;
  }
});

function renderProductResults(d) {
  const rows = d.ingredients.map(ing => {
    const riskBadge = !ing.has_risk_data
      ? `<span class="badge warn">no risk data yet</span>`
      : ing.is_common_allergen
        ? `<span class="badge risk">allergen</span>`
        : (ing.comedogenic_rating >= 3 ? `<span class="badge warn">comedogenic ${ing.comedogenic_rating}</span>` : `<span class="badge ok">low risk</span>`);
    return `<div class="ingredient-row">
      <span>${ing.name}${ing.estimated_tier ? ` <span style="color:var(--ink-soft); font-size:12px;">(${ing.estimated_tier})</span>` : ""}</span>
      ${riskBadge}
    </div>`;
  }).join("");

  const flags = d.risk_summary.flags.length
    ? `<ul class="flag-list">${d.risk_summary.flags.map(f => `<li>${f}</li>`).join("")}</ul>`
    : `<p style="font-size:14px; color:var(--sage);">No major flags detected.</p>`;

  const card = el(`
    <div class="result-card">
      <h3>Ingredient Analysis</h3>
      <p style="font-size:13px; color:var(--ink-soft);">
        ${d.risk_summary.ingredients_recognized} ingredients recognized,
        ${d.risk_summary.ingredients_with_risk_data} with known risk data.
      </p>
      ${flags}
      <div style="margin-top:14px;">${rows}</div>
      <div class="disclaimer-note">${d.risk_summary.disclaimer}</div>
    </div>
  `);
  document.getElementById("productResults").appendChild(card);
}

// ============================================
// RECOMMENDATIONS
// ============================================
const recAcne = document.getElementById("recAcne");
const recDark = document.getElementById("recDark");
recAcne.addEventListener("input", () => document.getElementById("recAcneVal").textContent = parseFloat(recAcne.value).toFixed(1));
recDark.addEventListener("input", () => document.getElementById("recDarkVal").textContent = parseFloat(recDark.value).toFixed(1));

document.getElementById("recSubmit").addEventListener("click", async () => {
  const btn = document.getElementById("recSubmit");
  btn.disabled = true;
  setStatus("recStatus", "Finding matches...");
  document.getElementById("recResults").innerHTML = "";

  const params = new URLSearchParams({
    skin_type: document.getElementById("recSkinType").value,
    acne_probability: recAcne.value,
    darkcircle_probability: recDark.value,
  });

  try {
    const data = await callApi(`/api/recommend/products?${params.toString()}`);
    renderRecommendations(data);
    setStatus("recStatus", `${data.count} matches found.`);
  } catch (e) {
    setStatus("recStatus", e.message, true);
  } finally {
    btn.disabled = false;
  }
});

function renderRecommendations(d) {
  const container = document.getElementById("recResults");
  d.recommendations.forEach(p => {
    const reasons = p.match_reasons.map(r => `<li>${r}</li>`).join("");
    const card = el(`
      <div class="result-card">
        <h3>${p.brand} — ${p.product_name}</h3>
        ${confidenceBand("Match score", p.match_score, 0, 8, p.match_score, p.match_score)}
        <ul class="flag-list">${reasons}</ul>
        <p style="font-size:13px; color:var(--ink-soft);">${p.key_ingredients || ""} &middot; ${p.price_range || ""}</p>
        <div class="buy-links">
          <a href="${p.nykaa_search_url}" target="_blank">Search on Nykaa &rarr;</a>
          <a href="${p.purplle_search_url}" target="_blank">Search on Purplle &rarr;</a>
        </div>
        <div class="disclaimer-note">${p.disclaimer}</div>
      </div>
    `);
    container.appendChild(card);
  });
}

// ============================================
// SYMPTOM CHECK
// ============================================
const symSeverity = document.getElementById("symSeverity");
symSeverity.addEventListener("input", () => document.getElementById("symSeverityVal").textContent = symSeverity.value);

document.getElementById("symSubmit").addEventListener("click", async () => {
  const btn = document.getElementById("symSubmit");
  btn.disabled = true;
  setStatus("symStatus", "Analyzing...");
  document.getElementById("symResults").innerHTML = "";

  const payload = {
    body_area: document.getElementById("symBodyArea").value || "unspecified",
    duration_days: parseInt(document.getElementById("symDuration").value) || 0,
    symptoms_text: document.getElementById("symText").value,
    severity: parseInt(symSeverity.value),
    skin_type: document.getElementById("symSkinType").value || null,
    acknowledge_otc_disclaimer: document.getElementById("symOtcAck").checked,
    recent_products: document.getElementById("symProducts").value
      ? document.getElementById("symProducts").value.split(",").map(s => s.trim()).filter(Boolean)
      : null,
  };

  const useLocation = document.getElementById("symUseLocation").checked;

  const submit = async () => {
    try {
      const data = await callApi("/api/symptom/report", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      renderSymptomResults(data);
      setStatus("symStatus", "Done.");
    } catch (e) {
      setStatus("symStatus", e.message, true);
    } finally {
      btn.disabled = false;
    }
  };

  if (useLocation && navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      pos => {
        payload.latitude = pos.coords.latitude;
        payload.longitude = pos.coords.longitude;
        submit();
      },
      () => submit()  // fall back without location if permission denied
    );
  } else {
    submit();
  }
});

function renderSymptomResults(d) {
  const causes = d.possible_causes.length
    ? `<ul class="flag-list">${d.possible_causes.map(c =>
        `<li><strong>${c.possible_cause}</strong>${c.note ? ` — ${c.note}` : ""}</li>`
      ).join("")}</ul>`
    : `<p style="font-size:14px; color:var(--ink-soft);">No specific pattern matched — that's not unusual for mild or nonspecific symptoms.</p>`;

  let avoidHtml = "";
  if (d.proactive_avoid_list && d.proactive_avoid_list.ingredients_to_watch.length) {
    avoidHtml = `
      <div style="margin-top:16px; padding-top:16px; border-top:1px solid var(--line);">
        <strong style="font-size:14px;">For ${d.proactive_avoid_list.skin_type} skin, consider avoiding:</strong>
        <div style="margin-top:8px;">
          ${d.proactive_avoid_list.ingredients_to_watch.map(i => `<span class="badge warn">${i}</span>`).join("")}
        </div>
        <p style="font-size:12.5px; color:var(--ink-soft); margin-top:8px;">${d.proactive_avoid_list.reason}</p>
      </div>`;
  }

  let otcHtml = "";
  if (d.otc_suggestions) {
    if (!d.otc_suggestions.shown) {
      otcHtml = `<p style="font-size:13px; color:var(--ink-soft); margin-top:14px;">${d.otc_suggestions.note}</p>`;
    } else if (d.otc_suggestions.suggestions.length) {
      otcHtml = `
        <div style="margin-top:16px; padding-top:16px; border-top:1px solid var(--line);">
          <strong style="font-size:14px;">General OTC suggestions</strong>
          <ul class="flag-list">${d.otc_suggestions.suggestions.map(s => `<li>${s.suggestion}</li>`).join("")}</ul>
          <p class="disclaimer-note">${d.otc_suggestions.disclaimer}</p>
        </div>`;
    }
  }

  let trendHtml = "";
  if (d.local_trend && d.local_trend.available) {
    trendHtml = `<p style="font-size:13px; color:var(--ink-soft); margin-top:10px;">${d.local_trend.note}</p>`;
  }

  const card = el(`
    <div class="result-card">
      <div class="urgency-banner ${d.urgency_level}">${d.urgency_message}</div>
      <h3>Possible Patterns</h3>
      ${causes}
      ${d.weather_context_note ? `<p style="font-size:13px; color:var(--ink-soft); margin-top:10px;">${d.weather_context_note}</p>` : ""}
      ${d.product_history_note ? `<p style="font-size:13px; color:var(--ink-soft); margin-top:6px;">${d.product_history_note}</p>` : ""}
      ${trendHtml}
      ${avoidHtml}
      ${otcHtml}
      <div class="disclaimer-note">${d.disclaimer}</div>
    </div>
  `);
  document.getElementById("symResults").appendChild(card);
}

// ============================================
// BATCH PRODUCT SCAN (upload recent products one by one)
// ============================================
const batchDropzone = document.getElementById("batchDropzone");
const batchFile = document.getElementById("batchFile");
batchDropzone.addEventListener("click", () => batchFile.click());

batchFile.addEventListener("change", async () => {
  const file = batchFile.files[0];
  if (!file) return;
  document.getElementById("batchFilename").textContent = file.name;

  const skinType = document.getElementById("symSkinType").value;
  setStatus("batchStatus", `Scanning ${file.name}...`);

  const params = new URLSearchParams();
  if (skinType) params.set("skin_type", skinType);

  const formData = new FormData();
  formData.append("file", file);

  try {
    const data = await callApi(`/api/product/scan-label?${params.toString()}`, { method: "POST", body: formData });
    renderBatchProductResult(file.name, data, skinType);
    setStatus("batchStatus", "Add another photo, or move on when you're done.");
  } catch (e) {
    setStatus("batchStatus", `Failed to scan ${file.name}: ${e.message}`, true);
  }

  batchFile.value = "";  // allow re-selecting the same filename for the next product
});

function renderBatchProductResult(filename, data, skinType) {
  const flagged = data.risk_summary.flags.length > 0;
  const verdictBadge = flagged
    ? `<span class="badge risk">worth caution</span>`
    : `<span class="badge ok">no major flags</span>`;

  const flagsHtml = data.risk_summary.flags.length
    ? `<ul class="flag-list">${data.risk_summary.flags.map(f => `<li>${f}</li>`).join("")}</ul>`
    : `<p style="font-size:13px; color:var(--ink-soft);">No ingredients flagged for concern.</p>`;

  const card = el(`
    <div class="result-card">
      <h3>${filename} ${verdictBadge}</h3>
      ${flagsHtml}
      <p style="font-size:12px; color:var(--ink-soft); margin-top:8px;">
        ${data.risk_summary.ingredients_recognized} ingredients recognized, ${data.risk_summary.ingredients_with_risk_data} with known risk data.
      </p>
    </div>
  `);
  document.getElementById("batchResults").appendChild(card);
}