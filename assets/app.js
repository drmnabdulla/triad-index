document.addEventListener("DOMContentLoaded", () => {
  const slidersEl = document.getElementById("sliders");
  const caseGrid = document.getElementById("case-grid");

  // ---- Case studies (independent of the calculator) ----
  if (caseGrid) {
    CASE_STUDIES.forEach((cs) => {
      const scores = computeScores(cs.selections);
      const card = document.createElement("article");
      card.className = "case-card";
      card.innerHTML = `
        <div class="case-card__sector">${cs.sector}</div>
        <h3>${cs.name}</h3>
        <p class="case-card__blurb">${cs.blurb}</p>
        <div class="case-card__scores">
          <span><b>${scores.TRL}</b>/9 TRL</span>
          <span><b>${scores.MRL}</b>/10 MRL</span>
          <span><b>${scores.CRL}</b>/9 CRL</span>
        </div>
        <p class="case-card__takeaway">${cs.takeaway}</p>
        <a class="btn btn--ghost" href="calculator.html?case=${cs.id}">Load into calculator &rarr;</a>
      `;
      caseGrid.appendChild(card);
    });
  }

  if (!slidersEl) return; // not the calculator page

  const state = {};
  Object.keys(CATEGORIES).forEach((cat) => { state[cat] = 1; });

  const gaugesEl = document.getElementById("gauges");
  const nextStepsEl = document.getElementById("next-steps");
  const criticalGapsEl = document.getElementById("critical-gaps");
  const benchmarkBody = document.getElementById("benchmark-body");
  let radarChart = null;

  Object.entries(CATEGORIES).forEach(([cat, def]) => {
    const row = document.createElement("div");
    row.className = "slider-row";
    row.innerHTML = `
      <div class="slider-row__head">
        <span class="slider-row__axis">${def.axis}</span>
        <span class="slider-row__name">${cat}</span>
        <span class="slider-row__level" id="lvl-${slug(cat)}">1 / ${def.max}</span>
      </div>
      <input type="range" min="1" max="${def.max}" value="1" step="1" id="range-${slug(cat)}" />
      <p class="slider-row__desc" id="desc-${slug(cat)}">${def.levels[0]}</p>
    `;
    slidersEl.appendChild(row);

    const input = row.querySelector(`#range-${slug(cat)}`);
    input.addEventListener("input", (e) => {
      const val = Number(e.target.value);
      state[cat] = val;
      document.getElementById(`lvl-${slug(cat)}`).textContent = `${val} / ${def.max}`;
      document.getElementById(`desc-${slug(cat)}`).textContent = def.levels[val - 1];
      render();
    });
  });

  function slug(s) {
    return s.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");
  }

  function gaugeSVG(label, value, max, color) {
    const pct = Math.max(0, Math.min(1, value / max));
    const r = 40, c = 2 * Math.PI * r;
    const offset = c * (1 - pct);
    return `
      <div class="gauge">
        <svg viewBox="0 0 100 100" class="gauge__svg">
          <circle cx="50" cy="50" r="${r}" class="gauge__track" />
          <circle cx="50" cy="50" r="${r}" class="gauge__fill" stroke="${color}"
            stroke-dasharray="${c}" stroke-dashoffset="${offset}"
            transform="rotate(-90 50 50)" />
          <text x="50" y="46" class="gauge__value" text-anchor="middle">${value}</text>
          <text x="50" y="64" class="gauge__max" text-anchor="middle">/ ${max}</text>
        </svg>
        <div class="gauge__label">${label}</div>
      </div>
    `;
  }

  function renderGauges(scores) {
    gaugesEl.innerHTML =
      gaugeSVG("Technology (TRL)", scores.TRL, AXIS_MAX.TRL, "#2f6fed") +
      gaugeSVG("Manufacturing (MRL)", scores.MRL, AXIS_MAX.MRL, "#0d9488") +
      gaugeSVG("Commercial (CRL)", scores.CRL, AXIS_MAX.CRL, "#d97706");
  }

  function renderNextSteps(scores) {
    const rows = [
      ["TRL", TRL_RULES, scores.TRL, AXIS_MAX.TRL],
      ["MRL", MRL_RULES, scores.MRL, AXIS_MAX.MRL],
      ["CRL", CRL_RULES, scores.CRL, AXIS_MAX.CRL]
    ];
    nextStepsEl.innerHTML = rows.map(([axis, rules, cur, max]) => {
      if (cur >= max) {
        return `<div class="next-step"><h4>${axis}</h4><p class="next-step__done">At maximum (${max}). No further gate to clear.</p></div>`;
      }
      const step = nextStep(state, rules, cur);
      const gapEntries = Object.entries(step.gaps);
      const gapHTML = gapEntries.length
        ? `<ul>${gapEntries.map(([cat, [c, r]]) => `<li>${cat}: currently ${c}, needs ${r}</li>`).join("")}</ul>`
        : `<p class="next-step__done">Requirements already met — level should update.</p>`;
      return `<div class="next-step"><h4>${axis} &rarr; target ${step.target}</h4>${gapHTML}</div>`;
    }).join("");
  }

  function renderCriticalGaps(scores) {
    const gaps = identifyCriticalGaps(state, scores).slice(0, 4);
    if (!gaps.length) {
      criticalGapsEl.innerHTML = `<p class="next-step__done">No critical gaps — every gate up to your current maximums is satisfied.</p>`;
      return;
    }
    criticalGapsEl.innerHTML = `<ol>${gaps.map((g) =>
      `<li><strong>${g.category}</strong> <span class="tag">${g.axis}</span> — level ${g.current} &rarr; ${g.required}
       <span class="impact">impact ${g.impact.toFixed(1)}</span></li>`
    ).join("")}</ol>`;
  }

  function renderBenchmark(scores) {
    benchmarkBody.innerHTML = Object.entries(BENCHMARKS).map(([stage, b]) => {
      const d = (a) => {
        const diff = scores[a] - b[a];
        const cls = diff >= 0 ? "diff diff--pos" : "diff diff--neg";
        return `<span class="${cls}">${diff >= 0 ? "+" : ""}${diff}</span>`;
      };
      return `<tr><td>${stage}</td><td>${b.TRL}</td><td>${b.MRL}</td><td>${b.CRL}</td>
        <td>${d("TRL")} / ${d("MRL")} / ${d("CRL")}</td></tr>`;
    }).join("");
  }

  function renderRadar() {
    const labels = Object.keys(CATEGORIES);
    const data = labels.map((cat) => state[cat] / CATEGORIES[cat].max);
    const ctx = document.getElementById("radar-canvas").getContext("2d");
    const cfg = {
      type: "radar",
      data: {
        labels,
        datasets: [{
          label: "Normalized maturity",
          data,
          backgroundColor: "rgba(47,111,237,0.12)",
          borderColor: "#2f6fed",
          pointBackgroundColor: "#2f6fed",
          borderWidth: 2
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        scales: {
          r: {
            min: 0, max: 1, ticks: { display: false, stepSize: 0.25 },
            grid: { color: "#e3e7eb" },
            angleLines: { color: "#e3e7eb" },
            pointLabels: { color: "#57606a", font: { size: 10, family: "IBM Plex Mono" } }
          }
        },
        plugins: { legend: { display: false } }
      }
    };
    if (radarChart) {
      radarChart.data = cfg.data;
      radarChart.update();
    } else {
      radarChart = new Chart(ctx, cfg);
    }
  }

  function render() {
    const scores = computeScores(state);
    renderGauges(scores);
    renderNextSteps(scores);
    renderCriticalGaps(scores);
    renderBenchmark(scores);
    renderRadar();
  }

  // If arriving from a case-study link (calculator.html?case=xyz), preload it.
  const params = new URLSearchParams(window.location.search);
  const caseId = params.get("case");
  if (caseId) {
    const cs = CASE_STUDIES.find((c) => c.id === caseId);
    if (cs) {
      Object.entries(cs.selections).forEach(([cat, val]) => {
        state[cat] = val;
        const input = document.getElementById(`range-${slug(cat)}`);
        if (input) input.value = val;
        const lvlEl = document.getElementById(`lvl-${slug(cat)}`);
        if (lvlEl) lvlEl.textContent = `${val} / ${CATEGORIES[cat].max}`;
        const descEl = document.getElementById(`desc-${slug(cat)}`);
        if (descEl) descEl.textContent = CATEGORIES[cat].levels[val - 1];
      });
    }
  }

  render();
});
